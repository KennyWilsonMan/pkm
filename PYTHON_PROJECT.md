# PKM Tools - Python Project Documentation

## Overview

The `pkm-tools` Python project provides utilities for managing the Personal Knowledge Management (PKM) repository. It handles cloning, updating, and synchronizing service repositories across the three main systems (Tomahawk, Man OMS, Panorama).

## Project Structure

```
pkm-tools/
├── pyproject.toml           # Project metadata and dependencies (PEP 621)
├── README.md                # Project-specific README
├── .python-version          # Python version specification
├── .gitignore              # Git ignore rules
├── .pre-commit-config.yaml # Pre-commit hooks configuration
├── src/
│   └── pkm_tools/          # Main package
│       ├── __init__.py     # Package initialization
│       ├── cli.py          # Command-line interface
│       ├── repo_sync.py    # Repository synchronization logic
│       ├── config.py       # Configuration management
│       └── utils.py        # Utility functions
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── test_repo_sync.py
│   ├── test_config.py
│   └── conftest.py         # Pytest configuration
└── .venv/                  # Virtual environment (not in git)
```

## Technology Stack

### Core Technologies
- **Python**: 3.11+ (modern Python with latest features)
- **Package Manager**: pip with pip-tools for dependency management
- **Build System**: setuptools with pyproject.toml (PEP 621)
- **Virtual Environment**: venv (Python standard library)

### Development Tools
- **Linting & Formatting**: Ruff (fast, modern alternative to flake8/black/isort)
- **Type Checking**: mypy (static type checking)
- **Testing**: pytest (modern testing framework)
- **Pre-commit**: Automated code quality checks before commits
- **Git Operations**: GitPython (Python library for Git operations)

### Key Dependencies
- **GitPython**: Git repository management
- **click**: Modern CLI framework
- **pydantic**: Data validation and settings management
- **rich**: Beautiful terminal output and progress bars
- **pyyaml**: YAML configuration file support

## Setup Instructions

### 1. Initial Setup

```bash
# Navigate to the pkm-tools directory
cd pkm-tools

# Create virtual environment
python3.11 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate     # On Windows

# Upgrade pip (Man Group: use Artifactory)
pip install -i https://repo.prod.m/artifactory/api/pypi/external-pypi/simple/ --upgrade pip

# Install package in development mode with dev dependencies (Man Group: use Artifactory)
pip install -i https://repo.prod.m/artifactory/api/pypi/external-pypi/simple/ -e ".[dev]"
```

**Man Group Specific**: All `pip install` commands must use the Man Group Artifactory PyPI index:
```bash
-i https://repo.prod.m/artifactory/api/pypi/external-pypi/simple/
```

### 2. Install Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually on all files (optional)
pre-commit run --all-files
```

### 3. Verify Installation

```bash
# Check installation
pkm-tools --help

# Run tests
pytest

# Run linting
ruff check .

# Run type checking
mypy src/
```

## Development Workflow

### Daily Development

1. **Activate virtual environment**:
   ```bash
   source .venv/bin/activate
   ```

2. **Make code changes** in `src/pkm_tools/`

3. **Run tests**:
   ```bash
   pytest
   # or with coverage
   pytest --cov=pkm_tools --cov-report=html
   ```

4. **Check code quality**:
   ```bash
   # Linting and formatting
   ruff check .
   ruff format .

   # Type checking
   mypy src/
   ```

5. **Commit changes** (pre-commit hooks run automatically):
   ```bash
   git add .
   git commit -m "Description of changes"
   ```

### Adding New Dependencies

```bash
# Add runtime dependency
# Edit pyproject.toml [project.dependencies]

# Add development dependency
# Edit pyproject.toml [project.optional-dependencies.dev]

