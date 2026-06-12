# AI Accounting Copilot: Week 2 Implementation Plan

This plan breaks down **Week 2 (Meter Reader Copilot)** into detailed, step-by-step phases. It incorporates the use of Eigent's native agents (Multi-Modal and Document Agents) and integrates the refined prompt logic to ensure smooth, autonomous batch execution with a single, user-friendly human-in-the-loop checkpoint.

---

## 📌 User Review Required
> [!IMPORTANT]
> - **Suggestion Prompt Logic:** Please review the revised English prompt in Phase 1. It is designed to run autonomously and process all images in a batch. If any image is unreadable, it will **skip** it and report it at the end, preventing the entire workflow from halting.

## ✅ Open Questions (Answered)
1. **ถ้ารูปอ่านไม่ออกให้ Skip แล้วไปสรุปตอนจบดีกว่าไหม?**
   * **คำตอบ:** **เป็นไอเดียที่ดีมากและ User-friendly กว่ามากๆ ครับ!** ถ้าเราให้ระบบหยุดทุกครั้งที่เจอรูปเบลอ การประมวลผลรูปอื่นๆ ที่เหลือก็จะถูกเบรกไปด้วย (Batch processing หยุดชะงัก) 
   * **วิธีแก้:** ผมได้ปรับ Prompt ใน Phase 1 ใหม่ โดยสั่งให้ AI: "ถ้ารูปไหนอ่านไม่ออก (Confidence = Low) ให้ข้ามรูปนั้นไปก่อน (Skip) แล้วทำรูปอื่นต่อไปจนเสร็จ จากนั้นค่อยเอาชื่อห้องที่อ่านไม่ออกมาลิสต์สรุปให้ User ดูในตอนท้ายสุด" เพื่อให้ User เลือกว่าจะพิมพ์เลขบอก หรือจะโยนรูปใหม่เข้าไปครับ

---

## 🚀 Proposed Changes (Phases)

### Phase 1: Customize Suggestion Prompts (UI & i18n)
**Objective:** Replace Eigent's default suggestion buttons with our Accounting workflows. We will use the highly optimized, English-based Master Prompt.

1. **Update `src/i18n/locales/th/layout.json`:**
   - Add the suggestion button for Monthly Calculation.
     ```json
     {
       "monthly-calc": "คำนวณบิลเดือนนี้",
       "monthly-calc-prompt": "You are an Accounting AI Copilot. Execute the monthly billing process autonomously. Do NOT pause between steps. Process all files in a batch.\n\n**Step 1 — Prepare Images**\n- Execute `scripts/process_inbox.py` to resize images to max 1024x1024px, extract Shop ID/unit type from filenames, and move them to `copilot_data/meter-photos/processed/YYYY-MM/`.\n\n**Step 2 — OCR (Meter Reading)**\n- Read images in the processed folder. Extract to JSON ONLY: `{\"shop_id\": \"...\", \"reading\": 1234, \"unit\": \"water\"|\"electric\", \"confidence\": \"high\"|\"low\"}`.\n- IF confidence is \"low\", SKIP Step 3 for this image, mark its status as 'Failed (Unreadable)', and continue processing the rest.\n\n**Step 3 — Excel Update (Strict Order)**\n- Open `copilot_data/excel-files/template/รายงาน...xlsx`. For each successfully read shop:\n  1. COPY value from 'Current Meter' to 'Previous Meter'.\n  2. ENTER the new reading from OCR into 'Current Meter'.\n  3. EMBED the resized meter photo in the corresponding row.\n- Save as: `copilot_data/excel-files/monthly/รายงาน_[YYYY-MM].xlsx`.\n\n**Step 4 — QC & Validation**\n- Execute `scripts/recalc.py` to check for `#REF!` or `#VALUE!`.\n- Verify: New Meter > Previous Meter, and Usage is between 1 and 500.\n\n**Step 5 — Final Summary**\n- Output a summary table showing: ห้อง | มิเตอร์เก่า | มิเตอร์ใหม่ | ใช้ไป | ประเภท | สถานะ (✅ ปกติ / ⚠️ ผิดปกติ / ❌ อ่านไม่ออก ข้ามการบันทึก)\n- For any shop with status ❌, ask the user to manually provide the reading or upload a new photo.\n- Ask the user to verify the Excel file and confirm before proceeding.\n\nCRITICAL: All your chat messages, step summaries, and outputs MUST be in Thai language."
     }
     ```

**Testing (Phase 1):**
- *Manual Test:* Click the "คำนวณบิลเดือนนี้" button and verify the prompt populates the chat input correctly.

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

### Phase 3: Workflow Execution (OCR + Excel + QC)
**Objective:** Monitor the Multi-Modal Agent and Document Agent as they follow the Master Prompt instructions.

1. **Execution Flow:**
   - User clicks the Suggestion Prompt.
   - Agent dynamically invokes Python tools, reads files, and updates the Excel for readable images.
   - Human reviews the final Thai summary table in the chat, provides missing readings for skipped images, and checks the saved Excel file.

**Testing (Phase 3):**
- *End-to-End Manual Test:* Drop 3 sample meter photos (two clear, one intentionally blurry) into the inbox. Click the suggestion prompt. Verify that:
  1. The workflow processes all 3 images without stopping.
  2. The 2 clear images get processed into Excel correctly.
  3. The final summary table in the chat shows the 2 successful updates and lists the 1 blurry image as "❌ อ่านไม่ออก" asking for user input.
