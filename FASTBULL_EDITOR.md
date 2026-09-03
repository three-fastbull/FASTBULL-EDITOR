# FASTBULL-EDITOR

ระบบตัดต่อวิดีโออัตโนมัติของ FASTBULL ซึ่งพัฒนาต่อจาก
[OpenMontage](https://github.com/calesthio/OpenMontage) โดยเริ่มจาก Runtime
แบบไม่เสียค่า API สำหรับงานตัดต่อและ Motion Graphics

## สิ่งที่พร้อมใช้งานแล้ว

- OpenMontage และ Python environment
- HyperFrames CLI 0.8.27
- Chromium Headless สำหรับตรวจและเรนเดอร์เฟรม
- FFmpeg สำหรับประกอบไฟล์วิดีโอ
- GSAP แบบ Local ไม่ต้องโหลดจาก CDN ระหว่างเรนเดอร์
- Noto Sans Thai เป็นฟอนต์สำรองสำหรับข้อความและซับภาษาไทย
- ปิด HyperFrames Telemetry

## ติดตั้งบน Linux หรือ Codex Workspace

ติดตั้ง OpenMontage ก่อน:

```bash
make setup
```

จากนั้นติดตั้ง HyperFrames Runtime:

```bash
bash scripts/setup_hyperframes_local.sh
```

สคริปต์จะติดตั้ง Runtime, เตรียม Chromium และบันทึกค่าที่จำเป็นลง `.env`
โดยอัตโนมัติ ไม่ต้องใช้ API key

## ต้นทุน

การตัดต่อด้วย HyperFrames, Chromium และ FFmpeg ภายในเครื่องมีค่า API
เท่ากับ 0 บาท แต่ยังใช้ทรัพยากร CPU, พื้นที่จัดเก็บ และเวลาในการเรนเดอร์

บริการสร้างภาพ วิดีโอ เสียง หรือ Stock Media จากผู้ให้บริการภายนอกเป็นส่วนเสริม
และอาจมีค่าใช้จ่ายภายหลัง ผู้ใช้สามารถเลือกเปิดเฉพาะบริการที่ต้องการได้

## หมายเหตุเรื่องไฟล์ติดตั้ง

Git จะไม่เก็บ `.env`, `node_modules/` และ `.runtime/` เพราะมีไฟล์เฉพาะเครื่อง
หรือไฟล์ขนาดใหญ่ เมื่อ Clone โปรเจกต์ลงเครื่องใหม่ ให้รันสคริปต์ติดตั้งด้านบน
เพื่อสร้างไฟล์เหล่านี้กลับมา

