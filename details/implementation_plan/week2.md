# AI Accounting Copilot: Week 2 Implementation Plan

This plan breaks down **Week 2 (Meter Reader Copilot)** into detailed, step-by-step phases. It incorporates the use of Eigent's native agents, custom Python scripts for speed, a robust "Native Agent Injection" deployment strategy, and UX/UI improvements (Login bypass & Stop button).

**Pseudocode and strict testing methodologies (manual/automation) are provided for each phase.**

---

## 📌 User Review Required
> [!IMPORTANT]
> - **Login Bypass Fix:** I've updated Phase 4 to solve the issue you encountered. When a user explicitly clicks "Logout", the backend clears the session, causing the auto-login to fail on the next restart. The best UX solution for a dedicated desktop app is to **hide the Logout button entirely**.

## ✅ Open Questions (Answered)
1. **ลองทำ Bypass ดูแล้ว แต่พอกด Logout แล้วปิดเปิดแอปใหม่ มันยังติดหน้า Login อยู่ เกิดจากอะไร?**
   * **คำตอบ:** เป็นกลไกความปลอดภัยของระบบครับ! พอเรากดปุ่ม "Logout" ในหน้าตั้งค่า ตัวระบบเบื้องหลังจะทำการ "ทำลาย Session" ทิ้งทั้งหมด พอเปิดแอปใหม่ปุ๊บ ฟังก์ชัน `Auto-login` ที่เราเขียนไว้มันวิ่งไปขอเข้าสู่ระบบ แต่มันโดนเซิร์ฟเวอร์ปฏิเสธ (เพราะเพิ่งสั่ง Logout ไป) มันเลยค้างอยู่ที่หน้าจอ Login เหมือนเดิมครับ
   * **วิธีแก้เด็ดขาด:** สำหรับแอปบัญชีที่รันแบบ Local เครื่องใครเครื่องมันแบบนี้ **พนักงานไม่มีความจำเป็นต้องกดปุ่ม Logout ครับ** ดังนั้นใน Phase 4 ผมได้เพิ่มคำสั่งให้เราเข้าไป **"ลบ/ซ่อนปุ่ม Logout"** ในหน้า Settings ทิ้งไปเลยครับ! พนักงานจะได้เผลอไปกดไม่ได้ และแอปก็จะ Auto-login ผ่านฉลุยตลอดกาลครับ (สำหรับตอนนี้ที่คุณติดหน้า Login อยู่ ให้กดปุ่ม Start Eigent ไปรอบนึงก่อนครับเพื่อสร้าง Session ใหม่)

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
**Objective:** Improve the user experience so the accountant doesn't face technical barriers like login screens, accidental logouts, or runaway AI processes.

**1. Login Bypass (`src/pages/Login.tsx`):**
   - Add a `useEffect` hook that triggers immediately when the component mounts.
   - It will call `handleAutoLogin()` automatically if the app is in local mode, skipping the UI rendering of the login page and redirecting directly to `/chat`.

**2. Remove Logout Button (`src/pages/Setting/General.tsx`):**
   - Find the `<Button onClick={() => authStore.logout()}>` block.
   - Comment it out or remove it. This prevents the accountant from accidentally destroying their session, ensuring the `auto-login` hook in `Login.tsx` never fails on subsequent restarts.

**3. Persistent Stop Button (`src/components/ProjectChatContainer/index.tsx` & `ChatBox`):**
   - Locate the UI element for the `handleSkip` function (Stop task).
   - Ensure it is persistently rendered floating near the chat input or within the active Task Card whenever `task.status === 'running' || task.status === 'pending'`.
   - Add clear Thai text: "🛑 หยุดการทำงาน" to make it user-friendly.

**Testing (Phase 4):**
- *Manual (Login & Logout):* Open the app, verify it bypasses login. Go to Settings and verify there is NO logout button available.
- *Manual (Stop Button):* Start the Monthly Calculation process. While the AI is processing the Python scripts, locate the "🛑 หยุดการทำงาน" button, click it, and verify the AI halts its process and logs a cancellation.
