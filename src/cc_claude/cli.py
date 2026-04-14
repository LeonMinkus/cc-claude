import os
from datetime import datetime, timezone

import click
import questionary
from rich.console import Console

from cc_claude.launcher import launch_claude
from cc_claude.store import ProjectStore

console = Console()


def _relative_time(iso_str):
    """Convert ISO timestamp to human-readable relative time."""
    try:
        dt = datetime.fromisoformat(iso_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        diff = now - dt
        seconds = int(diff.total_seconds())
        if seconds < 60:
            return "just now"
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes} min ago"
        hours = minutes // 60
        if hours < 24:
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        days = hours // 24
        if days < 30:
            return f"{days} day{'s' if days > 1 else ''} ago"
        months = days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    except (ValueError, TypeError):
        return "unknown"


def _open_project(store, project):
    """Touch the project timestamp and launch Claude Code."""
    store.touch_project(project["name"])
    console.print(
        f"  Opening [bold cyan]{project['name']}[/] in Claude Code..."
    )
    launch_claude(project["path"])


def _interactive_select(store):
    """Show interactive project selector."""
    projects = store.list_projects()
    if not projects:
        console.print(
            "[yellow]No projects tracked yet.[/]\n"
            "Run [bold]cc .[/] in a project directory to get started."
        )
        return

    # Build choices: name + path + relative time
    max_name = max(len(p["name"]) for p in projects)
    choices = []
    for p in projects:
        time_str = _relative_time(p.get("last_opened_at", ""))
        label = f"{p['name']:<{max_name}}  {p['path']}  ({time_str})"
        choices.append(questionary.Choice(title=label, value=p))

    selected = questionary.select(
        "Select a project to open in Claude Code:",
        choices=choices,
        pointer="›",
        use_shortcuts=False,
    ).ask()

    if selected is None:
        # User cancelled (Ctrl+C / ESC)
        return

    _open_project(store, selected)


class SmartGroup(click.Group):
    """Custom Click Group that routes path-like arguments to the 'open' command."""

    def parse_args(self, ctx, args):
        if (
            args
            and args[0] not in self.commands
            and (
                args[0] == "."
                or args[0].startswith("./")
                or args[0].startswith("../")
                or args[0].startswith("/")
                or args[0].startswith("~")
                or args[0].startswith(".\\")
                or args[0].startswith("..\\")
                or "\\" in args[0]
                or (len(args[0]) >= 2 and args[0][1] == ":")  # Windows drive letter
            )
        ):
            args = ["open"] + args
        return super().parse_args(ctx, args)


@click.group(cls=SmartGroup, invoke_without_command=True)
@click.pass_context
def main(ctx):
    """cc - Claude Code Project Manager

    Manage and launch Claude Code projects from your terminal.
    """
    if ctx.invoked_subcommand is None:
        store = ProjectStore()
        _interactive_select(store)


@main.command("list")
def list_cmd():
    """Interactive project selector (same as bare 'cc')."""
    store = ProjectStore()
    _interactive_select(store)


@main.command("open")
@click.argument("path_or_name")
def open_cmd(path_or_name):
    """Open a project in Claude Code.

    PATH_OR_NAME can be a directory path (auto-tracks it) or a tracked project name.
    """
    store = ProjectStore()

    # Check if it's a path (directory exists on disk)
    expanded = os.path.expanduser(path_or_name)
    resolved = os.path.realpath(expanded)
    if os.path.isdir(resolved):
        try:
            project = store.add_project(resolved)
        except ValueError as e:
            raise click.ClickException(str(e))
        _open_project(store, project)
        return

    # Otherwise treat as a project name
    project = store.get_project(path_or_name)
    if project is None:
        projects = store.list_projects()
        names = ", ".join(p["name"] for p in projects) if projects else "(none)"
        raise click.ClickException(
            f"Project '{path_or_name}' not found.\n"
            f"Tracked projects: {names}"
        )

    _open_project(store, project)


@main.command("rm")
@click.argument("name")
def rm_cmd(name):
    """Remove a project from tracking."""
    store = ProjectStore()
    if store.remove_project(name):
        console.print(f"  Removed [bold red]{name}[/] from tracking.")
    else:
        projects = store.list_projects()
        names = ", ".join(p["name"] for p in projects) if projects else "(none)"
        raise click.ClickException(
            f"Project '{name}' not found.\nTracked projects: {names}"
        )


@main.command("purge")
def purge_cmd():
    """Delete all stored project data."""
    store = ProjectStore()
    if not os.path.exists(store.data_dir):
        console.print("[yellow]Nothing to purge — no cc data found.[/]")
        return

    console.print(
        f"[bold red]This will delete all cc data at:[/] {store.data_dir}"
    )
    click.confirm("Are you sure?", abort=True)
    store.purge()
    console.print("[green]All cc data has been removed.[/]")
