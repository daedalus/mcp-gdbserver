# AGENTS.md — mcp-gdbserver

## Overview

MCP server for remote debugging with gdbserver. Provides tools to interact with gdbserver for remote debugging, including process management, breakpoint control, stepping, memory inspection, and expression evaluation.

## Commands

| Command | Description |
|---------|------------|
| `pytest` | Run test suite |
| `ruff format` | Format code |
| `ruff check` | Lint code |
| `mypy src/` | Type check |

## Development

```bash
# Setup
pip install -e ".[test]"

# Test
pytest

# Lint
ruff check src/ tests/
ruff format src/ tests/

# Type check
mypy src/
```

## Testing

The project uses pytest with pytest-cov for coverage. Tests are located in the `tests/` directory.

## Code Style

- Format: ruff
- Lint: ruff + mypy
- Docstrings: Google style

## Release

```bash
# Bump version
bumpversion patch  # or minor/major
git tag v<version>
git push && git push --tags
```

## MCP Server

```bash
# Install and use
pip install mcp-gdbserver
```

Add to your `mcp.json`:

```json
{
  "mcpServers": {
    "mcp-gdbserver": {
      "command": "mcp-gdbserver"
    }
  }
}
```
