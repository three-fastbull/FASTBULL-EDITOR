param(
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$LauncherPath = Join-Path $ProjectDir "FASTBULL_EDIT.bat"

if (-not (Test-Path $LauncherPath)) {
    throw "FASTBULL_EDIT.bat was not found in $ProjectDir"
}

$DesktopPath = [Environment]::GetFolderPath([Environment+SpecialFolder]::Desktop)
if (-not $DesktopPath) {
    throw "The Windows Desktop folder was not found"
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
    Write-Host "FASTBULL Editor shortcut was created on your Desktop." -ForegroundColor Green
    Write-Host "Double-click the shortcut and choose a video to begin."
}
