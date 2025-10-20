# PKM Tools

Utilities for managing the Personal Knowledge Management (PKM) repository for Discretionary Pre-Trade Implementation systems.

## Overview

PKM Tools provides command-line utilities to synchronize service repositories across three main systems:
- **Tomahawk (thk)**
- **Man OMS Pre-Trade (man-oms)**
- **Panorama**

The tool reads repository URLs from `repository-list.txt` files and automatically clones or updates them to keep your local PKM repository current.

## Installation

### Prerequisites

- Python 3.10 or higher
- Git
- SSH keys configured for repository access (if using SSH URLs)

### Setup

```bash
# Navigate to pkm-tools directory
cd pkm-tools

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate     # On Windows

# Upgrade pip
pip install -i https://repo.prod.m/artifactory/api/pypi/external-pypi/simple/ --upgrade pip

# Install package with development dependencies
# Note: At Man Group, use the Artifactory PyPI index
pip install -i https://repo.prod.m/artifactory/api/pypi/external-pypi/simple/ -e ".[dev]"

# Install pre-commit hooks (optional but recommended)
pre-commit install
```

**Man Group Note**: All `pip install` commands must use the `-i https://repo.prod.m/artifactory/api/pypi/external-pypi/simple/` flag to access packages through Man Group's Artifactory.

## Usage

### Sync Repositories

```bash
# Sync all systems
pkm sync

# Sync specific system
pkm sync --system thk
pkm sync --system man-oms
pkm sync --system panorama

# Sync specific branch (default is main)
pkm sync --system thk --branch develop
```

### Check Repository Status

```bash
# Show status of repositories for a system
pkm status --system thk
```

### List Systems

```bash
# List all available systems
pkm list-systems
```

### List Configured Repositories

```bash
# List repositories configured for a system
pkm list-repos --system thk
```

### Help

```bash
# Show general help
pkm --help

# Show command-specific help
pkm sync --help
pkm status --help
```

## Configuration

### Repository Lists

Add repository URLs to the appropriate `repository-list.txt` file for each system:

- `../systems/thk/service-repositories/repository-list.txt`
- `../systems/man-oms/service-repositories/repository-list.txt`
- `../systems/panorama/service-repositories/repository-list.txt`

**Format:**
```
# Comments start with #
git@github.com:org/repo-name.git
https://github.com/org/another-repo.git
```

### Environment Variables

- `PKM_ROOT`: Override PKM repository root directory
- `PKM_LOG_LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR)
- `PKM_GIT_SSH_COMMAND`: Custom SSH command for Git operations

Example:
```bash
export PKM_LOG_LEVEL=DEBUG
export PKM_GIT_SSH_COMMAND="ssh -i ~/.ssh/custom_key"
pkm sync --system thk
```

## Development

See [PYTHON_PROJECT.md](../PYTHON_PROJECT.md) for comprehensive development documentation including:
- Project structure and architecture
- Development workflow
- Testing strategy
- Code quality standards
- Pre-commit hooks explanation

### Quick Development Commands

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=pkm_tools --cov-report=html

# Run linting
ruff check .

# Auto-fix linting issues
ruff check . --fix

# Format code
ruff format .

# Type checking
mypy src/

# Run all pre-commit hooks manually
pre-commit run --all-files
```

## Features

- **Automatic Cloning**: Clones repositories that don't exist locally
- **Smart Updates**: Pulls latest changes for existing repositories
- **Branch Management**: Supports syncing specific branches
- **Progress Display**: Rich terminal output with progress indicators
- **Error Handling**: Graceful handling of Git errors with detailed logging
- **Status Checking**: View current state of all repositories
- **Multi-System Support**: Manage multiple system repositories independently

## Architecture

The project is organized into several modules:

- **cli.py**: Command-line interface using Click
- **repo_sync.py**: Core repository synchronization logic
- **config.py**: Configuration management with Pydantic
- **utils.py**: Utility functions for file operations and logging

## Troubleshooting

### SSH Authentication Issues

```bash
# Test SSH connection
ssh -T git@github.com

# Use custom SSH key
export PKM_GIT_SSH_COMMAND="ssh -i ~/.ssh/your_key"
```

### Repository Already Exists Error

The tool handles existing repositories automatically. If you encounter issues:

```bash
# Check repository status
pkm status --system thk

# Manually inspect the repository
cd ../systems/thk/service-repositories/repo-name
git status
```

### Network Issues

If pip install fails due to network issues, try:
```bash
pip install -i https://repo.prod.m/artifactory/api/pypi/external-pypi/simple/ --upgrade pip
pip install -i https://repo.prod.m/artifactory/api/pypi/external-pypi/simple/ -e ".[dev]" --no-cache-dir
```

## Contributing

This is an internal tool for the PKM repository. When making changes:

1. Create a feature branch
2. Make your changes
3. Run tests and linting
4. Commit (pre-commit hooks will run automatically)
5. Update documentation as needed

## License

MIT License - Internal use only

## Support

For issues or questions, refer to:
- [PYTHON_PROJECT.md](../PYTHON_PROJECT.md) - Comprehensive project documentation
- [SESSION_PROGRESS.md](../SESSION_PROGRESS.md) - Development session notes
