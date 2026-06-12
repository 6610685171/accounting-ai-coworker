# AI Accounting Copilot: Week 2 Implementation Plan

This plan breaks down **Week 2 (Meter Reader Copilot)** into detailed, step-by-step phases. It incorporates the use of Eigent's native agents (Multi-Modal and Document Agents) and integrates the detailed business logic and specific requirements found in `detail_timeline.md`.

---

## 📌 User Review Required
> [!IMPORTANT]
> - **Suggestion Prompt:** I've proposed modifying the existing hardcoded suggestions in the chat UI. Please confirm if changing the default suggestions to accounting-specific ones is acceptable.
> - **Workflow Orchestration:** We will use Eigent's built-in agents orchestrated via a single detailed Prompt. Does this align with how you envision the user interacting with the system?

## ✅ Open Questions (Answered)
1. **เรื่องการย่อรูป (Resize) เพื่อประหยัด Token:**
   * **คำตอบ:** ควรทำครับ! เราจะใช้สคริปต์ Python สั้นๆ ทำขั้นตอนนี้ก่อนส่งให้ AI เพื่อลดขนาดภาพและประหยัดค่าใช้จ่าย API 
2. **เรื่อง Agent สำหรับ QC ข้อมูล:**
   * **คำตอบ:** ไม่จำเป็นต้องสร้าง Agent แยก 4 ตัวเหมือนในแผนเดิมครับ เราจะลดความซับซ้อนโดยฝัง "เงื่อนไขการตรวจสอบ (Validation Rules)" ลงไปใน Workflow ของ Document Agent และใช้สคริปต์ `recalc.py` ของ Eigent ตรวจหา Error ใน Excel แทน
3. **เรื่อง Suggestion Prompt (ปุ่มกดคำสั่งด่วน):**
   * **คำตอบ:** เราสามารถแก้ไขข้อความในไฟล์ `layout.json` ให้เป็นคำสั่งของเราได้เลย (ทำใน Phase 1 ของสัปดาห์นี้) เมื่อกดแล้วระบบจะรัน Workflow ทั้งหมดทันที

---

## 🚀 Proposed Changes (Phases)

### Phase 1: Customize Suggestion Prompts (UI & i18n)
**Objective:** Replace Eigent's default suggestion buttons with our Accounting workflows to make it user-friendly.

1. **Update `src/i18n/locales/th/layout.json`:**
   - Modify the UI text to provide a 1-click execution button for the accountants.
     ```json
     {
       "monthly-calc": "คำนวณบิลเดือนนี้",
       "monthly-calc-prompt": "กรุณาเริ่มกระบวนการคำนวณบิลประจำเดือน\n1. จัดการรูปในโฟลเดอร์ \n2. อ่านเลขมิเตอร์และตรวจสอบความชัดเจน \n3. บันทึกลง Excel (ย้ายเลขเก่า, ใส่เลขใหม่, แนบรูป) \n4. รัน QC ตรวจสอบความผิดปกติ แล้วรอให้ฉันตรวจสอบผลลัพธ์"
     }
     ```
2. **Update `src/components/ChatBox/index.tsx` (If necessary):**
   - Bind the suggestion button directly to our new translation keys.

**Testing (Phase 1):**
- *Manual Test:* Restart the dev server, open the UI, click the "คำนวณบิลเดือนนี้" button, and verify the prompt correctly populates the chat input.

---

### Phase 2: File Management & Image Pre-processing Script
**Objective:** Handle the File Watcher & Mover logic and resize images before sending them to the expensive Multi-Modal Agent.

1. **Write `scripts/process_inbox.py`:**
   - Scan all images in `copilot_data/meter-photos/inbox/`.
   - Resize them to max 1024x1024px to save tokens.
   - Parse the filename (e.g., `V-A1_water_20260601.jpg`) to extract the Shop ID and unit type.
   - Move the resized images into a structured folder: `copilot_data/meter-photos/processed/YYYY-MM/`.
   - Move original raw images to `archive/`.

**Testing (Phase 2):**
- *Manual Test:* Place a large 5MB photo in the inbox, run the script, and check if the processed photo is correctly placed in a `YYYY-MM` folder and is under 500KB.

---

### Phase 3: Workflow Prompt Design & Execution (OCR + Excel + QC)
**Objective:** Tie the Multi-Modal Agent (OCR) and Document Agent (Excel + QC) together via the Master Prompt, integrating all constraints from `detail_timeline.md`.

1. **Configure the Multi-Modal Agent (OCR Reader):**
   - Instruct the agent to read images in the `processed/YYYY-MM/` folder.
   - **Constraint:** Output MUST be in JSON format: 
     `{"shop_name": "...", "reading": 1234, "unit": "water"|"electric", "confidence": "high"|"low"}`
   - **Error Handling:** If `confidence` is "low" (blurred/unreadable), the agent must immediately pause and alert the user in the chat: *"รูปห้อง [shop_name] อ่านไม่ออก รบกวนขอรูปใหม่ค่ะ"*

2. **Configure the Document Agent (Excel Writer):**
   - Open `copilot_data/excel-files/template/รายงาน...xlsx`.
   - **Core Logic:**
     - **Copy old meter value:** MUST copy the value from the "Current Meter" column and paste it into the "Previous Meter" column (to clear the slot and test formulas).
     - **Insert new reading:** Enter the new meter value from the OCR JSON.
     - **Embed Image:** Attach the resized meter photo directly into the row matching the shop.
   - Save the file as a new copy: `copilot_data/excel-files/monthly/รายงาน_[YYYY-MM].xlsx`.

3. **Built-in QC (Document Agent & recalc.py):**
   - The agent must verify logical constraints:
     - `new_meter > old_meter`.
     - Usage (`new_meter - old_meter`) is not suspiciously high (>500 units) or 0.
   - Run Eigent's built-in `scripts/recalc.py` on the saved file to ensure no `#REF!` or `#VALUE!` errors exist in the spreadsheet.
   - Compile a final summary report in the chat for the user to review.

**Testing (Phase 3):**
- *End-to-End Manual Test:* Drop 2 sample meter photos (one clear, one intentionally blurry) into the inbox. Click the suggestion prompt. Verify that:
  1. The blurry image triggers a chat warning.
  2. The clear image gets processed, Excel is updated (old meter moved, new meter entered, image embedded), and QC passes without formula errors.
