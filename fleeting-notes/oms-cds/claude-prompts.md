# Claude Code Session Prompts

This file logs all prompts and key responses for this project.

---

## [2025-11-21 14:30] User Prompt

**User:** familiarize yourself with where we are from /turbo/kewilson/github/pkm/SESSION_PROGRESS.md

**Actions Taken:**
- Read SESSION_PROGRESS.md from parent directory
- Created claude-prompts.md for session logging
- Created claude-session-state.md for state tracking
- Familiarized with PKM repository structure and current state

**Result:** Understood the PKM (Personal Knowledge Management) system setup with three main systems (Tomahawk/thk, Man OMS Pre-Trade/man-oms, and Panorama). The session progress shows a complete repository structure with docs folders, service repositories management, and a Python project (pkm-tools) that needs dependency installation. Currently in the fleeting-notes/oms-cds subdirectory.

---

## [2025-11-21 14:45] User Prompt

**User:** Use the sql-server MCP to connect to OMS DB and work out a query to find out a query that lists all the books that have positions on single name CDS or CDS on Index returns a list of books with counts of index and single name CDS

**Actions Taken:**
- Connected to OMS UAT database using SQL Server MCP
- Explored database schema using list_tables and get_table_schema
- Identified key tables: Inventory.BOOK, Inventory.SECURITY, Inventory.POSITION_CORE
- Clarified requirement: security class IDs 172 (single name CDS) and 29 (CDS on Index)
- Created comprehensive SQL query with JOINs and aggregations
- Tested query and found 67 active books with CDS positions
- Discovered that all positions are CDS Index (ID=29), zero Single Name CDS (ID=172)
- Verified security class names and confirmed mapping
- Created Python module (cds_book_analysis.py) with:
  - Main query for books with CDS positions
  - Helper queries for verification
  - Utility functions for data analysis
  - Documentation of findings

**Result:** Successfully created a working SQL query that returns books with CDS positions, including separate counts for CDS Index and Single Name CDS. Query returns 67 books, all with CDS Index positions only. The query is saved in cds_book_analysis.py for reuse.

**Key Findings:**
- Total books with CDS positions: 67
- All positions are CDS Index (security class ID 29)
- No active Single Name CDS positions (security class ID 172)
- Top book: AHL AEX2-UCREDIT with 2,746 CDS Index positions
- Query filters for active positions and books (END_DT > GETDATE())

---
