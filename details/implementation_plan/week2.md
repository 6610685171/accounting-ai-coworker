# AI Accounting Copilot: Week 2 Implementation Plan

This plan breaks down **Week 2 (Meter Reader Copilot)** into detailed, step-by-step phases. It incorporates the use of Eigent's native agents, custom Python scripts for speed, and a robust "Native Agent Injection" deployment strategy to make the app look premium and ready-to-use out of the box.

---

## 📌 User Review Required
> [!IMPORTANT]
> - **Native Agent Injection:** I completely agree with the other AI's suggestion! We will inject our agent deep into the codebase (Backend & Frontend) so it ships as a default agent alongside Developer and Document agents. Please review Phase 1 for this new deployment strategy.

## ✅ Open Questions (Answered)
1. **เราทำแบบเขา (มี Agent โผล่มาให้เลย) ได้ไหม?**
   * **คำตอบ:** **ทำได้ 100% ครับ และนี่คือวิธีที่ถูกต้องที่สุดในการทำซอฟต์แวร์ส่งมอบครับ!** AI อีกตัวแนะนำได้ถูกจุดเป๊ะเลยครับ 
   * จากการที่ผมเข้าไปค้นในโค้ดของ Eigent ตัว Agent ทั้ง 4 ตัวของเขานั้น **ไม่ได้ดึงจาก Database แต่ถูกเขียนฝัง (Hardcode) ไว้ใน Source Code ในส่วนของ Backend Factory** (ไฟล์อย่าง `developer.py`, `multi_modal.py` ฯลฯ) 
   * **วิธีแก้:** เราจะสร้างไฟล์ `accounting.py` แทรกเข้าไปเนียนๆ เป็น **Agent ตัวที่ 5** ในระบบเลยครับ พอ Build แอปเสร็จ พนักงานเปิดมาปุ๊บ จะมี **"Accounting Copilot"** ยิ้มแฉ่งรอรับงานเลย ดูพรีเมียมสุดๆ ครับ!

---

## 🚀 Proposed Changes (Phases)

### Phase 1: "Native Agent Injection" (Deploy as Built-in Agent)
**Objective:** Hardcode the `Accounting Copilot` directly into Eigent's backend and frontend so it becomes a default, ready-to-use feature for the accountant.

1. **Backend Integration (`backend/app/agent/factory/accounting.py`):**
   - Create a new factory class inheriting from Eigent's agent structure.
   - Inject our **Master Logic Prompt** (with the exact OCR, Excel, and QC logic) directly into the `system_message` of this Python class.
   - Register it in `backend/app/agent/factory/__init__.py`.

2. **Frontend UI Integration:**
   - Update `src/components/WorkFlow/agents.tsx` and `src/store/chatStore.ts` so "Accounting Copilot" appears in the Agent selection menu.
   - Update `src/i18n/locales/th/layout.json` to include our custom suggestion prompt:
     ```json
     "monthly-calc": "คำนวณบิลเดือนนี้",
     "monthly-calc-prompt": "รันกระบวนการทำบิลประจำเดือน {CURRENT_MONTH} กรุณาเริ่มได้เลย"
     ```

**Testing (Phase 1):**
- *Manual:* Restart the server. Open the browser and verify that "Accounting Copilot" is listed in the available agents. Click the "คำนวณบิลเดือนนี้" suggestion button and verify it triggers the newly created agent successfully.

---

### Phase 2: System Prompt (Master Logic inside `accounting.py`)
**Objective:** The core brain of the `Accounting Copilot`, embedded in Python.

**System Prompt (English for accuracy):**
```text
You are an Accounting AI Copilot. Your task is to process the monthly billing for the month of {CURRENT_MONTH}. Execute the workflow autonomously using your available tools.

**Step 0 — Fetch Images (Parallel execution allowed)**
- Execute `scripts/fetch_from_downloads.py`. This script will scan `~/Downloads/` for folders matching the pattern `DD/M/YYYY` (Electricity) and `DD/M/YYYY #1` (Water).

**Step 1 — Batch OCR (Meter Reading)**
- Process ALL images in the `processed/YYYY-MM/` folder in parallel.
- Extract to JSON ONLY: `{"shop_id": "...", "reading": 1234, "unit": "water"|"electric", "confidence": "high"|"low"}`.
- If confidence is "low", SKIP the Excel update for this specific image, mark it as ❌ Failed, and continue processing the rest.

