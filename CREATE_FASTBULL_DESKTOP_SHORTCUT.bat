@echo off
chcp 65001 >nul
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\create_fastbull_desktop_shortcut.ps1"
if errorlevel 1 (
  echo.
  echo สร้างไอคอนไม่สำเร็จ กรุณาส่งภาพหน้าจอนี้มาให้ตรวจ
  pause
  exit /b 1
)
echo.
pause
