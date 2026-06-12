# แผนแก้ไขระบบ Accounting AI Copilot (Bug Fix + Script Fix)

## ภาพรวมปัญหาที่พบ

จากการตรวจสอบ Codebase พบปัญหาหลัก 3 จุด:

| # | ปัญหา | ไฟล์ที่เกี่ยวข้อง | ความร้ายแรง |
|---|-------|-------------------|-------------|
| 1 | `accounting_agent` ไม่ได้ถูก import เข้า `construct_workforce` | `chat_service.py` | 🔴 Critical — ทำให้ Error ทันที |
| 2 | Hardcode path ใน `fetch_from_downloads.py` และ `ACCOUNTING_SYS_PROMPT` | `scripts/fetch_from_downloads.py`, `prompt.py` | 🟠 High — พังเมื่อรันบนเครื่องอื่น |
| 3 | Folder pattern ไม่ตรงกับชื่ออัลบั้ม LINE จริง (`DD/M/YYYY`) | `scripts/fetch_from_downloads.py` | 🟠 High — หารูปไม่เจอ |

---

## Phase 1 — แก้ Root Cause: เพิ่ม `accounting_agent` เข้า Workforce

### ปัญหาที่แก้
`accounting_agent` ถูกสร้างใน `factory/accounting.py` และ registered ใน `Agents` enum แล้ว แต่ฟังก์ชัน `construct_workforce()` ใน [chat_service.py](file:///Users/hare/meen/accounting-ai-coworker/backend/app/service/chat_service.py#L2116) ลืม import และไม่ได้เพิ่มเข้า Workforce → Coordinator ไม่รู้ว่ามี Agent นี้ → Error `NoneType object is not iterable`

### ไฟล์ที่แก้ไข

#### [MODIFY] [chat_service.py](file:///Users/hare/meen/accounting-ai-coworker/backend/app/service/chat_service.py#L31)

**1. เพิ่ม import `accounting_agent` (บรรทัด 31–38)**
```python
# BEFORE:
from app.agent.factory import (
    browser_agent,
    developer_agent,
    document_agent,
    mcp_agent,
    multi_modal_agent,
    question_confirm_agent,
    task_summary_agent,
)

# AFTER:
from app.agent.factory import (
    accounting_agent,   # ← เพิ่ม
    browser_agent,
    developer_agent,
    document_agent,
    mcp_agent,
    multi_modal_agent,
    question_confirm_agent,
    task_summary_agent,
)
```

**2. เพิ่ม `accounting_agent` เข้า asyncio.gather() (บรรทัด ~2257)**
```python
# BEFORE:
results = await asyncio.gather(
    asyncio.to_thread(_create_coordinator_and_task_agents),
    asyncio.to_thread(_create_new_worker_agent),
    asyncio.to_thread(browser_agent, options),
    developer_agent(options),
    document_agent(options),
    asyncio.to_thread(multi_modal_agent, options),
    mcp_agent(options),
)

# AFTER:
results = await asyncio.gather(
    asyncio.to_thread(_create_coordinator_and_task_agents),
    asyncio.to_thread(_create_new_worker_agent),
    asyncio.to_thread(browser_agent, options),
    developer_agent(options),
    document_agent(options),
    asyncio.to_thread(multi_modal_agent, options),
    mcp_agent(options),
    asyncio.to_thread(accounting_agent, options),  # ← เพิ่ม
)
```

**3. Unpack results และเพิ่มเข้า Workforce (บรรทัด ~2279)**
```python
# BEFORE unpack:
(
    coord_task_agents,
    new_worker_agent,
    searcher,
    developer,
    documenter,
    multi_modaler,
    mcp,
) = results

# AFTER unpack:
(
    coord_task_agents,
    new_worker_agent,
    searcher,
    developer,
    documenter,
    multi_modaler,
    mcp,
    accountant,       # ← เพิ่ม
) = results
```

**4. เพิ่ม worker ใน Workforce (บรรทัด ~2341)**
```python
# เพิ่มหลัง workforce.add_single_agent_worker("Multi-Modal Agent: ..."):
workforce.add_single_agent_worker(
    "Accounting Copilot: A specialist in monthly billing automation. "
    "It can process meter reading photos (OCR), update Excel reports, "
    "run Python scripts for file management, and perform QC checks. "
    "Use this agent for tasks related to electricity/water meter billing, "
    "Excel report updates, and monthly billing workflows.",
    accountant,
)
```

---

## Phase 2 — แก้ Path Hardcode ใน Scripts และ Prompt

### ปัญหาที่แก้
- `fetch_from_downloads.py` มี `BASE_DATA_DIR = "/Users/hare/meen/testai-cowork/copilot_data"` — Hardcode path
- `ACCOUNTING_SYS_PROMPT` มี path เดียวกันฝังอยู่
- ควรใช้ Path ที่คำนวณจาก Script Location แทน เพื่อให้ย้ายเครื่องได้

### ไฟล์ที่แก้ไข

#### [MODIFY] [fetch_from_downloads.py](file:///Users/hare/meen/accounting-ai-coworker/scripts/fetch_from_downloads.py#L22)

```python
# BEFORE:
DOWNLOADS_DIR = os.path.expanduser("~/Downloads")
BASE_DATA_DIR = "/Users/hare/meen/testai-cowork/copilot_data"

# AFTER:
DOWNLOADS_DIR = os.path.expanduser("~/Downloads")
# คำนวณ BASE_DATA_DIR จาก location ของ script เอง
# scripts/ อยู่ใน project root → copilot_data/ ก็อยู่ใน project root เช่นกัน
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)  # ขึ้นมา 1 ระดับ จาก scripts/ → project root
BASE_DATA_DIR = os.path.join(PROJECT_ROOT, "copilot_data")
```

#### [MODIFY] [prompt.py](file:///Users/hare/meen/accounting-ai-coworker/backend/app/agent/prompt.py#L316)

```python
# BEFORE (บรรทัด ~324):
- **Data Directory**: `/Users/hare/meen/testai-cowork/copilot_data`

# AFTER:
- **Data Directory**: Use the `get_copilot_data_dir()` helper or resolve relative to project root.
  The path is `<project_root>/copilot_data` where project root = parent of `backend/`.
  When running scripts, always use: python3 {working_directory}/../../scripts/fetch_from_downloads.py
```

> [!NOTE]
> วิธีที่ดีที่สุดคือให้ `ACCOUNTING_SYS_PROMPT` ไม่ hardcode path เลย แต่ให้ `accounting_agent()` ใน `factory/accounting.py` ส่ง `copilot_data_dir` เป็น parameter ผ่าน `.format()` แทน

#### [MODIFY] [accounting.py](file:///Users/hare/meen/accounting-ai-coworker/backend/app/agent/factory/accounting.py#L100)

```python
# เพิ่ม helper คำนวณ copilot_data_dir
import os as _os

def _get_copilot_data_dir():
    # backend/app/agent/factory/accounting.py
    # → ขึ้น 4 ระดับ → project root → copilot_data
    factory_dir = _os.path.dirname(_os.path.abspath(__file__))
    project_root = _os.path.dirname(  # project root
        _os.path.dirname(             # backend/
            _os.path.dirname(         # backend/app/
                _os.path.dirname(     # backend/app/agent/
                    factory_dir       # backend/app/agent/factory/
                )
            )
        )
    )
    return _os.path.join(project_root, "copilot_data")

# แล้วใน accounting_agent() เปลี่ยน:
system_message = ACCOUNTING_SYS_PROMPT.format(
    platform_system=platform.system(),
    platform_machine=platform.machine(),
    working_directory=working_directory,
    now_str=NOW_STR,
    copilot_data_dir=_get_copilot_data_dir(),   # ← เพิ่ม
    scripts_dir=os.path.join(os.path.dirname(...), "scripts"),  # ← เพิ่ม
)
```

#### [MODIFY] [prompt.py](file:///Users/hare/meen/accounting-ai-coworker/backend/app/agent/prompt.py#L316) (ต่อ)

```python
# เปลี่ยน ACCOUNTING_SYS_PROMPT ให้รับ variable:
ACCOUNTING_SYS_PROMPT = """\
...
- **Data Directory**: `{copilot_data_dir}`
...
**Step 0 — Fetch Images**
- Execute `python3 {scripts_dir}/fetch_from_downloads.py`
...
**Step 2 — Excel Update**
- Target File: `{copilot_data_dir}/excel-files/template/รายงานมิเตอร์ น้ำไฟฟ้า ปี 2569.xlsx`
...
"""
```

---

## Phase 3 — แก้ Folder Pattern ให้ตรงกับชื่ออัลบั้ม LINE จริง

### ปัญหาที่แก้
LINE ตั้งชื่ออัลบั้มว่า `DD/M/YYYY` (มี slash) เช่น `29/5/2569` หรือ `29/5/2569 #1`
แต่ regex เดิมรองรับแค่ `-`, `.`, `_`, ` ` ไม่ได้รองรับ `/` และไม่รองรับปีพุทธศักราช (2569)

### ไฟล์ที่แก้ไข

#### [MODIFY] [fetch_from_downloads.py](file:///Users/hare/meen/accounting-ai-coworker/scripts/fetch_from_downloads.py#L38)

```python
# BEFORE:
folder_pattern = re.compile(r'^(\d{1,2})[-._ ](\d{1,2})[-._ ](\d{4})(?: #1)?$')

# AFTER:
# รองรับ: "29/5/2569", "29/5/2569 #1", "29-5-2569", "29.5.2569 #1"
# ทั้งปี ค.ศ. (2026) และ พ.ศ. (2569)
folder_pattern = re.compile(
    r'^(\d{1,2})[/\-._](\d{1,2})[/\-._](\d{4})(?: #\d+)?$'
)
# หมายเหตุ: ชื่อโฟลเดอร์ที่มี "/" จะเป็น URL-encoded หรือถูก sanitize เป็น "-" โดย OS
# LINE บน macOS มักจะ sanitize "/" → "-" เมื่อ download เป็น folder name

# ตรวจสอบ unit_type จาก pattern " #1" หรือ " #ตัวเลข":
unit_type = "water" if re.search(r'#\d+', item) else "electric"
```

> [!IMPORTANT]
> **ต้องตรวจสอบก่อน execute Phase 3**: ให้คุณไปดูใน `~/Downloads/` ว่าชื่อโฟลเดอร์ที่ LINE สร้างมาจริงๆ มีรูปแบบอะไร (พิมพ์ `ls ~/Downloads/` ใน Terminal) เพื่อยืนยัน pattern ก่อนแก้ code

---

## Phase 4 — เพิ่ม Prompt ที่ขาดหายใน `ACCOUNTING_SYS_PROMPT`

### ปัญหาที่พบเพิ่มเติม
จาก Prompt ปัจจุบัน ยังขาดรายละเอียดสำคัญที่เคยตกลงกัน:

#### [MODIFY] [prompt.py](file:///Users/hare/meen/accounting-ai-coworker/backend/app/agent/prompt.py#L334)

```python
ACCOUNTING_SYS_PROMPT = """\
...
<workflow>
**Step 0 — Fetch Images**
- Execute: `python3 {scripts_dir}/fetch_from_downloads.py`
- This script scans `~/Downloads/` for folders matching LINE album name patterns:
  - Electricity: "DD/M/YYYY" format (e.g. "29/5/2569")  
  - Water: "DD/M/YYYY #1" format (e.g. "29/5/2569 #1")
- Images are resized/enhanced and moved to `{copilot_data_dir}/meter-photos/processed/YYYY-MM/`
- Output: list of processed files with shop_id and unit_type

**Step 1 — Batch OCR (Meter Reading)**
- สแกนโฟลเดอร์ `{copilot_data_dir}/meter-photos/processed/YYYY-MM/`
- ใช้ `read_image` วิเคราะห์รูปมิเตอร์ทีละรูป
- Extract: shop_id (จาก filename เช่น "A101_electric.jpg" → shop_id="A101"),
  reading (ตัวเลข), unit (water/electric), confidence
- ถ้า confidence ต่ำ: ข้าม Excel update สำหรับห้องนั้น และ mark เป็น failed

**Step 2 — Excel Update**
- Target: `{copilot_data_dir}/excel-files/template/รายงานมิเตอร์ น้ำไฟฟ้า ปี 2569.xlsx`
- ก่อนแก้ไข: สำเนาไปไว้ที่ `{copilot_data_dir}/excel-files/monthly/`
  ชื่อไฟล์: `รายงานมิเตอร์_YYYY-MM.xlsx`
- **Sheet naming**: ดูชื่อ sheet เดือนล่าสุด แล้ว duplicate มันและเปลี่ยนชื่อ
  - Format ไฟ: `ฟฟ ม.ค.69`, `ฟฟ ก.พ.69`, ... (ย่อเดือนภาษาไทย)
  - Format น้ำ: `ปป ม.ค.69`, `ปป ก.พ.69`, ...
- อัปเดต row ที่ตรงกับ shop_id:
  - คอลัมน์ "มิเตอร์เก่า" ← ค่า "มิเตอร์ใหม่" ของเดือนก่อน
  - คอลัมน์ "มิเตอร์ใหม่" ← ค่าที่ OCR ได้
  - Embed รูปในช่องที่กำหนด

**Step 3 — QC & Final Summary**
- ตรวจสอบ: มิเตอร์ใหม่ > มิเตอร์เก่า และ การใช้อยู่ในช่วง reasonable
- สรุปผลเป็นตาราง (ภาษาไทย):
  ห้อง | มิเตอร์เก่า | มิเตอร์ใหม่ | ใช้ไป | ประเภท | สถานะ
  (✅ ปกติ / ⚠️ ผิดปกติ / ❌ อ่านไม่ออก)
- ถ้ามีห้องที่ failed: ถามผู้ใช้ให้ใส่ค่าแบบ Manual
</workflow>
...
"""
```

---

## สรุป: ไฟล์ที่ต้องแก้ไขทั้งหมด

| ลำดับ | ไฟล์ | การเปลี่ยนแปลง |
|-------|------|----------------|
| 1 | [chat_service.py](file:///Users/hare/meen/accounting-ai-coworker/backend/app/service/chat_service.py) | Import + เพิ่ม accounting_agent ใน gather + unpack + add_worker |
| 2 | [accounting.py](file:///Users/hare/meen/accounting-ai-coworker/backend/app/agent/factory/accounting.py) | เพิ่ม `_get_copilot_data_dir()` + ส่ง param ใหม่ |
| 3 | [prompt.py](file:///Users/hare/meen/accounting-ai-coworker/backend/app/agent/prompt.py) | แก้ `ACCOUNTING_SYS_PROMPT` ลบ hardcode path + เพิ่ม `{copilot_data_dir}`, `{scripts_dir}` |
| 4 | [fetch_from_downloads.py](file:///Users/hare/meen/accounting-ai-coworker/scripts/fetch_from_downloads.py) | แก้ path + regex pattern |

**ไม่ต้องแก้ไข**: `agents.tsx`, `chatStore.ts`, `layout.json`, `task.py` — ถูกต้องอยู่แล้วครับ ✅

---

## วิธีทดสอบแต่ละ Phase

### Phase 1 Test — ทดสอบว่า Agent ปรากฏใน Workflow
**Manual:**
1. รีสตาร์ท Backend (`Ctrl+C` แล้วรัน `npm run dev` ใหม่)
2. เปิดแอป → สร้าง Project ใหม่
3. พิมพ์ prompt: `"รันกระบวนการทำบิลประจำเดือน พฤษภาคม 2569 กรุณาเริ่มได้เลย"`
4. ✅ **ผ่าน**: ไม่เกิด Error `NoneType object is not iterable` และเห็น "Accounting Copilot" ปรากฏใน Workflow Panel ด้านซ้าย
5. ✅ **ผ่าน**: Agent เริ่มทำ Step 0 (รัน fetch script)

### Phase 2 Test — ทดสอบ Path Resolution
**Manual:**
1. รัน script โดยตรง: `cd scripts && python3 fetch_from_downloads.py`
2. ✅ **ผ่าน**: ไม่ขึ้น `FileNotFoundError` เกี่ยวกับ path
3. ✅ **ผ่าน**: Script พิมพ์ `Scanning /Users/.../Downloads for meter reading folders...`

### Phase 3 Test — ทดสอบ Folder Pattern
**Manual:**
1. สร้างโฟลเดอร์ทดสอบใน `~/Downloads/`: `mkdir -p ~/Downloads/"29-5-2569"` และ `mkdir -p ~/Downloads/"29-5-2569 #1"`
2. ใส่รูป `.jpg` ทดสอบเข้าไปในโฟลเดอร์
3. รัน `python3 scripts/fetch_from_downloads.py`
4. ✅ **ผ่าน**: รูปถูก process และย้ายไปที่ `copilot_data/meter-photos/processed/YYYY-MM/`

### Phase 4 Test — ทดสอบ End-to-End ครั้งแรก (Integration Test)
**Manual (ใช้ข้อมูลจริงของเดือน พ.ค.):**
1. โหลดอัลบั้มจาก LINE มาใส่ใน `~/Downloads/` ตามชื่อจริง
2. รัน prompt: `"รันกระบวนการทำบิลประจำเดือน พฤษภาคม 2569 กรุณาเริ่มได้เลย"`
3. ✅ **ผ่าน Phase 4**: Agent ทำครบ 3 Step และแสดงตารางสรุปภาษาไทย
4. ✅ **ผ่าน**: ตาราง Excel ถูกอัปเดตใน monthly/ folder
5. เปรียบเทียบค่าในตารางกับเอกสารจริงของเดือน พ.ค.
