@echo off
setlocal
cd /d "%~dp0"
set "INPUT=%~1"
if "%INPUT%"=="" set /p "INPUT=ลากไฟล์วิดีโอมาวาง หรือพิมพ์ที่อยู่ไฟล์: "
set /p "MODE=โหมด (vlog / value / awareness / sales): "
if "%MODE%"=="" set "MODE=value"
set /p "HEADLINE=พาดหัว (เว้นว่างให้ระบบทำฉบับร่าง): "
set /p "PAGE=ชื่อเพจ: "
if "%PAGE%"=="" set "PAGE=FASTBULL"
set /p "CTA=ข้อความปิดคลิป (เว้นว่างใช้ค่าตามโหมด): "
set /p "BROLL=โฟลเดอร์ B-roll ที่ได้รับอนุญาต (เว้นว่างถ้าไม่มี): "

if "%BROLL%"=="" (
  if "%CTA%"=="" (
    ".venv\Scripts\python.exe" scripts\fastbull_editor.py run --input "%INPUT%" --mode "%MODE%" --headline "%HEADLINE%" --page-name "%PAGE%"
  ) else (
    ".venv\Scripts\python.exe" scripts\fastbull_editor.py run --input "%INPUT%" --mode "%MODE%" --headline "%HEADLINE%" --page-name "%PAGE%" --cta "%CTA%"
  )
) else (
  if "%CTA%"=="" (
    ".venv\Scripts\python.exe" scripts\fastbull_editor.py run --input "%INPUT%" --mode "%MODE%" --headline "%HEADLINE%" --page-name "%PAGE%" --broll "%BROLL%"
  ) else (
    ".venv\Scripts\python.exe" scripts\fastbull_editor.py run --input "%INPUT%" --mode "%MODE%" --headline "%HEADLINE%" --page-name "%PAGE%" --cta "%CTA%" --broll "%BROLL%"
  )
)
if errorlevel 1 (
  echo.
  echo เกิดข้อผิดพลาด ดูข้อความด้านบน
  pause
  exit /b 1
)
echo.
echo ตัดต่อเสร็จแล้ว เปิดโฟลเดอร์ FASTBULL_OUTPUT เพื่อดูไฟล์
pause
