# Claude Code Session State

**Project:** PKM - OMS CDS Documentation and Tools
**Last Updated:** 2025-11-21 15:45
**Status:** Active

## Current Context

Working on OMS CDS (Credit Default Swaps) documentation and tooling in the `fleeting-notes/oms-cds/` directory. Created comprehensive documentation structure with markdown files and developed a Streamlit application for CDS analysis with database connectivity.

## Current Plan

- [x] Add cds.md and credit-risk.md to README with backlinks
- [x] Create man-single-name-cds.md document with cross-references
- [x] Extract CDS position details from Rosetta screenshots
- [x] Set up src folder for Python development
- [x] Create Streamlit application structure
- [x] Implement database connection module using SQLAlchemy
- [x] Add CDS-specific queries from documentation
- [x] Fix numpy.int64 type error in queries
- [ ] Add SQL Server MCP configuration to project

## Completed Tasks

### Documentation Structure (2025-11-21)
- Created cross-referenced documentation in `/turbo/kewilson/github/pkm/fleeting-notes/oms-cds/`
- Added backlinks between README.md and all documentation files:
  - cds.md - Credit Default Swaps overview
  - credit-risk.md - Corporate bond default probabilities
  - man-single-name-cds.md - Man Group CDS implementation
  - security-envoy.md - Security creation via Rosa Security Envoy
  - rosetta-for-cds.md - Rosetta CDS workflows
  - cds-single-name-exposition.md - Single CDS trade exploration
- Organized README with "Core Concepts", "Documentation", and "Notes & Reference" sections

### Data Extraction (2025-11-21)
- Extracted from Rosetta Trade Details image:
  - Security ID: 24031746
  - Book IDs: 137878, 138462, 139750, 143434, 143479
  - Trade: CDS WORLDLINE 500(20-DEC-2026) GOLDMAN SACHS INTERNATIONAL 1,102.86bps
- Extracted complete CDS contract details (reference entity, terms, dates, pricing)

### Polyglot Notebook (2025-11-21)
- Set up `/turbo/kewilson/github/pkm/fleeting-notes/oms-cds/single--name-cds.ipynb`
- Created Python kernel connection using custom kernel spec (python3-custom)
- Added C# variables for bookId and securityId
- Created SQL query cells using #!sql-omsdb kernel
- Added Python cells to display results as pandas DataFrames

### Streamlit Application (2025-11-21)
- Created `/turbo/kewilson/github/pkm/fleeting-notes/oms-cds/src/` directory structure
- Built comprehensive Streamlit app (`app.py`) with:
  - Environment selection (dev/uat/prod)
  - Security ID and Book ID inputs
  - Database connection testing
  - Two-stage CDS analysis queries:
    1. CDS Security and Position (using security_id + book_id)
    2. Reference Entity/Issuer/RED CODE (cascading from issuer_id)
  - Transposed data display
  - Metrics visualization

### Database Connection Module (2025-11-21)
- Created `db_connection.py` based on MCP SQL Server pattern:
  - SQLAlchemy-based connections
  - Environment configuration (dev/uat/prod)
  - Proper connection string building with Windows Integrated Auth
  - ODBC Driver 17 for SQL Server
  - Named parameter support
  - Connection testing functionality
- Fixed numpy.int64 type error by converting to Python int

### Development Environment Setup (2025-11-21)
- Created `requirements.txt` with dependencies:
  - streamlit
  - pandas
  - pyodbc
  - sqlalchemy
  - plotly
- Created `README.md` with Pegasus environment setup instructions
- Documented using pegasus distribution 311-1

## Session History

### [2025-11-21 14:00]
- Accomplished: Set up complete documentation structure with cross-references
- Accomplished: Extracted CDS position data from Rosetta screenshots
- Next steps: Create analysis tools

### [2025-11-21 15:00]
- Accomplished: Created polyglot notebook with multi-kernel support
- Accomplished: Set up custom Python kernel spec to handle python3 vs python issue
- Next steps: Build Streamlit application

### [2025-11-21 15:30]
- Accomplished: Built complete Streamlit application with database connectivity
- Accomplished: Implemented proper SQLAlchemy connection pattern
- Accomplished: Added CDS-specific queries from documentation
- Accomplished: Fixed type conversion issues
- Next steps: Add MCP server configuration for SQL Server access

## Blockers/Issues

### Resolved
- ✅ Polyglot notebook Python kernel connection issue - Fixed by creating custom kernel spec at `/users/is/kewilson/.local/share/jupyter/kernels/python3-custom/`
- ✅ numpy.int64 type error in SQL queries - Fixed by converting to Python int

### Current
- None

## Important Context

### File Locations
- **Documentation**: `/turbo/kewilson/github/pkm/fleeting-notes/oms-cds/`
- **Streamlit App**: `/turbo/kewilson/github/pkm/fleeting-notes/oms-cds/src/`
- **Polyglot Notebook**: `/turbo/kewilson/github/pkm/fleeting-notes/oms-cds/single--name-cds.ipynb`
- **MCP SQL Server**: `/users/is/kewilson/source/repos/personal/mcp-sql-server/`

### Key Data Points
- Security ID: 24031746 (CDS WORLDLINE 500)
- Primary Book ID: 137878
- All Book IDs: 137878, 138462, 139750, 143434, 143479
- Issuer ID: 2690900
- RED Code: FOHED0

### Database Environments
- **DEV**: D-DB-OMS-01:2001
- **UAT**: U-DB-OMS-01:2001
- **PROD**: P-DB-OMS-01:2001
- All use OMS database with Windows Integrated Security

### SQL Queries in Use
1. CDS Security and Position - joins POSITION_CORE, SECURITY, SECURITY_CLASS
2. Reference Entity/Issuer - joins ISSUER, LEGAL_ENTITY

### Development Tools
- Pegasus distribution: 311-1
- Python kernel: python3-custom (using /usr/bin/python3)
- Database driver: ODBC Driver 17 for SQL Server
- Notebook kernels: csharp, sql-omsdb, pythonkernel

## Next Steps

1. Add SQL Server MCP configuration to `.claude/mcp.json`
2. Test MCP server connection
3. Consider adding more CDS analysis queries to Streamlit app
4. Add data visualization (plotly charts) to Streamlit app
5. Document reference obligation queries
