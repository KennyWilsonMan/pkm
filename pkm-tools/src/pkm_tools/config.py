"""Configuration management for PKM tools."""

from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class PKMConfig(BaseSettings):
    """Configuration for PKM tools."""

    pkm_root: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.parent.parent,
        description="Root directory of the PKM repository",
    )
    log_level: str = Field(default="INFO", description="Logging level")
    git_ssh_command: str | None = Field(default=None, description="Custom SSH command for Git")

    @field_validator("pkm_root")
    @classmethod
    def validate_pkm_root(cls, v: Path) -> Path:
        """Validate that PKM root exists."""
        if not v.exists():
            raise ValueError(f"PKM root directory does not exist: {v}")
        return v.resolve()

    @property
    def systems_dir(self) -> Path:
        """Get the systems directory."""
        return self.pkm_root / "systems"

    def get_system_dir(self, system: str) -> Path:
        """Get directory for a specific system.

        Args:
            system: System name (thk, man-oms, panorama)

        Returns:
            Path to system directory
        """
        system_dir = self.systems_dir / system
        if not system_dir.exists():
            raise ValueError(f"System directory does not exist: {system_dir}")
        return system_dir

    def get_repository_list_file(self, system: str) -> Path:
        """Get repository-list.txt file for a system.

        Args:
            system: System name (thk, man-oms, panorama)

        Returns:
            Path to repository-list.txt file
        """
        repo_list = self.get_system_dir(system) / "service-repositories" / "repository-list.txt"
        if not repo_list.exists():
            raise ValueError(f"Repository list file does not exist: {repo_list}")
        return repo_list

    def get_service_repositories_dir(self, system: str) -> Path:
        """Get service-repositories directory for a system.

        Args:
            system: System name (thk, man-oms, panorama)

        Returns:
            Path to service-repositories directory
        """
        service_repos_dir = self.get_system_dir(system) / "service-repositories"
        if not service_repos_dir.exists():
            raise ValueError(f"Service repositories directory does not exist: {service_repos_dir}")
        return service_repos_dir

    def list_systems(self) -> List[str]:
        """List all available systems.

        Returns:
            List of system names
        """
        if not self.systems_dir.exists():
            return []
        return [d.name for d in self.systems_dir.iterdir() if d.is_dir()]

    class Config:
        """Pydantic configuration."""

        env_prefix = "PKM_"
        case_sensitive = False
