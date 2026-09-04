$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Windows.Forms

$dialog = New-Object System.Windows.Forms.OpenFileDialog
$dialog.Title = "Choose a raw video for FASTBULL Editor"
$dialog.Filter = "Video files|*.mp4;*.mov;*.mkv;*.webm;*.m4v;*.avi|All files|*.*"
$dialog.Multiselect = $false
$dialog.CheckFileExists = $true

if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    Write-Output $dialog.FileName
}
