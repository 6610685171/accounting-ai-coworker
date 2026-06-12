# AI Accounting Copilot: Week 2 Implementation Plan

This plan breaks down **Week 2 (Meter Reader Copilot)** into detailed, step-by-step phases. It incorporates the use of Eigent's native agents, custom Python scripts for speed, and addresses the complexities of LINE album naming, Excel sheet management, and parallel processing. 

**Pseudocode and strict testing methodologies (manual/automation) are provided for each phase.**

---

## 📌 User Review Required
> [!IMPORTANT]
> - **Pseudocode Check:** Please review the pseudocode provided in Phase 3 for the automation scripts to ensure the logic aligns with your expectations.
> - **Custom Agent Creation:** I recommend creating a Custom Agent via the Eigent UI for this workflow, rather than just modifying the layout.json.

## ✅ Open Questions (Answered)
1. **เพิ่มชื่ออัลบั้ม LINE "DD/M/YYYY" และ "DD/M/YYYY #1" ลงไปใน Prompt ได้ไหม?**
   * **คำตอบ:** ได้ครับ อัปเดตลงในสคริปต์ `fetch_from_downloads.py` (ดู Pseudocode ด้านล่าง) เพื่อให้ดึงไฟล์น้ำและไฟมาได้อย่างถูกต้อง
2. **เรื่องชื่อ Sheet ใน Excel (Copy ของเดือนเก่ามาเปลี่ยนชื่อ)**
   * **คำตอบ:** ปรับ Prompt ให้ AI ทำการ **Duplicate Sheet ล่าสุด และเปลี่ยนชื่อเป็นเดือนปัจจุบัน** ก่อนเริ่มกรอกข้อมูลครับ
3. **ต้องบอก AI ไหมว่าตอนนี้คือเดือนอะไร?**
   * **คำตอบ:** เราจะแทรก "วันที่ปัจจุบันของคอมพิวเตอร์" ลงไปใน Prompt ผ่านโค้ดหน้า UI เลยครับ
4. **ควรสร้าง Agent ตัวใหม่สำหรับ Task นี้ในแอปไหม?**
   * **คำตอบ:** ควรสร้างครับ! ให้สร้าง Agent ชื่อ "Accounting Copilot" แล้วเอา Master Prompt ไปใส่ใน System Prompt
5. **ควรใช้ Sub-agent ไหม จะได้ทำงาน Parallel (เพราะมีถึง 60 รูป)?**
   * **คำตอบ:** ในกระบวนการ OCR ให้ใช้การทำ Batch Process พร้อมๆ กันเพื่อความรวดเร็วครับ
6. **มีเขียน Pseudocode ลงใน Plan หรือยัง?**
   * **คำตอบ:** ตอนแรกยังเขียนไม่ครบถ้วนครับ ขออภัยด้วย ตอนนี้ผมได้เพิ่ม Pseudocode ของทุกสคริปต์ที่ต้องใช้ พร้อมทั้งวิธีทดสอบอย่างละเอียดในแต่ละ Phase ตามที่คุณขอมาตั้งแต่แรกเรียบร้อยแล้วครับ!

---

## 🚀 Proposed Changes (Phases)

### Phase 1: Create Custom Agent & UI Trigger
**Objective:** Create a dedicated Agent persona in Eigent and link it to our Suggestion Prompt.

1. **Create Agent via UI (Manual Step for User):**
   - In Eigent, create a new Agent.
   - Name: `Accounting Copilot`
   - Description/System Prompt: *(Insert the Master Prompt below)*
   - Tools: Enable `Python Execution`, `File Reader/Writer`, `xlsx` (Excel operations).

2. **Update `src/components/ChatBox/index.tsx` & `layout.json`:**
   - Inject the dynamic date into the prompt execution so the AI knows the context.
   ```json
   "monthly-calc": "คำนวณบิลเดือนนี้",
   "monthly-calc-prompt": "รันกระบวนการทำบิลประจำเดือน {CURRENT_MONTH} กรุณาเริ่มได้เลย"
   ```

**Testing (Phase 1):**
- *Manual:* Open Eigent UI, verify the new suggestion button appears. Click it and ensure the text populates the input field correctly.
- *Automation:* Unit test (if React testing library is set up) to check if the button click triggers `setMessage` with the correct localized string.

---

### Phase 2: System Prompt (Master Logic)
**Objective:** The core brain of the `Accounting Copilot` Agent.

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

**Testing (Phase 2):**
- *Manual:* Paste the prompt into the System Prompt box of the Custom Agent and save. Send a generic test message to ensure the agent adopts the persona and responds in Thai.

---

### Phase 3: Python Automation Scripts
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
INBOX_DIR = "copilot_data/meter-photos/inbox/"
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
            # It's a LINE album folder
            unit_type = "water" if "#1" in item else "electric"
            
            for file in os.listdir(item_path):
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    img_path = os.path.join(item_path, file)
                    
                    # 1. Enhance & Resize
                    with Image.open(img_path) as img:
                        enhancer = ImageEnhance.Contrast(img)
                        enhanced_img = enhancer.enhance(1.2) # Boost contrast by 20%
                        enhanced_img.thumbnail(MAX_SIZE)
                        
                        # 2. Extract Shop ID from filename (assuming format ShopID.jpg)
                        # Example: "A1_001.jpg" -> "A1"
                        shop_id = file.split('_')[0].split('.')[0]
                        new_filename = f"{shop_id}_{unit_type}.jpg"
                        
                        # 3. Save directly to processed dir
                        out_path = os.path.join(target_processed_dir, new_filename)
                        enhanced_img.save(out_path, "JPEG", quality=85)
                        
            # Move the original downloaded folder to archive so it isn't processed again next month
            shutil.move(item_path, os.path.join("copilot_data/meter-photos/archive/", item))

if __name__ == "__main__":
    fetch_and_process_images()
    print("Fetch and processing complete.")
```

#### 2. Pseudocode: `scripts/batch_ocr.py` (Optional / If Eigent Multi-agent is too slow)
If having the AI agent read 60 images individually is too slow, we can write a script to make concurrent API calls to the LLM.

```python
import asyncio
import os
import json

async def ocr_image(image_path):
    # Pseudo-function calling LLM Vision API
    # prompt = "Read meter. Return JSON: shop_id, reading, unit, confidence"
    # response = await call_vision_api(image_path, prompt)
    # return json.loads(response)
    pass

async def main():
    folder = "copilot_data/meter-photos/processed/2026-06/"
    images = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.jpg')]
    
    # Run all 60 images in parallel
    tasks = [ocr_image(img) for img in images]
    results = await asyncio.gather(*tasks)
    
    with open("copilot_data/meter-photos/processed/2026-06/ocr_results.json", "w") as f:
        json.dump(results, f)

if __name__ == "__main__":
    asyncio.run(main())
```

**Testing (Phase 3):**
- *Manual:* 
  1. Create a dummy folder in `~/Downloads` named `29-06-2026 #1`.
  2. Put a dark/blurry meter photo inside it.
  3. Run `python scripts/fetch_from_downloads.py`.
  4. Verify the script automatically finds it, enhances the contrast, resizes it under 500KB, renames it with the `water` tag, saves it to `processed/YYYY-MM/`, and moves the original folder to `archive/`.
- *Automation:* Write a `pytest` file (`tests/test_fetch.py`) that sets up a temporary directory mocking `~/Downloads`, runs the script function, and asserts that the output files exist in the `processed/` temporary directory and have correct dimensions.
