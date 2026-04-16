import os
import shutil
import subprocess
import sys

import click

from cc_claude.watchdog import create_watchdog


def launch_claude(project_path, notify=True):
    """Launch Claude Code in the given project directory."""
    claude_path = shutil.which("claude")
    if not claude_path:
        raise click.ClickException(
            "claude CLI not found in PATH.\n"
            "Install it from: https://docs.anthropic.com/en/docs/claude-code"
        )

    if not os.path.isdir(project_path):
        raise click.ClickException(f"Directory does not exist: {project_path}")

    project_name = os.path.basename(os.path.realpath(project_path))

    if sys.platform == "win32":
        proc = subprocess.Popen(["claude"], cwd=project_path, shell=True)
        watchdog = None
        if notify:
            watchdog = create_watchdog(project_name=project_name)
            if watchdog:
                watchdog.start()
        try:
            proc.wait()
        finally:
            if watchdog:
                watchdog.stop()
        sys.exit(proc.returncode)
    else:
        os.chdir(project_path)
        os.execvp("claude", ["claude"])
