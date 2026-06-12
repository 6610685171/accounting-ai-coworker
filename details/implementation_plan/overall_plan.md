# **AI Accounting Copilot: Overall Implementation Plan (Revised with Eigent Native Agents)**

จากการตรวจสอบ `README.md` ของ Eigent แพลตฟอร์มมี Agent สำเร็จรูป (Pre-defined Agents) และฟีเจอร์พื้นฐานที่แข็งแกร่งมาก ซึ่งเรา **สามารถนำมาใช้ซ้ำ (Reuse) ได้เกือบ 100% โดยไม่ต้องเขียน Agent เองใหม่ตั้งแต่ต้น** สิ่งนี้จะช่วยประหยัดเวลาการพัฒนาได้อย่างมหาศาล

## 🔄 สรุปการจับคู่ (Mapping) เครื่องมือของ Eigent กับระบบของเรา

| งานในระบบบัญชีของเรา | Eigent Agent / Feature ที่จะนำมาใช้ | รายละเอียดการประยุกต์ใช้ |
| :--- | :--- | :--- |
| **1. เฝ้าดูรูปมิเตอร์ใหม่** | **Triggers (Native Feature)** | ใช้ระบบตั้งเวลา/เงื่อนไขของ Eigent เพื่อเช็คโฟลเดอร์ภาพอัตโนมัติ โดยไม่ต้องเขียน File Watcher เอง |
| **2. อ่านเลขมิเตอร์ (OCR)** | **Multi-Modal Agent** | ให้ Agent ตัวนี้อ่านรูปภาพมิเตอร์และสกัดตัวเลขออกมาเป็น JSON ได้เลย ไม่ต้องเขียนต่อ API Vision เอง |
| **3. กรอกไฟล์ Excel และ QC** | **Document Agent + `xlsx` Skill** | ใช้ Document Agent ร่วมกับ `xlsx` skill (ที่มีอยู่แล้วใน `resources/example-skills/xlsx`) เพื่อให้จัดการสูตรและวางภาพใน Excel อย่างปลอดภัย |
| **4. เชื่อมต่อ FlowAccount** | **MCP Integration (Native)** | Eigent รองรับ MCP ให้อยู่แล้ว แค่นำ FlowAccount MCP มาเสียบ ระบบก็จะเข้าใจวิธีดึง/สร้าง Draft Invoice ได้เอง |

---

## 🗓️ ไทม์ไลน์ 6 สัปดาห์ (อัปเดตใหม่ เน้นการใช้ Native Agents)

### **สัปดาห์ที่ 1: Foundation & Thai Localization**
* **เป้าหมาย:** เตรียมระบบพื้นฐานและแปลภาษา
* **งานที่ทำ:**
  * แปลไฟล์ใน `src/i18n/locales/` เป็นภาษาไทย
  * จัดเตรียมโฟลเดอร์สำหรับเอกสาร (`copilot_data/meter-photos`, `copilot_data/excel-files`)
  * กำหนดโครงสร้าง Database ลูกค้าใน Sheet ของ Excel

### **สัปดาห์ที่ 2: Meter Reader Copilot (ใช้ Multi-Modal & Document Agent)**
* **เป้าหมาย:** สกัดข้อความจากภาพมิเตอร์ลง Excel
* **งานที่ทำ:**
  * ตั้งค่า **Triggers** ให้เริ่มงานเมื่อมีไฟล์ภาพใหม่ใน Inbox
  * สร้าง Workflow ให้ส่งภาพไปที่ **Multi-Modal Agent** เพื่อทำ OCR สกัดเลขห้องและเลขมิเตอร์
  * ส่งข้อมูลที่สกัดได้ไปให้ **Document Agent** (ใช้ `xlsx` skill) เข้าไปเปิดไฟล์บริษัท, กรอกเลข, คัดลอกสูตรคำนวณเงิน, และฝังรูปภาพมิเตอร์ลงไป

### **สัปดาห์ที่ 3: Invoice Draft Copilot (ใช้ MCP Integration)**
* **เป้าหมาย:** ส่งข้อมูลจาก Excel ไปสร้างใบแจ้งหนี้
* **งานที่ทำ:**
  * ติดตั้งและทดสอบปลั๊กอิน FlowAccount MCP บน Eigent (ทดสอบกับ Test Company)
  * สร้าง Workflow ให้ Agent ดึงข้อมูลยอดสุทธิจากไฟล์ Excel แล้วเรียกใช้ MCP tool เพื่อสร้าง Draft Invoice โดยตรง

### **สัปดาห์ที่ 4: Human-in-the-Loop & Workflow Coordination**
* **เป้าหมาย:** วางจุดตรวจสอบให้มนุษย์เข้ามาแทรกแซง
* **งานที่ทำ:**
  * ใช้ฟีเจอร์ **Human-in-the-Loop** ของ Eigent ตั้งค่าแชทแจ้งเตือนให้พนักงานบัญชีกด "ตรวจสอบและอนุมัติ" ใน 2 จุดหลัก: 
    1. หลังอัปเดต Excel เสร็จ (ก่อนยิง FlowAccount)
    2. หลังสร้าง FlowAccount Draft เสร็จ (ก่อนยิงข้อความหาลูกค้า)

### **สัปดาห์ที่ 5: Flexible LINE Delivery (ใช้ Document Agent)**
* **เป้าหมาย:** สร้างข้อความส่ง LINE ที่แก้ไขได้
* **งานที่ทำ:**
  * ให้ **Document Agent** อ่าน Template การส่งข้อความจาก Excel
  * นำข้อมูลมาสวมใน Template และสร้างเป็นข้อความแจ้งหนี้/ส่งภาพ Invoice สรุปมาให้ในแชท Eigent
  * ให้พนักงานบัญชีสามารถ Copy ข้อความไปส่งเอง (Manual Mode) หรือถ้ามีเวลาอาจจะเชื่อมต่อ LINE MCP สำหรับส่งอัตโนมัติ

### **สัปดาห์ที่ 6: Polish, Edge Cases & Demo Prep**
* **เป้าหมาย:** เก็บงานและแก้ไขข้อผิดพลาด
* **งานที่ทำ:**
  * ปรับจูน Prompt ของ Multi-Modal Agent ให้รับมือกับภาพเบลอ หรือเลขมิเตอร์ที่ไม่สมเหตุสมผล
  * จัดทำเอกสารคู่มือ (User Guide)
  * เตรียมซ้อม Live Demo ทั้งระบบ
