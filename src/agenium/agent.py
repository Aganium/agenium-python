"""
AGENIUM Agent

High-level agent API with DNS registration, tool system, and messaging.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional

import httpx

from .core.types import AgentID, Session, SessionState, generate_id, validate_agent_name
from .crypto.keys import KeyPair, generate_keypair
from .dns.resolver import DNSResolver, ResolvedAgent
from .protocol.types import (
    EventFrame,
    RequestFrame,
    create_event_frame,
    create_request_frame,
)
from .tools.registry import ToolContext, ToolDefinition, ToolHandler, ToolInvokeResult, ToolRegistry

logger = logging.getLogger("agenium")

DEFAULT_DNS_SERVER = "185.204.169.26"
DEFAULT_DNS_PORT = 3000


@dataclass
class AgentConfig:
    """Configuration for an Agent."""

    dns_server: str = DEFAULT_DNS_SERVER
    dns_port: int = DEFAULT_DNS_PORT
    data_dir: str = "~/.agenium"
    connection_timeout_ms: int = 30_000
    request_timeout_ms: int = 30_000
    persistence: bool = True


@dataclass
class ConnectResult:
    """Result of connecting to another agent."""

    success: bool
    session: Optional[Session] = None
    error: Optional[str] = None


@dataclass
class DNSRegistrationResult:
    """Result of DNS registration."""

    success: bool
    domain: Optional[str] = None
    tools: int = 0
    error: Optional[str] = None


class Agent:
    """
    AGENIUM Agent — high-level API for agent-to-agent communication.

    Usage:
        agent = Agent("my-agent")

        @agent.tool("greet", description="Greet someone")
        async def greet(name: str) -> str:
            return f"Hello, {name}!"

        await agent.start(port=8443)
        await agent.register(api_key="dom_xxx")
    """

    def __init__(self, name: str, config: AgentConfig | None = None):
        if not validate_agent_name(name):
            raise ValueError(
                f"Invalid agent name: {name!r}. "
                "Must be 2-50 chars, lowercase alphanumeric/hyphens, no leading/trailing hyphen."
            )

        self._name = name
        self._config = config or AgentConfig()
        self._keys = generate_keypair()
        self._identity = AgentID(
            name=name,
            public_key=self._keys.public_key_b64,
            description=f"AGENIUM Agent: {name}",
        )
        self._tool_registry = ToolRegistry()
        self._resolver = DNSResolver(
            server=self._config.dns_server,
            port=self._config.dns_port,
        )
        self._sessions: dict[str, Session] = {}
        self._dns_api_key: str | None = None
        self._is_running = False
        self._request_handlers: dict[str, Callable] = {}
        self._event_handlers: dict[str, Callable] = {}

    # ========================================================================
    # Properties
    # ========================================================================

    @property
    def name(self) -> str:
        """Agent name."""
        return self._name

    @property
    def uri(self) -> str:
        """Agent URI (agent://name)."""
        return f"agent://{self._name}"

    @property
    def identity(self) -> AgentID:
        """Agent identity."""
        return self._identity

    @property
    def keys(self) -> KeyPair:
        """Agent key pair."""
        return self._keys

    @property
    def is_running(self) -> bool:
        """Whether the agent is running."""
        return self._is_running

    @property
    def sessions(self) -> dict[str, Session]:
        """Active sessions."""
        return dict(self._sessions)

    @property
    def tools(self) -> list[ToolDefinition]:
        """Registered tools."""
        return self._tool_registry.list_tools()

    # ========================================================================
    # Tool Registration
    # ========================================================================

    def tool(
        self,
        name: str,
        description: str = "",
        input_schema: dict[str, Any] | None = None,
        output_schema: dict[str, Any] | None = None,
    ) -> Callable:
        """
        Decorator to register a tool.

        Usage:
            @agent.tool("greet", description="Greet someone")
            async def greet(name: str) -> str:
                return f"Hello, {name}!"
        """

        def decorator(fn: ToolHandler) -> ToolHandler:
            self._tool_registry.register(
                name=name,
                handler=fn,
                description=description,
                input_schema=input_schema,
                output_schema=output_schema,
            )
            return fn

        return decorator

    def register_tool(
        self,
        name: str,
        handler: ToolHandler,
        description: str = "",
        input_schema: dict[str, Any] | None = None,
        output_schema: dict[str, Any] | None = None,
    ) -> ToolDefinition:
        """Register a tool programmatically."""
        return self._tool_registry.register(
            name=name,
            handler=handler,
            description=description,
            input_schema=input_schema,
            output_schema=output_schema,
        )

    async def invoke_tool(
        self, name: str, params: dict[str, Any], session_id: str = ""
    ) -> ToolInvokeResult:
        """Invoke a local tool."""
        ctx = ToolContext(session_id=session_id, agent_name=self._name)
        return await self._tool_registry.invoke(name, params, ctx)

    # ========================================================================
    # Lifecycle
    # ========================================================================

    async def start(self, port: int = 8443, host: str = "0.0.0.0") -> None:
        """
        Start the agent.

        In this initial release, this initializes the agent state.
        Full HTTP/2+mTLS server will be added in a future version.
        """
        if self._is_running:
            return

        self._is_running = True
        logger.info("Agent %s started (port=%d)", self._name, port)

    async def stop(self) -> None:
        """Gracefully stop the agent."""
        if not self._is_running:
            return

        # Close all sessions
        for session in self._sessions.values():
            session.state = SessionState.CLOSED

        self._sessions.clear()
        self._is_running = False
        logger.info("Agent %s stopped", self._name)

    # ========================================================================
    # DNS Registration
    # ========================================================================

    async def register(
        self,
        api_key: str,
        host: str | None = None,
    ) -> DNSRegistrationResult:
        """
        Register this agent on the AGENIUM DNS system.

        Args:
            api_key: DNS API key (format: dom_xxx)
            host: Override endpoint host (auto-detected if not provided)
        """
        self._dns_api_key = api_key

        tools_payload = [
            {
                "name": t.name,
                "description": t.description,
                **({"inputSchema": t.input_schema} if t.input_schema else {}),
            }
            for t in self._tool_registry.list_tools()
        ]

        dns_url = (
            f"http://{self._config.dns_server}:{self._config.dns_port}"
        )

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{dns_url}/dns/register",
                    json={
                        "name": self._name,
                        "endpoint": host or "auto",
                        "publicKey": self._keys.public_key_b64,
                        "tools": tools_payload,
                    },
                    headers={"Authorization": f"Bearer {api_key}"},
                )

                if resp.status_code in (200, 201):
                    data = resp.json()
                    return DNSRegistrationResult(
                        success=True,
                        domain=f"agent://{self._name}",
                        tools=len(tools_payload),
                    )
                else:
                    return DNSRegistrationResult(
                        success=False,
                        error=f"Registration failed: {resp.status_code} {resp.text}",
                    )

        except Exception as e:
            return DNSRegistrationResult(success=False, error=str(e))

    # ========================================================================
    # Connection
    # ========================================================================

    async def resolve(self, target: str) -> ResolvedAgent:
        """Resolve an agent name or URI to its endpoint."""
        return await self._resolver.resolve(target)

    async def connect(self, target: str) -> ConnectResult:
        """
        Connect to another agent.

        Args:
            target: Agent name ("my-agent") or URI ("agent://my-agent")

        Returns:
            ConnectResult with session info
        """
        try:
            resolved = await self._resolver.resolve(target)
        except Exception as e:
            return ConnectResult(success=False, error=f"DNS resolution failed: {e}")

        session = Session(
            id=generate_id(),
            local_agent=self._identity,
            remote_agent=AgentID(
                name=resolved.name,
                public_key=resolved.public_key,
            ),
            state=SessionState.ACTIVE,
        )

        self._sessions[session.id] = session
        return ConnectResult(success=True, session=session)

    # ========================================================================
    # Messaging
    # ========================================================================

    async def send(
        self, session_id: str, event: str, data: Any = None
    ) -> bool:
        """Send an event to a session."""
        session = self._sessions.get(session_id)
        if not session:
            logger.warning("Session not found: %s", session_id)
            return False

        frame = create_event_frame(event=event, data=data, session_id=session_id)
        # In this initial release, frame is created but transport is stub
        logger.debug("Event sent: %s → %s", event, session.remote_agent.name)
        return True

    async def call_tool(
        self,
        session_id: str,
        tool_name: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """
        Call a tool on a remote agent.

        Args:
            session_id: Active session ID
            tool_name: Name of the remote tool
            params: Tool parameters

        Returns:
            Tool result

        Raises:
            RuntimeError if session not found or call fails
        """
        session = self._sessions.get(session_id)
        if not session:
            raise RuntimeError(f"Session not found: {session_id}")

        frame = create_request_frame(
            method="tool.invoke",
            params={"tool": tool_name, "input": params or {}},
            session_id=session_id,
        )

        # Stub: in full implementation, this sends via mTLS transport
        logger.debug(
            "Tool call: %s.%s(%s)", session.remote_agent.name, tool_name, params
        )
        return None

    # ========================================================================
    # Event Handlers
    # ========================================================================

    def on_request(self, method: str, handler: Callable) -> None:
        """Register a handler for incoming requests."""
        self._request_handlers[method] = handler

    def on_event(self, event: str, handler: Callable) -> None:
        """Register a handler for incoming events."""
        self._event_handlers[event] = handler

    # ========================================================================
    # Repr
    # ========================================================================

    def __repr__(self) -> str:
        state = "running" if self._is_running else "stopped"
        return f"Agent({self._name!r}, {state}, tools={len(self._tool_registry)})"
