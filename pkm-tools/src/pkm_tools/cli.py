"""Command-line interface for PKM tools."""

import sys
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from pkm_tools.config import PKMConfig
from pkm_tools.repo_sync import RepositorySync, RepositorySyncError
from pkm_tools.utils import setup_logging

console = Console()


@click.group()
@click.option("--log-level", default="INFO", help="Logging level")
@click.pass_context
def main(ctx: click.Context, log_level: str) -> None:
    """PKM Tools - Manage your Personal Knowledge Management repository."""
    setup_logging(log_level)
    ctx.ensure_object(dict)
    try:
        ctx.obj["config"] = PKMConfig()
        ctx.obj["sync"] = RepositorySync(ctx.obj["config"])
    except Exception as e:
        console.print(f"[red]Error initializing PKM tools: {e}[/red]")
        sys.exit(1)


@main.command()
@click.option(
    "--system",
    type=click.Choice(["thk", "man-oms", "panorama", "all"]),
    default="all",
    help="System to sync (default: all)",
)
@click.option("--branch", default="main", help="Branch to sync (default: main)")
@click.pass_context
def sync(ctx: click.Context, system: str, branch: str) -> None:
    """Sync repositories for a system or all systems."""
    sync_manager: RepositorySync = ctx.obj["sync"]

    try:
        if system == "all":
            console.print("[bold blue]Syncing all systems...[/bold blue]")
            results = sync_manager.sync_all_systems(branch)

            # Display results
            for system_result in results["systems"]:
                _display_sync_results(system_result)
        else:
            console.print(f"[bold blue]Syncing system: {system}[/bold blue]")
            results = sync_manager.sync_system(system, branch)
            _display_sync_results(results)

    except RepositorySyncError as e:
        console.print(f"[red]Sync failed: {e}[/red]")
        sys.exit(1)


@main.command()
@click.option(
    "--system",
    type=click.Choice(["thk", "man-oms", "panorama", "all"]),
    default="all",
    help="System to clone (default: all)",
)
@click.option("--branch", default="main", help="Branch to clone (default: main)")
@click.pass_context
def clone(ctx: click.Context, system: str, branch: str) -> None:
    """Clone repositories for a system or all systems."""
    sync_manager: RepositorySync = ctx.obj["sync"]

    try:
        if system == "all":
            console.print("[bold blue]Cloning all systems...[/bold blue]")
            results = sync_manager.clone_all_systems(branch)

            # Display results
            for system_result in results["systems"]:
                _display_clone_results(system_result)
        else:
            console.print(f"[bold blue]Cloning system: {system}[/bold blue]")
            results = sync_manager.clone_system(system, branch)
            _display_clone_results(results)

    except RepositorySyncError as e:
        console.print(f"[red]Clone failed: {e}[/red]")
        sys.exit(1)


@main.command()
@click.option(
    "--system",
    type=click.Choice(["thk", "man-oms", "panorama"]),
    required=True,
    help="System to check status",
)
@click.pass_context
def status(ctx: click.Context, system: str) -> None:
    """Show status of repositories for a system."""
    sync_manager: RepositorySync = ctx.obj["sync"]

    try:
        statuses = sync_manager.get_repository_status(system)

        table = Table(title=f"Repository Status - {system}")
        table.add_column("Repository", style="cyan")
        table.add_column("Exists", style="green")
        table.add_column("Branch", style="yellow")
        table.add_column("Dirty", style="red")
        table.add_column("Commit", style="blue")

        for status_info in statuses:
            table.add_row(
                status_info["name"],
                "" if status_info["exists"] else "",
                status_info.get("branch", "-"),
                "" if status_info.get("dirty") else "",
                status_info.get("commit", "-"),
            )

        console.print(table)

    except RepositorySyncError as e:
        console.print(f"[red]Status check failed: {e}[/red]")
        sys.exit(1)


@main.command()
@click.pass_context
def list_systems(ctx: click.Context) -> None:
    """List all available systems."""
    config: PKMConfig = ctx.obj["config"]

    systems = config.list_systems()

    if not systems:
        console.print("[yellow]No systems found[/yellow]")
        return

    table = Table(title="Available Systems")
    table.add_column("System", style="cyan")
    table.add_column("Path", style="blue")

    for system in systems:
        system_path = config.get_system_dir(system)
        table.add_row(system, str(system_path))

    console.print(table)


@main.command()
@click.option(
    "--system",
    type=click.Choice(["thk", "man-oms", "panorama"]),
    required=True,
    help="System to list repositories",
)
@click.pass_context
def list_repos(ctx: click.Context, system: str) -> None:
    """List configured repositories for a system."""
    config: PKMConfig = ctx.obj["config"]

    try:
        from pkm_tools.utils import read_repository_list

        repo_list_file = config.get_repository_list_file(system)
        repos = read_repository_list(repo_list_file)

        if not repos:
            console.print(f"[yellow]No repositories configured for {system}[/yellow]")
            return

        table = Table(title=f"Configured Repositories - {system}")
        table.add_column("#", style="cyan")
        table.add_column("Repository URL", style="blue")

        for idx, repo_url in enumerate(repos, 1):
            table.add_row(str(idx), repo_url)

        console.print(table)
        console.print(f"\n[dim]Configuration file: {repo_list_file}[/dim]")

    except Exception as e:
        console.print(f"[red]Failed to list repositories: {e}[/red]")
        sys.exit(1)


def _display_sync_results(results: dict) -> None:
    """Display sync results in a formatted table.

    Args:
        results: Sync results dictionary
    """
    system = results["system"]
    synced = results["synced"]
    failed = results["failed"]

    console.print(f"\n[bold]System: {system}[/bold]")
    console.print(f"Synced: [green]{synced}[/green] | Failed: [red]{failed}[/red]\n")

    if results["repos"]:
        table = Table()
        table.add_column("Repository", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Details", style="dim")

        for repo in results["repos"]:
            status_color = "green" if repo["status"] == "success" else "red"
            status_text = f"[{status_color}]{repo['status'].upper()}[/{status_color}]"
            details = repo.get("error", "")
            table.add_row(repo["name"], status_text, details)

        console.print(table)


def _display_clone_results(results: dict) -> None:
    """Display clone results in a formatted table.

    Args:
        results: Clone results dictionary
    """
    system = results["system"]
    cloned = results["cloned"]
    failed = results["failed"]

    console.print(f"\n[bold]System: {system}[/bold]")
    console.print(f"Cloned: [green]{cloned}[/green] | Failed: [red]{failed}[/red]\n")

    if results["repos"]:
        table = Table()
        table.add_column("Repository", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Details", style="dim")

        for repo in results["repos"]:
            status_color = "green" if repo["status"] == "success" else "red"
            status_text = f"[{status_color}]{repo['status'].upper()}[/{status_color}]"
            details = repo.get("error", "")
            table.add_row(repo["name"], status_text, details)

        console.print(table)


if __name__ == "__main__":
    main()
