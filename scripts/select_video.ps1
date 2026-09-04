param(
    [Parameter(Mandatory = $true)]
    [string]$OutputPath,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$InputFiles
)

$ErrorActionPreference = "Stop"

if (Test-Path $OutputPath) {
    Remove-Item $OutputPath -Force
}

Add-Type -AssemblyName System.Windows.Forms

$SelectedFiles = @($InputFiles | Where-Object { $_ })
if ($SelectedFiles.Count -eq 0) {
    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.Title = "Choose one or more raw videos for FASTBULL Editor"
    $dialog.Filter = "Video files|*.mp4;*.mov;*.mkv;*.webm;*.m4v;*.avi|All files|*.*"
    $dialog.Multiselect = $true
    $dialog.CheckFileExists = $true
    $dialog.InitialDirectory = [Environment]::GetFolderPath([Environment+SpecialFolder]::MyVideos)

    if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
        exit 0
    }
    $SelectedFiles = @($dialog.FileNames)
}

$Utf8Bom = New-Object System.Text.UTF8Encoding -ArgumentList $true
[System.IO.File]::WriteAllLines($OutputPath, [string[]]$SelectedFiles, $Utf8Bom)
