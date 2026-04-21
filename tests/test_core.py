import pytest

from mcp_gdbserver import GdbDebugger


class TestGdbDebugger:
    """Tests for GdbDebugger class."""

    def test_version(self) -> None:
        """Test __version__ is defined."""
        from mcp_gdbserver import __version__

        assert __version__ == "0.1.0"

    def test_init(self) -> None:
        """Test GdbDebugger initialization."""
        debugger = GdbDebugger()

        assert debugger is not None
        assert hasattr(debugger, "_sessions")
        assert debugger._session_counter == 0

    def test_list_sessions_empty(self) -> None:
        """Test listing sessions when none exist."""
        debugger = GdbDebugger()
        sessions = debugger.list_sessions()

        assert sessions == []

    def test_start_gdbserver_basic(self) -> None:
        """Test starting gdbserver with minimal params."""
        debugger = GdbDebugger()
        session = debugger.start_gdbserver(port=23456)

        assert session is not None
        assert session.session_id == "session_1"
        assert session.port == 23456
        assert session.host == "localhost"
        assert session.status == "running"

    def test_start_gdbserver_with_program(self) -> None:
        """Test starting gdbserver with program."""
        debugger = GdbDebugger()
        session = debugger.start_gdbserver(port=23457, program="/bin/ls", args=["-la"])

        assert session is not None
        assert session.program == "/bin/ls"
        assert session.args == ["-la"]

    def test_start_gdbserver_multi(self) -> None:
        """Test starting gdbserver in multi mode."""
        debugger = GdbDebugger()
        session = debugger.start_gdbserver(port=23458, multi=True)

        assert session is not None
        assert session.status == "running"

    def test_start_gdbserver_with_attach(self) -> None:
        """Test starting gdbserver with attach."""
        debugger = GdbDebugger()
        session = debugger.start_gdbserver(port=23459, attach_pid=12345)

        assert session is not None
        assert session.status == "running"

    def test_get_session(self) -> None:
        """Test getting a session."""
        debugger = GdbDebugger()
        _ = debugger.start_gdbserver(port=23460)
        session = debugger.get_session("session_1")

        assert session is not None
        assert session.session_id == "session_1"

    def test_get_session_not_found(self) -> None:
        """Test getting non-existent session raises KeyError."""
        debugger = GdbDebugger()

        with pytest.raises(KeyError):
            debugger.get_session("session_999")

    def test_stop_session(self) -> None:
        """Test stopping a session."""
        debugger = GdbDebugger()
        _ = debugger.start_gdbserver(port=23461)
        result = debugger.stop_session("session_1")

        assert result["session_id"] == "session_1"
        assert result["status"] == "stopped"

    def test_stop_session_not_found(self) -> None:
        """Test stopping non-existent session raises KeyError."""
        debugger = GdbDebugger()

        with pytest.raises(KeyError):
            debugger.stop_session("session_999")


class TestGdbSession:
    """Tests for GdbSession dataclass."""

    def test_session_creation(self) -> None:
        """Test creating a session."""
        from mcp_gdbserver._core import GdbSession

        session = GdbSession(session_id="session_x", port=12345)

        assert session.session_id == "session_x"
        assert session.port == 12345
        assert session.host == "localhost"
        assert session.status == "stopped"
        assert session.gdbserver_pid is None

    def test_session_with_all_fields(self) -> None:
        """Test creating a session with all fields."""
        from mcp_gdbserver._core import Breakpoint, GdbSession

        bp = Breakpoint(id=1, type="breakpoint", address="0x400520", function="main")
        session = GdbSession(
            session_id="session_x",
            port=12345,
            gdbserver_pid=99999,
            host="0.0.0.0",
            program="/bin/myapp",
            status="running",
            args=["--debug"],
            breakpoints=[bp],
        )

        assert session.session_id == "session_x"
        assert session.port == 12345
        assert session.gdbserver_pid == 99999
        assert session.host == "0.0.0.0"
        assert session.program == "/bin/myapp"
        assert session.status == "running"
        assert session.args == ["--debug"]
        assert len(session.breakpoints) == 1
        assert session.breakpoints[0].id == 1


class TestBreakpoint:
    """Tests for Breakpoint dataclass."""

    def test_breakpoint_creation(self) -> None:
        """Test creating a breakpoint."""
        from mcp_gdbserver._core import Breakpoint

        bp = Breakpoint(id=1, type="breakpoint", address="0x400520")

        assert bp.id == 1
        assert bp.type == "breakpoint"
        assert bp.address == "0x400520"
        assert bp.enabled is True
        assert bp.hit_count == 0


class TestFrame:
    """Tests for Frame dataclass."""

    def test_frame_creation(self) -> None:
        """Test creating a frame."""
        from mcp_gdbserver._core import Frame

        frame = Frame(level=0, address="0x400520", function="main")

        assert frame.level == 0
        assert frame.address == "0x400520"
        assert frame.function == "main"
        assert frame.filename is None
        assert frame.line is None


class TestImports:
    """Test module imports."""

    def test_import_gdb_debugger(self) -> None:
        """Test importing GdbDebugger."""
        from mcp_gdbserver import GdbDebugger

        assert GdbDebugger is not None

    def test_import_version(self) -> None:
        """Test importing version."""
        from mcp_gdbserver import __version__

        assert __version__ == "0.1.0"

    def test_all_exports(self) -> None:
        """Test __all__ exports."""
        from mcp_gdbserver import __all__

        assert "GdbDebugger" in __all__
        assert "__version__" in __all__


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
