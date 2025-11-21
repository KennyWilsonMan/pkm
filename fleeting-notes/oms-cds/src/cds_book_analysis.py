"""
OMS CDS Book Analysis

This module contains queries and analysis for finding books with CDS positions.

Security Class IDs:
- 29: Credit Default Swap (CDS Index)
- 172: CDS Index (Single Name CDS)

Note: Based on analysis as of 2025-11-21, there are currently NO active positions
with security class ID 172 in the UAT database.
"""

from typing import Dict, List
import pandas as pd


# SQL Query: Books with CDS Positions (with Managing Entity)
BOOKS_WITH_CDS_QUERY = """
-- Find books with positions on Single Name CDS (29) or CDS Index (172)
-- Returns book info with counts of each CDS type and Managing Entity
SELECT
    b.BOOK_ID,
    b.BOOK_NAME,
    b.IS_ACTIVE,
    me.MANAGING_ENTITY_NAME,
    COUNT(DISTINCT CASE WHEN s.SECURITY_CLASS_ID = 29 THEN p.POSITION_ID END) AS Single_Name_CDS_Count,
    COUNT(DISTINCT CASE WHEN s.SECURITY_CLASS_ID = 172 THEN p.POSITION_ID END) AS CDS_Index_Count,
    COUNT(DISTINCT p.POSITION_ID) AS Total_CDS_Positions,
    COUNT(DISTINCT s.SECURITY_ID) AS Unique_Securities
FROM
    Inventory.BOOK b
    INNER JOIN Inventory.POSITION_CORE p ON b.BOOK_ID = p.BOOK_ID
    INNER JOIN Inventory.SECURITY s ON p.SECURITY_ID = s.SECURITY_ID
    INNER JOIN Inventory.FUND f ON b.FUND_ID = f.FUND_ID
    LEFT JOIN Inventory.MANAGING_ENTITY me ON f.MANAGING_ENTITY_ID = me.MANAGING_ENTITY_ID AND me.END_DT > GETDATE()
WHERE
    s.SECURITY_CLASS_ID IN (29, 172)  -- Single Name CDS (29) or CDS Index (172)
    AND p.END_DT > GETDATE()  -- Only active positions
    AND b.END_DT > GETDATE()  -- Only active books
    AND f.END_DT > GETDATE()  -- Only active funds
GROUP BY
    b.BOOK_ID,
    b.BOOK_NAME,
    b.IS_ACTIVE,
    me.MANAGING_ENTITY_NAME
ORDER BY
    Total_CDS_Positions DESC,
    b.BOOK_NAME
"""

# SQL Query: Books with Single-Name CDS (Security Class 29)
BOOKS_WITH_SINGLE_NAME_CDS_QUERY = """
-- Books with Single-Name CDS positions (individual company CDS)
SELECT
    b.BOOK_ID,
    b.BOOK_NAME,
    me.MANAGING_ENTITY_NAME,
    COUNT(DISTINCT p.POSITION_ID) AS Single_Name_CDS_Positions,
    COUNT(DISTINCT s.SECURITY_ID) AS Unique_Securities,
    COUNT(DISTINCT s.ISSUER_ID) AS Unique_Issuers
FROM
    Inventory.BOOK b
    INNER JOIN Inventory.POSITION_CORE p ON b.BOOK_ID = p.BOOK_ID
    INNER JOIN Inventory.SECURITY s ON p.SECURITY_ID = s.SECURITY_ID
    INNER JOIN Inventory.FUND f ON b.FUND_ID = f.FUND_ID
    LEFT JOIN Inventory.MANAGING_ENTITY me ON f.MANAGING_ENTITY_ID = me.MANAGING_ENTITY_ID AND me.END_DT > GETDATE()
WHERE
    s.SECURITY_CLASS_ID = 29  -- Credit Default Swap (Single-Name)
    AND p.END_DT > GETDATE()
    AND b.END_DT > GETDATE()
    AND f.END_DT > GETDATE()
GROUP BY
    b.BOOK_ID,
    b.BOOK_NAME,
    me.MANAGING_ENTITY_NAME
ORDER BY
    Single_Name_CDS_Positions DESC
"""

# SQL Query: Books with CDS Index (Security Class 172)
BOOKS_WITH_CDS_INDEX_QUERY = """
-- Books with CDS Index positions (e.g., CDX.EM, iTraxx)
SELECT
    b.BOOK_ID,
    b.BOOK_NAME,
    me.MANAGING_ENTITY_NAME,
    COUNT(DISTINCT p.POSITION_ID) AS CDS_Index_Positions,
    COUNT(DISTINCT s.SECURITY_ID) AS Unique_Securities,
    COUNT(DISTINCT s.ISSUER_ID) AS Unique_Index_Families
FROM
    Inventory.BOOK b
    INNER JOIN Inventory.POSITION_CORE p ON b.BOOK_ID = p.BOOK_ID
    INNER JOIN Inventory.SECURITY s ON p.SECURITY_ID = s.SECURITY_ID
    INNER JOIN Inventory.FUND f ON b.FUND_ID = f.FUND_ID
    LEFT JOIN Inventory.MANAGING_ENTITY me ON f.MANAGING_ENTITY_ID = me.MANAGING_ENTITY_ID AND me.END_DT > GETDATE()
WHERE
    s.SECURITY_CLASS_ID = 172  -- CDS Index
    AND p.END_DT > GETDATE()
    AND b.END_DT > GETDATE()
    AND f.END_DT > GETDATE()
GROUP BY
    b.BOOK_ID,
    b.BOOK_NAME,
    me.MANAGING_ENTITY_NAME
ORDER BY
    CDS_Index_Positions DESC
"""


