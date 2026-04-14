<div align="center">

# cc

**The fastest way to switch between Claude Code projects.**

[![PyPI version](https://img.shields.io/pypi/v/cc-claude?color=%2334D058&label=pypi)](https://pypi.org/project/cc-claude/)
[![Python](https://img.shields.io/pypi/pyversions/cc-claude)](https://pypi.org/project/cc-claude/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![CI](https://github.com/LeonMinkus/cc-claude/actions/workflows/ci.yml/badge.svg)](https://github.com/LeonMinkus/cc-claude/actions/workflows/ci.yml)

</div>

---

Stop `cd`-ing around and typing `claude` over and over.  
**`cc`** remembers every project you open and lets you jump back instantly.

```
$ cc
? Select a project to open in Claude Code:
> my-app          ~/code/my-app            (2 min ago)
  api-server      ~/code/api-server        (1 hour ago)
  dotfiles        ~/dotfiles               (3 days ago)
```

## Install

```bash
pip install cc-claude
```

That's it. You now have the `cc` command.

## Usage

### Open a project (auto-tracked)

```bash
cc .                  # current directory
cc ~/projects/my-app  # any path
```

The first time you open a directory, `cc` remembers it.  
Next time, just pick it from the list.

### Switch between projects

```bash
cc
```

Arrow keys to navigate, type to filter, Enter to launch.  
Projects are sorted by **last access time** — your most recent work is always on top.

### Open by name

```bash
cc open my-app
```

### Clean up

```bash
cc rm my-app   # stop tracking a project
cc purge       # remove all stored data
```

## All Commands

| Command | Description |
|---------|-------------|
| `cc` | Interactive project selector, sorted by last access time |
| `cc <path>` | Auto-track a directory and launch Claude Code there |
| `cc list` | Same as `cc` — interactive selector |
| `cc open <name>` | Open a tracked project by name |
| `cc rm <name>` | Remove a project from tracking |
| `cc purge` | Delete all stored data |

## How It Works

1. You run `cc .` or `cc ~/some/project` — the directory is saved to a local JSON file and Claude Code launches
2. You run `cc` — all saved projects appear in an interactive list, sorted by when you last opened them
3. You pick one — Claude Code launches in that directory

Data is stored in your OS data directory (`~/.local/share/cc-claude/` on Linux, `~/Library/Application Support/cc-claude/` on macOS, `AppData\Local\cc-claude\` on Windows). Run `cc purge` to remove it.

## Requirements

- Python 3.8+
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI installed and available as `claude`

## License

[MIT](LICENSE)
