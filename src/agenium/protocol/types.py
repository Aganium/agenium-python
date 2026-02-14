"""
AGENIUM Protocol Types

Frame types for agent-to-agent messaging.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from ..core.types import generate_id


class MessageType(str, Enum):
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    ERROR = "error"


class ErrorCodes:
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    TIMEOUT = -32000
    SESSION_NOT_FOUND = -32001
    DUPLICATE_MESSAGE = -32002


@dataclass
class RequestFrame:
    """A request expecting a response."""

    type: MessageType = MessageType.REQUEST
    id: str = field(default_factory=generate_id)
    method: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class ResponseFrame:
    """Response to a request."""

    type: MessageType = MessageType.RESPONSE
    id: str = field(default_factory=generate_id)
    request_id: str = ""
    result: Any = None
    session_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class EventFrame:
    """One-way event (no response expected)."""

    type: MessageType = MessageType.EVENT
    id: str = field(default_factory=generate_id)
    event: str = ""
    data: Any = None
    session_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class ErrorFrame:
    """Error response."""

    type: MessageType = MessageType.ERROR
    id: str = field(default_factory=generate_id)
    request_id: str = ""
    code: int = ErrorCodes.INTERNAL_ERROR
    message: str = ""
    data: Any = None
    session_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


AnyFrame = RequestFrame | ResponseFrame | EventFrame | ErrorFrame


def create_request_frame(
    method: str,
    params: dict[str, Any] | None = None,
    session_id: str | None = None,
) -> RequestFrame:
    """Create a new request frame."""
    return RequestFrame(method=method, params=params or {}, session_id=session_id)


def create_response_frame(
    request_id: str,
    result: Any = None,
    session_id: str | None = None,
) -> ResponseFrame:
    """Create a response frame for a request."""
    return ResponseFrame(request_id=request_id, result=result, session_id=session_id)


def create_event_frame(
    event: str,
    data: Any = None,
    session_id: str | None = None,
) -> EventFrame:
    """Create a new event frame."""
    return EventFrame(event=event, data=data, session_id=session_id)


def create_error_frame(
    request_id: str,
    code: int = ErrorCodes.INTERNAL_ERROR,
    message: str = "",
    data: Any = None,
    session_id: str | None = None,
) -> ErrorFrame:
    """Create an error response frame."""
    return ErrorFrame(
        request_id=request_id, code=code, message=message, data=data, session_id=session_id
    )


def validate_frame(frame: AnyFrame) -> bool:
    """Validate a frame has required fields."""
    if not isinstance(frame, (RequestFrame, ResponseFrame, EventFrame, ErrorFrame)):
        return False
    if not frame.id:
        return False
    if isinstance(frame, RequestFrame) and not frame.method:
        return False
    if isinstance(frame, ResponseFrame) and not frame.request_id:
        return False
    if isinstance(frame, EventFrame) and not frame.event:
        return False
    if isinstance(frame, ErrorFrame) and not frame.request_id:
        return False
    return True
