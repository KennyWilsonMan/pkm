"""
OMS CDS Analysis - Streamlit App

This app demonstrates CDS analysis using data from the OMS database.
"""

import streamlit as st
import pandas as pd
from db_connection import execute_query, test_connection, SQL_CONNECTIONS

# Page config
st.set_page_config(
    page_title="OMS CDS Analysis",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("📊 OMS CDS Analysis")
st.markdown("---")

# Sidebar for inputs
st.sidebar.header("Analysis Mode")
analysis_mode = st.sidebar.radio(
    "Choose Analysis",
    ["Book CDS Overview", "Specific Position Lookup"],
    index=0
)

if analysis_mode == "Specific Position Lookup":
    st.sidebar.header("CDS Position Selection")
    security_id = st.sidebar.number_input("Security ID", value=24031746, step=1)
    book_id = st.sidebar.number_input("Book ID", value=137878, step=1)

# Database environment selection
st.sidebar.header("Database Connection")
env = st.sidebar.selectbox(
    "Environment",
    options=list(SQL_CONNECTIONS.keys()),
    index=1  # Default to "uat"
)

# Test connection button
if st.sidebar.button("🔌 Test Connection"):
    with st.spinner("Testing connection..."):
        if test_connection(env):
            st.sidebar.success(f"✅ Connected to {env.upper()}")
        else:
            st.sidebar.error(f"❌ Failed to connect to {env.upper()}")

# Main content based on analysis mode
if analysis_mode == "Book CDS Overview":
    st.header("📚 Books with CDS Positions")
    st.markdown(f"**Database Environment:** `{env.upper()}`")

    # Filters section
    st.sidebar.markdown("---")
    st.sidebar.header("Filters")

    # Get list of managing entities
    try:
        query_entities = """
        SELECT DISTINCT
            COALESCE(me.MANAGING_ENTITY_NAME, 'Unknown') AS MANAGING_ENTITY_NAME
        FROM
            Inventory.BOOK b
            INNER JOIN Inventory.POSITION_CORE p ON b.BOOK_ID = p.BOOK_ID
            INNER JOIN Inventory.SECURITY s ON p.SECURITY_ID = s.SECURITY_ID
            INNER JOIN Inventory.FUND f ON b.FUND_ID = f.FUND_ID
            LEFT JOIN Inventory.MANAGING_ENTITY me ON f.MANAGING_ENTITY_ID = me.MANAGING_ENTITY_ID AND me.END_DT > GETDATE()
        WHERE
            s.SECURITY_CLASS_ID = 29
            AND p.END_DT > GETDATE()
            AND b.END_DT > GETDATE()
            AND f.END_DT > GETDATE()
            AND p.BOOKED_QUANTITY != 0.0
        ORDER BY
            MANAGING_ENTITY_NAME
        """
        df_entities = execute_query(env, query_entities)
        entity_list = ["All"] + df_entities['MANAGING_ENTITY_NAME'].tolist()
    except:
        entity_list = ["All"]

    selected_entity = st.sidebar.selectbox(
        "Managing Entity",
        options=entity_list,
        index=0
    )

    # Get list of books based on selected entity
    try:
        entity_filter_books = ""
        if selected_entity != "All":
            safe_entity = selected_entity.replace("'", "''")
            entity_filter_books = f"AND COALESCE(me.MANAGING_ENTITY_NAME, 'Unknown') = '{safe_entity}'"

        query_books = f"""
        SELECT TOP 10
            b.BOOK_ID,
            b.BOOK_NAME,
            COUNT(DISTINCT p.POSITION_ID) AS CDS_Positions
        FROM
            Inventory.BOOK b
            INNER JOIN Inventory.POSITION_CORE p ON b.BOOK_ID = p.BOOK_ID
            INNER JOIN Inventory.SECURITY s ON p.SECURITY_ID = s.SECURITY_ID
            INNER JOIN Inventory.FUND f ON b.FUND_ID = f.FUND_ID
            LEFT JOIN Inventory.MANAGING_ENTITY me ON f.MANAGING_ENTITY_ID = me.MANAGING_ENTITY_ID AND me.END_DT > GETDATE()
        WHERE
            s.SECURITY_CLASS_ID = 29
            AND p.END_DT > GETDATE()
            AND b.END_DT > GETDATE()
            AND f.END_DT > GETDATE()
            AND p.BOOKED_QUANTITY != 0.0
            {entity_filter_books}
        GROUP BY
            b.BOOK_ID,
            b.BOOK_NAME
        ORDER BY
            CDS_Positions DESC
        """
        df_books = execute_query(env, query_books)
        book_options = ["None"] + [f"{row['BOOK_NAME']} ({row['BOOK_ID']})" for _, row in df_books.iterrows()]
        book_ids = {f"{row['BOOK_NAME']} ({row['BOOK_ID']})": row['BOOK_ID'] for _, row in df_books.iterrows()}
    except:
        book_options = ["None"]
        book_ids = {}

    selected_book = st.sidebar.selectbox(
        "Select Book",
        options=book_options,
        index=0
    )

    # Get list of top 10 securities from the selected book
    if selected_book != "None":
        try:
            book_id_for_securities = book_ids.get(selected_book)
            if book_id_for_securities:
                query_securities = f"""
                SELECT TOP 10
                    s.SECURITY_ID,
                    s.SECURITY_NAME,
                    COUNT(DISTINCT p.POSITION_ID) AS Position_Count,
                    SUM(p.BOOKED_QUANTITY) AS Total_Quantity
                FROM
                    Inventory.SECURITY s
                    INNER JOIN Inventory.POSITION_CORE p ON s.SECURITY_ID = p.SECURITY_ID
                WHERE
                    p.BOOK_ID = {book_id_for_securities}
                    AND s.SECURITY_CLASS_ID = 29
                    AND p.END_DT > GETDATE()
                    AND p.BOOKED_QUANTITY != 0.0
                GROUP BY
                    s.SECURITY_ID,
                    s.SECURITY_NAME
                ORDER BY
                    Position_Count DESC,
                    ABS(SUM(p.BOOKED_QUANTITY)) DESC
                """
                df_securities = execute_query(env, query_securities)
                security_options = ["None"] + [f"{row['SECURITY_NAME'][:60]}... ({row['SECURITY_ID']})" if len(row['SECURITY_NAME']) > 60 else f"{row['SECURITY_NAME']} ({row['SECURITY_ID']})" for _, row in df_securities.iterrows()]
                security_ids = {f"{row['SECURITY_NAME'][:60]}... ({row['SECURITY_ID']})" if len(row['SECURITY_NAME']) > 60 else f"{row['SECURITY_NAME']} ({row['SECURITY_ID']})": row['SECURITY_ID'] for _, row in df_securities.iterrows()}
            else:
                security_options = ["None"]
                security_ids = {}
        except:
            security_options = ["None"]
            security_ids = {}
    else:
        security_options = ["None"]
        security_ids = {}

    selected_security = st.sidebar.selectbox(
        "Select Security",
        options=security_options,
        index=0,
        disabled=(selected_book == "None")
    )

    st.markdown("---")

    # Automatically load data (no button needed)
    try:
        with st.spinner(f"Querying {env.upper()} database..."):

            # Query: Books with CDS Positions (Security Class 29)
            st.subheader("📚 Top 10 Books with CDS Positions")
            st.caption("Security Class 29 - Credit Default Swaps")

            # Build query with optional managing entity filter
            entity_filter = ""
            if selected_entity != "All":
                # Escape single quotes in entity name for SQL
                safe_entity = selected_entity.replace("'", "''")
                entity_filter = f"AND COALESCE(me.MANAGING_ENTITY_NAME, 'Unknown') = '{safe_entity}'"

            query_cds = f"""
            SELECT TOP 10
                b.BOOK_ID,
                b.BOOK_NAME,
                COALESCE(me.MANAGING_ENTITY_NAME, 'Unknown') AS MANAGING_ENTITY_NAME,
                COUNT(DISTINCT p.POSITION_ID) AS CDS_Positions,
                COUNT(DISTINCT s.SECURITY_ID) AS Unique_Securities,
                COUNT(DISTINCT s.ISSUER_ID) AS Unique_Issuers
            FROM
                Inventory.BOOK b
                INNER JOIN Inventory.POSITION_CORE p ON b.BOOK_ID = p.BOOK_ID
                INNER JOIN Inventory.SECURITY s ON p.SECURITY_ID = s.SECURITY_ID
                INNER JOIN Inventory.FUND f ON b.FUND_ID = f.FUND_ID
                LEFT JOIN Inventory.MANAGING_ENTITY me ON f.MANAGING_ENTITY_ID = me.MANAGING_ENTITY_ID AND me.END_DT > GETDATE()
            WHERE
                s.SECURITY_CLASS_ID = 29  -- Credit Default Swap
                AND p.END_DT > GETDATE()
                AND b.END_DT > GETDATE()
                AND f.END_DT > GETDATE()
                AND p.BOOKED_QUANTITY != 0.0
                {entity_filter}
            GROUP BY
                b.BOOK_ID,
                b.BOOK_NAME,
                me.MANAGING_ENTITY_NAME
            ORDER BY
                CDS_Positions DESC
            """

            df_cds = execute_query(env, query_cds)

            if not df_cds.empty:
                entity_msg = f" for {selected_entity}" if selected_entity != "All" else ""
                st.success(f"✅ Found {len(df_cds)} books with CDS positions{entity_msg}")

                # Display metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Positions", f"{df_cds['CDS_Positions'].sum():,}")
                with col2:
                    st.metric("Total Securities", f"{df_cds['Unique_Securities'].sum():,}")
                with col3:
                    st.metric("Total Issuers", f"{df_cds['Unique_Issuers'].sum():,}")

                # Display table
                st.dataframe(
                    df_cds.style.format({
                        'CDS_Positions': '{:,}',
                        'Unique_Securities': '{:,}',
                        'Unique_Issuers': '{:,}'
                    }),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.warning("⚠️ No CDS positions found")

            # Show positions for selected book (if no security selected)
            if selected_book != "None" and selected_security == "None":
                st.markdown("---")
                book_id = book_ids.get(selected_book)
                if book_id:
                    st.subheader(f"🔍 Recent CDS Positions for {selected_book}")
                    st.caption("10 Most Recent Positions by Start Date")

                    query_positions = f"""
                    SELECT TOP 10
                        s.SECURITY_NAME,
                        i.ISSUER_NAME,
                        p.BOOKED_QUANTITY,
                        p.START_DT,
                        p.POSITION_ID,
                        p.BOOK_ID,
                        s.SECURITY_ID
                    FROM
                        Inventory.POSITION_CORE p
                        INNER JOIN Inventory.SECURITY s ON p.SECURITY_ID = s.SECURITY_ID
                        LEFT JOIN Inventory.ISSUER i ON s.ISSUER_ID = i.ISSUER_ID
                    WHERE
                        p.BOOK_ID = {book_id}
                        AND s.SECURITY_CLASS_ID = 29
                        AND p.END_DT > GETDATE()
                        AND p.BOOKED_QUANTITY != 0.0
                    ORDER BY
                        p.START_DT DESC
                    """

                    df_positions = execute_query(env, query_positions)

                    if not df_positions.empty:
                        st.success(f"✅ Found {len(df_positions)} recent positions")

                        # Format the dataframe
                        df_positions['START_DT'] = pd.to_datetime(df_positions['START_DT']).dt.strftime('%Y-%m-%d %H:%M')

                        # Reorder columns as requested
                        column_order = ['SECURITY_NAME', 'ISSUER_NAME', 'BOOKED_QUANTITY', 'START_DT', 'POSITION_ID', 'BOOK_ID', 'SECURITY_ID']
                        df_positions = df_positions[column_order]

                        # Display table
                        st.dataframe(
                            df_positions.style.format({
                                'BOOKED_QUANTITY': '{:,.2f}',
                                'POSITION_ID': '{:,}',
                                'BOOK_ID': '{:,}',
                                'SECURITY_ID': '{:,}'
                            }),
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info("ℹ️ No positions found for this book")

            # Show CDS details for selected security (Specific Position Lookup mode)
            if selected_security != "None":
                st.markdown("---")
                security_id = security_ids.get(selected_security)
                book_id = book_ids.get(selected_book)
                if security_id and book_id:
                    st.subheader(f"🔍 CDS Position Details")
                    st.caption(f"Security: {selected_security}")

                    # Query 1: CDS Security and Position
                    query_security_detail = f"""
                    SELECT
                        S.SECURITY_NAME,
                        SC.SECURITY_CLASS_NAME,
                        PC.BOOKED_OPEN_QUANTITY,
                        PC.BOOKED_QUANTITY,
                        S.ISSUER_ID
                    FROM
                        Inventory.POSITION_CORE PC
                    INNER JOIN
                        Inventory.[SECURITY] S ON S.SECURITY_ID = PC.SECURITY_ID
                    INNER JOIN
                        Inventory.SECURITY_CLASS SC ON SC.SECURITY_CLASS_ID = S.SECURITY_CLASS_ID
                    WHERE
                        PC.SECURITY_ID = {security_id}
                    AND
                        PC.BOOK_ID = {book_id}
                    """

                    df_security_detail = execute_query(env, query_security_detail)

                    if not df_security_detail.empty:
                        st.success("✅ CDS Security data retrieved successfully!")

                        # Display as transposed table
                        df_transposed = df_security_detail.T
                        df_transposed.columns = ['Value']
                        st.dataframe(df_transposed, use_container_width=True)

                        # Extract issuer_id for next query
                        issuer_id = int(df_security_detail['ISSUER_ID'].iloc[0])

                        # Display key metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Security Class", df_security_detail['SECURITY_CLASS_NAME'].iloc[0])
                        with col2:
                            st.metric("Booked Open Quantity", f"{df_security_detail['BOOKED_OPEN_QUANTITY'].iloc[0]:,.2f}")
                        with col3:
                            st.metric("Booked Quantity", f"{df_security_detail['BOOKED_QUANTITY'].iloc[0]:,.2f}")

                        st.markdown("---")

                        # Query 2: Reference Entity / Issuer / RED CODE
                        st.subheader("Reference Entity / Issuer / RED CODE")
                        query_issuer = f"""
                        SELECT
                            I.ISSUER_NAME,
                            I.LEGAL_ENTITY_ID,
                            LE.LEGAL_NAME,
                            LE.MARKIT_RED_ENTITY
                        FROM
                            Inventory.ISSUER I
                        INNER JOIN
                            Inventory.LEGAL_ENTITY LE ON LE.LEGAL_ENTITY_ID = I.LEGAL_ENTITY_ID
                        WHERE
                            I.ISSUER_ID = {issuer_id}
                        """

                        df_issuer = execute_query(env, query_issuer)

                        if not df_issuer.empty:
                            st.success("✅ Issuer data retrieved successfully!")

                            # Display as transposed table
                            df_issuer_transposed = df_issuer.T
                            df_issuer_transposed.columns = ['Value']
                            st.dataframe(df_issuer_transposed, use_container_width=True)

                            # Display issuer metrics
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Issuer Name", df_issuer['ISSUER_NAME'].iloc[0])
                            with col2:
                                st.metric("RED Code", df_issuer['MARKIT_RED_ENTITY'].iloc[0])
                        else:
                            st.warning("⚠️ No issuer data found")
                    else:
                        st.warning("⚠️ No position data found for this security/book combination")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

else:  # Specific Position Lookup mode
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Security ID", security_id)
    with col2:
        st.metric("Book ID", book_id)

    st.markdown("---")

    # Query button
    if st.button("🔍 Query CDS Details"):
        try:
            with st.spinner(f"Querying {env.upper()} database..."):

                # Query 1: CDS Security and Position
                st.subheader("1. CDS Security and Position")
                query_security = """
                SELECT
                    S.SECURITY_NAME,
                    SC.SECURITY_CLASS_NAME,
                    PC.BOOKED_OPEN_QUANTITY,
                    PC.BOOKED_QUANTITY,
                    S.ISSUER_ID
                FROM
                    Inventory.POSITION_CORE PC
                INNER JOIN
                    Inventory.[SECURITY] S ON S.SECURITY_ID = PC.SECURITY_ID
                INNER JOIN
                    Inventory.SECURITY_CLASS SC ON SC.SECURITY_CLASS_ID = S.SECURITY_CLASS_ID
                WHERE
                    PC.SECURITY_ID = :security_id
                AND
                    PC.BOOK_ID = :book_id
                """

                df_security = execute_query(env, query_security, params={
                    "security_id": security_id,
                    "book_id": book_id
                })

                if not df_security.empty:
                    st.success("✅ CDS Security data retrieved successfully!")

                    # Display as transposed table
                    df_transposed = df_security.T
                    df_transposed.columns = ['Value']
                    st.dataframe(df_transposed, use_container_width=True)

                    # Extract issuer_id for next query (convert to Python int)
                    issuer_id = int(df_security['ISSUER_ID'].iloc[0])

                    # Display key metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Security Class", df_security['SECURITY_CLASS_NAME'].iloc[0])
                    with col2:
                        st.metric("Booked Open Quantity", f"{df_security['BOOKED_OPEN_QUANTITY'].iloc[0]:,.2f}")
                    with col3:
                        st.metric("Booked Quantity", f"{df_security['BOOKED_QUANTITY'].iloc[0]:,.2f}")

                    st.markdown("---")

                    # Query 2: Reference Entity / Issuer / RED CODE
                    st.subheader("2. Reference Entity / Issuer / RED CODE")
                    query_issuer = """
                    SELECT
                        I.ISSUER_NAME,
                        I.LEGAL_ENTITY_ID,
                        LE.LEGAL_NAME,
                        LE.MARKIT_RED_ENTITY
                    FROM
                        Inventory.ISSUER I
                    INNER JOIN
                        Inventory.LEGAL_ENTITY LE ON LE.LEGAL_ENTITY_ID = I.LEGAL_ENTITY_ID
                    WHERE
                        I.ISSUER_ID = :issuer_id
                    """

                    df_issuer = execute_query(env, query_issuer, params={"issuer_id": issuer_id})

                    if not df_issuer.empty:
                        st.success("✅ Issuer data retrieved successfully!")

                        # Display as transposed table
                        df_issuer_transposed = df_issuer.T
                        df_issuer_transposed.columns = ['Value']
                        st.dataframe(df_issuer_transposed, use_container_width=True)

                        # Display issuer metrics
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Issuer Name", df_issuer['ISSUER_NAME'].iloc[0])
                        with col2:
                            st.metric("RED Code", df_issuer['MARKIT_RED_ENTITY'].iloc[0])
                    else:
                        st.warning("⚠️ No issuer data found")

                else:
                    st.warning("⚠️ No data found for this Security ID and Book ID combination")

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

# Footer
st.markdown("---")
st.markdown("*OMS CDS Analysis Tool - Built with Streamlit*")
