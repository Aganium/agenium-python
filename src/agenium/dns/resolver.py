"""
DNS Resolver

Resolves agent:// URIs to endpoints via the AGENIUM DNS system.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

import httpx

from ..core.types import parse_agent_uri, validate_agent_name


# ============================================================================
# Types
# ============================================================================


@dataclass
class AgentTool:
    """A tool advertised by an agent in DNS."""

    name: str
    description: str = ""
    input_schema: Optional[dict[str, Any]] = None
    output_schema: Optional[dict[str, Any]] = None


@dataclass
class ResolvedAgent:
    """Result of resolving an agent name via DNS."""

    name: str
    endpoint: str
    public_key: str
    tools: list[AgentTool] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    ttl: int = 300
    resolved_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def uri(self) -> str:
        return f"agent://{self.name}"


class DNSErrorCode(str, Enum):
    NOT_FOUND = "NOT_FOUND"
    INVALID_NAME = "INVALID_NAME"
    TIMEOUT = "TIMEOUT"
    SERVER_ERROR = "SERVER_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"


class DNSError(Exception):
    """Error during DNS resolution."""

    def __init__(self, code: DNSErrorCode, message: str):
        self.code = code
        super().__init__(f"[{code.value}] {message}")


# ============================================================================
# Cache
# ============================================================================


@dataclass
class _CacheEntry:
    agent: ResolvedAgent
    expires_at: float


# ============================================================================
# Resolver
# ============================================================================


@dataclass
class DNSResolverConfig:
    server: str = "185.204.169.26"
    timeout_ms: int = 10_000
    default_ttl_seconds: int = 300
    use_https: bool = False
    port: int = 3000


class DNSResolver:
    """
    Resolve agent:// URIs to endpoints via the AGENIUM DNS system.

    Usage:
        resolver = DNSResolver()
        agent = await resolver.resolve("my-agent")
        print(agent.endpoint)
    """

    def __init__(
        self,
        server: str = "185.204.169.26",
        port: int = 3000,
        timeout_ms: int = 10_000,
        use_https: bool = False,
    ):
        self._config = DNSResolverConfig(
            server=server,
            port=port,
            timeout_ms=timeout_ms,
            use_https=use_https,
        )
        self._cache: dict[str, _CacheEntry] = {}
        self._base_url = (
            f"{'https' if use_https else 'http'}://{server}:{port}"
        )

    async def resolve(self, name: str) -> ResolvedAgent:
        """
        Resolve an agent name to its endpoint.

        Args:
            name: Agent name (e.g. "my-agent") or URI ("agent://my-agent")

        Returns:
            ResolvedAgent with endpoint, tools, etc.

        Raises:
            DNSError on failure
        """
        # Handle both name and URI
        if name.startswith("agent://"):
            parsed = parse_agent_uri(name)
            if parsed is None:
                raise DNSError(DNSErrorCode.INVALID_NAME, f"Invalid URI: {name}")
            name = parsed

        if not validate_agent_name(name):
            raise DNSError(DNSErrorCode.INVALID_NAME, f"Invalid agent name: {name}")

        # Check cache
        cached = self._cache.get(name)
        if cached and cached.expires_at > time.time():
            return cached.agent

        # Resolve via HTTP
        try:
            async with httpx.AsyncClient(timeout=self._config.timeout_ms / 1000) as client:
                resp = await client.get(f"{self._base_url}/dns/lookup/{name}")

                if resp.status_code == 404:
                    raise DNSError(DNSErrorCode.NOT_FOUND, f"Agent not found: {name}")

                if resp.status_code != 200:
                    raise DNSError(
                        DNSErrorCode.SERVER_ERROR,
                        f"DNS server error: {resp.status_code}",
                    )

                data = resp.json()

        except httpx.TimeoutException:
            raise DNSError(DNSErrorCode.TIMEOUT, f"DNS lookup timed out for {name}")
        except httpx.ConnectError as e:
            raise DNSError(DNSErrorCode.NETWORK_ERROR, f"Cannot reach DNS server: {e}")
        except DNSError:
            raise
        except Exception as e:
            raise DNSError(DNSErrorCode.SERVER_ERROR, f"Unexpected error: {e}")

        # Parse response
        agent_data = data.get("agent", data)
        tools_raw = agent_data.get("tools", [])
        tools = [
            AgentTool(
                name=t.get("name", ""),
                description=t.get("description", ""),
                input_schema=t.get("inputSchema") or t.get("input_schema"),
                output_schema=t.get("outputSchema") or t.get("output_schema"),
            )
            for t in tools_raw
        ]

        agent = ResolvedAgent(
            name=name,
            endpoint=agent_data.get("endpoint", ""),
            public_key=agent_data.get("publicKey", agent_data.get("public_key", "")),
            tools=tools,
            capabilities=agent_data.get("capabilities", []),
            ttl=agent_data.get("ttl", self._config.default_ttl_seconds),
            metadata={
                k: v
                for k, v in agent_data.items()
                if k not in ("name", "endpoint", "publicKey", "public_key", "tools", "capabilities", "ttl")
            },
        )

        # Cache
        self._cache[name] = _CacheEntry(
            agent=agent,
            expires_at=time.time() + agent.ttl,
        )

        return agent

    async def resolve_uri(self, uri: str) -> ResolvedAgent:
        """Resolve a full agent:// URI."""
        return await self.resolve(uri)

    def clear_cache(self) -> None:
        """Clear the DNS cache."""
        self._cache.clear()

    def cache_size(self) -> int:
        """Number of entries in cache."""
        return len(self._cache)
