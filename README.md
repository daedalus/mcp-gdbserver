# mcp-gdbserver

MCP server for remote debugging with gdbserver - provides full debugging capabilities including process management, breakpoint control, stepping, memory inspection, and more.

[![PyPI](https://img.shields.io/pypi/v/mcp-gdbserver.svg)](https://pypi.org/project/mcp-gdbserver/)
[![Python](https://img.shields.io/pypi/pyversions/mcp-gdbserver.svg)](https://pypi.org/project/mcp-gdbserver/)
[![Coverage](https://codecov.io/gh/daedalus/mcp-gdbserver/branch/main/graph/badge.svg)](https://codecov.io/gh/daedalus/mcp-gdbserver)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## Install

```bash
pip install mcp-gdbserver
```

## Usage

```python
from mcp_gdbserver import GdbDebugger

# Create debugger instance
debugger = GdbDebugger()

# Start gdbserver to debug a program
session = debugger.start_gdbserver(port=2345, program="/bin/myapp", args=["--debug"])

# Get session info
sessions = debugger.list_sessions()

# Stop session
debugger.stop_session("session_1")
```

## CLI

```bash
mcp-gdbserver --help
```

## Tools

The MCP server provides 19 debugging tools organized into 4 categories:

### Process Management
- `gdbserver_start` - Start gdbserver to debug a program remotely
- `gdbserver_start_multi` - Start gdbserver in multi-process mode
- `gdbserver_attach` - Attach to a running process
- `gdbserver_list_sessions` - List all active sessions
- `gdbserver_stop` - Stop a debugging session

### Breakpoint Control
- `gdbserver_set_breakpoint` - Set a breakpoint at a location
- `gdbserver_delete_breakpoint` - Delete a breakpoint

### Execution Control
- `gdbserver_continue` - Continue execution
- `gdbserver_step` - Step one instruction (into functions)
- `gdbserver_next` - Execute one instruction (over functions)
- `gdbserver_interrupt` - Interrupt execution

### Inspection
- `gdbserver_stack_frames` - Get call stack frames
- `gdbserver_local_variables` - Get local variables
- `gdbserver_list_threads` - List all threads
- `gdbserver_select_thread` - Switch to a thread
- `gdbserver_read_register` - Read CPU registers
- `gdbserver_read_memory` - Read memory contents
- `gdbserver_evaluate` - Evaluate an expression
- `gdbserver_load_symbols` - Load symbol file

## MCP Configuration

Add to your MCP config:

```json
{
  "mcpServers": {
    "mcp-gdbserver": {
      "command": "mcp-gdbserver",
      "env": {}
    }
  }
}
```

## Development

```bash
git clone https://github.com/daedalus/mcp-gdbserver.git
cd mcp-gdbserver
pip install -e ".[test]"

# run tests
pytest

# format
ruff format src/ tests/

# lint
ruff check src/ tests/

# type check
mypy src/
```

mcp-name: io.github.daedalus/mcp-gdbserver