$ErrorActionPreference = "Stop"

$ScriptName = Split-Path -Leaf $MyInvocation.MyCommand.Path
$OS = "Windows"
$Arch = if ([Environment]::Is64BitOperatingSystem) { "x86_64" } else { "x86" }

Write-Host "${ScriptName}: detected OS=$OS ARCH=$Arch"

# sanity check: warn if no venv is active
if (-not $env:VIRTUAL_ENV) {
    Write-Host "${ScriptName}: WARNING - no venv appears to be active."
    Write-Host "${ScriptName}: run '.\.venv\Scripts\Activate.ps1' first, or this build"
    Write-Host "${ScriptName}: may use the wrong python/PyQt5 (or none at all)."
    $confirm = Read-Host "${ScriptName}: continue anyway? [y/N]"
    if ($confirm -ne "y" -and $confirm -ne "Y") {
        Write-Host "${ScriptName}: aborting."
        exit 1
    }
}

if ($Arch -ne "x86_64") {
    Write-Host "${ScriptName}: unsupported Windows arch '$Arch' (x86_64 only for now)"
    exit 1
}

Write-Host "${ScriptName}: building Windows onedir build"

# Note: PyInstaller on Windows uses ';' as the --add-data separator, not ':'
pyinstaller `
    --windowed `
    --onedir `
    --name APacKsplorer `
    --icon assets\APacKsplorer.ico `
    --add-data "tools;tools" `
    --add-data "ui;ui" `
    --add-data "forms;forms" `
    --add-data "assets;assets" `
    --noconfirm `
    .\gui\main_window.py

Write-Host "${ScriptName}: output at dist\APacKsplorer\"
Write-Host "${ScriptName}: done."

# xtra flags for reference: --debug=all