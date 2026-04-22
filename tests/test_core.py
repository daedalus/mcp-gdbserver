from unittest.mock import MagicMock, Mock, patch

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

    @patch("mcp_gdbserver._core.subprocess.Popen")
    def test_start_gdbserver_basic(self, mock_popen: Mock) -> None:
        """Test starting gdbserver with minimal params."""
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        debugger = GdbDebugger()
        session = debugger.start_gdbserver(port=23456)

        assert session is not None
        assert session.session_id == "session_1"
        assert session.port == 23456
        assert session.host == "localhost"
        assert session.status == "running"

    @patch("mcp_gdbserver._core.subprocess.Popen")
    def test_start_gdbserver_with_program(self, mock_popen: Mock) -> None:
        """Test starting gdbserver with program."""
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        debugger = GdbDebugger()
        session = debugger.start_gdbserver(port=23457, program="/bin/ls", args=["-la"])

        assert session is not None
        assert session.program == "/bin/ls"
        assert session.args == ["-la"]

    @patch("mcp_gdbserver._core.subprocess.Popen")
    def test_start_gdbserver_multi(self, mock_popen: Mock) -> None:
        """Test starting gdbserver in multi mode."""
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        debugger = GdbDebugger()
        session = debugger.start_gdbserver(port=23458, multi=True)

        assert session is not None
        assert session.status == "running"

    @patch("mcp_gdbserver._core.subprocess.Popen")
    def test_start_gdbserver_with_attach(self, mock_popen: Mock) -> None:
        """Test starting gdbserver with attach."""
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        debugger = GdbDebugger()
        session = debugger.start_gdbserver(port=23459, attach_pid=12345)

        assert session is not None
        assert session.status == "running"

    @patch("mcp_gdbserver._core.subprocess.Popen")
    def test_get_session(self, mock_popen: Mock) -> None:
        """Test getting a session."""
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

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

    @patch("mcp_gdbserver._core.subprocess.Popen")
    def test_stop_session(self, mock_popen: Mock) -> None:
        """Test stopping a session."""
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

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


class TestGdbMI:
    """Tests for GdbMI class - parse results."""

    def test_parse_result_with_token(self) -> None:
        """Test parsing result with token."""
        import io

        from mcp_gdbserver._core import GdbMI

        stdin = io.StringIO()
        stdout = io.StringIO()
        stderr = io.StringIO()

        gdbmi = GdbMI(stdin, stdout, stderr)
        gdbmi._running = False
        result = gdbmi._parse_result("1^done")

        assert result["token"] == 1
        assert result["result"] == "^done"

    def test_parse_result_without_token(self) -> None:
        """Test parsing result without token."""
        import io

        from mcp_gdbserver._core import GdbMI

        stdin = io.StringIO()
        stdout = io.StringIO()
        stderr = io.StringIO()

        gdbmi = GdbMI(stdin, stdout, stderr)
        gdbmi._running = False
        result = gdbmi._parse_result("^done")

        assert result["result"] == "^done"

    def test_parse_result_raw(self) -> None:
        """Test parsing raw result."""
        import io

        from mcp_gdbserver._core import GdbMI

        stdin = io.StringIO()
        stdout = io.StringIO()
        stderr = io.StringIO()

        gdbmi = GdbMI(stdin, stdout, stderr)
        gdbmi._running = False
        result = gdbmi._parse_result("some random output")

        assert result["raw"] == "some random output"


class TestGdbDebuggerConnect:
    """Tests for GdbDebugger connect functionality."""

    @patch("mcp_gdbserver._core.subprocess.Popen")
    def test_connect_gdb(self, mock_popen: Mock) -> None:
        """Test connecting to gdb."""
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stderr = MagicMock()
        mock_popen.return_value = mock_process

        debugger = GdbDebugger()
        debugger.start_gdbserver(port=23456, program="/bin/test")
        gdb = debugger.connect_gdb("session_1")

        assert gdb is not None
        assert debugger.get_gdb("session_1") is gdb

    @patch("mcp_gdbserver._core.subprocess.Popen")
    def test_get_gdb_not_found(self, mock_popen: Mock) -> None:
        """Test getting non-existent gdb session."""
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        debugger = GdbDebugger()
        debugger.start_gdbserver(port=23456)

        assert debugger.get_gdb("nonexistent") is None


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
