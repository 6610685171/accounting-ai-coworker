# AI Accounting Copilot: Week 1 Implementation Plan

This plan breaks down **Week 1 (Foundation & Thai Localization)** into detailed, step-by-step phases. The goal is to establish a solid foundation for the AI Accounting Copilot using the Eigent framework, ensuring the UI is localized, the backend directories are prepared, and we have validated the ability to safely manipulate the company's existing Excel files via Python.

---

## 📌 User Review Required
> [!IMPORTANT]
> - **Folder Structure:** Please review Phase 2. Is `copilot_data/` an acceptable root directory for all generated/processed files, or should it be placed elsewhere?
> ตอบ: เอาเป็นอันนี้ไปก่อนก็ได้ เดี๋ยวตอนใช้งานจริงจะค่อยให้ถามuserอีกทีว่าให้สร้างfolderใหม่ไว้ที่...มั้ย หรืออยากเลือกโฟลเดอร์ที่มีอยู่แล้ว ให้ส่งpathมาได้เลย ไรงี้ (สำหรับของเรา ฉันต้องการให้มันอยู่ใน /Users/hare/meen/testai-cowork (ถ้ายังไม่มีก็สร้างใหม่))
> - **Customer DB:** For Phase 2, I propose creating a separate `customer_database.xlsx` (or a dedicated sheet in the existing report) to store `LINE_USER_ID`, `DELIVERY_MODE`, etc. Does this align with how you want to manage data?
> ตอบ: ไม่ต้องแยกสร้าง customer_database.xlsx ใหม่นะคะ ให้รวมไปอยู่ในรายงานมิเตอร์ น้ำไฟฟ้า ปี 2569.xlsx ชีท ชื่อ รายช่ือร้านค้า โดยเพิ่มคอลัมน์ LINE_USER_ID, DELIVERY_MODE, CONTACT_PREFERENCE ต่อท้ายคอลัมน์เดิมไปได้เลยค่ะ 

## ✅ Open Questions (Answered)
- **API Keys:** We will mock the Claude Vision / GPT-4o API keys and LINE OA Token for now.
- **FlowAccount:** We will use a real FlowAccount account but create a new company specifically for testing/demos.
- **Environment:** We are developing locally on the `develop` branch (branched from `main`).

---

## 🚀 Proposed Changes (Phases)

### Phase 1: Thai Localization (Frontend)
**Objective:** Translate the Eigent UI into Thai for accountants.

1. **Copy Locale Directory:**
   - Copy the existing English locale folder `src/i18n/locales/en-us/` and rename it to `src/i18n/locales/th/`.
2. **Translate JSON Files:**
   - Translate all UI strings inside the JSON files in `src/i18n/locales/th/` (e.g., `layout.json`, `setting.json`, `chat.json`, `dashboard.json`) into Thai.
3. **Register the Language:**
   - Update `src/i18n/locales/index.ts` to export the new `th` folder.
   - Update `src/i18n/index.ts` to add 'th' as a supported language and optionally set it as the default if desired.

**Testing (Phase 1):**
- *Manual Test:* Run `npm run dev`. Go to the web UI, switch the language to Thai (ภาษาไทย). Verify that all menus, buttons, and settings are readable and do not break the layout.

---

### Phase 2: Backend Folder Structure & Customer DB Setup
**Objective:** Prepare the workspace for multi-agent file processing and future LINE integrations.

1. **Create Directories:**
   Create a structured directory tree for the pipeline:
   - `copilot_data/meter-photos/inbox/` (Incoming photos)
   - `copilot_data/meter-photos/processed/` (Photos after OCR)
   - `copilot_data/meter-photos/archive/` (Completed)
   - `copilot_data/excel-files/template/` (Base Excel files)
   - `copilot_data/excel-files/monthly/` (Generated reports)
   - `copilot_data/output/invoices/` (Generated FlowAccount PDFs/Images)
   - `copilot_data/config/message-templates/` (LINE templates)
2. **Customer Database:**
   - Create a simple `copilot_data/config/customer_database.xlsx` (or add a sheet to the existing report).
   - Columns: `ShopID`, `ShopName`, `RentAmount`, `LINE_USER_ID`, `DELIVERY_MODE` (auto/manual), `CONTACT_PREFERENCE` (pdf/image).

**Testing (Phase 2):**
- *Automation:* A simple bash script or Python test to verify `os.path.exists()` for all directories.
- *Manual Test:* Open `customer_database.xlsx` in Excel/Numbers to verify the column headers are correct.

---

### Phase 3: Excel Automation Proof of Concept (openpyxl)
**Objective:** Ensure we can safely open, edit, and save the company's complex Excel template (`รายงานมิเตอร์ น้ำไฟฟ้า ปี 2569.xlsx`) without breaking formulas or styles.

1. **Copy Template:**
   - Move `details/รายงานมิเตอร์ น้ำไฟฟ้า ปี 2569.xlsx` to `copilot_data/excel-files/template/`.
2. **Write `scripts/excel_test.py`:**
   - Implement a script to test openpyxl capabilities.
   - *Requirement from Eigent xlsx skill:* We MUST use Excel formulas (e.g., `=SUM(A1:A10)`), not hardcoded Python calculations for any arithmetic.

**Pseudocode:**
```python
import openpyxl
from openpyxl.drawing.image import Image
import shutil
import os

TEMPLATE_PATH = "copilot_data/excel-files/template/รายงานมิเตอร์ น้ำไฟฟ้า ปี 2569.xlsx"
OUTPUT_PATH = "copilot_data/excel-files/monthly/test_output_2026_06.xlsx"

def test_excel_automation():
    # 1. Load Workbook
    wb = openpyxl.load_workbook(TEMPLATE_PATH)
    sheet = wb.active # Or target specific sheet by name
    
    # 2. Simulate finding a shop row (e.g., "V-A1") and modifying meter values
    row_idx = 10 # Mock row
    prev_meter_col = 'D'
    new_meter_col = 'E'
    
    # Move old value to previous column to check formula
    sheet[f"{prev_meter_col}{row_idx}"] = sheet[f"{new_meter_col}{row_idx}"].value
    
    # Insert new meter reading
    sheet[f"{new_meter_col}{row_idx}"] = 1205
    
    # Formula for usage (New - Old) should already exist in the template, 
    # but if we need to write one: 
    # sheet[f"F{row_idx}"] = f"={new_meter_col}{row_idx}-{prev_meter_col}{row_idx}"
    
    # 3. Embed an image
    # Note: Requires a mock image in the processed folder
    mock_img_path = "copilot_data/meter-photos/processed/mock_photo.jpg"
    if os.path.exists(mock_img_path):
        img = Image(mock_img_path)
        img.width, img.height = 100, 100 # Resize image
        sheet.add_image(img, f"Z{row_idx}") # Place image in column Z
    
    # 4. Save Workbook
    wb.save(OUTPUT_PATH)
    print(f"Saved test file to {OUTPUT_PATH}")

if __name__ == "__main__":
    test_excel_automation()
```

**Testing (Phase 3):**
- *Automation:* Use Eigent's `scripts/recalc.py` to recalculate the saved file. This script uses LibreOffice to evaluate formulas and scans for `#REF!`, `#VALUE!`, or `#DIV/0!` errors. 
  `python scripts/recalc.py copilot_data/excel-files/monthly/test_output_2026_06.xlsx`
- *Manual Test:* Open `test_output_2026_06.xlsx` in MS Excel or Google Sheets. Verify that the layout, merged cells, colors, and formulas are intact, and that the image is visible inside the expected cell.
