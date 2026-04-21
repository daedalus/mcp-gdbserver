#!/usr/bin/env python3
"""
MCP Server for gdbserver remote debugging.

This server provides tools to interact with gdbserver for remote debugging,
including process management, breakpoint control, stepping, memory inspection,
and evaluation capabilities.
"""

from __future__ import annotations

import json
from typing import Any

import fastmcp
from pydantic import BaseModel, Field

from mcp_gdbserver._core import GdbDebugger, GdbSession

mcp = fastmcp.FastMCP("gdbserver_mcp")

DEBUGGER: GdbDebugger | None = None


def _get_debugger() -> GdbDebugger:
    global DEBUGGER
    if DEBUGGER is None:
        DEBUGGER = GdbDebugger()
    return DEBUGGER


def _format_session_response(session: GdbSession) -> dict[str, Any]:
    return {
        "session_id": session.session_id,
        "status": session.status,
        "host": session.host,
        "port": session.port,
        "program": session.program,
        "gdbserver_pid": session.gdbserver_pid,
    }


def _handle_error(e: Exception) -> str:
    if isinstance(e, KeyError):
        return "Error: Session not found. Please check the session_id is correct."
    elif isinstance(e, OSError):
        return f"Error: OS error occurred: {str(e)}"
    elif isinstance(e, TimeoutError):
        return "Error: Operation timed out. Please try again."
    return f"Error: Unexpected error occurred: {type(e).__name__}"


class StartGdbserverInput(BaseModel):
    host: str = Field(
        default="localhost",
        description="Host to listen on (e.g., 'localhost', '0.0.0.0')",
    )
    port: int = Field(
        default=2345, description="TCP port to listen on", ge=1024, le=65535
    )
    program: str | None = Field(
        default=None, description="Path to executable to debug (e.g., '/path/to/myapp')"
    )
    args: list[str] | None = Field(
        default=None, description="Arguments to pass to the program"
    )


class StartGdbserverMultiInput(BaseModel):
    host: str = Field(default="localhost", description="Host to listen on")
    port: int = Field(
        default=2345, description="TCP port to listen on", ge=1024, le=65535
    )


class AttachToProcessInput(BaseModel):
    pid: int = Field(..., description="Process ID to attach to", ge=1)
    host: str = Field(default="localhost", description="Host to listen on")
    port: int = Field(
        default=2345, description="TCP port to listen on", ge=1024, le=65535
    )


class SessionIdInput(BaseModel):
    session_id: str = Field(
        ..., description="ID of the debugging session (e.g., 'session_1')"
    )


class SetBreakpointInput(BaseModel):
    session_id: str = Field(..., description="ID of the debugging session")
    location: str = Field(
        ..., description="Breakpoint location (e.g., 'main', 'foo.c:42', '*0x400520')"
    )
    condition: str | None = Field(
        default=None, description="Optional condition for the breakpoint"
    )


class DeleteBreakpointInput(BaseModel):
    session_id: str = Field(..., description="ID of the debugging session")
    breakpoint_id: int = Field(..., description="ID of breakpoint to delete")


class SelectThreadInput(BaseModel):
    session_id: str = Field(..., description="ID of the debugging session")
    thread_id: int = Field(..., description="Thread ID to select")


class ReadMemoryInput(BaseModel):
    session_id: str = Field(..., description="ID of the debugging session")
    address: str = Field(
        ..., description="Memory address (e.g., '0x400520', '&variable')"
    )
    offset: int = Field(default=0, description="Byte offset from address")
    length: int = Field(
        default=64, description="Number of bytes to read", ge=1, le=1024
    )


class ReadRegisterInput(BaseModel):
    session_id: str = Field(..., description="ID of the debugging session")
    reg: str | None = Field(
        default=None,
        description="Register name (e.g., 'rax', 'rip', 'rsp'). If None, reads all.",
    )


class EvaluateExpressionInput(BaseModel):
    session_id: str = Field(..., description="ID of the debugging session")
    expression: str = Field(
        ..., description="Expression to evaluate (e.g., 'x + 5', 'strlen(str)')"
    )


class LoadSymbolsInput(BaseModel):
    session_id: str = Field(..., description="ID of the debugging session")
    file: str = Field(..., description="Path to executable with symbols")


class StackFramesInput(BaseModel):
    session_id: str = Field(..., description="ID of the debugging session")
    max_depth: int = Field(
        default=10, description="Maximum number of frames to retrieve", ge=1, le=100
    )


class GetLocalVariablesInput(BaseModel):
    session_id: str = Field(..., description="ID of the debugging session")


