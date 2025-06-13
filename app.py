import streamlit as st
import pandas as pd

st.set_page_config(page_title="XLSX vs XLSM Verifier", layout="wide")

st.title("📋 XLSX vs XLSM Data Verification Tool")

# === Upload Files ===
xlsm_file = st.file_uploader("Upload XLSM File (Building_Unit_Details sheet)", type="xlsm")
xlsx_file = st.file_uploader("Upload XLSX File (Table C)", type="xlsx")

if xlsm_file and xlsx_file:
    # === Load XLSM ===
    raw_xlsm_df = pd.read_excel(xlsm_file, sheet_name="Building_Unit_Details", header=None)
    xlsm_df = raw_xlsm_df[7:].copy()
    xlsm_df.columns = raw_xlsm_df.iloc[6].tolist()

    # === Load XLSX Table C ===
    xlsx = pd.ExcelFile(xlsx_file)
    table_c = xlsx.parse("Table C")

    # === Extract Sold Table ===
    sold_start = next(i for i, row in table_c.iterrows() if row.astype(str).str.contains("Flat No", na=False).any())
    sold_end = next(i for i, row in table_c.iterrows() if row.astype(str).str.contains("TOTAL", na=False, case=False).any() and i > sold_start)
    sold_table = table_c.iloc[sold_start+1:sold_end, 0:5].copy()
    sold_table.columns = [
        'Sr.No ', 'Flat No ', 'Carpet Area In Sq.Mtrs ',
        'Unit Consideration as per Agreement /Letter Of Allotment',
        'Received Amount '
    ]

    # === Extract Unsold Table ===
    unsold_start = next(i for i, row in table_c.iterrows() if row.astype(str).str.contains("Flat No /Shop No", na=False).any())
    unsold_start += 2
    unsold_end = next(i for i, row in table_c.iterrows() if row.astype(str).str.contains("TOTAL", na=False, case=False).any() and i > unsold_start)
    unsold_table = table_c.iloc[unsold_start:unsold_end, 0:4].copy()
    unsold_table.columns = [
        'Sr.No ', 'Flat No /Shop No', 'Carpet Area In Sq.Mtrs ',
        'Unit Consideration as per Readyrecknor Rate'
    ]



    # === Filter XLSM Data ===
    sold_xlsm = xlsm_df[xlsm_df['Unit Sale Category * '].isin(['Sold', 'Booked'])].copy()
    unsold_xlsm = xlsm_df[xlsm_df['Unit Sale Category * '] == 'Unsold'].copy()
    
    # Check if XLSM is empty (which seems to be the case based on your description)
    if len(sold_xlsm) == 0 and len(unsold_xlsm) == 0:
        st.error("❌ **CRITICAL ISSUE**: XLSM file appears to be empty!")
        st.error("The XLSM Building_Unit_Details sheet has no data entries.")
        
        if len(sold_table) > 0:
            st.error(f"XLSX has {len(sold_table)} sold units but XLSM has 0 entries")
        if len(unsold_table) > 0:
            st.error(f"XLSX has {len(unsold_table)} unsold units but XLSM has 0 entries")
            
        st.stop()

    # === Rename Columns for Consistency ===
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

    # === Clean Data ===
    def clean_df(df):
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.strip().str.upper().str.replace("-", " ", regex=False)
            if "Amount" in col or "Unit Consideration as per Agreement /Letter Of Allotment" in col or "Area" in col:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df

    sold_table = clean_df(sold_table)
    sold_xlsm = clean_df(sold_xlsm)
    unsold_table = clean_df(unsold_table)
    unsold_xlsm = clean_df(unsold_xlsm)


    def check_status_mismatches(sold_table, sold_key, unsold_table, unsold_key, sold_xlsm, unsold_xlsm):
        mismatches = []

        # Normalize
        def normalize(df, col):
            return df[col].astype(str).str.strip().str.upper().str.replace("-", " ", regex=False)

        sold_table[sold_key] = normalize(sold_table, sold_key)
        unsold_table[unsold_key] = normalize(unsold_table, unsold_key)
        sold_xlsm['Flat No '] = normalize(sold_xlsm, 'Flat No ')
        unsold_xlsm['Flat No /Shop No'] = normalize(unsold_xlsm, 'Flat No /Shop No')

        sold_xlsx_flats = set(sold_table[sold_key])
        unsold_xlsx_flats = set(unsold_table[unsold_key])
        sold_xlsm_flats = set(sold_xlsm['Flat No '])
        unsold_xlsm_flats = set(unsold_xlsm['Flat No /Shop No'])

        # ✅ Only flag mismatch when status is different in XLSX vs XLSM

        # Sold in XLSX but marked Unsold in XLSM
        for flat in sold_xlsx_flats:
            if flat not in sold_xlsm_flats and flat in unsold_xlsm_flats:
                mismatches.append(f"❌ {flat} is Sold in XLSX but entered wrongly as Unsold in XLSM")

        # Unsold in XLSX but marked Sold in XLSM
        for flat in unsold_xlsx_flats:
            if flat not in unsold_xlsm_flats and flat in sold_xlsm_flats:
                mismatches.append(f"❌ {flat} is Unsold in XLSX but entered wrongly as Sold in XLSM")

        return mismatches




    # === Comparison Logic ===
    def compare_tables(std_df, source_df, table_name, key_col, fields_to_check, opposite_df=None, opposite_table_name=None, opposite_key_col=None):
        mismatches = []

        # Normalize key columns
        source_df[key_col] = source_df[key_col].astype(str).str.strip().str.upper().str.replace("-", " ", regex=False)
        std_df[key_col] = std_df[key_col].astype(str).str.strip().str.upper().str.replace("-", " ", regex=False)

        # # Check for category mismatches
        # if opposite_df is not None and opposite_key_col:
        #     opposite_keys = set(opposite_df[opposite_key_col].unique())
        #     this_keys = set(source_df[key_col].unique())

        #     # Flats that are in this table but not in the opposite table (purely sold or unsold)
        #     for flat in this_keys:
        #         if flat in opposite_keys:
        #             correct_status = table_name
        #             wrong_status = opposite_table_name

        #             # Only flag if the flat is present in THIS XLSX table and categorized wrongly in XLSM
        #             if table_name == "SOLD" and flat in unsold_xlsm['Flat No /Shop No'].values:
        #                 mismatches.append(
        #                     f"❌ {flat} is Sold in XLSX but entered wrongly as Unsold in XLSM"
        #                 )
        #             elif table_name == "UNSOLD" and flat in sold_xlsm['Flat No '].values:
        #                 mismatches.append(
        #                     f"❌ {flat} is Unsold in XLSX but entered wrongly as Sold in XLSM"
        #                 )

        # Field value mismatches
        for _, row in source_df.iterrows():
            key_val = row[key_col]
            match = std_df[std_df[key_col] == key_val]
            if match.empty:
                continue

            match_row = match.iloc[0]

            for field in fields_to_check:
                val1 = row.get(field, "")
                val2 = match_row.get(field, "")

                if isinstance(val1, str): val1 = val1.strip()
                if isinstance(val2, str): val2 = val2.strip()
                if pd.isnull(val1): val1 = 0
                if pd.isnull(val2): val2 = 0

                if "Carpet Area" in field:
                    val1 = round(float(val1), 2)
                    val2 = round(float(val2), 2)
                    if abs(val1 - val2) > 0.01:
                        mismatches.append(f"[{table_name}] Flat No '{key_val}' → {field} mismatch: {val1} ≠ {val2}")
                else:
                    val1 = round(float(val1), 0)
                    val2 = round(float(val2), 0)
                    if abs(val1 - val2) > 1:
                        mismatches.append(f"[{table_name}] Flat No '{key_val}' → {field} mismatch: {val1} ≠ {val2}")

        return mismatches





    # === Run Comparison ===
    sold_fields = [
        'Carpet Area In Sq.Mtrs ',
        'Unit Consideration as per Agreement /Letter Of Allotment',
        'Received Amount '
    ]
    unsold_fields = [
        'Carpet Area In Sq.Mtrs ',
        'Unit Consideration as per Readyrecknor Rate'
    ]

    status_value_mismatches_sold = compare_tables(
        sold_table, sold_xlsm,
        table_name="SOLD",
        key_col='Flat No ',
        fields_to_check=sold_fields,
        opposite_df=unsold_xlsm,
        opposite_table_name="UNSOLD",
        opposite_key_col='Flat No /Shop No'
    )

    status_value_mismatches_unsold = compare_tables(
        unsold_table, unsold_xlsm,
        table_name="UNSOLD",
        key_col='Flat No /Shop No',
        fields_to_check=unsold_fields,
        opposite_df=sold_xlsm,
        opposite_table_name="SOLD",
        opposite_key_col='Flat No '
    )



    # === Display Report ===
    st.subheader("🔍 VERIFICATION REPORT")

    status_conflicts = check_status_mismatches(
        sold_table, 'Flat No ', unsold_table, 'Flat No /Shop No', sold_xlsm, unsold_xlsm
    )


    all_mismatches = status_conflicts + status_value_mismatches_sold + status_value_mismatches_unsold




    if not all_mismatches:
        st.success("✅ All entries matched correctly.")
    else:
        for issue in all_mismatches:
            if issue.startswith("❌"):
                st.warning(issue)
            else:
                st.error(issue)


