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
    ["Book CDS Overview", "Specific Position Lookup"],
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

else:  # Specific Position Lookup mode
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

# Footer
st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns([2, 1, 2])
with footer_col2:
    st.markdown("<div style='text-align: center; color: #888; padding: 1rem;'>📊 OMS CDS Analysis Tool<br/>Built with Streamlit</div>", unsafe_allow_html=True)
