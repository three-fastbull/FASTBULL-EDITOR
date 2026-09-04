$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Windows.Forms

$dialog = New-Object System.Windows.Forms.OpenFileDialog
$dialog.Title = "เลือกคลิปดิบสำหรับ FASTBULL Editor"
$dialog.Filter = "ไฟล์วิดีโอ|*.mp4;*.mov;*.mkv;*.webm;*.m4v;*.avi|ไฟล์ทั้งหมด|*.*"
$dialog.Multiselect = $false
$dialog.CheckFileExists = $true

if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    Write-Output $dialog.FileName
}
