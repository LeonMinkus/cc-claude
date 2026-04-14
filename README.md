# cc - Claude Code Project Manager

Manage and launch [Claude Code](https://docs.anthropic.com/en/docs/claude-code) projects from your terminal.

## Install

```bash
pip install cc-claude
```

## Quick Start

```bash
# Open current directory in Claude Code (auto-tracks it)
cc .

# Open a specific path
cc ~/projects/my-app

# Interactive project selector (arrow keys + Enter)
cc

# Open a tracked project by name
cc open my-app

# Remove a project from tracking
cc rm my-app

# Delete all stored data
cc purge
```

## Commands

| Command | Description |
|---------|-------------|
| `cc` | Interactive project selector sorted by last access time |
| `cc <path>` | Auto-track + launch Claude Code in that directory |
| `cc list` | Same as `cc` — interactive project selector |
| `cc open <name>` | Open a tracked project by name |
| `cc rm <name>` | Remove a project from tracking |
| `cc purge` | Delete all stored data |

## Requirements

- Python 3.8+
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed and available as `claude`
