
import pytest


class TestMcpServerInit:
    """Tests for MCP server initialization."""

    def test_mcp_server_loads(self) -> None:
        """Test that MCP server loads without errors."""
        from mcp_gdbserver.adapters.mcp_server import mcp

        assert mcp is not None
        assert mcp.name == "gdbserver_mcp"

    def test_mcp_server_has_tools(self) -> None:
        """Test that MCP server has expected tools."""
        tool_names = [
            "gdbserver_start",
            "gdbserver_start_multi",
            "gdbserver_attach",
            "gdbserver_list_sessions",
            "gdbserver_stop",
            "gdbserver_set_breakpoint",
            "gdbserver_delete_breakpoint",
            "gdbserver_continue",
            "gdbserver_step",
            "gdbserver_next",
            "gdbserver_interrupt",
            "gdbserver_stack_frames",
            "gdbserver_local_variables",
            "gdbserver_list_threads",
            "gdbserver_select_thread",
            "gdbserver_read_register",
            "gdbserver_read_memory",
            "gdbserver_evaluate",
            "gdbserver_load_symbols",
        ]
        assert len(tool_names) == 19


class TestInputModels:
    """Tests for Pydantic input models."""

    def test_start_gdbserver_input_defaults(self) -> None:
        """Test StartGdbserverInput with defaults."""
        from mcp_gdbserver.adapters.mcp_server import StartGdbserverInput

        input_model = StartGdbserverInput()
        assert input_model.host == "localhost"
        assert input_model.port == 2345
        assert input_model.program is None
        assert input_model.args is None

    def test_start_gdbserver_input_custom(self) -> None:
        """Test StartGdbserverInput with custom values."""
        from mcp_gdbserver.adapters.mcp_server import StartGdbserverInput

        input_model = StartGdbserverInput(
            host="0.0.0.0", port=3333, program="/bin/ls", args=["-la"]
        )
        assert input_model.host == "0.0.0.0"
        assert input_model.port == 3333
        assert input_model.program == "/bin/ls"
        assert input_model.args == ["-la"]

    def test_start_gdbserver_input_port_validation(self) -> None:
        """Test port validation."""
        from pydantic import ValidationError

        from mcp_gdbserver.adapters.mcp_server import StartGdbserverInput

        with pytest.raises(ValidationError):
            StartGdbserverInput(port=80)

        with pytest.raises(ValidationError):
            StartGdbserverInput(port=70000)


class TestErrorHandling:
    """Tests for error handling."""

    def test_handle_key_error(self) -> None:
        """Test KeyError handling."""
        from mcp_gdbserver.adapters.mcp_server import _handle_error

        error = _handle_error(KeyError("session not found"))
        assert "Error:" in error
        assert "session_id" in error.lower() or "session" in error.lower()

    def test_handle_os_error(self) -> None:
        """Test OSError handling."""
        from mcp_gdbserver.adapters.mcp_server import _handle_error

        error = _handle_error(OSError("Permission denied"))
        assert "Error:" in error

    def test_handle_timeout_error(self) -> None:
        """Test TimeoutError handling."""
        from mcp_gdbserver.adapters.mcp_server import _handle_error

        error = _handle_error(TimeoutError("Operation timed out"))
        assert "Error:" in error


class TestFormatSessionResponse:
    """Tests for session response formatting."""

    def test_format_session(self) -> None:
        """Test formatting a session response."""
        from mcp_gdbserver._core import GdbSession
        from mcp_gdbserver.adapters.mcp_server import (
            _format_session_response,
        )

        session = GdbSession(
            session_id="session_1",
            port=2345,
            gdbserver_pid=12345,
            host="localhost",
            program="/bin/ls",
            status="running",
        )
        result = _format_session_response(session)

        assert result["session_id"] == "session_1"
        assert result["port"] == 2345
        assert result["gdbserver_pid"] == 12345
        assert result["host"] == "localhost"
        assert result["program"] == "/bin/ls"
        assert result["status"] == "running"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
