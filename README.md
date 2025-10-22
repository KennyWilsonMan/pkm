# Personal Knowledge Management System
## Head of Discretionary Pre-Trade Implementation

This repository serves as a comprehensive personal knowledge management (PKM) system for managing systems, analysis, and documentation related to the Discretionary Pre-Trade Implementation role.

## Quick Start

### 1. Install Dependencies

```bash
# Navigate to pkm-tools directory
cd pkm-tools

# Activate virtual environment
source .venv/bin/activate

# Install the package (first time only)
# Note: At Man Group, use the Artifactory PyPI index
pip install -i https://repo.prod.m/artifactory/api/pypi/external-pypi/simple/ -e ".[dev]"

# Install pre-commit hooks (optional, recommended)
pre-commit install
```

**Note**: The `-i` flag specifies Man Group's Artifactory PyPI repository. This is required for all `pip install` commands at Man Group.

### 2. Configure Repositories

Add repository URLs to the system-specific files:
- `systems/thk/service-repositories/repository-list.txt`
- `systems/man-oms/service-repositories/repository-list.txt`
- `systems/panorama/service-repositories/repository-list.txt`

### 3. Sync Repositories

```bash
# Sync all systems
pkm sync

# Or sync a specific system
pkm sync --system thk
pkm sync --system man-oms
pkm sync --system panorama

# Check status
pkm status --system thk
```

### Daily Usage

```bash
# Always activate the virtual environment first
cd pkm-tools
source .venv/bin/activate

# Update all repositories
pkm sync

# Check what's configured
pkm list-systems
pkm list-repos --system thk
```

## Purpose

This PKM system provides:
- Centralized tracking of main branches from service repositories across three core systems
- Analysis and documentation workspace
- Python tools for repository management and synchronization
- Knowledge base for system architecture and implementation decisions

## System Structure

### Core Systems

The repository tracks three main systems under the `systems/` directory:

#### 1. Tomahawk (`systems/thk/`)
Pre-trade system components and services for Tomahawk.

#### 2. Man OMS Pre-Trade (`systems/man-oms/`)
Man OMS pre-trade implementation services and components.

#### 3. Panorama (`systems/panorama/`)
Panorama system services and components.

## Repository Structure

```
pkm/
├── README.md                 # This file
├── systems/                  # Core systems repositories
│   ├── thk/                 # Tomahawk services
│   │   ├── docs/            # Tomahawk-specific documentation
│   │   │   ├── architecture/    # System architecture documentation
│   │   │   ├── analysis/        # Technical analysis and research
│   │   │   └── decisions/       # ADRs and implementation decisions
│   │   └── service-repositories/  # Service repository main branches
│   │       ├── repository-list.txt  # List of repository URLs to track
│   │       └── [cloned repos]       # Cloned service repositories
│   ├── man-oms/             # Man OMS Pre-Trade services
│   │   ├── docs/            # Man OMS-specific documentation
│   │   │   ├── architecture/    # System architecture documentation
│   │   │   ├── analysis/        # Technical analysis and research
│   │   │   └── decisions/       # ADRs and implementation decisions
│   │   └── service-repositories/  # Service repository main branches
│   │       ├── repository-list.txt  # List of repository URLs to track
│   │       └── [cloned repos]       # Cloned service repositories
│   └── panorama/            # Panorama services
│       ├── docs/            # Panorama-specific documentation
│       │   ├── architecture/    # System architecture documentation
│       │   ├── analysis/        # Technical analysis and research
│       │   └── decisions/       # ADRs and implementation decisions
│       └── service-repositories/  # Service repository main branches
│           ├── repository-list.txt  # List of repository URLs to track
│           └── [cloned repos]       # Cloned service repositories
└── tools/                   # Python utilities for repo management
    ├── sync_repos.py        # Sync main branches from service repos
    ├── update_all.py        # Update all tracked repositories
    └── config.yaml          # Repository configuration
```

## Managing Service Repositories

Each system has a `repository-list.txt` file in its `service-repositories/` folder:
- [systems/thk/service-repositories/repository-list.txt](systems/thk/service-repositories/repository-list.txt)
- [systems/man-oms/service-repositories/repository-list.txt](systems/man-oms/service-repositories/repository-list.txt)
- [systems/panorama/service-repositories/repository-list.txt](systems/panorama/service-repositories/repository-list.txt)

Add repository URLs (one per line) to these files. The Python tools will use these lists to clone new repositories or update existing ones.

## Python Tools

