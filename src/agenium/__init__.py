"""
AGENIUM — Local, Stateful Agent-to-Agent Communication SDK

Usage:
    from agenium import Agent, DNSResolver, AgentConfig
"""

__version__ = "0.1.0"

from .agent import Agent, AgentConfig, ConnectResult, DNSRegistrationResult
from .dns import DNSResolver, ResolvedAgent, AgentTool
from .protocol import (
    MessageType,
    RequestFrame,
    ResponseFrame,
    EventFrame,
    ErrorFrame,
    create_request_frame,
    create_response_frame,
    create_event_frame,
    create_error_frame,
)
from .tools import ToolRegistry, ToolDefinition
from .core import (
    AgentID,
    AgentEndpoint,
    SessionState,
    parse_agent_uri,
    validate_agent_name,
    to_agent_uri,
)

__all__ = [
    # Agent
    "Agent",
    "AgentConfig",
    "ConnectResult",
    "DNSRegistrationResult",
    # DNS
    "DNSResolver",
    "ResolvedAgent",
    "AgentTool",
    # Protocol
    "MessageType",
    "RequestFrame",
    "ResponseFrame",
    "EventFrame",
    "ErrorFrame",
    "create_request_frame",
    "create_response_frame",
    "create_event_frame",
    "create_error_frame",
    # Tools
    "ToolRegistry",
    "ToolDefinition",
    # Core
    "AgentID",
    "AgentEndpoint",
    "SessionState",
    "parse_agent_uri",
    "validate_agent_name",
    "to_agent_uri",
]
