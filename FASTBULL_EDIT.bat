@echo off
chcp 65001 >nul
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo ยังตั้งค่าระบบไม่เสร็จ กรุณาดับเบิลคลิก FASTBULL_SETUP_WINDOWS.bat ก่อน 1 ครั้ง
  pause
  exit /b 1
)

set "INPUT=%~1"
if not defined INPUT (
  for /f "usebackq delims=" %%I in (`powershell -NoProfile -STA -ExecutionPolicy Bypass -File "scripts\select_video.ps1"`) do set "INPUT=%%I"
)
if not defined INPUT exit /b 0
if not exist "%INPUT%" (
  echo ไม่พบไฟล์วิดีโอ: %INPUT%
  pause
  exit /b 1
)

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