**Step 2 — Excel Update (Strict Order)**
- Target File: `copilot_data/excel-files/รายงาน...xlsx`.
- BEFORE making row edits: DUPLICATE the previous month's sheet and RENAME the new sheet to the current month format (e.g., '{CURRENT_MONTH}').
- For each successfully read shop on the NEW sheet:
  1. COPY value from 'Current Meter' to 'Previous Meter'.
  2. ENTER the new reading from OCR into 'Current Meter'.
  3. EMBED the resized meter photo in the corresponding row.

**Step 3 — QC & Final Summary**
- Run `scripts/recalc.py` to check the new sheet for `#REF!` or `#VALUE!`.
- Verify: New Meter > Previous Meter, and Usage is < 500.
- Output a final summary table in THAI:
  ห้อง | มิเตอร์เก่า | มิเตอร์ใหม่ | ใช้ไป | ประเภท | สถานะ (✅ ปกติ / ⚠️ ผิดปกติ / ❌ อ่านไม่ออก ข้ามการบันทึก)
- Ask the user to provide manual readings for any ❌ shops.

CRITICAL: All your chat messages and the final summary MUST be in Thai.
```

---

### Phase 3: Python Automation Scripts (Pseudocode & Testing)
**Objective:** Handle the heavy lifting (File fetching, resizing, image enhancement) via fast Python scripts.

#### 1. Pseudocode: `scripts/fetch_from_downloads.py`
This script finds the LINE albums downloaded to the PC, copies them to our working directory, and applies contrast enhancement/resizing.

```python
import os
import shutil
import re
from datetime import datetime
from PIL import Image, ImageEnhance

DOWNLOADS_DIR = os.path.expanduser("~/Downloads")
PROCESSED_DIR = "copilot_data/meter-photos/processed/"
MAX_SIZE = (1024, 1024)

def fetch_and_process_images():
    current_month_folder = datetime.now().strftime("%Y-%m")
    target_processed_dir = os.path.join(PROCESSED_DIR, current_month_folder)
    os.makedirs(target_processed_dir, exist_ok=True)
    
    # Regex for DD/M/YYYY or DD/M/YYYY #1
    folder_pattern = re.compile(r'^\d{1,2}-\d{1,2}-\d{4}(?: #1)?$')
    
    # Find matching folders in Downloads
    for item in os.listdir(DOWNLOADS_DIR):
        item_path = os.path.join(DOWNLOADS_DIR, item)
        if os.path.isdir(item_path) and folder_pattern.match(item):
            unit_type = "water" if "#1" in item else "electric"
            for file in os.listdir(item_path):
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    img_path = os.path.join(item_path, file)
                    
                    # 1. Enhance & Resize
                    with Image.open(img_path) as img:
                        enhancer = ImageEnhance.Contrast(img)
                        enhanced_img = enhancer.enhance(1.2) # Boost contrast
                        enhanced_img.thumbnail(MAX_SIZE)
                        
                        # 2. Extract Shop ID
                        shop_id = file.split('_')[0].split('.')[0]
                        new_filename = f"{shop_id}_{unit_type}.jpg"
                        
                        # 3. Save directly to processed dir
                        out_path = os.path.join(target_processed_dir, new_filename)
                        enhanced_img.save(out_path, "JPEG", quality=85)
                        
            # Move the original folder to archive
            shutil.move(item_path, os.path.join("copilot_data/meter-photos/archive/", item))

if __name__ == "__main__":
    fetch_and_process_images()
```

**Testing (Phase 3):**
- *Manual:* 
  1. Create a dummy folder in `~/Downloads` named `29-06-2026 #1`.
  2. Put a dark/blurry meter photo inside it.
  3. Run `python scripts/fetch_from_downloads.py`.
  4. Verify the script automatically finds it, enhances the contrast, resizes it under 500KB, renames it with the `water` tag, saves it to `processed/YYYY-MM/`, and moves the original folder to `archive/`.
- *Automation:* Write a `pytest` file (`tests/test_fetch.py`) that sets up a temporary directory mocking `~/Downloads`, runs the script function, and asserts that the output files exist in the `processed/` temporary directory and have correct dimensions.
