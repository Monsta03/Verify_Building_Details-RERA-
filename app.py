import streamlit as st
import pandas as pd

# === Page Setup ===
st.set_page_config(page_title="XLSX vs XLSM Verifier", layout="wide")
st.markdown("<style>div.block-container{padding-top:2rem;}</style>", unsafe_allow_html=True)

# === Sidebar ===
with st.sidebar:
    st.title("📊 XLSX vs XLSM Verifier")
    st.markdown("""
    Upload:
    - 🟠 **XLSM**: From ERP (`Building_Unit_Details` sheet)
    - 🔵 **XLSX**: From CA/Consultant (`Table C`)

    This tool compares sold/unsold unit data & values to catch:
    - 🟠 Status mismatches
    - 🔵 Area / Amount mismatches

    **Made for Speed & Accuracy**
    """)

# === Header ===
st.title("📋 XLSX vs XLSM Data Verification Tool")
st.markdown("---")

# === Upload Section in Columns ===
col1, col2 = st.columns(2)
with col1:
    xlsm_file = st.file_uploader("📥 Upload XLSM File", type="xlsm", key="xlsm")
with col2:
    xlsx_file = st.file_uploader("📥 Upload XLSX File", type="xlsx", key="xlsx")

# === If files uploaded ===
if xlsm_file and xlsx_file:
    raw_xlsm_df = pd.read_excel(xlsm_file, sheet_name="Building_Unit_Details", header=None)
    xlsm_df = raw_xlsm_df[7:].copy()
    xlsm_df.columns = raw_xlsm_df.iloc[6].tolist()

    xlsx = pd.ExcelFile(xlsx_file)
    table_c = xlsx.parse("Table C")

    # === Extract Tables (Safe Parsing for Optional Tables) ===
    try:
        sold_start = next(i for i, row in table_c.iterrows() if row.astype(str).str.contains("Flat No", na=False).any())
        sold_end = next(
            (i for i, row in table_c.iterrows()
             if row.astype(str).str.contains("TOTAL", na=False, case=False).any() and i > sold_start),
            sold_start + 1
        )
        sold_table = table_c.iloc[sold_start + 1:sold_end, 0:5].copy()
        sold_table.columns = [
            'Sr.No ', 'Flat No ', 'Carpet Area In Sq.Mtrs ',
            'Unit Consideration as per Agreement /Letter Of Allotment',
            'Received Amount '
        ]
    except StopIteration:
        sold_table = pd.DataFrame(columns=[
            'Sr.No ', 'Flat No ', 'Carpet Area In Sq.Mtrs ',
            'Unit Consideration as per Agreement /Letter Of Allotment',
            'Received Amount '
        ])

    try:
        unsold_start = next(i for i, row in table_c.iterrows() if row.astype(str).str.contains("Flat No /Shop No", na=False).any()) + 2
        unsold_end = next(
            (i for i, row in table_c.iterrows()
             if row.astype(str).str.contains("TOTAL", na=False, case=False).any() and i > unsold_start),
            unsold_start
        )
        unsold_table = table_c.iloc[unsold_start:unsold_end, 0:4].copy()
        unsold_table.columns = [
            'Sr.No ', 'Flat No /Shop No', 'Carpet Area In Sq.Mtrs ',
            'Unit Consideration as per Readyrecknor Rate'
        ]
    except StopIteration:
        unsold_table = pd.DataFrame(columns=[
            'Sr.No ', 'Flat No /Shop No', 'Carpet Area In Sq.Mtrs ',
            'Unit Consideration as per Readyrecknor Rate'
        ])

    # === Filter XLSM ===
    sold_xlsm = xlsm_df[xlsm_df['Unit Sale Category * '].isin(['Sold', 'Booked'])].copy()
    unsold_xlsm = xlsm_df[xlsm_df['Unit Sale Category * '] == 'Unsold'].copy()

    if len(sold_xlsm) == 0 and len(unsold_xlsm) == 0:
        st.error("❌ **CRITICAL**: XLSM file has no Sold/Unsold entries!")
        st.stop()

    # === Rename columns to match ===
    sold_xlsm = sold_xlsm.rename(columns={
        'Apartment / Unit Number*': 'Flat No ',
        'Unit Carpet Area *  (In Sqm)': 'Carpet Area In Sq.Mtrs ',
        'Unit Consideration as per Agreement / Allotment (In INR)': 'Unit Consideration as per Agreement /Letter Of Allotment',
        'Received Amount  (In INR)': 'Received Amount '
    })
    unsold_xlsm = unsold_xlsm.rename(columns={
        'Apartment / Unit Number*': 'Flat No /Shop No',
        'Unit Carpet Area *  (In Sqm)': 'Carpet Area In Sq.Mtrs ',
        'Unit Consideration as per Ready Reckoner Rate (In INR)': 'Unit Consideration as per Readyrecknor Rate'
    })

    # === Cleaning Function ===
    def clean_df(df):
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.strip().str.upper().str.replace("-", " ", regex=False)
            if "Amount" in col or "Consideration" in col or "Area" in col:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df

    sold_table = clean_df(sold_table)
    unsold_table = clean_df(unsold_table)
    sold_xlsm = clean_df(sold_xlsm)
    unsold_xlsm = clean_df(unsold_xlsm)

    # === Helper functions ===
    def check_status_mismatches(sold_table, sold_key, unsold_table, unsold_key, sold_xlsm, unsold_xlsm):
        mismatches = []

        def norm(df, col): return df[col].astype(str).str.strip().str.upper().str.replace("-", " ", regex=False)

        sold_table[sold_key] = norm(sold_table, sold_key)
        unsold_table[unsold_key] = norm(unsold_table, unsold_key)
        sold_xlsm['Flat No '] = norm(sold_xlsm, 'Flat No ')
        unsold_xlsm['Flat No /Shop No'] = norm(unsold_xlsm, 'Flat No /Shop No')

        sold_xlsx_flats = set(sold_table[sold_key])
        unsold_xlsx_flats = set(unsold_table[unsold_key])
        sold_xlsm_flats = set(sold_xlsm['Flat No '])
        unsold_xlsm_flats = set(unsold_xlsm['Flat No /Shop No'])

        for flat in sold_xlsx_flats:
            if flat not in sold_xlsm_flats and flat in unsold_xlsm_flats:
                mismatches.append({"Flat": flat, "Issue": "Sold in XLSX but Unsold in XLSM"})

        for flat in unsold_xlsx_flats:
            if flat not in unsold_xlsm_flats and flat in sold_xlsm_flats:
                mismatches.append({"Flat": flat, "Issue": "Unsold in XLSX but Sold in XLSM"})

        return mismatches

    def compare_values(std_df, source_df, table_name, key_col, fields):
        mismatches = []
        if std_df.empty or source_df.empty:
            return mismatches

        std_df[key_col] = std_df[key_col].astype(str).str.strip().str.upper().str.replace("-", " ", regex=False)
        source_df[key_col] = source_df[key_col].astype(str).str.strip().str.upper().str.replace("-", " ", regex=False)

        for _, row in source_df.iterrows():
            key_val = row[key_col]
            match = std_df[std_df[key_col] == key_val]
            if match.empty:
                continue
            match_row = match.iloc[0]

            for field in fields:
                val1 = row.get(field, 0)
                val2 = match_row.get(field, 0)

                if "Carpet Area" in field:
                    if round(float(val1), 2) != round(float(val2), 2):
                        mismatches.append({
                            "Flat": key_val, "Issue": f"{field} mismatch", "XLSX": val1, "XLSM": val2
                        })
                else:
                    if round(float(val1), 0) != round(float(val2), 0):
                        mismatches.append({
                            "Flat": key_val, "Issue": f"{field} mismatch", "XLSX": val1, "XLSM": val2
                        })
        return mismatches

    # === Run Checks ===
    status_mismatches = check_status_mismatches(
        sold_table, 'Flat No ', unsold_table, 'Flat No /Shop No', sold_xlsm, unsold_xlsm
    )
    sold_mismatches = compare_values(sold_table, sold_xlsm, "SOLD", 'Flat No ', [
        'Carpet Area In Sq.Mtrs ', 'Unit Consideration as per Agreement /Letter Of Allotment', 'Received Amount '
    ])
    unsold_mismatches = compare_values(unsold_table, unsold_xlsm, "UNSOLD", 'Flat No /Shop No', [
        'Carpet Area In Sq.Mtrs ', 'Unit Consideration as per Readyrecknor Rate'
    ])

    # === Output Summary ===
    st.subheader("✅ Summary Report")
    if not status_mismatches and not sold_mismatches and not unsold_mismatches:
        st.success("🎉 All entries matched perfectly!")
    else:
        st.info("Some mismatches found. Expand below to review.")

    # === Detailed Mismatch Display ===
    if status_mismatches:
        with st.expander("🔴 Status Mismatches"):
            st.dataframe(pd.DataFrame(status_mismatches))

    if sold_mismatches:
        with st.expander("🟠 Sold Value Mismatches"):
            st.dataframe(pd.DataFrame(sold_mismatches))

    if unsold_mismatches:
        with st.expander("🔵 Unsold Value Mismatches"):
            st.dataframe(pd.DataFrame(unsold_mismatches))

# === Footer (Always Visible) ===
st.markdown(
    """
    <style>
    .footer-fixed {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #262730;
        color: #ffffff;
        text-align: center;
        padding: 0.8rem 0;
        font-size: 1.45rem;
        z-index: 100;
        border-top: 1px solid #444;
    }
    </style>
    <div class="footer-fixed">
        &copy; 2025 Aryan Parte. All rights reserved.
    </div>
    """,
    unsafe_allow_html=True
)
