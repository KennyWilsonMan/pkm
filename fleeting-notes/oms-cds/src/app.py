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
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main > div {
        padding-top: 2rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 1rem 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.title("📊 OMS CDS Analysis")
st.markdown("**Interactive Credit Default Swap Position Analytics**")
st.markdown("---")

# Sidebar configuration
st.sidebar.header("⚙️ Configuration")

# Database environment selection
env = st.sidebar.selectbox(
    "Database Environment",
    options=list(SQL_CONNECTIONS.keys()),
    index=1,  # Default to "uat"
    help="Select the database environment to query"
)

# Test connection in an expander
with st.sidebar.expander("🔌 Connection Test", expanded=False):
    if st.button("Test Connection", use_container_width=True):
        with st.spinner("Testing connection..."):
            if test_connection(env):
                st.success(f"✅ Connected to {env.upper()}")
            else:
                st.error(f"❌ Failed to connect to {env.upper()}")

st.sidebar.markdown("---")

# Analysis mode selection
st.sidebar.header("📋 Analysis Mode")
analysis_mode = st.sidebar.radio(
    "Choose Analysis",
    ["Book CDS Overview", "Specific Position Lookup", "CDS Creator"],
    index=0,
    help="Select the type of analysis you want to perform"
)

if analysis_mode == "Specific Position Lookup":
    st.sidebar.info("💡 For direct lookup, enter Security ID and Book ID below")
    st.sidebar.number_input("Security ID", value=24031746, step=1, key="manual_security_id")
    st.sidebar.number_input("Book ID", value=137878, step=1, key="manual_book_id")

# Main content based on analysis mode
if analysis_mode == "Book CDS Overview":
    # Header with environment badge
    col1, col2 = st.columns([3, 1])
    with col1:
        st.header("📚 Books with CDS Positions")
    with col2:
        st.markdown(f"<div style='text-align: right; padding: 1rem;'><span style='background-color: #4CAF50; color: white; padding: 0.5rem 1rem; border-radius: 0.25rem; font-weight: bold;'>{env.upper()}</span></div>", unsafe_allow_html=True)

    # CDS System Overview
    st.markdown("### 📊 CDS System Overview")

    col1, col2 = st.columns(2)

    # Currency Information
    with col1:
        st.markdown("#### 💱 CDS Currencies")
        try:
            query_currencies = """
            SELECT DISTINCT
                C.ISO_CODE
            FROM
                Inventory.SECURITY S
                INNER JOIN Inventory.CURRENCY C ON S.CURRENCY_ID = C.CURRENCY_ID
            WHERE
                S.SECURITY_CLASS_ID = 29  -- Credit Default Swap
                AND S.END_DT > GETDATE()
                AND C.END_DT > GETDATE()
            ORDER BY
                C.ISO_CODE
            """
            df_currencies = execute_query(env, query_currencies)

            if not df_currencies.empty:
                currencies_list = df_currencies['ISO_CODE'].tolist()
                currencies_str = ", ".join(currencies_list)

                st.metric("Total Currencies", len(currencies_list))
                st.info(f"**Currencies:** {currencies_str}")

            # Show SQL query in expander
            with st.expander("🔍 View SQL Query", expanded=False):
                st.code(query_currencies, language="sql")
        except Exception as e:
            st.warning(f"⚠️ Unable to load currency information: {str(e)}")

    # Reference Entity Information
    with col2:
        st.markdown("#### 🏢 Reference Entities")
        try:
            query_ref_entities = """
            SELECT
                COUNT(DISTINCT I.ISSUER_ID) AS Total_Reference_Entities,
                COUNT(DISTINCT S.SECURITY_ID) AS Total_CDS_Securities
            FROM
                Inventory.SECURITY S
                INNER JOIN Inventory.ISSUER I ON S.ISSUER_ID = I.ISSUER_ID
            WHERE
                S.SECURITY_CLASS_ID = 29  -- Credit Default Swap
                AND S.END_DT > GETDATE()
                AND I.END_DT > GETDATE()
            """
            df_ref_entities = execute_query(env, query_ref_entities)

            if not df_ref_entities.empty:
                total_entities = int(df_ref_entities['Total_Reference_Entities'].iloc[0])
                total_securities = int(df_ref_entities['Total_CDS_Securities'].iloc[0])

                st.metric("Total Reference Entities", f"{total_entities:,}")
                st.info(f"**CDS Securities:** {total_securities:,}")

            # Show SQL query in expander
            with st.expander("🔍 View SQL Query", expanded=False):
                st.code(query_ref_entities, language="sql")
        except Exception as e:
            st.warning(f"⚠️ Unable to load reference entity information: {str(e)}")

    # Top Reference Entities by CDS count
    st.markdown("#### 🔝 Top 10 Reference Entities by CDS Count")
    try:
        query_top_entities = """
        SELECT TOP 10
            I.ISSUER_NAME,
            COUNT(DISTINCT S.SECURITY_ID) AS CDS_Count
        FROM
            Inventory.SECURITY S
            INNER JOIN Inventory.ISSUER I ON S.ISSUER_ID = I.ISSUER_ID
        WHERE
            S.SECURITY_CLASS_ID = 29  -- Credit Default Swap
            AND S.END_DT > GETDATE()
            AND I.END_DT > GETDATE()
        GROUP BY
            I.ISSUER_NAME
        ORDER BY
            CDS_Count DESC
        """
        df_top_entities = execute_query(env, query_top_entities)

        if not df_top_entities.empty:
            st.dataframe(
                df_top_entities.style.format({
                    'CDS_Count': '{:,}'
                }),
                use_container_width=True,
                hide_index=True,
                height=400
            )

        # Show SQL query in expander
        with st.expander("🔍 View SQL Query", expanded=False):
            st.code(query_top_entities, language="sql")
    except Exception as e:
        st.warning(f"⚠️ Unable to load top reference entities: {str(e)}")

    st.markdown("---")

    # Filters section
    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Filters")

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

    # Get list of securities from recent positions in the selected book
    # This matches the positions table so all visible positions have their securities in the dropdown
    if selected_book != "None":
        try:
            book_id_for_securities = book_ids.get(selected_book)
            if book_id_for_securities:
                query_securities = f"""
                SELECT DISTINCT
                    s.SECURITY_ID,
                    s.SECURITY_NAME,
                    MAX(p.START_DT) AS Latest_Position_Date
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
                    Latest_Position_Date DESC
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
                entity_msg = f" for **{selected_entity}**" if selected_entity != "All" else ""
                st.success(f"✅ Found **{len(df_cds)}** books with non-zero CDS positions{entity_msg}")

                # Show SQL query in expander
                with st.expander("🔍 View SQL Query", expanded=False):
                    st.code(query_cds, language="sql")

                # Display metrics in a more prominent way
                st.markdown("#### 📈 Portfolio Summary")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    total_positions = df_cds['CDS_Positions'].sum()
                    st.metric(
                        "Total Positions",
                        f"{total_positions:,}",
                        help="Sum of all CDS positions across selected books"
                    )
                with col2:
                    total_securities = df_cds['Unique_Securities'].sum()
                    st.metric(
                        "Unique Securities",
                        f"{total_securities:,}",
                        help="Number of distinct securities"
                    )
                with col3:
                    total_issuers = df_cds['Unique_Issuers'].sum()
                    st.metric(
                        "Unique Issuers",
                        f"{total_issuers:,}",
                        help="Number of distinct reference entities"
                    )
                with col4:
                    avg_positions = total_positions / len(df_cds) if len(df_cds) > 0 else 0
                    st.metric(
                        "Avg Positions/Book",
                        f"{avg_positions:,.1f}",
                        help="Average number of positions per book"
                    )

                st.markdown("---")

                # Display table with better formatting
                st.markdown("#### 📋 Book Details")
                st.dataframe(
                    df_cds.style.format({
                        'CDS_Positions': '{:,}',
                        'Unique_Securities': '{:,}',
                        'Unique_Issuers': '{:,}'
                    }),
                    use_container_width=True,
                    hide_index=True,
                    height=400
                )
            else:
                st.warning("⚠️ No CDS positions found with the current filters")
                st.info("💡 Try selecting a different managing entity or check if there are active positions in the database.")

            # Show positions for selected book (always show when book is selected)
            if selected_book != "None":
                st.markdown("---")
                book_id = book_ids.get(selected_book)
                if book_id:
                    # Section header
                    st.markdown(f"### 🔍 Recent CDS Positions")
                    st.info(f"**Book:** {selected_book}")
                    st.caption("Showing 10 most recent positions with non-zero quantities, ordered by start date")

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

                    # Show SQL query in expander
                    with st.expander("🔍 View SQL Query", expanded=False):
                        st.code(query_positions, language="sql")

                    if not df_positions.empty:
                        # Position summary metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Positions Shown", len(df_positions))
                        with col2:
                            total_qty = df_positions['BOOKED_QUANTITY'].sum()
                            st.metric("Total Quantity", f"{total_qty:,.2f}")
                        with col3:
                            unique_securities = df_positions['SECURITY_ID'].nunique()
                            st.metric("Unique Securities", unique_securities)

                        # Format the dataframe
                        df_positions['START_DT'] = pd.to_datetime(df_positions['START_DT']).dt.strftime('%Y-%m-%d %H:%M')

                        # Reorder columns
                        column_order = ['SECURITY_NAME', 'ISSUER_NAME', 'BOOKED_QUANTITY', 'START_DT', 'POSITION_ID', 'BOOK_ID', 'SECURITY_ID']
                        df_positions = df_positions[column_order]

                        # Display table with improved styling
                        st.dataframe(
                            df_positions.style.format({
                                'BOOKED_QUANTITY': '{:,.2f}'
                            }),
                            use_container_width=True,
                            hide_index=True,
                            height=400
                        )
                    else:
                        st.info("ℹ️ No active positions found for this book")
                        st.caption("This may indicate all positions have been closed or have zero quantities.")

            # Show CDS details for selected security (in addition to positions table)
            if selected_book != "None" and selected_security != "None":
                st.markdown("---")
                security_id = security_ids.get(selected_security)
                book_id = book_ids.get(selected_book)
                if security_id and book_id:
                    # Header with security name
                    st.subheader("🎯 CDS Position Details")
                    st.info(f"**Security:** {selected_security}")

                    # Query 1: CDS Security and Position (with reference obligation ID, currencies, maturity, coupon, identifiers, position details)
                    query_security_detail = f"""
                    SELECT
                        PC.POSITION_ID,
                        S.SECURITY_NAME,
                        SC.SECURITY_CLASS_NAME,
                        PC.BOOKED_OPEN_QUANTITY,
                        PC.BOOKED_QUANTITY,
                        PC.MARK_VALUE,
                        PC.MARK_PRICE,
                        S.ISSUER_ID,
                        SFI.REFERENCE_OBLIGATION_SECURITY_ID,
                        SEC_CURR.ISO_CODE AS SECURITY_CURRENCY,
                        FUND_CURR.ISO_CODE AS FUND_CURRENCY,
                        S.MATURITY_DATE,
                        SFI.COUPON_RATE,
                        S.ISIN,
                        S.CUSIP,
                        S.BB_GLOBAL AS FIGI
                    FROM
                        Inventory.POSITION_CORE PC
                    INNER JOIN
                        Inventory.[SECURITY] S ON S.SECURITY_ID = PC.SECURITY_ID
                    INNER JOIN
                        Inventory.SECURITY_CLASS SC ON SC.SECURITY_CLASS_ID = S.SECURITY_CLASS_ID
                    INNER JOIN
                        Inventory.BOOK B ON PC.BOOK_ID = B.BOOK_ID
                    INNER JOIN
                        Inventory.FUND F ON B.FUND_ID = F.FUND_ID
                    LEFT JOIN
                        Inventory.SECURITY_FIXED_INCOME SFI ON S.SECURITY_ID = SFI.SECURITY_ID AND SFI.END_DT > GETDATE()
                    LEFT JOIN
                        Inventory.CURRENCY SEC_CURR ON S.CURRENCY_ID = SEC_CURR.CURRENCY_ID AND SEC_CURR.END_DT > GETDATE()
                    LEFT JOIN
                        Inventory.CURRENCY FUND_CURR ON F.CURRENCY_ID = FUND_CURR.CURRENCY_ID AND FUND_CURR.END_DT > GETDATE()
                    WHERE
                        PC.SECURITY_ID = {security_id}
                    AND
                        PC.BOOK_ID = {book_id}
                    """

                    # Query 2: Reference Entity / Issuer / RED CODE
                    query_issuer_template = """
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

                    # Query 3: Reference Obligation Security Details
                    query_ref_obligation_template = """
                    SELECT
                        REF_SEC.SECURITY_ID,
                        REF_SEC.SECURITY_NAME,
                        REF_SEC_CLASS.SECURITY_CLASS_NAME,
                        REF_ISSUER.ISSUER_NAME,
                        REF_SEC.ISIN,
                        REF_SEC.CUSIP,
                        REF_SEC.BB_GLOBAL AS FIGI,
                        REF_SEC.MATURITY_DATE,
                        REF_SFI.COUPON_RATE,
                        REF_CURR.ISO_CODE AS CURRENCY
                    FROM
                        Inventory.SECURITY_FIXED_INCOME SFI
                    INNER JOIN
                        Inventory.[SECURITY] REF_SEC ON REF_SEC.SECURITY_ID = SFI.REFERENCE_OBLIGATION_SECURITY_ID
                    INNER JOIN
                        Inventory.SECURITY_CLASS REF_SEC_CLASS ON REF_SEC_CLASS.SECURITY_CLASS_ID = REF_SEC.SECURITY_CLASS_ID
                    LEFT JOIN
                        Inventory.ISSUER REF_ISSUER ON REF_SEC.ISSUER_ID = REF_ISSUER.ISSUER_ID
                    LEFT JOIN
                        Inventory.SECURITY_FIXED_INCOME REF_SFI ON REF_SEC.SECURITY_ID = REF_SFI.SECURITY_ID AND REF_SFI.END_DT > GETDATE()
                    LEFT JOIN
                        Inventory.CURRENCY REF_CURR ON REF_SEC.CURRENCY_ID = REF_CURR.CURRENCY_ID AND REF_CURR.END_DT > GETDATE()
                    WHERE
                        SFI.SECURITY_ID = {cds_security_id}
                        AND SFI.END_DT > GETDATE()
                    """

                    df_security_detail = execute_query(env, query_security_detail)

                    # Show SQL queries in expander
                    with st.expander("🔍 View SQL Queries", expanded=False):
                        st.markdown("**CDS Security & Position Query:**")
                        st.code(query_security_detail, language="sql")
                        st.markdown("---")
                        st.markdown("**Reference Entity Query:**")
                        st.code(query_issuer_template, language="sql")
                        st.markdown("---")
                        st.markdown("**Reference Obligation Query:**")
                        st.code(query_ref_obligation_template, language="sql")

                    if not df_security_detail.empty:
                        # Extract data
                        position_id = df_security_detail['POSITION_ID'].iloc[0]
                        security_name = df_security_detail['SECURITY_NAME'].iloc[0]
                        security_class = df_security_detail['SECURITY_CLASS_NAME'].iloc[0]
                        booked_open_qty = df_security_detail['BOOKED_OPEN_QUANTITY'].iloc[0]
                        booked_qty = df_security_detail['BOOKED_QUANTITY'].iloc[0]
                        mark_value = df_security_detail['MARK_VALUE'].iloc[0]
                        mark_price = df_security_detail['MARK_PRICE'].iloc[0]
                        issuer_id = int(df_security_detail['ISSUER_ID'].iloc[0])
                        ref_obligation_id = df_security_detail['REFERENCE_OBLIGATION_SECURITY_ID'].iloc[0]
                        security_currency = df_security_detail['SECURITY_CURRENCY'].iloc[0]
                        fund_currency = df_security_detail['FUND_CURRENCY'].iloc[0]
                        maturity_date = df_security_detail['MATURITY_DATE'].iloc[0]
                        coupon_rate = df_security_detail['COUPON_RATE'].iloc[0]
                        cds_isin = df_security_detail['ISIN'].iloc[0]
                        cds_cusip = df_security_detail['CUSIP'].iloc[0]
                        cds_figi = df_security_detail['FIGI'].iloc[0]

                        # Get issuer data
                        query_issuer = query_issuer_template.format(issuer_id=issuer_id)
                        df_issuer = execute_query(env, query_issuer)

                        # Get reference obligation data if available
                        df_ref_obligation = pd.DataFrame()
                        if pd.notna(ref_obligation_id):
                            query_ref_obligation = query_ref_obligation_template.format(cds_security_id=security_id)
                            df_ref_obligation = execute_query(env, query_ref_obligation)

                        # Create tabs for organized display
                        tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🏢 Reference Entity", "📄 Reference Obligation", "📋 Raw Data"])

                        with tab1:
                            st.markdown("### Position Summary")

                            # Row 1: IDs
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric(
                                    "Position ID",
                                    position_id,
                                    help="Unique identifier for this position"
                                )
                            with col2:
                                st.metric(
                                    "Security ID",
                                    security_id,
                                    help="Unique identifier for this security"
                                )
                            with col3:
                                st.metric(
                                    "Book ID",
                                    book_id,
                                    help="Book where this position is held"
                                )

                            # Row 2: Quantities
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric(
                                    "Booked Open Quantity",
                                    f"{booked_open_qty:,.2f}",
                                    help="Current open quantity"
                                )
                            with col2:
                                st.metric(
                                    "Booked Quantity",
                                    f"{booked_qty:,.2f}",
                                    delta=f"{booked_qty - booked_open_qty:,.2f}" if booked_qty != booked_open_qty else None,
                                    help="Total booked quantity"
                                )

                            # Row 3: Mark Value and Price
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric(
                                    "Mark Value",
                                    f"{mark_value:,.2f}" if pd.notna(mark_value) else "N/A",
                                    help="Current mark-to-market value"
                                )
                            with col2:
                                st.metric(
                                    "Mark Price",
                                    f"{mark_price:,.4f}" if pd.notna(mark_price) else "N/A",
                                    help="Current mark-to-market price"
                                )

                            # Row 4: Fund Currency
                            st.metric(
                                "Fund Currency",
                                fund_currency if pd.notna(fund_currency) else "N/A",
                                help="Base currency of the fund/book"
                            )

                            st.markdown("---")

                            # Security & Currency details
                            st.markdown("### Security Information")

                            # Row 1: Security Name and Class
                            info_col1, info_col2 = st.columns(2)
                            with info_col1:
                                st.metric(
                                    "Security Name",
                                    security_name[:50] + "..." if len(security_name) > 50 else security_name,
                                    help=security_name if len(security_name) > 50 else "Name of the CDS security"
                                )
                            with info_col2:
                                st.metric(
                                    "Security Class",
                                    security_class,
                                    help="Type of security instrument"
                                )

                            # Row 2: Security Currency
                            st.metric(
                                "Security Currency",
                                security_currency if pd.notna(security_currency) else "N/A",
                                help="Currency in which the security is denominated"
                            )

                            # Row 3: Maturity Date and Coupon Rate
                            mat_col1, mat_col2 = st.columns(2)
                            with mat_col1:
                                if pd.notna(maturity_date):
                                    formatted_maturity = pd.to_datetime(maturity_date).strftime('%Y-%m-%d')
                                    st.metric(
                                        "Maturity Date",
                                        formatted_maturity,
                                        help="Maturity date of the CDS contract"
                                    )
                                else:
                                    st.metric("Maturity Date", "N/A", help="Maturity date not available")
                            with mat_col2:
                                st.metric(
                                    "Coupon Rate",
                                    f"{coupon_rate:.4f}%" if pd.notna(coupon_rate) else "N/A",
                                    help="Annual coupon rate of the CDS"
                                )

                            # Row 4: Security Identifiers (ISIN, CUSIP, FIGI)
                            id_col1, id_col2, id_col3 = st.columns(3)
                            with id_col1:
                                st.metric(
                                    "ISIN",
                                    cds_isin if pd.notna(cds_isin) else "N/A",
                                    help="International Securities Identification Number"
                                )
                            with id_col2:
                                st.metric(
                                    "CUSIP",
                                    cds_cusip if pd.notna(cds_cusip) else "N/A",
                                    help="Committee on Uniform Securities Identification Procedures number"
                                )
                            with id_col3:
                                st.metric(
                                    "FIGI",
                                    cds_figi if pd.notna(cds_figi) else "N/A",
                                    help="Financial Instrument Global Identifier (Bloomberg)"
                                )

                        with tab2:
                            if not df_issuer.empty:
                                st.markdown("### Reference Entity Details")

                                # Row 1: Issuer Name and Legal Name
                                iss_col1, iss_col2 = st.columns(2)
                                with iss_col1:
                                    issuer_name = df_issuer['ISSUER_NAME'].iloc[0]
                                    st.metric(
                                        "Issuer Name",
                                        issuer_name[:50] + "..." if len(issuer_name) > 50 else issuer_name,
                                        help=issuer_name if len(issuer_name) > 50 else "Name of the issuing entity"
                                    )
                                with iss_col2:
                                    legal_name = df_issuer['LEGAL_NAME'].iloc[0]
                                    st.metric(
                                        "Legal Name",
                                        legal_name[:50] + "..." if len(legal_name) > 50 else legal_name,
                                        help=legal_name if len(legal_name) > 50 else "Full legal name of the entity"
                                    )

                                # Row 2: Legal Entity ID and RED Code
                                id_col1, id_col2 = st.columns(2)
                                with id_col1:
                                    st.metric(
                                        "Legal Entity ID",
                                        df_issuer['LEGAL_ENTITY_ID'].iloc[0],
                                        help="Legal entity identifier"
                                    )
                                with id_col2:
                                    red_code = df_issuer['MARKIT_RED_ENTITY'].iloc[0]
                                    st.metric(
                                        "RED Code",
                                        red_code if pd.notna(red_code) else "N/A",
                                        help="Markit RED (Reference Entity Database) code"
                                    )

                            else:
                                st.warning("⚠️ No issuer data found for this security")

                        with tab3:
                            st.markdown("### Reference Obligation Details")

                            if not df_ref_obligation.empty:
                                # Row 1: Security Name and Security Class
                                ref_col1, ref_col2 = st.columns(2)
                                with ref_col1:
                                    ref_sec_name = df_ref_obligation['SECURITY_NAME'].iloc[0]
                                    st.metric(
                                        "Security Name",
                                        ref_sec_name[:50] + "..." if len(ref_sec_name) > 50 else ref_sec_name,
                                        help=ref_sec_name if len(ref_sec_name) > 50 else "Name of the reference obligation security"
                                    )
                                with ref_col2:
                                    ref_sec_class = df_ref_obligation['SECURITY_CLASS_NAME'].iloc[0]
                                    st.metric(
                                        "Security Class",
                                        ref_sec_class,
                                        help="Type of security"
                                    )

                                # Row 2: Issuer and Security ID
                                iss_col1, iss_col2 = st.columns(2)
                                with iss_col1:
                                    ref_issuer_name = df_ref_obligation['ISSUER_NAME'].iloc[0]
                                    if pd.notna(ref_issuer_name):
                                        st.metric(
                                            "Issuer",
                                            ref_issuer_name[:50] + "..." if len(ref_issuer_name) > 50 else ref_issuer_name,
                                            help=ref_issuer_name if len(ref_issuer_name) > 50 else "Issuer of the reference obligation"
                                        )
                                    else:
                                        st.metric("Issuer", "N/A", help="Issuer information not available")
                                with iss_col2:
                                    st.metric(
                                        "Security ID",
                                        df_ref_obligation['SECURITY_ID'].iloc[0],
                                        help="Unique identifier for the reference obligation"
                                    )

                                # Row 3: Currency
                                ref_currency = df_ref_obligation['CURRENCY'].iloc[0]
                                st.metric(
                                    "Currency",
                                    ref_currency if pd.notna(ref_currency) else "N/A",
                                    help="Currency in which the reference obligation is denominated"
                                )

                                # Row 4: Maturity Date and Coupon Rate
                                mat_col1, mat_col2 = st.columns(2)
                                with mat_col1:
                                    ref_maturity = df_ref_obligation['MATURITY_DATE'].iloc[0]
                                    if pd.notna(ref_maturity):
                                        formatted_ref_maturity = pd.to_datetime(ref_maturity).strftime('%Y-%m-%d')
                                        st.metric(
                                            "Maturity Date",
                                            formatted_ref_maturity,
                                            help="Maturity date of the reference obligation"
                                        )
                                    else:
                                        st.metric("Maturity Date", "N/A", help="Maturity date not available")
                                with mat_col2:
                                    ref_coupon = df_ref_obligation['COUPON_RATE'].iloc[0]
                                    st.metric(
                                        "Coupon Rate",
                                        f"{ref_coupon:.4f}%" if pd.notna(ref_coupon) else "N/A",
                                        help="Annual coupon rate"
                                    )

                                # Row 5: Security Identifiers (ISIN, CUSIP, FIGI)
                                ident_col1, ident_col2, ident_col3 = st.columns(3)
                                with ident_col1:
                                    ref_isin = df_ref_obligation['ISIN'].iloc[0]
                                    st.metric(
                                        "ISIN",
                                        ref_isin if pd.notna(ref_isin) else "N/A",
                                        help="International Securities Identification Number"
                                    )
                                with ident_col2:
                                    ref_cusip = df_ref_obligation['CUSIP'].iloc[0]
                                    st.metric(
                                        "CUSIP",
                                        ref_cusip if pd.notna(ref_cusip) else "N/A",
                                        help="Committee on Uniform Securities Identification Procedures number"
                                    )
                                with ident_col3:
                                    ref_figi = df_ref_obligation['FIGI'].iloc[0]
                                    st.metric(
                                        "FIGI",
                                        ref_figi if pd.notna(ref_figi) else "N/A",
                                        help="Financial Instrument Global Identifier (Bloomberg)"
                                    )

                            elif pd.isna(ref_obligation_id):
                                st.info("ℹ️ No reference obligation is defined for this CDS")
                                st.caption("This CDS may not have a specific reference obligation security linked in the system.")
                            else:
                                st.warning("⚠️ Reference obligation data not found")
                                st.caption(f"Reference Obligation Security ID: {int(ref_obligation_id)}")

                        with tab4:
                            st.markdown("### Security & Position Data")
                            st.dataframe(
                                df_security_detail.style.format({
                                    'BOOKED_OPEN_QUANTITY': '{:,.2f}',
                                    'BOOKED_QUANTITY': '{:,.2f}'
                                }),
                                use_container_width=True,
                                hide_index=True
                            )

                            if not df_issuer.empty:
                                st.markdown("### Issuer & Legal Entity Data")
                                st.dataframe(
                                    df_issuer,
                                    use_container_width=True,
                                    hide_index=True
                                )

                    else:
                        st.error("❌ No position data found for this security/book combination")
                        st.info("💡 Please verify the Security ID and Book ID are correct and that an active position exists.")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

elif analysis_mode == "Specific Position Lookup":
    st.info("💡 **Direct Position Lookup Mode** - Enter Security ID and Book ID to query specific CDS position details")

    # Get the values from sidebar
    security_id = st.session_state.get('manual_security_id', 24031746)
    book_id = st.session_state.get('manual_book_id', 137878)

    # Display input values
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Security ID", security_id, help="Unique identifier for the CDS security")
    with col2:
        st.metric("Book ID", book_id, help="Book where the position is held")

    st.markdown("---")

    # Query button
    if st.button("🔍 Query CDS Details", type="primary", use_container_width=True):
        try:
            with st.spinner(f"Querying {env.upper()} database..."):

                # Query 1: CDS Security and Position (with reference obligation ID, currencies, maturity, coupon, identifiers, position details)
                query_security = """
                SELECT
                    PC.POSITION_ID,
                    S.SECURITY_NAME,
                    SC.SECURITY_CLASS_NAME,
                    PC.BOOKED_OPEN_QUANTITY,
                    PC.BOOKED_QUANTITY,
                    PC.MARK_VALUE,
                    PC.MARK_PRICE,
                    S.ISSUER_ID,
                    SFI.REFERENCE_OBLIGATION_SECURITY_ID,
                    SEC_CURR.ISO_CODE AS SECURITY_CURRENCY,
                    FUND_CURR.ISO_CODE AS FUND_CURRENCY,
                    S.MATURITY_DATE,
                    SFI.COUPON_RATE,
                    S.ISIN,
                    S.CUSIP,
                    S.BB_GLOBAL AS FIGI
                FROM
                    Inventory.POSITION_CORE PC
                INNER JOIN
                    Inventory.[SECURITY] S ON S.SECURITY_ID = PC.SECURITY_ID
                INNER JOIN
                    Inventory.SECURITY_CLASS SC ON SC.SECURITY_CLASS_ID = S.SECURITY_CLASS_ID
                INNER JOIN
                    Inventory.BOOK B ON PC.BOOK_ID = B.BOOK_ID
                INNER JOIN
                    Inventory.FUND F ON B.FUND_ID = F.FUND_ID
                LEFT JOIN
                    Inventory.SECURITY_FIXED_INCOME SFI ON S.SECURITY_ID = SFI.SECURITY_ID AND SFI.END_DT > GETDATE()
                LEFT JOIN
                    Inventory.CURRENCY SEC_CURR ON S.CURRENCY_ID = SEC_CURR.CURRENCY_ID AND SEC_CURR.END_DT > GETDATE()
                LEFT JOIN
                    Inventory.CURRENCY FUND_CURR ON F.CURRENCY_ID = FUND_CURR.CURRENCY_ID AND FUND_CURR.END_DT > GETDATE()
                WHERE
                    PC.SECURITY_ID = :security_id
                AND
                    PC.BOOK_ID = :book_id
                """

                # Query 2: Reference Entity / Issuer / RED CODE
                query_issuer_template = """
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

                # Query 3: Reference Obligation Security Details
                query_ref_obligation_template = """
                SELECT
                    REF_SEC.SECURITY_ID,
                    REF_SEC.SECURITY_NAME,
                    REF_SEC_CLASS.SECURITY_CLASS_NAME,
                    REF_ISSUER.ISSUER_NAME,
                    REF_SEC.ISIN,
                    REF_SEC.CUSIP,
                    REF_SEC.BB_GLOBAL AS FIGI,
                    REF_SEC.MATURITY_DATE,
                    REF_SFI.COUPON_RATE,
                    REF_CURR.ISO_CODE AS CURRENCY
                FROM
                    Inventory.SECURITY_FIXED_INCOME SFI
                INNER JOIN
                    Inventory.[SECURITY] REF_SEC ON REF_SEC.SECURITY_ID = SFI.REFERENCE_OBLIGATION_SECURITY_ID
                INNER JOIN
                    Inventory.SECURITY_CLASS REF_SEC_CLASS ON REF_SEC_CLASS.SECURITY_CLASS_ID = REF_SEC.SECURITY_CLASS_ID
                LEFT JOIN
                    Inventory.ISSUER REF_ISSUER ON REF_SEC.ISSUER_ID = REF_ISSUER.ISSUER_ID
                LEFT JOIN
                    Inventory.SECURITY_FIXED_INCOME REF_SFI ON REF_SEC.SECURITY_ID = REF_SFI.SECURITY_ID AND REF_SFI.END_DT > GETDATE()
                LEFT JOIN
                    Inventory.CURRENCY REF_CURR ON REF_SEC.CURRENCY_ID = REF_CURR.CURRENCY_ID AND REF_CURR.END_DT > GETDATE()
                WHERE
                    SFI.SECURITY_ID = :cds_security_id
                    AND SFI.END_DT > GETDATE()
                """

                df_security = execute_query(env, query_security, params={
                    "security_id": security_id,
                    "book_id": book_id
                })

                # Show SQL queries in expander
                with st.expander("🔍 View SQL Queries", expanded=False):
                    st.markdown("**CDS Security & Position Query:**")
                    st.code(query_security, language="sql")
                    st.markdown("---")
                    st.markdown("**Reference Entity Query:**")
                    st.code(query_issuer_template, language="sql")
                    st.markdown("---")
                    st.markdown("**Reference Obligation Query:**")
                    st.code(query_ref_obligation_template, language="sql")

                if not df_security.empty:
                    # Extract data
                    position_id = df_security['POSITION_ID'].iloc[0]
                    security_name = df_security['SECURITY_NAME'].iloc[0]
                    security_class = df_security['SECURITY_CLASS_NAME'].iloc[0]
                    booked_open_qty = df_security['BOOKED_OPEN_QUANTITY'].iloc[0]
                    booked_qty = df_security['BOOKED_QUANTITY'].iloc[0]
                    mark_value = df_security['MARK_VALUE'].iloc[0]
                    mark_price = df_security['MARK_PRICE'].iloc[0]
                    issuer_id = int(df_security['ISSUER_ID'].iloc[0])
                    ref_obligation_id = df_security['REFERENCE_OBLIGATION_SECURITY_ID'].iloc[0]
                    security_currency = df_security['SECURITY_CURRENCY'].iloc[0]
                    fund_currency = df_security['FUND_CURRENCY'].iloc[0]
                    maturity_date = df_security['MATURITY_DATE'].iloc[0]
                    coupon_rate = df_security['COUPON_RATE'].iloc[0]
                    cds_isin = df_security['ISIN'].iloc[0]
                    cds_cusip = df_security['CUSIP'].iloc[0]
                    cds_figi = df_security['FIGI'].iloc[0]

                    # Get issuer data
                    df_issuer = execute_query(env, query_issuer_template, params={"issuer_id": issuer_id})

                    # Get reference obligation data if available
                    df_ref_obligation = pd.DataFrame()
                    if pd.notna(ref_obligation_id):
                        df_ref_obligation = execute_query(env, query_ref_obligation_template, params={"cds_security_id": security_id})

                    # Success message
                    st.success("✅ CDS position data retrieved successfully!")

                    # Create tabs for organized display
                    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🏢 Reference Entity", "📄 Reference Obligation", "📋 Raw Data"])

                    with tab1:
                        st.markdown("### Position Summary")

                        # Row 1: IDs
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric(
                                "Position ID",
                                position_id,
                                help="Unique identifier for this position"
                            )
                        with col2:
                            st.metric(
                                "Security ID",
                                security_id,
                                help="Unique identifier for this security"
                            )
                        with col3:
                            st.metric(
                                "Book ID",
                                book_id,
                                help="Book where this position is held"
                            )

                        # Row 2: Quantities
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric(
                                "Booked Open Quantity",
                                f"{booked_open_qty:,.2f}",
                                help="Current open quantity"
                            )
                        with col2:
                            st.metric(
                                "Booked Quantity",
                                f"{booked_qty:,.2f}",
                                delta=f"{booked_qty - booked_open_qty:,.2f}" if booked_qty != booked_open_qty else None,
                                help="Total booked quantity"
                            )

                        # Row 3: Mark Value and Price
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric(
                                "Mark Value",
                                f"{mark_value:,.2f}" if pd.notna(mark_value) else "N/A",
                                help="Current mark-to-market value"
                            )
                        with col2:
                            st.metric(
                                "Mark Price",
                                f"{mark_price:,.4f}" if pd.notna(mark_price) else "N/A",
                                help="Current mark-to-market price"
                            )

                        # Row 4: Fund Currency
                        st.metric(
                            "Fund Currency",
                            fund_currency if pd.notna(fund_currency) else "N/A",
                            help="Base currency of the fund/book"
                        )

                        st.markdown("---")

                        # Security & Currency details
                        st.markdown("### Security Information")

                        # Row 1: Security Name and Class
                        info_col1, info_col2 = st.columns(2)
                        with info_col1:
                            st.metric(
                                "Security Name",
                                security_name[:50] + "..." if len(security_name) > 50 else security_name,
                                help=security_name if len(security_name) > 50 else "Name of the CDS security"
                            )
                        with info_col2:
                            st.metric(
                                "Security Class",
                                security_class,
                                help="Type of security instrument"
                            )

                        # Row 2: Security Currency
                        st.metric(
                            "Security Currency",
                            security_currency if pd.notna(security_currency) else "N/A",
                            help="Currency in which the security is denominated"
                        )

                        # Row 3: Maturity Date and Coupon Rate
                        mat_col1, mat_col2 = st.columns(2)
                        with mat_col1:
                            if pd.notna(maturity_date):
                                formatted_maturity = pd.to_datetime(maturity_date).strftime('%Y-%m-%d')
                                st.metric(
                                    "Maturity Date",
                                    formatted_maturity,
                                    help="Maturity date of the CDS contract"
                                )
                            else:
                                st.metric("Maturity Date", "N/A", help="Maturity date not available")
                        with mat_col2:
                            st.metric(
                                "Coupon Rate",
                                f"{coupon_rate:.4f}%" if pd.notna(coupon_rate) else "N/A",
                                help="Annual coupon rate of the CDS"
                            )

                        # Row 4: Security Identifiers (ISIN, CUSIP, FIGI)
                        id_col1, id_col2, id_col3 = st.columns(3)
                        with id_col1:
                            st.metric(
                                "ISIN",
                                cds_isin if pd.notna(cds_isin) else "N/A",
                                help="International Securities Identification Number"
                            )
                        with id_col2:
                            st.metric(
                                "CUSIP",
                                cds_cusip if pd.notna(cds_cusip) else "N/A",
                                help="Committee on Uniform Securities Identification Procedures number"
                            )
                        with id_col3:
                            st.metric(
                                "FIGI",
                                cds_figi if pd.notna(cds_figi) else "N/A",
                                help="Financial Instrument Global Identifier (Bloomberg)"
                            )

                    with tab2:
                        if not df_issuer.empty:
                            st.markdown("### Reference Entity Details")

                            # Row 1: Issuer Name and Legal Name
                            iss_col1, iss_col2 = st.columns(2)
                            with iss_col1:
                                issuer_name = df_issuer['ISSUER_NAME'].iloc[0]
                                st.metric(
                                    "Issuer Name",
                                    issuer_name[:50] + "..." if len(issuer_name) > 50 else issuer_name,
                                    help=issuer_name if len(issuer_name) > 50 else "Name of the issuing entity"
                                )
                            with iss_col2:
                                legal_name = df_issuer['LEGAL_NAME'].iloc[0]
                                st.metric(
                                    "Legal Name",
                                    legal_name[:50] + "..." if len(legal_name) > 50 else legal_name,
                                    help=legal_name if len(legal_name) > 50 else "Full legal name of the entity"
                                )

                            # Row 2: Legal Entity ID and RED Code
                            id_col1, id_col2 = st.columns(2)
                            with id_col1:
                                st.metric(
                                    "Legal Entity ID",
                                    df_issuer['LEGAL_ENTITY_ID'].iloc[0],
                                    help="Legal entity identifier"
                                )
                            with id_col2:
                                red_code = df_issuer['MARKIT_RED_ENTITY'].iloc[0]
                                st.metric(
                                    "RED Code",
                                    red_code if pd.notna(red_code) else "N/A",
                                    help="Markit RED (Reference Entity Database) code"
                                )

                        else:
                            st.warning("⚠️ No issuer data found for this security")

                    with tab3:
                        st.markdown("### Reference Obligation Details")

                        if not df_ref_obligation.empty:
                            # Row 1: Security Name and Security Class
                            ref_col1, ref_col2 = st.columns(2)
                            with ref_col1:
                                ref_sec_name = df_ref_obligation['SECURITY_NAME'].iloc[0]
                                st.metric(
                                    "Security Name",
                                    ref_sec_name[:50] + "..." if len(ref_sec_name) > 50 else ref_sec_name,
                                    help=ref_sec_name if len(ref_sec_name) > 50 else "Name of the reference obligation security"
                                )
                            with ref_col2:
                                ref_sec_class = df_ref_obligation['SECURITY_CLASS_NAME'].iloc[0]
                                st.metric(
                                    "Security Class",
                                    ref_sec_class,
                                    help="Type of security"
                                )

                            # Row 2: Issuer and Security ID
                            iss_col1, iss_col2 = st.columns(2)
                            with iss_col1:
                                ref_issuer_name = df_ref_obligation['ISSUER_NAME'].iloc[0]
                                if pd.notna(ref_issuer_name):
                                    st.metric(
                                        "Issuer",
                                        ref_issuer_name[:50] + "..." if len(ref_issuer_name) > 50 else ref_issuer_name,
                                        help=ref_issuer_name if len(ref_issuer_name) > 50 else "Issuer of the reference obligation"
                                    )
                                else:
                                    st.metric("Issuer", "N/A", help="Issuer information not available")
                            with iss_col2:
                                st.metric(
                                    "Security ID",
                                    df_ref_obligation['SECURITY_ID'].iloc[0],
                                    help="Unique identifier for the reference obligation"
                                )

                            # Row 3: Currency
                            ref_currency = df_ref_obligation['CURRENCY'].iloc[0]
                            st.metric(
                                "Currency",
                                ref_currency if pd.notna(ref_currency) else "N/A",
                                help="Currency in which the reference obligation is denominated"
                            )

                            # Row 4: Maturity Date and Coupon Rate
                            mat_col1, mat_col2 = st.columns(2)
                            with mat_col1:
                                ref_maturity = df_ref_obligation['MATURITY_DATE'].iloc[0]
                                if pd.notna(ref_maturity):
                                    formatted_ref_maturity = pd.to_datetime(ref_maturity).strftime('%Y-%m-%d')
                                    st.metric(
                                        "Maturity Date",
                                        formatted_ref_maturity,
                                        help="Maturity date of the reference obligation"
                                    )
                                else:
                                    st.metric("Maturity Date", "N/A", help="Maturity date not available")
                            with mat_col2:
                                ref_coupon = df_ref_obligation['COUPON_RATE'].iloc[0]
                                st.metric(
                                    "Coupon Rate",
                                    f"{ref_coupon:.4f}%" if pd.notna(ref_coupon) else "N/A",
                                    help="Annual coupon rate"
                                )

                            # Row 5: Security Identifiers (ISIN, CUSIP, FIGI)
                            ident_col1, ident_col2, ident_col3 = st.columns(3)
                            with ident_col1:
                                ref_isin = df_ref_obligation['ISIN'].iloc[0]
                                st.metric(
                                    "ISIN",
                                    ref_isin if pd.notna(ref_isin) else "N/A",
                                    help="International Securities Identification Number"
                                )
                            with ident_col2:
                                ref_cusip = df_ref_obligation['CUSIP'].iloc[0]
                                st.metric(
                                    "CUSIP",
                                    ref_cusip if pd.notna(ref_cusip) else "N/A",
                                    help="Committee on Uniform Securities Identification Procedures number"
                                )
                            with ident_col3:
                                ref_figi = df_ref_obligation['FIGI'].iloc[0]
                                st.metric(
                                    "FIGI",
                                    ref_figi if pd.notna(ref_figi) else "N/A",
                                    help="Financial Instrument Global Identifier (Bloomberg)"
                                )

                        elif pd.isna(ref_obligation_id):
                            st.info("ℹ️ No reference obligation is defined for this CDS")
                            st.caption("This CDS may not have a specific reference obligation security linked in the system.")
                        else:
                            st.warning("⚠️ Reference obligation data not found")
                            st.caption(f"Reference Obligation Security ID: {int(ref_obligation_id)}")

                    with tab4:
                        st.markdown("### Security & Position Data")
                        st.dataframe(
                            df_security.style.format({
                                'BOOKED_OPEN_QUANTITY': '{:,.2f}',
                                'BOOKED_QUANTITY': '{:,.2f}'
                            }),
                            use_container_width=True,
                            hide_index=True
                        )

                        if not df_issuer.empty:
                            st.markdown("### Issuer & Legal Entity Data")
                            st.dataframe(
                                df_issuer,
                                use_container_width=True,
                                hide_index=True
                            )

                else:
                    st.error("❌ No data found for this Security ID and Book ID combination")
                    st.info("💡 Please verify the Security ID and Book ID are correct and that an active position exists.")

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            with st.expander("🔧 Error Details"):
                import traceback
                st.code(traceback.format_exc())

elif analysis_mode == "CDS Creator":
    # Header with environment badge
    col1, col2 = st.columns([3, 1])
    with col1:
        st.header("🛠️ CDS Creator")
    with col2:
        st.markdown(f"<div style='text-align: right; padding: 1rem;'><span style='background-color: #4CAF50; color: white; padding: 0.5rem 1rem; border-radius: 0.25rem; font-weight: bold;'>{env.upper()}</span></div>", unsafe_allow_html=True)

    st.info("💡 **CDS Creator Tool** - Create new CDS positions")
    st.markdown("---")

    # Get currencies from database
    try:
        query_currencies = """
        SELECT DISTINCT
            C.CURRENCY_ID,
            C.ISO_CODE
        FROM
            Inventory.SECURITY S
            INNER JOIN Inventory.CURRENCY C ON S.CURRENCY_ID = C.CURRENCY_ID
        WHERE
            S.SECURITY_CLASS_ID = 29  -- Credit Default Swap
            AND S.END_DT > GETDATE()
            AND C.END_DT > GETDATE()
        ORDER BY
            C.ISO_CODE
        """
        df_currencies = execute_query(env, query_currencies)

        if not df_currencies.empty:
            # Create mapping of ISO_CODE to CURRENCY_ID
            currency_map = dict(zip(df_currencies['ISO_CODE'], df_currencies['CURRENCY_ID']))
            currency_options = df_currencies['ISO_CODE'].tolist()

            # Get reference entities from database
            try:
                query_ref_entities = """
                SELECT DISTINCT
                    I.ISSUER_ID,
                    I.ISSUER_NAME,
                    I.LEGAL_ENTITY_ID,
                    LE.MARKIT_RED_ENTITY
                FROM
                    Inventory.SECURITY S
                    INNER JOIN Inventory.ISSUER I ON S.ISSUER_ID = I.ISSUER_ID
                    LEFT JOIN Inventory.LEGAL_ENTITY LE ON I.LEGAL_ENTITY_ID = LE.LEGAL_ENTITY_ID
                WHERE
                    S.SECURITY_CLASS_ID = 29  -- Credit Default Swap
                    AND S.END_DT > GETDATE()
                    AND I.END_DT > GETDATE()
                ORDER BY
                    I.ISSUER_NAME
                """
                df_ref_entities = execute_query(env, query_ref_entities)

                if not df_ref_entities.empty:
                    # Create mapping of ISSUER_NAME to tuple of (ISSUER_ID, LEGAL_ENTITY_ID, RED_CODE)
                    issuer_map = {}
                    for _, row in df_ref_entities.iterrows():
                        issuer_map[row['ISSUER_NAME']] = {
                            'issuer_id': row['ISSUER_ID'],
                            'legal_entity_id': row['LEGAL_ENTITY_ID'],
                            'red_code': row['MARKIT_RED_ENTITY']
                        }
                    issuer_options = df_ref_entities['ISSUER_NAME'].tolist()

                    # Generate maturity dates (20th of Mar, Jun, Sep, Dec for next 5 years)
                    from datetime import datetime, date
                    from dateutil.relativedelta import relativedelta

                    today = date.today()
                    maturity_dates = []
                    maturity_map = {}

                    # Generate dates for next 5 years
                    months = [3, 6, 9, 12]  # Mar, Jun, Sep, Dec
                    month_names = {3: 'mar', 6: 'jun', 9: 'sep', 12: 'dec'}

                    for year_offset in range(6):  # Current year + 5 more years
                        target_year = today.year + year_offset
                        for month in months:
                            maturity_date = date(target_year, month, 20)
                            # Only include future dates
                            if maturity_date > today:
                                # Create label like "mar25", "jun25", etc.
                                label = f"{month_names[month]}{str(target_year)[2:]}"
                                maturity_dates.append(label)
                                maturity_map[label] = maturity_date

                    # Create form
                    with st.form("cds_creator_form"):
                        st.markdown("## 📝 CDS Security Information")

                        # Section 1: Basic Security Info
                        st.markdown("### 1️⃣ Security Details")

                        # Row 1: Currency, Maturity, Coupon
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            selected_currency_iso = st.selectbox(
                                "Security Currency *",
                                options=currency_options,
                                help="Currency in which the CDS is denominated"
                            )

                        with col2:
                            selected_maturity_label = st.selectbox(
                                "Maturity Date *",
                                options=maturity_dates,
                                help="Select CDS maturity (20th of Mar/Jun/Sep/Dec)"
                            )

                        with col3:
                            coupon_rate = st.number_input(
                                "Coupon Rate (%) *",
                                min_value=0.0,
                                max_value=100.0,
                                value=1.0,
                                step=0.0001,
                                format="%.4f",
                                help="Annual coupon rate (e.g., 1.0000 for 1%)"
                            )

                        # Row 2: Docs Clause
                        # Create mapping for docs clause
                        docs_clause_map = {
                            "CR - Credit Risk": 1,
                            "MM - Money Market": 2,
                            "MR - Market Risk": 3,
                            "XR - Cross Risk (Exchange Risk)": 4,
                            "CR14 - Credit Risk (14-day)": 5,
                            "MM14 - Money Market (14-day)": 6,
                            "MR14 - Market Risk (14-day)": 7,
                            "XR14 - Cross Risk (14-day, Exchange Risk)": 8
                        }
                        docs_clause_options = list(docs_clause_map.keys())

                        selected_docs_clause_label = st.selectbox(
                            "Docs Clause *",
                            options=docs_clause_options,
                            help="Documentation clause type for the CDS"
                        )

                        st.markdown("---")

                        # Section 2: Reference Entity
                        st.markdown("### 2️⃣ Reference Entity")
                        st.info(f"💡 Searching through {len(issuer_options):,} reference entities")

                        # Use multiselect with max_selections=1 for searchable single selection
                        selected_issuer_names = st.multiselect(
                            "Reference Entity (Issuer) *",
                            options=issuer_options,
                            max_selections=1,
                            help="Type to search through 1,300+ reference entities"
                        )

                        st.markdown("---")

                        # Submit button
                        submitted = st.form_submit_button(
                            "🚀 Create CDS",
                            type="primary",
                            use_container_width=True
                        )

                    # Handle form submission
                    if submitted:
                        # Validation
                        errors = []
                        if not selected_issuer_names:
                            errors.append("Reference Entity is required")

                        if errors:
                            st.error("❌ **Validation Errors:**")
                            for error in errors:
                                st.markdown(f"- {error}")
                        else:
                            # Get the currency_id from the selected ISO code
                            selected_currency_id = currency_map[selected_currency_iso]

                            # Get the issuer data from the selected issuer name
                            selected_issuer_name = selected_issuer_names[0]
                            issuer_data = issuer_map[selected_issuer_name]
                            selected_issuer_id = issuer_data['issuer_id']
                            selected_legal_entity_id = issuer_data['legal_entity_id']
                            selected_red_code = issuer_data['red_code']

                            # Get the maturity date from the selected label
                            selected_maturity_date = maturity_map[selected_maturity_label]

                            # Get the docs clause ID from the selected label
                            selected_docs_clause_id = docs_clause_map[selected_docs_clause_label]

                            st.success("✅ **CDS Information Captured**")

                            # Display all selections
                            st.markdown("### 📋 All Selections")

                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("#### Security Information")
                                st.write(f"**Currency ISO:** {selected_currency_iso}")
                                st.write(f"**Currency ID:** {selected_currency_id}")
                                st.write(f"**Maturity Label:** {selected_maturity_label}")
                                st.write(f"**Maturity Date:** {selected_maturity_date.strftime('%Y-%m-%d')}")
                                st.write(f"**Coupon Rate:** {coupon_rate:.4f}%")
                                st.write(f"**Docs Clause:** {selected_docs_clause_label}")
                                st.write(f"**Docs Clause ID:** {selected_docs_clause_id}")
                            with col2:
                                st.markdown("#### Reference Entity")
                                st.write(f"**Issuer Name:** {selected_issuer_name}")
                                st.write(f"**Issuer ID:** {selected_issuer_id}")
                                st.write(f"**Legal Entity ID:** {selected_legal_entity_id}")
                                st.write(f"**RED Code:** {selected_red_code if pd.notna(selected_red_code) else 'N/A'}")

                            st.markdown("---")

                            # Summary for database insertion
                            st.markdown("### 🗄️ Database Values")
                            st.code(f"""
Security Table:
- CURRENCY_ID: {selected_currency_id}
- MATURITY_DATE: {selected_maturity_date}
- ISSUER_ID: {selected_issuer_id}
- SECURITY_CLASS_ID: 29 (Credit Default Swap)

Security Fixed Income Table:
- COUPON_RATE: {coupon_rate}
- DOCS_CLAUSE_ID: {selected_docs_clause_id}

Issuer/Legal Entity Info:
- LEGAL_ENTITY_ID: {selected_legal_entity_id}
- RED_CODE: {selected_red_code if pd.notna(selected_red_code) else 'N/A'}
                            """, language="python")

                            st.info("💡 These values are ready for database insertion")

                            # Add button to actually create the security
                            st.markdown("---")
                            st.markdown("### 🚀 Create Security")

                            if st.button("📤 Call API to Create CDS Security", type="primary", use_container_width=True):
                                try:
                                    import requests
                                    import subprocess

                                    # Get Kerberos ticket for authentication
                                    st.info("🔐 Authenticating with Kerberos...")

                                    # The SecurityEnvoy API endpoint
                                    api_url = "https://rosa-securityenvoy-n1-dev.maninvestments.ad.man.com:8374/api/GenericSecurity/GetOrCreateCdsOnSingleName"

                                    # Prepare the request payload
                                    payload = {
                                        "currencyId": selected_currency_id,
                                        "maturityDate": selected_maturity_date.strftime('%Y-%m-%d'),
                                        "issuerId": selected_issuer_id,
                                        "couponRate": coupon_rate,
                                        "docsClauseId": selected_docs_clause_id
                                    }

                                    st.write("**Request Payload:**")
                                    st.json(payload)

                                    # Make the API call with Kerberos authentication
                                    # Using requests-kerberos for automatic Kerberos authentication
                                    from requests_kerberos import HTTPKerberosAuth, OPTIONAL

                                    response = requests.post(
                                        api_url,
                                        json=payload,
                                        auth=HTTPKerberosAuth(mutual_authentication=OPTIONAL),
                                        headers={
                                            "Content-Type": "application/json",
                                            "Accept": "application/json"
                                        },
                                        verify=True  # Verify SSL certificate
                                    )

                                    # Check response
                                    if response.status_code in [200, 201]:
                                        st.success("✅ **CDS Security Created Successfully!**")
                                        st.write("**Response:**")
                                        st.json(response.json())

                                        # Display created security details
                                        created_data = response.json()
                                        if 'securityId' in created_data:
                                            st.balloons()
                                            st.success(f"🎉 **Security ID: {created_data['securityId']}**")
                                    else:
                                        st.error(f"❌ **API Error ({response.status_code})**")
                                        st.write("**Error Response:**")
                                        st.code(response.text)

                                except ImportError as e:
                                    st.error("❌ **Missing Required Package**")
                                    st.code("""
# Install required package:
pip install requests-kerberos

# Or in your pegasus environment:
pegasus activate your-env
pip install requests-kerberos
                                    """)
                                    st.info("💡 `requests-kerberos` is needed for Kerberos authentication")

                                except Exception as e:
                                    st.error(f"❌ **Error calling API:** {str(e)}")
                                    with st.expander("🔧 Error Details"):
                                        import traceback
                                        st.code(traceback.format_exc())

                                    st.info("""
💡 **Troubleshooting Steps:**

1. **Check Kerberos ticket:**
   ```bash
   klist
   ```

2. **Renew ticket if expired:**
   ```bash
   kinit
   ```

3. **Verify network access:**
   ```bash
   curl -I https://rosa-securityenvoy-n1-dev.maninvestments.ad.man.com:8374/swagger/index.html
   ```

4. **Check API documentation:**
   https://rosa-securityenvoy-n1-dev.maninvestments.ad.man.com:8374/swagger/index.html
                                    """)

                else:
                    st.warning("⚠️ No reference entities found in the system")

            except Exception as e:
                st.error(f"❌ Error loading reference entities: {str(e)}")
                with st.expander("🔧 Error Details"):
                    import traceback
                    st.code(traceback.format_exc())

        else:
            st.warning("⚠️ No currencies found in the system")

    except Exception as e:
        st.error(f"❌ Error loading currencies: {str(e)}")
        with st.expander("🔧 Error Details"):
            import traceback
            st.code(traceback.format_exc())

# Footer
st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns([2, 1, 2])
with footer_col2:
    st.markdown("<div style='text-align: center; color: #888; padding: 1rem;'>📊 OMS CDS Analysis Tool<br/>Built with Streamlit</div>", unsafe_allow_html=True)
