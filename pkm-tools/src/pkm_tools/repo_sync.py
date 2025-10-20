"""Repository synchronization logic."""

import logging
from pathlib import Path
from typing import List

import git
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from pkm_tools.config import PKMConfig
from pkm_tools.utils import extract_repo_name, read_repository_list

logger = logging.getLogger(__name__)
console = Console()


class RepositorySyncError(Exception):
    """Exception raised when repository sync fails."""

    pass


class RepositorySync:
    """Handle repository synchronization operations."""

    def __init__(self, config: PKMConfig):
        """Initialize repository sync.

        Args:
            config: PKM configuration
        """
        self.config = config

    def sync_system(self, system: str, branch: str = "main") -> dict:
        """Sync all repositories for a system.

        Args:
            system: System name (thk, man-oms, panorama)
            branch: Branch to sync (default: main)

        Returns:
            Dictionary with sync results
        """
        logger.info(f"Syncing repositories for system: {system}")

        try:
            repo_list_file = self.config.get_repository_list_file(system)
            service_repos_dir = self.config.get_service_repositories_dir(system)
        except ValueError as e:
            raise RepositorySyncError(str(e)) from e

        repos = read_repository_list(repo_list_file)

        if not repos:
            logger.warning(f"No repositories found in {repo_list_file}")
            return {"system": system, "synced": 0, "failed": 0, "repos": []}

        results = {"system": system, "synced": 0, "failed": 0, "repos": []}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            for repo_url in repos:
                repo_name = extract_repo_name(repo_url)
                task = progress.add_task(f"Syncing {repo_name}...", total=None)

                try:
                    self._sync_repository(repo_url, service_repos_dir, branch)
                    results["synced"] += 1
                    results["repos"].append({"name": repo_name, "status": "success", "url": repo_url})
                    logger.info(f"Successfully synced: {repo_name}")
                except Exception as e:
                    results["failed"] += 1
                    results["repos"].append(
                        {"name": repo_name, "status": "failed", "url": repo_url, "error": str(e)}
                    )
                    logger.error(f"Failed to sync {repo_name}: {e}")
                finally:
                    progress.remove_task(task)

        return results

    def clone_system(self, system: str, branch: str = "main") -> dict:
        """Clone all repositories for a system.

        Args:
            system: System name (thk, man-oms, panorama)
            branch: Branch to clone (default: main)

        Returns:
            Dictionary with clone results
        """
        logger.info(f"Cloning repositories for system: {system}")

        try:
            repo_list_file = self.config.get_repository_list_file(system)
            service_repos_dir = self.config.get_service_repositories_dir(system)
        except ValueError as e:
            raise RepositorySyncError(str(e)) from e

        repos = read_repository_list(repo_list_file)

        if not repos:
            logger.warning(f"No repositories found in {repo_list_file}")
            return {"system": system, "cloned": 0, "failed": 0, "repos": []}

        results = {"system": system, "cloned": 0, "failed": 0, "repos": []}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            for repo_url in repos:
                repo_name = extract_repo_name(repo_url)
                task = progress.add_task(f"Cloning {repo_name}...", total=None)

                try:
                    self._clone_repository(repo_url, service_repos_dir, branch)
                    results["cloned"] += 1
                    results["repos"].append({"name": repo_name, "status": "success", "url": repo_url})
                    logger.info(f"Successfully cloned: {repo_name}")
                except Exception as e:
                    results["failed"] += 1
                    results["repos"].append(
                        {"name": repo_name, "status": "failed", "url": repo_url, "error": str(e)}
                    )
                    logger.error(f"Failed to clone {repo_name}: {e}")
                finally:
                    progress.remove_task(task)

        return results

    def _sync_repository(self, repo_url: str, target_dir: Path, branch: str) -> None:
        """Sync a single repository (only if it already exists).

        Args:
            repo_url: Git repository URL
            target_dir: Directory where repositories are stored
            branch: Branch to sync

        Raises:
            RepositorySyncError: If sync fails or repository doesn't exist
        """
        repo_name = extract_repo_name(repo_url)
        repo_path = target_dir / repo_name

        if not repo_path.exists():
            raise RepositorySyncError(
                f"Repository {repo_name} does not exist. Use 'clone' command to clone it first."
            )

        try:
            # Repository exists, pull latest changes
            logger.debug(f"Updating existing repository: {repo_name}")
            repo = git.Repo(repo_path)

            # Ensure we're on the correct branch
            if repo.active_branch.name != branch:
                logger.debug(f"Checking out branch: {branch}")
                repo.git.checkout(branch)

            # Pull latest changes
            origin = repo.remotes.origin
            origin.pull(branch)

        except git.GitCommandError as e:
            raise RepositorySyncError(f"Git operation failed for {repo_name}: {e}") from e
        except Exception as e:
            raise RepositorySyncError(f"Unexpected error syncing {repo_name}: {e}") from e

    def _clone_repository(self, repo_url: str, target_dir: Path, branch: str) -> None:
        """Clone a single repository (only if it doesn't already exist).

        Args:
            repo_url: Git repository URL
            target_dir: Directory where repositories are stored
            branch: Branch to clone

        Raises:
            RepositorySyncError: If clone fails or repository already exists
        """
        repo_name = extract_repo_name(repo_url)
        repo_path = target_dir / repo_name

        if repo_path.exists():
            raise RepositorySyncError(
                f"Repository {repo_name} already exists. Use 'sync' command to update it."
            )

        try:
            # Repository doesn't exist, clone it
            logger.debug(f"Cloning new repository: {repo_name}")
            git.Repo.clone_from(
                repo_url,
                repo_path,
                branch=branch,
                env={"GIT_SSH_COMMAND": self.config.git_ssh_command}
                if self.config.git_ssh_command
                else None,
            )

        except git.GitCommandError as e:
            raise RepositorySyncError(f"Git operation failed for {repo_name}: {e}") from e
        except Exception as e:
            raise RepositorySyncError(f"Unexpected error cloning {repo_name}: {e}") from e

    def sync_all_systems(self, branch: str = "main") -> dict:
        """Sync repositories for all systems.

        Args:
            branch: Branch to sync (default: main)

        Returns:
            Dictionary with sync results for all systems
        """
        systems = self.config.list_systems()

        if not systems:
            logger.warning("No systems found")
            return {"systems": []}

        results = {"systems": []}

        for system in systems:
            logger.info(f"Processing system: {system}")
            try:
                system_result = self.sync_system(system, branch)
                results["systems"].append(system_result)
            except RepositorySyncError as e:
                logger.error(f"Failed to sync system {system}: {e}")
                results["systems"].append(
                    {"system": system, "synced": 0, "failed": 0, "repos": [], "error": str(e)}
                )

        return results

    def clone_all_systems(self, branch: str = "main") -> dict:
        """Clone repositories for all systems.

        Args:
            branch: Branch to clone (default: main)

        Returns:
            Dictionary with clone results for all systems
        """
        systems = self.config.list_systems()

        if not systems:
            logger.warning("No systems found")
            return {"systems": []}

        results = {"systems": []}

        for system in systems:
            logger.info(f"Processing system: {system}")
            try:
                system_result = self.clone_system(system, branch)
                results["systems"].append(system_result)
            except RepositorySyncError as e:
                logger.error(f"Failed to clone system {system}: {e}")
                results["systems"].append(
                    {"system": system, "cloned": 0, "failed": 0, "repos": [], "error": str(e)}
                )

        return results

    def get_repository_status(self, system: str) -> List[dict]:
        """Get status of all repositories for a system.

        Args:
            system: System name (thk, man-oms, panorama)

        Returns:
            List of repository status dictionaries
        """
        try:
            repo_list_file = self.config.get_repository_list_file(system)
            service_repos_dir = self.config.get_service_repositories_dir(system)
        except ValueError as e:
            raise RepositorySyncError(str(e)) from e

        repos = read_repository_list(repo_list_file)
        statuses = []

        for repo_url in repos:
            repo_name = extract_repo_name(repo_url)
            repo_path = service_repos_dir / repo_name

            status = {"name": repo_name, "url": repo_url, "exists": repo_path.exists()}

            if repo_path.exists():
                try:
                    repo = git.Repo(repo_path)
                    status["branch"] = repo.active_branch.name
                    status["dirty"] = repo.is_dirty()
                    status["untracked"] = len(repo.untracked_files) > 0
                    status["commit"] = repo.head.commit.hexsha[:8]
                except Exception as e:
                    status["error"] = str(e)

            statuses.append(status)

        return statuses
