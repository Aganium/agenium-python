"""Tests for tool registry."""

import asyncio

import pytest

from agenium.tools.registry import ToolContext, ToolRegistry


@pytest.fixture
def registry():
    return ToolRegistry()


class TestToolRegistry:
    def test_register(self, registry: ToolRegistry):
        async def handler(name: str) -> str:
            return f"hi {name}"

        defn = registry.register("greet", handler, description="Greet someone")
        assert defn.name == "greet"
        assert defn.description == "Greet someone"
        assert len(registry) == 1

    def test_unregister(self, registry: ToolRegistry):
        async def handler() -> str:
            return "ok"

        registry.register("test", handler)
        assert registry.unregister("test") is True
        assert registry.unregister("test") is False
        assert len(registry) == 0

    def test_list_tools(self, registry: ToolRegistry):
        async def h1() -> str:
            return "a"

        async def h2() -> str:
            return "b"

        registry.register("a", h1)
        registry.register("b", h2)
        tools = registry.list_tools()
        assert len(tools) == 2
        names = {t.name for t in tools}
        assert names == {"a", "b"}

    def test_contains(self, registry: ToolRegistry):
        async def handler() -> str:
            return "ok"

        registry.register("exists", handler)
        assert "exists" in registry
        assert "missing" not in registry

    @pytest.mark.asyncio
    async def test_invoke_success(self, registry: ToolRegistry):
        async def add(a: int, b: int) -> int:
            return a + b

        registry.register("add", add)
        ctx = ToolContext(session_id="s1", agent_name="test")
        result = await registry.invoke("add", {"a": 2, "b": 3}, ctx)
        assert result.success is True
        assert result.result == 5

    @pytest.mark.asyncio
    async def test_invoke_not_found(self, registry: ToolRegistry):
        ctx = ToolContext(session_id="s1", agent_name="test")
        result = await registry.invoke("missing", {}, ctx)
        assert result.success is False
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_invoke_error(self, registry: ToolRegistry):
        async def fail() -> None:
            raise ValueError("boom")

        registry.register("fail", fail)
        ctx = ToolContext(session_id="s1", agent_name="test")
        result = await registry.invoke("fail", {}, ctx)
        assert result.success is False
        assert "boom" in result.error
