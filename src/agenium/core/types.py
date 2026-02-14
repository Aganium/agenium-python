"""
AGENIUM Core Types

Fundamental data structures for agent-to-agent communication.
"""

from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# ============================================================================
# Agent Identity
# ============================================================================


@dataclass
class AgentID:
    """Unique identifier for an agent in the network."""

    name: str
    """Unique name (used in agent:// URI)."""

    public_key: str
    """Ed25519 public key (base64 encoded)."""

    description: str = ""
    """Optional human-readable description."""


@dataclass
class AgentToolRef:
    """A tool/function that an agent exposes."""

    name: str
    description: str = ""


@dataclass
class AgentEndpoint:
    """Resolved endpoint for connecting to an agent."""

    agent_id: AgentID
    url: str
    cert_fingerprint: Optional[str] = None
    protocol_versions: list[str] = field(default_factory=lambda: ["1.0"])
    capabilities: list[str] = field(default_factory=list)
    tools: list[AgentToolRef] = field(default_factory=list)
    ttl: int = 300
    resolved_at: float = field(default_factory=time.time)


# ============================================================================
# Session State Machine
# ============================================================================


class SessionState(str, Enum):
    """Session lifecycle states."""

    INITIATING = "initiating"
    HANDSHAKE = "handshake"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    RESUMING = "resuming"
    CLOSING = "closing"
    CLOSED = "closed"
    ERROR = "error"


@dataclass
class Session:
    """An active session between two agents."""

    id: str
    local_agent: AgentID
    remote_agent: AgentID
    state: SessionState = SessionState.INITIATING
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


# ============================================================================
# URI Parsing
# ============================================================================

_AGENT_NAME_RE = re.compile(r"^[a-z0-9\u0080-\uffff]([a-z0-9\u0080-\uffff-]*[a-z0-9\u0080-\uffff])?$")


def parse_agent_uri(uri: str) -> Optional[str]:
    """
    Parse agent:// URI and return the agent name.

    Format: agent://name
    - Length: 2-50 characters
    - Characters: lowercase alphanumeric, hyphens, unicode (IDN)
    - Must not start or end with hyphen

    Returns None if invalid.

    >>> parse_agent_uri("agent://alice")
    'alice'
    >>> parse_agent_uri("agent://my-agent")
    'my-agent'
    >>> parse_agent_uri("invalid") is None
    True
    """
    if not uri.startswith("agent://"):
        return None

    name = uri[8:].lower()

    if len(name) < 2 or len(name) > 50:
        return None

    if name.startswith("-") or name.endswith("-"):
        return None

    if not _AGENT_NAME_RE.match(name):
        return None

    return name


def is_valid_agent_uri(uri: str) -> bool:
    """Check if a string is a valid agent:// URI."""
    return parse_agent_uri(uri) is not None


def validate_agent_name(name: str) -> bool:
    """
    Validate an agent name (without the agent:// prefix).

    >>> validate_agent_name("alice")
    True
    >>> validate_agent_name("a")
    False
    """
    if len(name) < 2 or len(name) > 50:
        return False
    if name.startswith("-") or name.endswith("-"):
        return False
    return bool(_AGENT_NAME_RE.match(name.lower()))


def to_agent_uri(name: str) -> str:
    """Convert a name to agent:// URI format."""
    return f"agent://{name.lower()}"


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())
