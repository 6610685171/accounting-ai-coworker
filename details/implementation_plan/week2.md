# AI Accounting Copilot: Week 2 Implementation Plan

This plan breaks down **Week 2 (Meter Reader Copilot)** into detailed, step-by-step phases. It incorporates the use of Eigent's native agents, custom Python scripts for speed, a robust "Native Agent Injection" deployment strategy, and UX/UI improvements (Login bypass & Stop button).

**Pseudocode and strict testing methodologies (manual/automation) are provided for each phase.**

---

## 📌 User Review Required
> [!IMPORTANT]
> - **App Shell Modifications:** I have added **Phase 4** to address your new requests regarding the Login Screen and the Stop Button. Please review to ensure this covers what you need.

## ✅ Open Questions (Answered)
1. **ตอนนี้มันไม่มีปุ่มให้ AI หยุดการทำงาน เพิ่มได้ไหม?**
   * **คำตอบ:** **ทำได้สบายมากครับ!** จากการตรวจสอบโค้ดหน้าต่างแชท (`src/components/ChatBox/index.tsx`) ระบบมีฟังก์ชันหยุดทำงาน (Stop/Skip Task) ฝังอยู่แล้ว แต่อาจจะซ่อนอยู่หรือแสดงผลไม่ชัดเจนตอนที่ AI กำลังคิด ผมจะเพิ่ม Task ในการดึงปุ่ม "Stop 🛑" ออกมาโชว์ให้เห็นชัดๆ ตลอดเวลาที่ AI กำลังทำงานครับ
2. **ตอนเปิดแอป ต้อง Login ก่อนถึงจะใช้ได้ แก้ให้ไม่ต้อง Login ได้ไหม?**
   * **คำตอบ:** **แก้ได้ครับ!** ตัวโค้ดเดิมมีระบบ `Auto-login` สำหรับการรันบนเครื่อง Local (ออฟไลน์) ไว้อยู่แล้ว แต่อาจจะยังต้องให้ User กดปุ่ม หรือรอจังหวะเด้งเข้าหน้า Login ก่อน ผมจะแก้ไขโค้ดหน้า `Login.tsx` และไฟล์ Routing ให้มันทำการ Auto-login และเด้งข้ามเข้าหน้าทำงานหลัก (Dashboard) อัตโนมัติทันทีที่เปิดโปรแกรมครับ พนักงานบัญชีจะได้เปิดปุ๊บใช้ได้ปั๊บ!

---

## 🚀 Proposed Changes (Phases)

### Phase 1: "Native Agent Injection" (Deploy as Built-in Agent)
**Objective:** Hardcode the `Accounting Copilot` directly into Eigent's backend and frontend so it becomes a default, ready-to-use feature for the accountant.

1. **Backend Integration (`backend/app/agent/factory/accounting.py`):**
   - Create a new factory class inheriting from Eigent's agent structure.
   - Inject our **Master Logic Prompt** directly into the `system_message`.
   - Register it in `backend/app/agent/factory/__init__.py`.

2. **Frontend UI Integration:**
   - Update `src/components/WorkFlow/agents.tsx` and `src/store/chatStore.ts` to list "Accounting Copilot".
   - Update `src/i18n/locales/th/layout.json` to include our custom suggestion prompt:
     ```json
     "monthly-calc": "คำนวณบิลเดือนนี้",
     "monthly-calc-prompt": "รันกระบวนการทำบิลประจำเดือน {CURRENT_MONTH} กรุณาเริ่มได้เลย"
     ```

**Testing (Phase 1):**
- *Manual:* Restart the server. Verify "Accounting Copilot" is listed in the available agents. Click the "คำนวณบิลเดือนนี้" suggestion button and verify it triggers.

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

### Phase 3: Python Automation Scripts
*(Pseudocodes for `fetch_from_downloads.py` and batch processing are intact from previous revisions).*

---

### Phase 4: App Shell Modifications (Stop Button & Login Bypass)
**Objective:** Improve the user experience so the accountant doesn't face technical barriers like login screens or runaway AI processes.

**1. Login Bypass (`src/pages/Login.tsx`):**
   - Add a `useEffect` hook that triggers immediately when the component mounts.
   - It will call `handleAutoLogin()` automatically if the app is in local mode, skipping the UI rendering of the login page and redirecting directly to `/chat`.
   ```javascript
   // Pseudocode for src/pages/Login.tsx
   useEffect(() => {
       if (isLocalMode) {
           handleAutoLogin();
       }
   }, []);
   ```

**2. Persistent Stop Button (`src/components/ProjectChatContainer/index.tsx` & `ChatBox`):**
   - Locate the UI element for the `handleSkip` function (Stop task).
   - Ensure it is persistently rendered floating near the chat input or within the active Task Card whenever `task.status === 'running' || task.status === 'pending'`.
   - Add clear Thai text: "🛑 หยุดการทำงาน" to make it user-friendly.

**Testing (Phase 4):**
- *Manual (Login):* Open the app in incognito or clear local storage. Verify that the app briefly loads and jumps straight to the dashboard without asking for an email/password.
- *Manual (Stop Button):* Start the Monthly Calculation process. While the AI is processing the Python scripts, locate the "🛑 หยุดการทำงาน" button, click it, and verify the AI halts its process and logs a cancellation.