# Reinstall to pick up new dependencies (Man Group: use Artifactory)
pip install -i https://repo.prod.m/artifactory/api/pypi/external-pypi/simple/ -e ".[dev]"
```

## Configuration

### pyproject.toml
Modern Python project configuration following PEP 621 standard:
- Project metadata (name, version, description)
- Dependencies specification
- Build system configuration
- Tool configurations (ruff, mypy, pytest)

### .python-version
Specifies Python 3.11 as the project's Python version. Used by:
- pyenv (automatic version switching)
- IDEs (Python interpreter selection)

### .pre-commit-config.yaml

Pre-commit hooks are automated checks that run **before** you make a git commit. They act as a quality gate, catching issues early before code enters the repository.

#### What Pre-commit Hooks Do

**Purpose**: Automatically enforce code quality standards and catch common mistakes before they're committed to version control.

**How They Work**:
1. You stage your changes: `git add .`
2. You attempt to commit: `git commit -m "message"`
3. Pre-commit hooks run automatically
4. If all checks pass → commit succeeds
5. If any check fails → commit is blocked, you fix issues, then retry

#### Configured Hooks

**1. Basic File Checks** (`pre-commit-hooks`)
- **trailing-whitespace**: Removes unnecessary spaces at end of lines (keeps code clean)
- **end-of-file-fixer**: Ensures files end with a newline (POSIX standard)
- **check-yaml**: Validates YAML syntax (catches broken config files)
- **check-json**: Validates JSON syntax (catches broken JSON files)
- **check-added-large-files**: Prevents accidentally committing large files (>1MB)
- **check-merge-conflict**: Detects unresolved merge conflict markers (<<<<<<, >>>>>>)
- **mixed-line-ending**: Ensures consistent line endings (LF vs CRLF)

**2. Ruff Linting & Formatting**
- **ruff (linting)**: Checks code for style violations, bugs, and bad patterns
  - Enforces PEP 8 style guide
  - Detects unused imports and variables
  - Finds potential bugs (e.g., mutable default arguments)
  - Sorts imports alphabetically
  - Auto-fixes issues when possible
- **ruff-format**: Automatically formats code consistently
  - Standardizes indentation, spacing, quotes
  - Makes code readable and uniform across the project

**3. mypy Type Checking**
- **mypy**: Validates type hints and catches type-related bugs
  - Ensures function parameters have correct types
  - Detects potential None errors before runtime
  - Catches mismatched return types
  - Validates generic types and collections

#### Benefits

1. **Catch Bugs Early**: Find issues before they reach code review or production
2. **Consistent Code Style**: Everyone's code looks the same (no style debates)
3. **Save Review Time**: Reviewers focus on logic, not formatting
4. **Prevent Mistakes**: Can't commit broken YAML, huge files, or merge conflicts
5. **Learn Best Practices**: Hooks teach you better coding patterns
6. **No Manual Checks**: Automation ensures nothing is forgotten

#### Example Workflow

```bash
# Make changes to code
vim src/pkm_tools/cli.py

# Stage changes
git add src/pkm_tools/cli.py

# Attempt commit
git commit -m "Add new CLI command"

# Pre-commit runs automatically:
# ✓ Trailing whitespace.... Passed
# ✓ Fix End of Files....... Passed
# ✓ Check Yaml............. Passed
# ✓ Ruff................... Failed
#   - src/pkm_tools/cli.py:15: Unused import 'sys'
# ✗ Commit blocked!

# Fix the issue
vim src/pkm_tools/cli.py  # Remove unused import

# Try again
git commit -m "Add new CLI command"
# ✓ All checks passed!
# [main abc1234] Add new CLI command
```

#### Bypassing Hooks (Use Sparingly)

Sometimes you need to commit without running hooks (e.g., work-in-progress):
```bash
git commit --no-verify -m "WIP: incomplete feature"
```

**Warning**: Only bypass hooks when absolutely necessary. They exist to protect code quality.

#### Manual Execution

Run hooks manually without committing:
```bash
# Run on all files
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files

# Run on staged files only
pre-commit run
```

### Ruff Configuration
Modern, fast linter and formatter configured in `pyproject.toml`:
- Line length: 100 characters
- Python 3.11+ syntax
- Selected rule sets: pycodestyle, pyflakes, isort, type checking
- Auto-fix enabled where safe

### mypy Configuration
Static type checking configured in `pyproject.toml`:
- Strict mode enabled
- Disallow untyped definitions
- Warn on unused ignores
- Check untyped definitions

### pytest Configuration
Test framework configured in `pyproject.toml`:
- Test discovery in `tests/` directory
- Coverage reporting
- Verbose output

## Package Architecture

### CLI Module (`cli.py`)
Entry point for command-line interface using Click:
- `pkm-tools sync` - Sync repositories for a specific system or all systems
- `pkm-tools update` - Update all repositories to latest main branch
- `pkm-tools status` - Show status of all tracked repositories
- `pkm-tools list` - List all configured repositories

### Repository Sync Module (`repo_sync.py`)
Core logic for repository operations:
- Read repository URLs from `repository-list.txt` files
- Clone repositories if they don't exist
- Pull latest changes if they exist
- Handle Git errors gracefully
- Progress reporting with rich library

### Configuration Module (`config.py`)
Configuration management using Pydantic:
- Load system configurations
- Validate repository URLs
- Path resolution
- Settings management

### Utils Module (`utils.py`)
Utility functions:
- File operations
- Path handling
- Logging setup
- Error handling helpers

## Testing Strategy

### Unit Tests
Test individual functions and classes in isolation:
- `test_config.py` - Configuration loading and validation
- `test_repo_sync.py` - Repository synchronization logic
- Mock external dependencies (Git operations)

### Integration Tests
Test end-to-end workflows:
- Clone and update operations
- Multiple system handling
- Error scenarios

### Test Fixtures (`conftest.py`)
Reusable test fixtures:
- Temporary directory setup
- Mock repository configurations
- Sample repository-list.txt files

## Code Quality Standards

### Style Guide
- Follow PEP 8 with Ruff's opinionated defaults
- Line length: 100 characters
- Use type hints for all functions
- Docstrings for all public functions (Google style)

### Type Hints
```python
from pathlib import Path
from typing import List, Optional

