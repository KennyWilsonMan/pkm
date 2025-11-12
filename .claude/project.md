# Personal Knowledge Management (PKM) Project

## Project Structure

This is a multi-system repository containing various projects and their associated documentation.

### Repository Organization

Repositories are organized under the `systems/` directory with the following structure:

```
systems/
├── man-oms/          # MAN OMS (Order Management System) related projects
├── panorama/         # Panorama related projects
└── thk/              # Tomahawk (THK) related projects
    ├── service-repositories/    # Contains repository-list.txt with repo URLs
    └── tomahawk2/              # Main Tomahawk2 repository (git submodule/clone)
```

### Systems with Code

Currently available systems with code repositories:

#### Tomahawk (THK) - `systems/thk/`
- **Status**: Active repository
- **Repository**: `tomahawk2/` (cloned from ssh://git@mangit.maninvestments.com:7999/ets/tomahawk2.git)
- **Contents**: Full git repository with source code
- **Documentation**: `docs/` directory
- **Service Repositories**: `service-repositories/repository-list.txt`

#### MAN OMS - `systems/man-oms/`
- **Status**: Documentation and configuration only
- **Contents**:
  - `docs/` - System documentation
  - `service-repositories/` - Repository lists
- **Note**: No code repositories cloned yet

#### Panorama - `systems/panorama/`
- **Status**: Documentation and configuration only
- **Contents**:
  - `docs/` - System documentation
  - `service-repositories/` - Repository lists
- **Note**: No code repositories cloned yet

### Working with Repositories

When asked about specific systems or services:
- **Tomahawk/THK**: Code available in `systems/thk/tomahawk2/`
- **OMS**: Look in `systems/man-oms/` (docs only currently)
- **Panorama**: Look in `systems/panorama/` (docs only currently)

### Repository Lists

Repository lists are maintained in `service-repositories/repository-list.txt` files within each system directory. These files contain:
- Git URLs for service repositories
- Format: One repository URL per line
- Lines starting with `#` are comments

### Root Level Directories

- `rfc/`: Request for Comments and design documents
- `.claude/`: Claude Code configuration and custom commands
- `systems/`: Main directory containing all system-specific content