The `tools/` directory contains Python utilities for managing the service repositories:

- **sync_repos.py**: Clone or update main branches from repositories listed in repository-list.txt files
- **update_all.py**: Batch update all tracked repositories across all systems to their latest main branch
- **config.yaml**: Configuration file for tool settings

### Usage

```bash
# Update all repositories across all systems
python tools/update_all.py

# Sync specific system
python tools/sync_repos.py --system thk
```

## Getting Started

1. Add repository URLs to the `repository-list.txt` files for each system
2. Run the initial sync: `python tools/update_all.py`
3. Add system-specific documentation in each system's `docs/` folder

## Workflow

1. **Daily Sync**: Run `python tools/update_all.py` to keep repositories current
2. **Documentation**: Add system-specific architecture docs, analysis, and decisions to each system's `docs/` folder
   - `systems/thk/docs/` for Tomahawk documentation
   - `systems/man-oms/docs/` for Man OMS documentation
   - `systems/panorama/docs/` for Panorama documentation
3. **Review**: Use the centralized structure to review changes across systems

## Configuration

Add repository URLs to the appropriate `repository-list.txt` file:

**Tomahawk** ([systems/thk/service-repositories/repository-list.txt](systems/thk/service-repositories/repository-list.txt)):
```
git@github.com:org/thk-service-1.git
git@github.com:org/thk-service-2.git
```

**Man OMS** ([systems/man-oms/service-repositories/repository-list.txt](systems/man-oms/service-repositories/repository-list.txt)):
```
git@github.com:org/oms-service-1.git
```

**Panorama** ([systems/panorama/service-repositories/repository-list.txt](systems/panorama/service-repositories/repository-list.txt)):
```
git@github.com:org/panorama-service-1.git
```

## Contributing

This is a personal knowledge management system. All updates and documentation should reflect current understanding and implementation state of the three core systems.

## Claude Code Integration

This project includes custom Claude Code slash commands and MCP (Model Context Protocol) integrations for enhanced development workflows.

### Available Slash Commands

#### `/get-order-by-id`
Retrieves comprehensive order information from the OMS GraphQL UAT environment.

**Usage:**
```
/get-order-by-id 175268
```

**What it does:**
- Fetches complete order details including status, type, and dates
- Retrieves security information (ISIN, CUSIP, Bloomberg identifiers)
- Shows investment decision details and decision makers
- Lists allocations across books, funds, and strategies
- Displays ticket information
- Provides execution and booking details with prices
- Shows complete order event timeline
- Highlights any compliance issues and overrides

**Benefits:**
- Optimized to use only 4 MCP calls instead of 7+
- Pre-configured with correct GraphQL schema knowledge
- Consistent, formatted output
- Built-in error handling

**Location:** `.claude/commands/get-order-by-id.md`

### MCP Servers

#### OMS GraphQL UAT (`omsGraphUAT`)
Provides access to the Order Management System GraphQL UAT environment.

**Available Tools:**
- `graphql_query` - Execute GraphQL queries with size controls
- `graphql_validate` - Validate queries before execution
- `graphql_schema` - Retrieve the GraphQL schema
- `graphql_list_queries` - Discover available queries with filtering
- `graphql_expand_type` - Explore type definitions
- `graphql_explore` - Execute queries with intelligent data aggregation
- `graphql_introspect` - Full schema introspection
- `oauth_status` - Check OAuth configuration

**Authentication:**
Run `/mcp` to authenticate with the OMS GraphQL UAT environment before using order-related commands.

### Creating Custom Slash Commands

To create a new slash command:

1. Create a new `.md` file in `.claude/commands/`
2. Define the command behavior and instructions
3. Include specific GraphQL queries or tool usage patterns
4. Document input/output format and error handling

Example structure:
```markdown
# Command Name

Description of what the command does.

## Input
What the user provides.

## Task
Step-by-step instructions for Claude Code.

## Output Format
How to present results.
```

### Sub-Agents

Claude Code can launch specialized sub-agents for complex tasks:

- **general-purpose** - Multi-step tasks, code search, complex operations
- **Explore** - Fast codebase exploration with pattern matching
- **statusline-setup** - Configure Claude Code status line
- **output-style-setup** - Create custom output styles

Use sub-agents when tasks require multiple rounds of exploration or complex multi-step operations.

## Notes

- Repositories in `systems/` are read-only copies of main branches
- Use this PKM for reference and analysis, not active development
- Keep tools and documentation up to date as systems evolve
- Slash commands are project-specific and optimized for this workflow