def sync_repository(
    repo_url: str,
    target_path: Path,
    branch: str = "main"
) -> bool:
    """Sync a repository to the target path.

    Args:
        repo_url: Git repository URL
        target_path: Local path for repository
        branch: Branch to sync (default: main)

    Returns:
        True if successful, False otherwise
    """
    ...
```

### Error Handling
- Use custom exceptions for domain-specific errors
- Log errors with appropriate levels
- Provide helpful error messages to users
- Graceful degradation when possible

## Building and Distribution

### Local Development Build
```bash
pip install -e .
```

### Production Build
```bash
# Build distribution packages
python -m build

# Generates:
# dist/pkm_tools-0.1.0-py3-none-any.whl
# dist/pkm_tools-0.1.0.tar.gz
```

### Installation from Build
```bash
pip install dist/pkm_tools-0.1.0-py3-none-any.whl
```

## Environment Variables

The project supports configuration via environment variables:

- `PKM_ROOT`: Root directory of the PKM repository (auto-detected)
- `PKM_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `PKM_GIT_SSH_COMMAND`: Custom SSH command for Git operations

## Troubleshooting

### Virtual Environment Issues
```bash
# Recreate virtual environment
rm -rf .venv
python3.11 -m venv .venv
source .venv/bin/activate
pip install -i https://repo.prod.m/artifactory/api/pypi/external-pypi/simple/ -e ".[dev]"
```

### Git Authentication Issues
```bash
# Ensure SSH keys are set up
ssh -T git@github.com

# Or use HTTPS with credentials
git config --global credential.helper store
```

### Import Errors
```bash
# Reinstall package in development mode (Man Group: use Artifactory)
pip install -i https://repo.prod.m/artifactory/api/pypi/external-pypi/simple/ -e .
```

### Pre-commit Hook Failures
```bash
# Update pre-commit hooks
pre-commit autoupdate

# Run manually to see detailed errors
pre-commit run --all-files
```

## Future Enhancements

### Planned Features
1. **Parallel repository updates** - Update multiple repos concurrently
2. **Repository health checks** - Verify repository integrity
3. **Conflict detection** - Warn about local changes before update
4. **Branch management** - Support for tracking non-main branches
5. **Report generation** - Generate sync reports in markdown/HTML
6. **Interactive mode** - TUI for repository management
7. **Webhook support** - Trigger syncs on repository updates
8. **Configuration templates** - Pre-configured setups for common scenarios

### Performance Optimizations
- Caching of repository metadata
- Incremental updates using Git shallow clones
- Parallel operations using asyncio

### Additional Tooling
- Docker container for consistent environment
- CI/CD pipeline for automated testing
- Documentation generation with Sphinx
- Package publishing to PyPI (if needed)

## References

- [PEP 621 - Project Metadata](https://peps.python.org/pep-0621/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [GitPython Documentation](https://gitpython.readthedocs.io/)
- [Click Documentation](https://click.palletsprojects.com/)
- [pytest Documentation](https://docs.pytest.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

## Maintenance

### Updating Dependencies
```bash
# Check for outdated packages
pip list --outdated

# Update specific package
pip install --upgrade package-name

# Update all packages (careful!)
pip install --upgrade $(pip freeze | cut -d= -f1)
```

### Version Bumping
1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create git tag: `git tag v0.2.0`
4. Push tag: `git push origin v0.2.0`

### Code Review Checklist
- [ ] All tests pass
- [ ] Type hints added
- [ ] Docstrings updated
- [ ] Pre-commit hooks pass
- [ ] No new warnings from mypy
- [ ] Test coverage maintained/improved
- [ ] Documentation updated
