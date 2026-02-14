"""Tests for core types and utilities."""

from agenium.core.types import (
    AgentID,
    Session,
    SessionState,
    generate_id,
    is_valid_agent_uri,
    parse_agent_uri,
    to_agent_uri,
    validate_agent_name,
)


class TestParseAgentURI:
    def test_valid_uri(self):
        assert parse_agent_uri("agent://alice") == "alice"

    def test_valid_uri_with_hyphens(self):
        assert parse_agent_uri("agent://my-agent") == "my-agent"

    def test_valid_uri_with_numbers(self):
        assert parse_agent_uri("agent://bot123") == "bot123"

    def test_invalid_no_prefix(self):
        assert parse_agent_uri("alice") is None

    def test_invalid_too_short(self):
        assert parse_agent_uri("agent://a") is None

    def test_invalid_leading_hyphen(self):
        assert parse_agent_uri("agent://-bad") is None

    def test_invalid_trailing_hyphen(self):
        assert parse_agent_uri("agent://bad-") is None

    def test_case_insensitive(self):
        assert parse_agent_uri("agent://MyAgent") == "myagent"


class TestValidateAgentName:
    def test_valid(self):
        assert validate_agent_name("alice") is True
        assert validate_agent_name("my-agent") is True
        assert validate_agent_name("bot123") is True

    def test_invalid(self):
        assert validate_agent_name("a") is False
        assert validate_agent_name("-bad") is False
        assert validate_agent_name("") is False
        assert validate_agent_name("a" * 51) is False


class TestToAgentURI:
    def test_basic(self):
        assert to_agent_uri("alice") == "agent://alice"

    def test_uppercase_lowered(self):
        assert to_agent_uri("Alice") == "agent://alice"


class TestIsValidAgentURI:
    def test_valid(self):
        assert is_valid_agent_uri("agent://alice") is True

    def test_invalid(self):
        assert is_valid_agent_uri("http://alice") is False


class TestGenerateID:
    def test_unique(self):
        ids = {generate_id() for _ in range(100)}
        assert len(ids) == 100

    def test_format(self):
        id_ = generate_id()
        assert len(id_) == 36  # UUID format


class TestSession:
    def test_create(self):
        agent = AgentID(name="test", public_key="abc")
        session = Session(id="s1", local_agent=agent, remote_agent=agent)
        assert session.state == SessionState.INITIATING
        assert session.id == "s1"
