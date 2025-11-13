"""Repository synchronization logic."""

import json
import logging
import os
import re
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

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

    def _get_default_branch(self, repo: git.Repo) -> str:
        """Get the default branch of a repository.

        Args:
            repo: Git repository object

        Returns:
            Name of the default branch
        """
        try:
            # Try to get the default branch from remote HEAD
            for ref in repo.remotes.origin.refs:
                if ref.name == "origin/HEAD":
                    # Extract branch name from origin/HEAD -> origin/master format
                    return ref.ref.name.replace("origin/", "")

            # Fallback: try common branch names
            for branch_name in ["main", "master", "develop"]:
                try:
                    repo.git.rev_parse("--verify", f"origin/{branch_name}")
                    return branch_name
                except git.GitCommandError:
                    continue

            # Last resort: use current branch
            return repo.active_branch.name
        except Exception:
            # If all else fails, default to main
            return "main"

    def sync_system(self, system: str, branch: str | None = None) -> dict:
        """Sync all repositories for a system.

        Args:
            system: System name (thk, man-oms, GCP)
            branch: Branch to sync (default: None, which auto-detects the default branch)

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
                    sync_info = self._sync_repository(repo_url, service_repos_dir, branch)
                    results["synced"] += 1
                    results["repos"].append({
                        "name": repo_name,
                        "status": "success",
                        "url": repo_url,
                        "had_changes": sync_info.get("had_changes", False),
                        "action": sync_info.get("action", "synced")
                    })
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
            system: System name (thk, man-oms, GCP)
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

    def update_system(self, system: str, branch: str | None = None) -> dict:
        """Update all repositories for a system (clone if doesn't exist, sync if it does).

        Args:
            system: System name (thk, man-oms, GCP)
            branch: Branch to update (default: None, which auto-detects the default branch)

        Returns:
            Dictionary with update results
        """
        logger.info(f"Updating repositories for system: {system}")

        try:
            repo_list_file = self.config.get_repository_list_file(system)
            service_repos_dir = self.config.get_service_repositories_dir(system)
        except ValueError as e:
            raise RepositorySyncError(str(e)) from e

        repos = read_repository_list(repo_list_file)

        if not repos:
            logger.warning(f"No repositories found in {repo_list_file}")
            return {"system": system, "updated": 0, "failed": 0, "repos": []}

        results = {"system": system, "updated": 0, "failed": 0, "repos": []}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            for repo_url in repos:
                repo_name = extract_repo_name(repo_url)
                task = progress.add_task(f"Updating {repo_name}...", total=None)

                try:
                    update_info = self._update_repository(repo_url, service_repos_dir, branch)
                    results["updated"] += 1
                    results["repos"].append({
                        "name": repo_name,
                        "status": "success",
                        "url": repo_url,
                        "had_changes": update_info.get("had_changes", False),
                        "action": update_info.get("action", "updated")
                    })
                    logger.info(f"Successfully updated: {repo_name}")
                except Exception as e:
                    results["failed"] += 1
                    results["repos"].append(
                        {"name": repo_name, "status": "failed", "url": repo_url, "error": str(e)}
                    )
                    logger.error(f"Failed to update {repo_name}: {e}")
                finally:
                    progress.remove_task(task)

        return results

    def _sync_repository(self, repo_url: str, target_dir: Path, branch: str | None = None) -> dict:
        """Sync a single repository (only if it already exists).

        Args:
            repo_url: Git repository URL
            target_dir: Directory where repositories are stored
            branch: Branch to sync (if None, auto-detect default branch)

        Returns:
            Dictionary with sync information including whether changes were pulled

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

            # Store the current commit before pulling
            current_commit = repo.head.commit.hexsha

            # Auto-detect default branch if not specified
            if branch is None:
                branch = self._get_default_branch(repo)
                logger.debug(f"Auto-detected default branch: {branch}")

            # Ensure we're on the correct branch
            if repo.active_branch.name != branch:
                logger.debug(f"Checking out branch: {branch}")
                repo.git.checkout(branch)

            # Pull latest changes
            origin = repo.remotes.origin
            pull_info = origin.pull(branch)

            # Check if changes were pulled
            new_commit = repo.head.commit.hexsha
            had_changes = current_commit != new_commit

            return {"had_changes": had_changes, "action": "synced"}

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

    def _update_repository(self, repo_url: str, target_dir: Path, branch: str | None = None) -> dict:
        """Update a repository (clone if doesn't exist, sync if it does).

        Args:
            repo_url: Git repository URL
            target_dir: Directory where repositories are stored
            branch: Branch to clone/sync (if None, auto-detect for existing repos)

        Returns:
            Dictionary with update information including action taken and whether changes occurred

        Raises:
            RepositorySyncError: If update fails
        """
        repo_name = extract_repo_name(repo_url)
        repo_path = target_dir / repo_name

        if repo_path.exists():
            # Repository exists, sync it
            logger.debug(f"Repository {repo_name} exists, syncing...")
            return self._sync_repository(repo_url, target_dir, branch)
        else:
            # Repository doesn't exist, clone it
            logger.debug(f"Repository {repo_name} doesn't exist, cloning...")
            # For cloning, we need a branch - use auto-detection logic if not specified
            if branch is None:
                # Check if we can determine the default branch from remote
                # For now, we'll use 'main' as fallback for cloning
                # Once cloned, sync operations will auto-detect
                branch = "main"
                logger.debug(f"No branch specified for clone, trying: {branch}")
                try:
                    self._clone_repository(repo_url, target_dir, branch)
                except RepositorySyncError as e:
                    # If 'main' doesn't work, try 'master'
                    if "branch" in str(e).lower() or "pathspec" in str(e).lower():
                        logger.debug(f"Branch {branch} failed, trying 'master'")
                        branch = "master"
                        # Clean up failed clone attempt if directory was created
                        if repo_path.exists():
                            import shutil
                            shutil.rmtree(repo_path)
                        self._clone_repository(repo_url, target_dir, branch)
                    else:
                        raise
            else:
                self._clone_repository(repo_url, target_dir, branch)

            return {"had_changes": True, "action": "cloned"}

    def sync_all_systems(self, branch: str | None = None) -> dict:
        """Sync repositories for all systems.

        Args:
            branch: Branch to sync (default: None, which auto-detects the default branch)

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

    def update_all_systems(self, branch: str | None = None) -> dict:
        """Update repositories for all systems (clone if doesn't exist, sync if it does).

        Args:
            branch: Branch to update (default: None, which auto-detects the default branch)

        Returns:
            Dictionary with update results for all systems
        """
        systems = self.config.list_systems()

        if not systems:
            logger.warning("No systems found")
            return {"systems": []}

        results = {"systems": []}

        for system in systems:
            logger.info(f"Processing system: {system}")
            try:
                system_result = self.update_system(system, branch)
                results["systems"].append(system_result)
            except RepositorySyncError as e:
                logger.error(f"Failed to update system {system}: {e}")
                results["systems"].append(
                    {"system": system, "updated": 0, "failed": 0, "repos": [], "error": str(e)}
                )

        return results

    def get_repository_status(self, system: str) -> List[dict]:
        """Get status of all repositories for a system.

        Args:
            system: System name (thk, man-oms, GCP)

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

    def get_branches(self, system: str) -> List[dict]:
        """Get branch information for all repositories in a system.

        Args:
            system: System name (thk, man-oms, GCP)

        Returns:
            List of dictionaries with repository name and branch information
        """
        try:
            repo_list_file = self.config.get_repository_list_file(system)
            service_repos_dir = self.config.get_service_repositories_dir(system)
        except ValueError as e:
            raise RepositorySyncError(str(e)) from e

        repos = read_repository_list(repo_list_file)
        branches = []

        for repo_url in repos:
            repo_name = extract_repo_name(repo_url)
            repo_path = service_repos_dir / repo_name

            branch_info = {"name": repo_name, "exists": repo_path.exists()}

            if repo_path.exists():
                try:
                    repo = git.Repo(repo_path)
                    branch_info["branch"] = repo.active_branch.name

                    # Check if branch is ahead/behind remote
                    try:
                        remote_branch = f"origin/{repo.active_branch.name}"
                        local_commit = repo.head.commit
                        remote_commit = repo.commit(remote_branch)

                        ahead = list(repo.iter_commits(f"{remote_branch}..HEAD"))
                        behind = list(repo.iter_commits(f"HEAD..{remote_branch}"))

                        branch_info["ahead"] = len(ahead)
                        branch_info["behind"] = len(behind)
                    except Exception:
                        # If we can't determine ahead/behind, just skip it
                        pass

                except Exception as e:
                    branch_info["error"] = str(e)

            branches.append(branch_info)

        return branches

    def parse_pr_url(self, pr_url: str) -> Tuple[str, str, str]:
        """Parse BitBucket pull request URL.

        Args:
            pr_url: BitBucket PR URL (e.g., https://mangit.maninvestments.com/projects/ETS/repos/tomahawk2/pull-requests/123)

        Returns:
            Tuple of (project_key, repo_slug, pr_id)

        Raises:
            ValueError: If URL format is invalid
        """
        # Match BitBucket Server PR URL format
        pattern = r"https://[^/]+/projects/([^/]+)/repos/([^/]+)/pull-requests/(\d+)"
        match = re.match(pattern, pr_url)

        if not match:
            raise ValueError(f"Invalid BitBucket PR URL format: {pr_url}")

        return match.group(1), match.group(2), match.group(3)

    def get_pr_info(self, pr_url: str) -> dict:
        """Get pull request information from BitBucket API.

        Args:
            pr_url: BitBucket PR URL

        Returns:
            Dictionary with PR information including source branch

        Raises:
            RepositorySyncError: If API call fails or token is missing
        """
        token = os.environ.get("BITBUCKET_TOKEN")
        if not token:
            raise RepositorySyncError(
                "BITBUCKET_TOKEN environment variable not set. "
                "Please set it to your BitBucket personal access token."
            )

        try:
            project_key, repo_slug, pr_id = self.parse_pr_url(pr_url)
        except ValueError as e:
            raise RepositorySyncError(str(e)) from e

        # BitBucket Server REST API endpoint
        api_url = f"https://mangit.maninvestments.com/rest/api/1.0/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}"

        logger.debug(f"Fetching PR info from: {api_url}")

        try:
            # Create request with authorization header
            request = Request(api_url)
            request.add_header("Authorization", f"Bearer {token}")
            request.add_header("Accept", "application/json")

            # Make the request
            with urlopen(request, timeout=10) as response:
                response_data = response.read()
                pr_data = json.loads(response_data)

            return {
                "project": project_key,
                "repo": repo_slug,
                "pr_id": pr_id,
                "title": pr_data.get("title", ""),
                "source_branch": pr_data["fromRef"]["displayId"],
                "target_branch": pr_data["toRef"]["displayId"],
                "author": pr_data["author"]["user"]["displayName"],
            }

        except (HTTPError, URLError) as e:
            raise RepositorySyncError(f"Failed to fetch PR information: {e}") from e
        except (KeyError, ValueError) as e:
            raise RepositorySyncError(f"Failed to parse PR response: {e}") from e

    def find_repository_system(self, repo_name: str) -> Optional[str]:
        """Find which system contains a repository.

        Args:
            repo_name: Repository name

        Returns:
            System name if found, None otherwise
        """
        systems = self.config.list_systems()

        for system in systems:
            try:
                repo_list_file = self.config.get_repository_list_file(system)
                repos = read_repository_list(repo_list_file)

                for repo_url in repos:
                    if extract_repo_name(repo_url) == repo_name:
                        return system
            except ValueError:
                # System doesn't have repository list, skip
                continue

        return None

    def checkout_pr_branch(self, pr_url: str) -> dict:
        """Checkout the branch from a pull request URL.

        Args:
            pr_url: BitBucket PR URL

        Returns:
            Dictionary with checkout information

        Raises:
            RepositorySyncError: If checkout fails
        """
        # Get PR information
        pr_info = self.get_pr_info(pr_url)
        repo_name = pr_info["repo"]
        branch_name = pr_info["source_branch"]

        logger.info(f"PR #{pr_info['pr_id']}: {pr_info['title']}")
        logger.info(f"Repository: {repo_name}, Branch: {branch_name}")

        # Find which system has this repository
        system = self.find_repository_system(repo_name)
        if not system:
            raise RepositorySyncError(
                f"Repository '{repo_name}' not found in any system. "
                f"Available systems: {', '.join(self.config.list_systems())}"
            )

        logger.info(f"Found repository in system: {system}")

        # Get repository path
        service_repos_dir = self.config.get_service_repositories_dir(system)
        repo_path = service_repos_dir / repo_name

        if not repo_path.exists():
            raise RepositorySyncError(
                f"Repository '{repo_name}' not cloned yet. "
                f"Please run 'pkm update --system {system}' first."
            )

        # Checkout the branch
        try:
            repo = git.Repo(repo_path)

            # Fetch latest from remote
            logger.debug("Fetching from remote...")
            origin = repo.remotes.origin
            origin.fetch()

            # Check if branch exists locally
            local_branch_exists = branch_name in [b.name for b in repo.branches]

            if local_branch_exists:
                logger.debug(f"Checking out existing local branch: {branch_name}")
                repo.git.checkout(branch_name)
                # Pull latest changes
                logger.debug("Pulling latest changes...")
                origin.pull(branch_name)
            else:
                # Create and checkout new branch tracking remote
                logger.debug(f"Creating new local branch tracking origin/{branch_name}")
                repo.git.checkout("-b", branch_name, f"origin/{branch_name}")

            return {
                "system": system,
                "repo": repo_name,
                "branch": branch_name,
                "pr_id": pr_info["pr_id"],
                "pr_title": pr_info["title"],
                "author": pr_info["author"],
            }

        except git.GitCommandError as e:
            raise RepositorySyncError(f"Git operation failed: {e}") from e
        except Exception as e:
            raise RepositorySyncError(f"Unexpected error during checkout: {e}") from e
