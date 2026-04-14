import os
import shutil
import subprocess
import sys

import click


def launch_claude(project_path):
    """Launch Claude Code in the given project directory."""
    claude_path = shutil.which("claude")
    if not claude_path:
        raise click.ClickException(
            "claude CLI not found in PATH.\n"
            "Install it from: https://docs.anthropic.com/en/docs/claude-code"
        )

    if not os.path.isdir(project_path):
        raise click.ClickException(f"Directory does not exist: {project_path}")

    if sys.platform == "win32":
        result = subprocess.run(["claude"], cwd=project_path, shell=True)
        sys.exit(result.returncode)
    else:
        os.chdir(project_path)
        os.execvp("claude", ["claude"])
