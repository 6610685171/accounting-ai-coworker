# AI Accounting Copilot: Week 2 Implementation Plan

This plan breaks down **Week 2 (Meter Reader Copilot)** into detailed, step-by-step phases. It incorporates the use of Eigent's native agents (Multi-Modal and Document Agents) and integrates the refined prompt logic to ensure smooth, autonomous execution with a single, user-friendly human-in-the-loop checkpoint.

---

## 📌 User Review Required
> [!IMPORTANT]
> - **Suggestion Prompt Logic:** Please review the revised English prompt in Phase 1. It is designed to run autonomously without pausing at every step, only stopping at the end to present the summary table in Thai.

## ✅ Open Questions (Answered)
1. **Human-in-the-loop เยอะไปไหม?**
   * **คำตอบ:** ใช่ครับ การให้ AI หยุดรอทุกขั้นตอนจะทำให้เสียเวลาและจุกจิกเกินไป แผนดั้งเดิมของเรา (`detail_timeline.md`) ระบุให้มี Gate 1 แค่จุดเดียวคือ "หลัง OCR & กรอก Excel เสร็จ" ดังนั้นผมปรับ Prompt ให้รันรวดเดียวตั้งแต่ขั้น 1-4 แล้วค่อยมาสรุปตารางให้ผู้ใช้กดยืนยันทีเดียวจบครับ (ยกเว้นกรณีภาพเบลออ่านไม่ออก ค่อยหยุดถาม)
2. **ควรเขียน Prompt เป็นภาษาไทยหรืออังกฤษ?**
   * **คำตอบ:** **ควรเขียนโครงสร้างคำสั่ง (Logic) เป็นภาษาอังกฤษ แต่บังคับ Output เป็นภาษาไทยครับ** เพราะ AI ทุกตัวบนโลก (รวมถึงในแพลตฟอร์ม Eigent) ถูกเทรนด้วยภาษาอังกฤษเป็นหลัก การสั่งงานแบบมี Logic ซับซ้อน (เช่น การย้ายโฟลเดอร์, ลำดับการทำ Excel, เงื่อนไข QC) ภาษาอังกฤษจะทำให้ AI ทำตามได้เป๊ะที่สุดและไม่หลุดโฟกัส แต่เราจะใส่คำสั่งบรรทัดสุดท้ายตัวใหญ่ๆ ว่า **"All chat responses and summaries MUST be in Thai"** เพื่อให้การสื่อสารกับเราเป็นภาษาไทยทั้งหมดครับ

---

## 🚀 Proposed Changes (Phases)

### Phase 1: Customize Suggestion Prompts (UI & i18n)
**Objective:** Replace Eigent's default suggestion buttons with our Accounting workflows. We will use the highly optimized, English-based Master Prompt.

1. **Update `src/i18n/locales/th/layout.json`:**
   - Add the suggestion button for Monthly Calculation.
     ```json
     {
       "monthly-calc": "คำนวณบิลเดือนนี้",
       "monthly-calc-prompt": "You are an Accounting AI Copilot. Execute the monthly billing process autonomously. Do NOT pause between steps unless an error requires user input.\n\n**Step 1 — Prepare Images**\n- Execute `scripts/process_inbox.py` to resize images to max 1024x1024px, extract Shop ID/unit type from filenames, and move them to `copilot_data/meter-photos/processed/YYYY-MM/`.\n\n**Step 2 — OCR (Meter Reading)**\n- Read images in the processed folder. Extract to JSON ONLY: `{\"shop_id\": \"...\", \"reading\": 1234, \"unit\": \"water\"|\"electric\", \"confidence\": \"high\"|\"low\"}`.\n- IF confidence is \"low\", PAUSE immediately, output in Thai: \"รูปห้อง [shop_id] อ่านไม่ออก รบกวนส่งรูปมาอีกครั้งนะคะ\" (หรือเจนคำตอบให้userเองได้เลย) and wait for user.\n\n**Step 3 — Excel Update (Strict Order)**\n- Open `copilot_data/excel-files/template/รายงาน...xlsx`. For each shop:\n  1. COPY value from 'Current Meter' to 'Previous Meter'.\n  2. ENTER the new reading from OCR into 'Current Meter'.\n  3. EMBED the resized meter photo in the corresponding row.\n- Save as: `copilot_data/excel-files/monthly/รายงาน_[YYYY-MM].xlsx`.\n\n**Step 4 — QC & Validation**\n- Execute `scripts/recalc.py` to check for `#REF!` or `#VALUE!`.\n- Verify: New Meter > Previous Meter, and Usage is between 1 and 500.\n\n**Step 5 — Final Summary**\n- Output a summary table showing: ห้อง | มิเตอร์เก่า | มิเตอร์ใหม่ | ใช้ไป | ประเภท | สถานะ (✅ ปกติ / ⚠️ ผิดปกติ)\n- Ask the user to verify the Excel file and confirm.\n\nCRITICAL: All your chat messages, step summaries, and outputs MUST be in Thai language."
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
   - Agent dynamically invokes Python tools, reads files, and updates the Excel.
   - Human reviews the final Thai summary table in the chat and checks the saved Excel file.

**Testing (Phase 3):**
- *End-to-End Manual Test:* Drop 2 sample meter photos (one clear, one intentionally blurry) into the inbox. Click the suggestion prompt. Verify that:
  1. The blurry image triggers a chat warning in Thai.
  2. The clear image gets processed, Excel is updated (old meter moved, new meter entered, image embedded), and QC passes without formula errors.
  3. The final summary table is presented in Thai, awaiting user confirmation.
