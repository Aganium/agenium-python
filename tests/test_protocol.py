"""Tests for protocol types."""

from agenium.protocol.types import (
    ErrorCodes,
    ErrorFrame,
    EventFrame,
    MessageType,
    RequestFrame,
    ResponseFrame,
    create_error_frame,
    create_event_frame,
    create_request_frame,
    create_response_frame,
    validate_frame,
)


class TestFrameCreation:
    def test_request(self):
        frame = create_request_frame("tool.invoke", {"tool": "greet"})
        assert frame.type == MessageType.REQUEST
        assert frame.method == "tool.invoke"
        assert frame.params == {"tool": "greet"}
        assert frame.id

    def test_response(self):
        frame = create_response_frame("req-1", result={"ok": True})
        assert frame.type == MessageType.RESPONSE
        assert frame.request_id == "req-1"
        assert frame.result == {"ok": True}

    def test_event(self):
        frame = create_event_frame("ping", data={"ts": 123})
        assert frame.type == MessageType.EVENT
        assert frame.event == "ping"
        assert frame.data == {"ts": 123}

    def test_error(self):
        frame = create_error_frame("req-1", ErrorCodes.METHOD_NOT_FOUND, "not found")
        assert frame.type == MessageType.ERROR
        assert frame.code == -32601
        assert frame.message == "not found"


class TestValidateFrame:
    def test_valid_request(self):
        frame = create_request_frame("test")
        assert validate_frame(frame) is True

    def test_invalid_request_no_method(self):
        frame = RequestFrame()
        assert validate_frame(frame) is False

    def test_valid_response(self):
        frame = create_response_frame("req-1")
        assert validate_frame(frame) is True

    def test_invalid_response_no_request_id(self):
        frame = ResponseFrame()
        assert validate_frame(frame) is False

    def test_valid_event(self):
        frame = create_event_frame("test")
        assert validate_frame(frame) is True

    def test_invalid_not_a_frame(self):
        assert validate_frame("not a frame") is False  # type: ignore
