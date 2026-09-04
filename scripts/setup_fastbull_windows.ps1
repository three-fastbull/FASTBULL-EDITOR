$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectDir

function Refresh-Path {
    $machine = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $user = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machine;$user"
}

function Ensure-WingetPackage([string]$Command, [string]$PackageId) {
    if (-not (Get-Command $Command -ErrorAction SilentlyContinue)) {
        if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
            throw "ไม่พบ $Command และไม่พบ winget กรุณาติดตั้ง $PackageId แล้วรันไฟล์นี้ใหม่"
        }
        winget install --id $PackageId --exact --accept-package-agreements --accept-source-agreements
        Refresh-Path
    }
}

Ensure-WingetPackage "python" "Python.Python.3.12"
Ensure-WingetPackage "node" "OpenJS.NodeJS.LTS"
Ensure-WingetPackage "ffmpeg" "Gyan.FFmpeg"

$nodeMajor = [int]((& node --version).TrimStart("v").Split(".")[0])
if ($nodeMajor -lt 22) { throw "ต้องใช้ Node.js 22 ขึ้นไป แต่พบ $(& node --version)" }

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3.12 -m venv .venv
} else {
    & python -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements-fastbull.txt
& .\.venv\Scripts\python.exe scripts\download_whisper_model.py --model small

Push-Location remotion-composer
& npm.cmd ci
Pop-Location

& npm.cmd install --ignore-scripts --no-save --package-lock=false hyperframes@0.8.27

$browserCandidates = @(
    "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
)
$BrowserPath = $browserCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $BrowserPath) { throw "ไม่พบ Microsoft Edge หรือ Google Chrome สำหรับเรนเดอร์วิดีโอ" }
$env:HYPERFRAMES_BROWSER_PATH = $BrowserPath

if (-not (Test-Path .env)) { Copy-Item .env.example .env }
$envBody = Get-Content .env -Raw
$settings = @{
    HYPERFRAMES_BROWSER_PATH = $BrowserPath
    HYPERFRAMES_NO_UPDATE_CHECK = "1"
    HYPERFRAMES_NO_AUTO_INSTALL = "1"
    HYPERFRAMES_NO_TELEMETRY = "1"
}
foreach ($key in $settings.Keys) {
    $line = "$key=$($settings[$key])"
    if ($envBody -match "(?m)^$key=.*$") {
        $envBody = [regex]::Replace($envBody, "(?m)^$key=.*$", $line)
    } else {
        $envBody = $envBody.TrimEnd() + "`r`n$line`r`n"
    }
}
Set-Content .env -Value $envBody -Encoding utf8

& .\node_modules\.bin\hyperframes.cmd telemetry disable
& .\.venv\Scripts\python.exe scripts\fastbull_editor.py doctor
& "$PSScriptRoot\create_fastbull_desktop_shortcut.ps1" -Quiet
Write-Host "FASTBULL Editor พร้อมใช้งาน ค่า API 0 บาท" -ForegroundColor Green
Write-Host "สร้างไอคอน FASTBULL Editor บน Desktop แล้ว" -ForegroundColor Green
