# MCP GDBServer

MCP server for remote debugging with gdbserver.

## When to use this skill

Use this skill when you need to:
- Debug programs remotely
- Control process execution
- Set breakpoints
- Inspect memory and registers
- Analyze call stacks

## Tools

**Process Management:**
- `gdbserver_start` - Start gdbserver to debug a program
- `gdbserver_start_multi` - Start in multi-process mode
- `gdbserver_attach` - Attach to running process
- `gdbserver_list_sessions` - List active sessions
- `gdbserver_stop` - Stop debugging session

**Breakpoint Control:**
- `gdbserver_set_breakpoint` - Set breakpoint
- `gdbserver_delete_breakpoint` - Delete breakpoint

**Execution Control:**
- `gdbserver_continue` - Continue execution
- `gdbserver_step` - Step into functions
- `gdbserver_next` - Step over functions
- `gdbserver_interrupt` - Interrupt execution

**Inspection:**
- `gdbserver_stack_frames` - Get call stack
- `gdbserver_local_variables` - Get local variables
- `gdbserver_list_threads` - List threads
- `gdbserver_select_thread` - Switch thread
- `gdbserver_read_register` - Read CPU registers
- `gdbserver_read_memory` - Read memory
- `gdbserver_evaluate` - Evaluate expression

## Install

```bash
pip install mcp-gdbserver
```