@mcp.tool(
    name="gdbserver_start",
    annotations={
        "title": "Start gdbserver",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def gdbserver_start(params: StartGdbserverInput) -> str:
    """
    Start gdbserver to debug a program remotely on TCP port.

    This tool spawns a new gdbserver process that listens on the specified host
    and port, ready for a GDB client to connect. The session can then be used
    for breakpoint management, execution control, and inspection.

    Args:
        params (StartGdbserverInput): Validated input parameters containing:
            - host (str): Host to listen on, default 'localhost'
            - port (int): TCP port between 1024-65535, default 2345
            - program (Optional[str]): Path to executable to debug
            - args (Optional[list[str]]): Program arguments

    Returns:
        str: JSON-formatted string containing session information:

        Success response:
        {
            "session_id": str,      # Session ID (e.g., "session_1")
            "status": str,         # "running" or "exited"
            "host": str,          # Host address
            "port": int,          # TCP port
            "program": str,       # Path to executable or null
            "gdbserver_pid": int   # PID of gdbserver process
        }

        Error response:
        "Error: <error message>"

    Examples:
        - Use when: "Start debugging /path/to/myapp on port 3333" -> params with port=3333, program="/path/to/myapp"
        - Use when: "Start gdbserver on port 4444" -> params with port=4444
        - Don't use when: Need to attach to running process (use gdbserver_attach instead)
        - Don't use when: Need multi-process mode (use gdbserver_start_multi instead)
    """
    try:
        debugger = _get_debugger()
        session = debugger.start_gdbserver(
            host=params.host,
            port=params.port,
            program=params.program,
            args=params.args,
            multi=False,
        )
        return json.dumps(_format_session_response(session))
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="gdbserver_start_multi",
    annotations={
        "title": "Start gdbserver in Multi-Process Mode",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def gdbserver_start_multi(params: StartGdbserverMultiInput) -> str:
    """
    Start gdbserver in multi-process mode.

    In multi-process mode, gdbserver can debug multiple programs in the
    same session without exiting when one program finishes. Use this when
    you need to debug several processes sequentially.

    Args:
        params (StartGdbserverMultiInput): Validated input parameters containing:
            - host (str): Host to listen on
            - port (int): TCP port between 1024-65535

    Returns:
        str: JSON-formatted string containing session information:

        Success response:
        {
            "session_id": str,
            "status": str,
            "host": str,
            "port": int,
            "gdbserver_pid": int
        }

        Error response:
        "Error: <error message>"

    Examples:
        - Use when: "Start multi-process gdbserver on port 4444" -> params with port=4444
        - Don't use when: Need to debug single program (use gdbserver_start instead)
    """
    try:
        debugger = _get_debugger()
        session = debugger.start_gdbserver(
            host=params.host,
            port=params.port,
            multi=True,
        )
        return json.dumps(_format_session_response(session))
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="gdbserver_attach",
    annotations={
        "title": "Attach gdbserver to Running Process",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def gdbserver_attach(params: AttachToProcessInput) -> str:
    """
    Attach gdbserver to a running process.

    This tool spawns gdbserver and attaches it to an existing process by PID.
    You can then connect with GDB to debug the running process.

    Args:
        params (AttachToProcessInput): Validated input parameters containing:
            - pid (int): Process ID to attach to (must be >= 1)
            - host (str): Host to listen on
            - port (int): TCP port between 1024-65535

    Returns:
        str: JSON-formatted string containing session information:

        Success response:
        {
            "session_id": str,
            "status": str,
            "host": str,
            "port": int,
            "gdbserver_pid": int
        }

        Error response:
        "Error: <error message>"

    Examples:
        - Use when: "Attach to process 12345 on port 3456" -> params with pid=12345, port=3456
        - Don't use when: Need to start new program (use gdbserver_start instead)
    """
    try:
        debugger = _get_debugger()
        session = debugger.start_gdbserver(
            host=params.host,
            port=params.port,
            attach_pid=params.pid,
        )
        return json.dumps(_format_session_response(session))
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="gdbserver_list_sessions",
    annotations={
        "title": "List Debug Sessions",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def gdbserver_list_sessions() -> str:
    """
    List all active debugging sessions.

    This tool returns information about all current gdbserver sessions
    that are being managed by this MCP server.

    Returns:
        str: JSON-formatted string containing session list:

        Success response:
        [
            {
                "session_id": str,
                "status": str,
                "host": str,
                "port": int,
                "program": str,
                "gdbserver_pid": int
            }
        ]

        Error response:
        "Error: <error message>"

    Examples:
        - Use when: "What sessions are running?" -> no params needed
    """
    try:
        debugger = _get_debugger()
        sessions = debugger.list_sessions()
        return json.dumps(sessions)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="gdbserver_stop",
    annotations={
        "title": "Stop Debug Session",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def gdbserver_stop(params: SessionIdInput) -> str:
    """
    Stop a debugging session and terminate gdbserver.

    This tool stops the specified gdbserver session and terminates the
    gdbserver process. The session will no longer be available.

    Args:
        params (SessionIdInput): Validated input parameters containing:
            - session_id (str): ID of session to stop

    Returns:
        str: JSON-formatted string:

        Success response:
        {"session_id": str, "status": "stopped"}

        Error response:
        "Error: Session not found. Please check the session_id is correct."

    Examples:
        - Use when: "Stop session session_1" -> params with session_id="session_1"
    """
    try:
        debugger = _get_debugger()
        result = debugger.stop_session(params.session_id)
        return json.dumps(result)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="gdbserver_set_breakpoint",
    annotations={
        "title": "Set Breakpoint",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def gdbserver_set_breakpoint(params: SetBreakpointInput) -> str:
    """
    Set a breakpoint at the specified location.

    This tool connects to the gdbserver session and sets a breakpoint
    at the specified location using GDB/MI protocol.

    Args:
        params (SetBreakpointInput): Validated input parameters containing:
            - session_id (str): ID of the debugging session
            - location (str): Breakpoint location (function, file:line, or *address)
            - condition (Optional[str]): Optional condition

    Returns:
        str: JSON-formatted string containing breakpoint information:

        Success response:
        {
            "location": str,
            "result": dict  # GDB breakpoint-insert result
        }

        Error response:
        "Error: <error message>"

    Examples:
        - Use when: "Set breakpoint at main" -> params with location="main"
        - Use when: "Set breakpoint at line 42 in foo.c" -> params with location="foo.c:42"
        - Use when: "Set breakpoint at address 0x400520" -> params with location="*0x400520"
        - Use when: "Set conditional breakpoint at main when x > 5" -> params with location="main", condition="x > 5"
    """
    try:
        debugger = _get_debugger()
        debugger.get_session(params.session_id)
        gdb = debugger.connect_gdb(params.session_id)
        result = gdb.breakpoint_insert(params.location, params.condition)
        return json.dumps({"location": params.location, "result": result})
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="gdbserver_delete_breakpoint",
    annotations={
        "title": "Delete Breakpoint",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def gdbserver_delete_breakpoint(params: DeleteBreakpointInput) -> str:
    """
    Delete a breakpoint by ID.

    This tool removes a previously set breakpoint from the debug session.

    Args:
        params (DeleteBreakpointInput): Validated input parameters containing:
            - session_id (str): ID of the debugging session
            - breakpoint_id (int): ID of breakpoint to delete

    Returns:
        str: JSON-formatted string:

        Success response:
        {"breakpoint_id": int, "deleted": true}

        Error response:
        "Error: <error message>"

    Examples:
        - Use when: "Delete breakpoint 1" -> params with breakpoint_id=1
    """
    try:
        debugger = _get_debugger()
        debugger.get_session(params.session_id)
        gdb = debugger.connect_gdb(params.session_id)
        gdb.breakpoint_delete(params.breakpoint_id)
        return json.dumps({"breakpoint_id": params.breakpoint_id, "deleted": True})
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="gdbserver_continue",
    annotations={
        "title": "Continue Execution",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def gdbserver_continue(params: SessionIdInput) -> str:
    """
    Continue execution of the debugged program.

    This tool sends the continue command to the debugged program,
    allowing it to run until a breakpoint is hit or the
    program exits.

    Args:
        params (SessionIdInput): Validated input parameters containing:
            - session_id (str): ID of the debugging session

    Returns:
        str: JSON-formatted string containing GDB result:

        Success response:
        {"result": str}

        Error response:
        "Error: <error message>"

    Examples:
        - Use when: "Continue execution of session_1" -> params with session_id="session_1"
    """
    try:
        debugger = _get_debugger()
        debugger.get_session(params.session_id)
        gdb = debugger.connect_gdb(params.session_id)
        result = gdb.exec_continue()
        return json.dumps({"result": result})
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="gdbserver_step",
    annotations={
        "title": "Step One Instruction",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def gdbserver_step(params: SessionIdInput) -> str:
    """
    Step one instruction (stepping into function calls).

    This tool executes a single instruction, stepping into
    any function calls encountered.

    Args:
        params (SessionIdInput): Validated input parameters containing:
            - session_id (str): ID of the debugging session

    Returns:
        str: JSON-formatted string containing GDB result:

        Error response:
        "Error: <error message>"

    Examples:
        - Use when: "Step one instruction" -> params with session_id="session_1"
    """
    try:
        debugger = _get_debugger()
        debugger.get_session(params.session_id)
        gdb = debugger.connect_gdb(params.session_id)
        result = gdb.exec_step()
        return json.dumps({"result": result})
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="gdbserver_next",
    annotations={
        "title": "Execute One Instruction",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def gdbserver_next(params: SessionIdInput) -> str:
    """
    Execute one instruction (skipping function calls).

    This tool executes a single instruction, but does not step into
    function calls - they execute as a single unit.

    Args:
        params (SessionIdInput): Validated input parameters containing:
            - session_id (str): ID of the debugging session

    Returns:
        str: JSON-formatted string containing GDB result:

        Error response:
        "Error: <error message>"

    Examples:
        - Use when: "Step over one instruction" -> params with session_id="session_1"
    """
    try:
        debugger = _get_debugger()
        debugger.get_session(params.session_id)
        gdb = debugger.connect_gdb(params.session_id)
        result = gdb.exec_next()
        return json.dumps({"result": result})
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="gdbserver_interrupt",
    annotations={
        "title": "Interrupt Execution",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def gdbserver_interrupt(params: SessionIdInput) -> str:
    """
    Interrupt executing program.

    This tool sends an interrupt signal to the debugged program,
    causing it to stop at the current instruction.

    Args:
        params (SessionIdInput): Validated input parameters containing:
            - session_id (str): ID of the debugging session

    Returns:
        str: JSON-formatted string containing GDB result:

        Error response:
        "Error: <error message>"

    Examples:
        - Use when: "Stop the running program" -> params with session_id="session_1"
    """
    try:
        debugger = _get_debugger()
        debugger.get_session(params.session_id)
        gdb = debugger.connect_gdb(params.session_id)
        result = gdb.exec_interrupt()
        return json.dumps({"result": result})
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="gdbserver_stack_frames",
    annotations={
        "title": "Get Stack Frames",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def gdbserver_stack_frames(params: StackFramesInput) -> str:
    """
    Get stack frames from the debugged program.

    This tool retrieves the call stack frames, showing the
    execution path to the current location.

    Args:
        params (StackFramesInput): Validated input parameters containing:
            - session_id (str): ID of the debugging session
            - max_depth (int): Maximum frames to retrieve (1-100, default 10)

    Returns:
        str: JSON-formatted string containing stack frame information:

        Error response:
        "Error: <error message>"

    Examples:
        - Use when: "Show call stack" -> params with session_id="session_1"
    """
    try:
        debugger = _get_debugger()
        debugger.get_session(params.session_id)
        gdb = debugger.connect_gdb(params.session_id)
        result = gdb.stack_list_frames(params.max_depth)
        return json.dumps({"result": result})
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="gdbserver_local_variables",
    annotations={
        "title": "Get Local Variables",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def gdbserver_local_variables(params: GetLocalVariablesInput) -> str:
    """
    Get local variables in current frame.

    This tool retrieves all local variables in the current
    stack frame along with their values.

    Args:
        params (GetLocalVariablesInput): Validated input parameters containing:
            - session_id (str): ID of the debugging session

    Returns:
        str: JSON-formatted string containing variable information:

        Error response:
        "Error: <error message>"

    Examples:
        - Use when: "Show local variables" -> params with session_id="session_1"
    """
    try:
        debugger = _get_debugger()
        debugger.get_session(params.session_id)
        gdb = debugger.connect_gdb(params.session_id)
        result = gdb.stack_list_variables()
        return json.dumps({"result": result})
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="gdbserver_list_threads",
    annotations={
        "title": "List Threads",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def gdbserver_list_threads(params: SessionIdInput) -> str:
    """
    List all threads in the debugged program.

    This tool retrieves information about all threads
    running in the debugged process.

    Args:
        params (SessionIdInput): Validated input parameters containing:
            - session_id (str): ID of the debugging session

    Returns:
        str: JSON-formatted string containing thread information:

        Error response:
        "Error: <error message>"

    Examples:
        - Use when: "Show all threads" -> params with session_id="session_1"
    """
    try:
        debugger = _get_debugger()
        debugger.get_session(params.session_id)
        gdb = debugger.connect_gdb(params.session_id)
        result = gdb.thread_list()
        return json.dumps({"result": result})
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="gdbserver_select_thread",
    annotations={
        "title": "Select Thread",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def gdbserver_select_thread(params: SelectThreadInput) -> str:
    """
    Select a thread to debug.

    This tool switches the current context to the specified thread.

    Args:
        params (SelectThreadInput): Validated input parameters containing:
            - session_id (str): ID of the debugging session
            - thread_id (int): Thread ID to select

    Returns:
        str: JSON-formatted string containing result:

        Error response:
        "Error: <error message>"

    Examples:
        - Use when: "Switch to thread 2" -> params with thread_id=2
    """
    try:
        debugger = _get_debugger()
        debugger.get_session(params.session_id)
        gdb = debugger.connect_gdb(params.session_id)
        result = gdb.thread_select(params.thread_id)
        return json.dumps({"result": result})
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="gdbserver_read_register",
    annotations={
        "title": "Read Register",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def gdbserver_read_register(params: ReadRegisterInput) -> str:
    """
    Read register values.

    This tool reads the values of CPU registers. If no specific
    register is provided, it reads all registers.

    Args:
        params (ReadRegisterInput): Validated input parameters containing:
            - session_id (str): ID of the debugging session
            - reg (Optional[str]): Register name (e.g., 'rax', 'rip')

    Returns:
        str: JSON-formatted string containing register values:

        Error response:
        "Error: <error message>"

    Examples:
        - Use when: "Read all registers" -> params with reg=None
        - Use when: "Read RIP register" -> params with reg="rip"
    """
    try:
        debugger = _get_debugger()
        debugger.get_session(params.session_id)
        gdb = debugger.connect_gdb(params.session_id)
        if params.reg:
            result = gdb.register_read(params.reg)
        else:
            result = gdb.register_list()
        return json.dumps({"result": result})
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="gdbserver_read_memory",
    annotations={
        "title": "Read Memory",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def gdbserver_read_memory(params: ReadMemoryInput) -> str:
    """
    Read memory from the debugged program.

    This tool reads raw memory from the debugged process at the
    specified address.

    Args:
        params (ReadMemoryInput): Validated input parameters containing:
            - session_id (str): ID of the debugging session
            - address (str): Memory address (e.g., '0x400520')
            - offset (int): Byte offset from address (default 0)
            - length (int): Bytes to read (1-1024, default 64)

    Returns:
        str: JSON-formatted string containing memory contents:

        Error response:
        "Error: <error message>"

    Examples:
        - Use when: "Read 64 bytes from 0x600a00" -> params with address="0x600a00"
        - Use when: "Read 16 bytes from variable address" -> params with address="&buffer", length=16
    """
    try:
        debugger = _get_debugger()
        debugger.get_session(params.session_id)
        gdb = debugger.connect_gdb(params.session_id)
        result = gdb.memory_read(params.address, params.offset, params.length)
        return json.dumps({"result": result})
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="gdbserver_evaluate",
    annotations={
        "title": "Evaluate Expression",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def gdbserver_evaluate(params: EvaluateExpressionInput) -> str:
    """
    Evaluate an expression in the current context.

    This tool evaluates a C/C++ expression using the current
    program state, allowing you to call functions, perform
    arithmetic, and inspect variables.

    Args:
        params (EvaluateExpressionInput): Validated input parameters containing:
            - session_id (str): ID of the debugging session
            - expression (str): Expression to evaluate

    Returns:
        str: JSON-formatted string containing result:

        Error response:
        "Error: <error message>"

    Examples:
        - Use when: "What is x + 5?" -> params with expression="x + 5"
        - Use when: "Get string length" -> params with expression="strlen(buffer)"
        - Use when: "Call a function" -> params with expression="my_function(arg)"
    """
    try:
        debugger = _get_debugger()
        debugger.get_session(params.session_id)
        gdb = debugger.connect_gdb(params.session_id)
        result = gdb.data_evaluate_expression(params.expression)
        return json.dumps({"result": result})
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="gdbserver_load_symbols",
    annotations={
        "title": "Load Symbol File",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def gdbserver_load_symbols(params: LoadSymbolsInput) -> str:
    """
    Load a symbol file for debugging.

    This tool loads symbols from an executable file
    for debugging.

    Args:
        params (LoadSymbolsInput): Validated input parameters containing:
            - session_id (str): ID of the debugging session
            - file (str): Path to executable with symbols

    Returns:
        str: JSON-formatted string containing result:

        Error response:
        "Error: <error message>"

    Examples:
        - Use when: "Load symbols from /path/to/app" -> params with file="/path/to/app"
    """
    try:
        debugger = _get_debugger()
        debugger.get_session(params.session_id)
        gdb = debugger.connect_gdb(params.session_id)
        result = gdb.file_exec_and_symbols(params.file)
        return json.dumps({"result": result})
    except Exception as e:
        return _handle_error(e)


if __name__ == "__main__":
    mcp.run()
