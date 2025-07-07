# 📊 XLSX vs XLSM Data Verification Tool

A Streamlit web app to **verify and compare building unit data** from two Excel sources:
- 🟠 **XLSM** (typically from ERP systems, like Mahareara)
- 🔵 **XLSX** (from CA/Consultant, containing Table C)

---

## 🚀 Features

- ✅ Checks **status mismatches** (e.g., sold in one but unsold in another)
- 📐 Verifies **carpet area** differences
- 💰 Flags **unit consideration** and **received amount** mismatches
- 📁 Simple drag-and-drop file upload interface
- 🌗 Supports dark mode and responsive design (tested on [Streamlit Cloud](https://streamlit.io/))
- 👨‍💼 Built for **developers, auditors, real estate consultants**, and **finance teams**

---

## 📷 Screenshots

![image](https://github.com/user-attachments/assets/e03c6467-6995-48af-b105-7911776c1fea)

![image](https://github.com/user-attachments/assets/8af56ea7-d4c9-45a7-b06d-b802092d9ca3)

![image](https://github.com/user-attachments/assets/e9c50158-295b-4f66-838d-858e8a79eb3c)

---

## 📁 File Requirements

### 🔸 `XLSM` file
- Must contain sheet: **`Building_Unit_Details`**
- Contains ERP exported unit data (Sold, Booked, Unsold)

### 🔹 `XLSX` file
- Must contain sheet: **`Table C`**
- Provided by CA/Consultant

---

## ⚙️ Tech Stack

- `Python`
- `Streamlit`
- `pandas`
- `openpyxl`

---

## 📦 Installation & Local Run

```bash
# 1. Clone the repo
git clone https://github.com/aryanparte03/Verify_Building_Details-RERA-.git
cd Verify_Building_Details-RERA-

# 2. Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
