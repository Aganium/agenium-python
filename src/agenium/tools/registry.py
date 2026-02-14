"""
Tool Registry

Register, list, and invoke tools on an agent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional


ToolHandler = Callable[..., Awaitable[Any]]


@dataclass
class ToolDefinition:
    """Definition of a tool that an agent can expose."""

    name: str
    description: str = ""
    input_schema: Optional[dict[str, Any]] = None
    output_schema: Optional[dict[str, Any]] = None


@dataclass
class ToolContext:
    """Context passed to tool handlers."""

    session_id: str
    agent_name: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolInvokeResult:
    """Result of invoking a tool."""

    success: bool
    result: Any = None
    error: Optional[str] = None


class ToolRegistry:
    """Registry for agent tools."""

    def __init__(self) -> None:
        self._tools: dict[str, tuple[ToolDefinition, ToolHandler]] = {}

    def register(
        self,
        name: str,
        handler: ToolHandler,
        description: str = "",
        input_schema: dict[str, Any] | None = None,
        output_schema: dict[str, Any] | None = None,
    ) -> ToolDefinition:
        """Register a tool."""
        defn = ToolDefinition(
            name=name,
            description=description,
            input_schema=input_schema,
            output_schema=output_schema,
        )
        self._tools[name] = (defn, handler)
        return defn

    def unregister(self, name: str) -> bool:
        """Unregister a tool. Returns True if it existed."""
        return self._tools.pop(name, None) is not None

    def get(self, name: str) -> tuple[ToolDefinition, ToolHandler] | None:
        """Get a tool definition and handler by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[ToolDefinition]:
        """List all registered tools."""
        return [defn for defn, _ in self._tools.values()]

    async def invoke(
        self, name: str, params: dict[str, Any], context: ToolContext
    ) -> ToolInvokeResult:
        """
        Invoke a tool by name.

        Returns ToolInvokeResult with success/result or error.
        """
        entry = self._tools.get(name)
        if entry is None:
            return ToolInvokeResult(success=False, error=f"Tool not found: {name}")

        _, handler = entry
        try:
            result = await handler(**params)
            return ToolInvokeResult(success=True, result=result)
        except TypeError as e:
            return ToolInvokeResult(success=False, error=f"Invalid parameters: {e}")
        except Exception as e:
            return ToolInvokeResult(success=False, error=f"Tool error: {e}")

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools
