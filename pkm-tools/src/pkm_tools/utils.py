"""Utility functions for PKM tools."""

import logging
from pathlib import Path
from typing import List


def setup_logging(level: str = "INFO") -> None:
    """Set up logging configuration.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def read_repository_list(file_path: Path) -> List[str]:
    """Read repository URLs from a repository-list.txt file.

    Args:
        file_path: Path to repository-list.txt file

    Returns:
        List of repository URLs (comments and empty lines removed)
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Repository list file not found: {file_path}")

    repos = []
    with file_path.open() as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith("#"):
                repos.append(line)

    return repos


def extract_repo_name(repo_url: str) -> str:
    """Extract repository name from URL.

    Args:
        repo_url: Git repository URL

    Returns:
        Repository name (without .git extension)

    Examples:
        >>> extract_repo_name("git@github.com:org/my-repo.git")
        'my-repo'
        >>> extract_repo_name("https://github.com/org/my-repo.git")
        'my-repo'
    """
    # Handle both SSH and HTTPS URLs
    name = repo_url.split("/")[-1]
    # Remove .git extension if present
    if name.endswith(".git"):
        name = name[:-4]
    return name
