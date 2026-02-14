"""Tests for the Agent class."""

import pytest

from agenium.agent import Agent, AgentConfig


class TestAgentCreation:
    def test_create(self):
        agent = Agent("test-agent")
        assert agent.name == "test-agent"
        assert agent.uri == "agent://test-agent"
        assert not agent.is_running

    def test_invalid_name(self):
        with pytest.raises(ValueError):
            Agent("a")  # too short

    def test_with_config(self):
        config = AgentConfig(dns_server="1.2.3.4", dns_port=5000)
        agent = Agent("my-agent", config=config)
        assert agent.name == "my-agent"

    def test_repr(self):
        agent = Agent("test-agent")
        assert "test-agent" in repr(agent)
        assert "stopped" in repr(agent)


class TestToolDecorator:
    def test_register_tool(self):
        agent = Agent("test-agent")

        @agent.tool("greet", description="Greet someone")
        async def greet(name: str) -> str:
            return f"Hello, {name}!"

        tools = agent.tools
        assert len(tools) == 1
        assert tools[0].name == "greet"
        assert tools[0].description == "Greet someone"

    def test_register_multiple_tools(self):
        agent = Agent("test-agent")

        @agent.tool("a")
        async def tool_a() -> str:
            return "a"

        @agent.tool("b")
        async def tool_b() -> str:
            return "b"

        assert len(agent.tools) == 2


class TestAgentLifecycle:
    @pytest.mark.asyncio
    async def test_start_stop(self):
        agent = Agent("test-agent")
        assert not agent.is_running

        await agent.start()
        assert agent.is_running

        await agent.stop()
        assert not agent.is_running

    @pytest.mark.asyncio
    async def test_double_start(self):
        agent = Agent("test-agent")
        await agent.start()
        await agent.start()  # should not error
        assert agent.is_running
        await agent.stop()

    @pytest.mark.asyncio
    async def test_invoke_local_tool(self):
        agent = Agent("test-agent")

        @agent.tool("add")
        async def add(a: int, b: int) -> int:
            return a + b

        result = await agent.invoke_tool("add", {"a": 3, "b": 4})
        assert result.success
        assert result.result == 7


class TestAgentCrypto:
    def test_has_keys(self):
        agent = Agent("test-agent")
        assert agent.keys.public_key_b64
        assert len(agent.keys.public_key_b64) > 10

    def test_unique_keys(self):
        a1 = Agent("agent-one")
        a2 = Agent("agent-two")
        assert a1.keys.public_key_b64 != a2.keys.public_key_b64
