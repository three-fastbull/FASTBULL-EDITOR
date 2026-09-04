# FASTBULL-EDITOR

ระบบตัดต่อคลิปพูดและ VLOG แนวตั้งอัตโนมัติของ FASTBULL พัฒนาต่อจาก
[OpenMontage](https://github.com/calesthio/OpenMontage) และใช้ Runtime
ในเครื่องแบบไม่เสียค่า API

## งานที่ระบบทำในคำสั่งเดียว

- ตรวจความละเอียด เสียง ระยะเวลา และสุ่มเฟรมจากไฟล์ดิบ
- ถอดเสียงไทยด้วย Whisper พร้อมเวลารายคำและแบ่งคำด้วย PyThaiNLP
- ตรวจช่วงเงียบ คำซ้ำ คำฟิลเลอร์ และคำความมั่นใจต่ำ
- ตัดช่วงเงียบแบบมีระยะเผื่อเพื่อไม่กินพยางค์
- เลือกจังหวะสำหรับ VLOG, คุณค่า, Awareness หรือ Sales
- ปรับเสียงพูดและความดังสำหรับโซเชียล
- จับคู่ B-roll ในเครื่อง หรือสร้าง Motion Card เมื่อลูกค้าไม่มีภาพประกอบ
- ใส่ซับ พาดหัว SPORT LUXURY Navy–Gold เอฟเฟกต์เสียง และ CTA
- ส่งออก 1080×1920 H.264/AAC พร้อม `quality_report.json`

## ติดตั้ง

Windows: ดับเบิลคลิก `FASTBULL_SETUP_WINDOWS.bat`

Linux/macOS ที่มี Python, Node 22+ และ FFmpeg:

```bash
bash scripts/setup_fastbull_free.sh
```

ตรวจความพร้อม:

```bash
.venv/bin/python scripts/fastbull_editor.py doctor
```

## ตัดคลิป

Windows: ลาก MP4 ไปวางบน `FASTBULL_EDIT.bat`

หรือใช้คำสั่ง:

```bash
.venv/bin/python scripts/fastbull_editor.py run \
  --input clip.mp4 --mode value \
  --headline "มีเงินแล้ว มีเวลาหรือยัง?" \
  --page-name FASTBULL --cta "กดติดตาม"
```

ผลลัพธ์และรายงานอยู่ใน `FASTBULL_OUTPUT/` ถ้ามี B-roll ที่ได้รับอนุญาต
ให้เพิ่ม `--broll path/to/folder`

## ต้นทุน

FFmpeg, Whisper, PyThaiNLP, Remotion, HyperFrames, Chromium และเสียงที่สร้างในเครื่อง
มีค่า API 0 บาท แต่ยังใช้ทรัพยากร CPU/GPU พื้นที่เก็บไฟล์ อินเทอร์เน็ตตอนติดตั้ง
และค่าไฟ บริการสร้างสื่อหรือ Stock ภายนอกไม่จำเป็นและจะไม่ถูกเรียกอัตโนมัติ

## หมายเหตุเรื่องไฟล์ติดตั้ง

Git ไม่เก็บ `.env`, `.venv`, `node_modules` และ `.runtime` เพราะเป็นไฟล์เฉพาะเครื่อง
หรือมีขนาดใหญ่ เมื่อ Clone ลงเครื่องใหม่ให้รันตัวติดตั้งเพื่อสร้างกลับมา

## ขอบเขตความปลอดภัย

ระบบแก้เฉพาะคำที่ผู้ใช้ยืนยันผ่านไฟล์ corrections และลบช่วงเงียบอัตโนมัติ
คำไม่ชัด คำเคลม ชื่อเฉพาะ ตัวเลข และประโยคที่อาจพูดผิดจะถูกทำเครื่องหมายไว้
ให้คนตรวจ ไม่เดาแล้วลบทิ้ง ก่อนส่งลูกค้าต้องดูและฟังเต็มคลิปหนึ่งรอบ
