param(
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$LauncherPath = Join-Path $ProjectDir "FASTBULL_EDIT.bat"

if (-not (Test-Path $LauncherPath)) {
    throw "ไม่พบ FASTBULL_EDIT.bat ใน $ProjectDir"
}

$DesktopPath = [Environment]::GetFolderPath([Environment+SpecialFolder]::Desktop)
if (-not $DesktopPath) {
    throw "ไม่พบโฟลเดอร์ Desktop ของ Windows"
}

$ShortcutPath = Join-Path $DesktopPath "FASTBULL Editor.lnk"
$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $LauncherPath
$Shortcut.WorkingDirectory = $ProjectDir
$Shortcut.Description = "FASTBULL Automatic Video Editor"
$Shortcut.IconLocation = "$env:SystemRoot\System32\imageres.dll,15"
$Shortcut.WindowStyle = 1
$Shortcut.Save()

if (-not $Quiet) {
    Write-Host "สร้างไอคอน FASTBULL Editor บน Desktop แล้ว" -ForegroundColor Green
    Write-Host "จากนี้ดับเบิลคลิกไอคอน แล้วเลือกคลิปที่ต้องการตัดได้เลย"
}