# SQL Query: Check for Single Name CDS Positions
CHECK_SINGLE_NAME_CDS_QUERY = """
-- Check if there are ANY positions with security class ID 172 (Single Name CDS)
SELECT
    COUNT(*) AS Position_Count,
    COUNT(DISTINCT p.BOOK_ID) AS Book_Count,
    COUNT(DISTINCT s.SECURITY_ID) AS Security_Count
FROM
    Inventory.POSITION_CORE p
    INNER JOIN Inventory.SECURITY s ON p.SECURITY_ID = s.SECURITY_ID
WHERE
    s.SECURITY_CLASS_ID = 172  -- Single Name CDS
    AND p.END_DT > GETDATE()  -- Active positions only
"""


# SQL Query: Verify Security Class Names
VERIFY_SECURITY_CLASSES_QUERY = """
-- Verify the security class names for IDs 29 and 172
SELECT
    SECURITY_CLASS_ID,
    SECURITY_CLASS_NAME
FROM
    Inventory.SECURITY_CLASS
WHERE
    SECURITY_CLASS_ID IN (29, 172)
    AND END_DT > GETDATE()
"""


def get_books_with_cds_summary(df: pd.DataFrame) -> Dict[str, int]:
    """
    Get summary statistics from books with CDS query results.

    Args:
        df: DataFrame returned from BOOKS_WITH_CDS_QUERY

    Returns:
        Dictionary with summary statistics
    """
    if df.empty:
        return {
            "total_books": 0,
            "total_cds_index_positions": 0,
            "total_single_name_cds_positions": 0,
            "total_positions": 0
        }

    return {
        "total_books": len(df),
        "total_cds_index_positions": int(df['CDS_Index_Count'].sum()),
        "total_single_name_cds_positions": int(df['Single_Name_CDS_Count'].sum()),
        "total_positions": int(df['Total_CDS_Positions'].sum()),
        "books_with_only_cds_index": len(df[df['Single_Name_CDS_Count'] == 0]),
        "books_with_only_single_name": len(df[df['CDS_Index_Count'] == 0]),
        "books_with_both": len(df[(df['CDS_Index_Count'] > 0) & (df['Single_Name_CDS_Count'] > 0)])
    }


def get_top_books_by_positions(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """
    Get top N books by total CDS positions.

    Args:
        df: DataFrame returned from BOOKS_WITH_CDS_QUERY
        n: Number of top books to return

    Returns:
        DataFrame with top N books
    """
    return df.nlargest(n, 'Total_CDS_Positions')


# Query Results Summary (as of 2025-11-21)
QUERY_RESULTS_SUMMARY = """
Query Results Summary (UAT Database - 2025-11-21)
==================================================

Total Books with CDS Positions: 67
- All 67 books have ONLY Single-Name CDS (ID=29) positions
- ZERO books have CDS Index (ID=172) positions

Top 5 Books by Total CDS Positions:
1. AHL AEX2-UCREDIT (108361): 2,746 positions - Managing Entity: AHL FUNDS
2. AHL TRM1-TRISK (137153): 1,148 positions - Managing Entity: AHL FUNDS
3. MSL BPL1-RVCDSUS (142919): 957 positions - Managing Entity: AHL FUNDS
4. AHL TAR0-TRISK (137152): 945 positions - Managing Entity: AHL FUNDS
5. Man 1783 I SP-RVCDSUS (142094): 886 positions - Managing Entity: AHL FUNDS

Security Class Mapping (CORRECTED):
- ID 29 = "Credit Default Swap" (Single-Name CDS on individual companies like AB Electrolux, Care UK, etc.)
- ID 172 = "CDS Index" (Index products like CDX.EM, iTraxx)

Join Path for Managing Entity:
BOOK → FUND → MANAGING_ENTITY
- BOOK.FUND_ID → FUND.FUND_ID
- FUND.MANAGING_ENTITY_ID → MANAGING_ENTITY.MANAGING_ENTITY_ID

Note: There are CDS Index securities (ID 172) defined in the system (e.g., CDX-EMS39V1-5Y),
but no active positions currently exist on these securities.
"""


if __name__ == "__main__":
    # Example usage with the db_connection module
    try:
        from db_connection import execute_query

        print("Fetching books with CDS positions...")
        df = execute_query("uat", BOOKS_WITH_CDS_QUERY)

        print(f"\nFound {len(df)} books with CDS positions\n")

        # Display summary
        summary = get_books_with_cds_summary(df)
        print("Summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")

        # Display top 10 books
        print("\nTop 10 Books by Total CDS Positions:")
        top_books = get_top_books_by_positions(df, 10)
        print(top_books[['BOOK_NAME', 'CDS_Index_Count', 'Single_Name_CDS_Count', 'Total_CDS_Positions']])

    except ImportError:
        print("db_connection module not available. Please run queries manually.")
        print("\nUse BOOKS_WITH_CDS_QUERY constant for the main query.")
