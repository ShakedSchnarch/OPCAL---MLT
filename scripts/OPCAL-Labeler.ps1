$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

function New-LocalVenv {
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        & py -3.12 -m venv .venv
        return
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        & python -m venv .venv
        return
    }

    throw "Python 3.12 is required. Install it from python.org, then rerun this script."
}

if (-not (Test-Path ".venv")) {
    Write-Host "Creating local Python environment..."
    New-LocalVenv
}

$VenvPython = Join-Path $RootDir ".venv\Scripts\python.exe"

Write-Host "Installing/updating OPCAL-MLT dependencies..."
& $VenvPython -m pip install --upgrade pip setuptools wheel
& $VenvPython -m pip install -e .

Write-Host "Launching OPCAL-Labeler..."
& (Join-Path $RootDir ".venv\Scripts\opcal-mlt.exe")
