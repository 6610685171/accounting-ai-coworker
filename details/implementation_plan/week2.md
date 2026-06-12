# AI Accounting Copilot: Week 2 Implementation Plan

This plan breaks down **Week 2 (Meter Reader Copilot)** into detailed, step-by-step phases. It incorporates the use of Eigent's native agents (Multi-Modal and Document Agents) and addresses the questions regarding token optimization, Quality Control (QC), and UI Suggestion Prompts.

---

## 📌 User Review Required
> [!IMPORTANT]
> - **Suggestion Prompt:** I've proposed modifying the existing hardcoded suggestions in the chat UI. Please confirm if changing the default suggestions to accounting-specific ones is acceptable.
> - **Workflow Orchestration:** We will use Eigent's built-in agents orchestrated via a single detailed Prompt. Does this align with how you envision the user interacting with the system?

## ✅ Open Questions (Answered)
1. **เรื่องการย่อรูป (Resize) เพื่อประหยัด Token:**
   * **คำตอบ:** ควรทำครับ! รูปถ่ายมือถือมักจะใหญ่เกินความจำเป็น การย่อรูป (เช่น ให้ด้านยาวไม่เกิน 1024px) จะช่วยประหยัด Token และทำให้ API ตอบสนองไวขึ้นมาก เราจะใช้สคริปต์ Python สั้นๆ ทำขั้นตอนนี้ก่อนส่งให้ AI
2. **เรื่อง Agent สำหรับ QC ข้อมูล:**
   * **คำตอบ:** ไม่จำเป็นต้องสร้าง Agent แยกต่างหากให้เปลืองทรัพยากรครับ เราสามารถฝัง "เงื่อนไขการตรวจสอบ (Validation Rules)" ลงไปใน Prompt ของ Document Agent ได้เลย (เช่น "ห้ามให้เลขใหม่น้อยกว่าเลขเก่า") และให้มนุษย์ (Human-in-the-loop) เป็นคนยืนยันความถูกต้องขั้นสุดท้าย (QC หลัก) ก่อนไปสัปดาห์ที่ 3
3. **เรื่อง Suggestion Prompt (ปุ่มกดคำสั่งด่วน):**
   * **คำตอบ:** จากการไปตรวจสอบโค้ดใน `src/components/ChatBox/index.tsx` พบว่ามีปุ่ม Suggestion ฝังอยู่จริง โดยจะดึงข้อความจากไฟล์แปลภาษา (`layout.json`) เราสามารถเปลี่ยนข้อความเหล่านี้เป็นคำสั่งของเราได้เลย (ทำใน Week 2 นี้ได้เลยครับ เพื่อให้พนักงานบัญชีกดปุ่มเดียวแล้ว AI เริ่มรันตาม Flow ได้ทันที)

---

## 🚀 Proposed Changes (Phases)

### Phase 1: Customize Suggestion Prompts (UI & i18n)
**Objective:** Replace Eigent's default suggestion buttons with our Accounting workflows to make it user-friendly.

1. **Update `src/components/ChatBox/index.tsx` (Optional but recommended for clean code):**
   - Modify lines 1424-1437 to use our custom translation keys (e.g., `layout.monthly-calc`, `layout.monthly-calc-prompt`).
2. **Update `src/i18n/locales/th/layout.json`:**
   - Add the new keys:
     ```json
     {
       "monthly-calc": "คำนวณบิลเดือนนี้",
       "monthly-calc-prompt": "กรุณาเริ่มกระบวนการคำนวณบิลประจำเดือน 1. ตรวจสอบโฟลเดอร์ภาพมิเตอร์ 2. ย่อขนาดภาพ 3. ทำ OCR อ่านเลขมิเตอร์ 4. บันทึกลง Excel พร้อมแนบรูป และรอให้ฉันตรวจสอบ"
     }
     ```

**Testing (Phase 1):**
- *Manual Test:* Restart the dev server, open the UI, and click the "คำนวณบิลเดือนนี้" button. Verify that the prompt text is correctly populated into the chat input box.

---

### Phase 2: Image Pre-processing Script (Token Optimization)
**Objective:** Create a fast, local script to resize images before sending them to the expensive Multi-Modal Agent.

1. **Write `scripts/resize_images.py`:**
   - A simple script using `Pillow` (PIL) to read all images in `copilot_data/meter-photos/inbox/`.
   - Resize them (e.g., max 1024px width/height, compressed JPEG).
   - Save the output to `copilot_data/meter-photos/processed/` and move the originals to `archive/`.

**Pseudocode:**
```python
import os
from PIL import Image

INBOX_DIR = "copilot_data/meter-photos/inbox/"
PROCESSED_DIR = "copilot_data/meter-photos/processed/"
MAX_SIZE = (1024, 1024)

def optimize_images():
    for filename in os.listdir(INBOX_DIR):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            in_path = os.path.join(INBOX_DIR, filename)
            out_path = os.path.join(PROCESSED_DIR, filename)
            
            with Image.open(in_path) as img:
                img.thumbnail(MAX_SIZE) # Resizes maintaining aspect ratio
                img.save(out_path, "JPEG", quality=85)
            
            # Optionally move original to archive
            os.rename(in_path, f"copilot_data/meter-photos/archive/{filename}")

if __name__ == "__main__":
    optimize_images()
```

**Testing (Phase 2):**
- *Manual Test:* Place a large 5MB photo in the inbox, run `python scripts/resize_images.py`, and check if the processed photo is under 500KB while still readable.

---

### Phase 3: Workflow Prompt Design & Execution
**Objective:** Tie the Developer Agent (for resizing), Multi-Modal Agent (for OCR), and Document Agent (for Excel) together via a single Master Prompt.

1. **Configure the Master Prompt:**
   When the user clicks the Suggestion Prompt from Phase 1, Eigent's orchestrator will break down the task. We need to ensure the system prompt or the suggestion prompt explicitly directs the agents:
   - **Step 1 (Developer Agent):** Run `python scripts/resize_images.py`.
   - **Step 2 (Multi-Modal Agent):** Look at all images in `copilot_data/meter-photos/processed/` and extract `{"shop_id": "...", "water_meter": 123, "electric_meter": 456}`.
   - **Step 3 (Document Agent):** Use the `xlsx` skill to open `copilot_data/excel-files/template/รายงาน...xlsx`. For each `shop_id`, copy the previous month's meter to the "old" column, insert the new values, embed the corresponding image from the `processed/` folder, and save it to the `monthly/` folder.
   - **Step 4 (Built-in QC):** The Document Agent must verify that `new_meter >= old_meter`. If not, flag it in the final summary response.

**Testing (Phase 3):**
- *End-to-End Manual Test:* Drop 2 sample meter photos into the inbox. Click the suggestion prompt in the UI. Monitor Eigent as it assigns the tasks to the different agents. Finally, open the resulting Excel file to verify the numbers, formulas, and images are correctly placed.
