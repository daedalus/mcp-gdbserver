name: mcp-gdbserver
description: >
  MCP server for remote debugging with gdbserver. Provides tools for process management, breakpoint control, execution control, and inspection.
  Triggers on keywords related to gdbserver, remote debugging, GDB, breakpoints, and debugging tools.
---

# mcp-gdbserver Skill

MCP server for remote debugging with gdbserver. Provides comprehensive debugging capabilities including process management, breakpoint control, stepping, memory inspection, and expression evaluation.

## Usage

After loading the skill, you can use all gdbserver debugging tools:

- Start gdbserver: `gdbserver_start`, `gdbserver_start_multi`, `gdbserver_attach`
- Control execution: `gdbserver_continue`, `gdbserver_step`, `gdbserver_next`, `gdbserver_interrupt`
- Manage breakpoints: `gdbserver_set_breakpoint`, `gdbserver_delete_breakpoint`
- Inspect state: `gdbserver_stack_frames`, `gdbserver_local_variables`, `gdbserver_list_threads`, `gdbserver_read_register`, `gdbserver_read_memory`, `gdbserver_evaluate`
- Session management: `gdbserver_list_sessions`, `gdbserver_stop`

## Examples

- "Start gdbserver to debug myapp on port 3333"
- "Set a breakpoint at main function"
- "Show me the call stack"
- "Read the rip register"
- "What is the value of variable x?"
- "Continue execution until breakpoint"