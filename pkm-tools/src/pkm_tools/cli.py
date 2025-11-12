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
@click.option("--branch", default=None, help="Branch to sync (default: auto-detect from repository)")
@click.pass_context
def sync(ctx: click.Context, system: str, branch: Optional[str]) -> None:
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
    help="System to update (default: all)",
)
@click.option("--branch", default=None, help="Branch to update (default: auto-detect from repository)")
@click.pass_context
def update(ctx: click.Context, system: str, branch: Optional[str]) -> None:
    """Update repositories (clone if new, sync if existing)."""
    sync_manager: RepositorySync = ctx.obj["sync"]

    try:
        if system == "all":
            console.print("[bold blue]Updating all systems...[/bold blue]")
            results = sync_manager.update_all_systems(branch)

            # Display results
            for system_result in results["systems"]:
                _display_update_results(system_result)
        else:
            console.print(f"[bold blue]Updating system: {system}[/bold blue]")
            results = sync_manager.update_system(system, branch)
            _display_update_results(results)

    except RepositorySyncError as e:
        console.print(f"[red]Update failed: {e}[/red]")
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
@click.option(
    "--system",
    type=click.Choice(["thk", "man-oms", "panorama", "all"]),
    default="all",
    help="System to show branches for (default: all)",
)
@click.pass_context
def branches(ctx: click.Context, system: str) -> None:
    """Show current branch for each repository."""
    sync_manager: RepositorySync = ctx.obj["sync"]
    config: PKMConfig = ctx.obj["config"]

    try:
        if system == "all":
            systems = config.list_systems()
            for sys_name in systems:
                _display_branches(sync_manager, sys_name)
        else:
            _display_branches(sync_manager, system)

    except RepositorySyncError as e:
        console.print(f"[red]Failed to get branch information: {e}[/red]")
        sys.exit(1)


@main.command()
@click.argument("pr_url")
@click.pass_context
def checkout(ctx: click.Context, pr_url: str) -> None:
    """Checkout a branch from a BitBucket pull request URL.

    Requires BITBUCKET_TOKEN environment variable to be set.

    Example:
        pkm checkout https://mangit.maninvestments.com/projects/ETS/repos/tomahawk2/pull-requests/123
    """
    sync_manager: RepositorySync = ctx.obj["sync"]

    try:
        console.print(f"[blue]Fetching PR information...[/blue]")
        result = sync_manager.checkout_pr_branch(pr_url)

        console.print()
        console.print(f"[green]✓ Successfully checked out PR branch![/green]")
        console.print()
        console.print(f"[bold]PR Details:[/bold]")
        console.print(f"  PR #[cyan]{result['pr_id']}[/cyan]: {result['pr_title']}")
        console.print(f"  Author: [yellow]{result['author']}[/yellow]")
        console.print()
        console.print(f"[bold]Repository:[/bold]")
        console.print(f"  System: [cyan]{result['system']}[/cyan]")
        console.print(f"  Repository: [cyan]{result['repo']}[/cyan]")
        console.print(f"  Branch: [yellow]{result['branch']}[/yellow]")

    except RepositorySyncError as e:
        console.print(f"[red]Checkout failed: {e}[/red]")
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
            if repo["status"] == "success":
                # Check if changes were pulled
                had_changes = repo.get("had_changes", False)
                if had_changes:
                    status_text = "[green]✓ UPDATED[/green]"
                    details = "[yellow]↓ Changes pulled[/yellow]"
                else:
                    status_text = "[green]✓ UP-TO-DATE[/green]"
                    details = "[dim]No changes[/dim]"
            else:
                status_text = "[red]✗ FAILED[/red]"
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


def _display_update_results(results: dict) -> None:
    """Display update results in a formatted table.

    Args:
        results: Update results dictionary
    """
    system = results["system"]
    updated = results["updated"]
    failed = results["failed"]

    console.print(f"\n[bold]System: {system}[/bold]")
    console.print(f"Updated: [green]{updated}[/green] | Failed: [red]{failed}[/red]\n")

    if results["repos"]:
        table = Table()
        table.add_column("Repository", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Details", style="dim")

        for repo in results["repos"]:
            if repo["status"] == "success":
                action = repo.get("action", "updated")
                had_changes = repo.get("had_changes", False)

                if action == "cloned":
                    status_text = "[green]✓ CLONED[/green]"
                    details = "[blue]⬇ New repository[/blue]"
                elif had_changes:
                    status_text = "[green]✓ UPDATED[/green]"
                    details = "[yellow]↓ Changes pulled[/yellow]"
                else:
                    status_text = "[green]✓ UP-TO-DATE[/green]"
                    details = "[dim]No changes[/dim]"
            else:
                status_text = "[red]✗ FAILED[/red]"
                details = repo.get("error", "")

            table.add_row(repo["name"], status_text, details)

        console.print(table)


def _display_branches(sync_manager: RepositorySync, system: str) -> None:
    """Display branch information for a system.

    Args:
        sync_manager: Repository sync manager
        system: System name
    """
    branches = sync_manager.get_branches(system)

    table = Table(title=f"Branches - {system}")
    table.add_column("Repository", style="cyan")
    table.add_column("Branch", style="yellow")
    table.add_column("Status", style="dim")

    for branch_info in branches:
        if not branch_info["exists"]:
            table.add_row(
                branch_info["name"],
                "[dim]not cloned[/dim]",
                ""
            )
        elif "error" in branch_info:
            table.add_row(
                branch_info["name"],
                "[red]error[/red]",
                branch_info["error"]
            )
        else:
            branch_name = branch_info.get("branch", "-")
            ahead = branch_info.get("ahead", 0)
            behind = branch_info.get("behind", 0)

            # Build status indicator
            status_parts = []
            if ahead > 0:
                status_parts.append(f"[green]↑{ahead}[/green]")
            if behind > 0:
                status_parts.append(f"[yellow]↓{behind}[/yellow]")

            status = " ".join(status_parts) if status_parts else "[dim]up to date[/dim]"

            table.add_row(branch_info["name"], branch_name, status)

    console.print(table)
    console.print()  # Add spacing between systems


if __name__ == "__main__":
    main()
