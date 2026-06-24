$Rebuild = $args -contains "--rebuild"
$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

function Get-PythonCommand {
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        & py -3.12 -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) {
            return @("py", "-3.12")
        }
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        & python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) {
            return @("python")
        }
    }

    throw "Python 3.12 is required. Install it from python.org, then rerun this script."
}

function Invoke-Python {
    param([string[]]$PythonCommand, [string[]]$PythonArgs)
    if ($PythonCommand.Length -gt 1) {
        $PrefixArgs = $PythonCommand[1..($PythonCommand.Length - 1)]
        & $PythonCommand[0] @PrefixArgs @PythonArgs
    } else {
        & $PythonCommand[0] @PythonArgs
    }
}

function New-LocalVenv {
    param([string[]]$PythonCommand)
    Invoke-Python $PythonCommand @("-m", "venv", ".venv")
}

function Test-LocalInstall {
    param([string]$VenvPython)
    if (-not (Test-Path $VenvPython)) {
        return $false
    }
    & $VenvPython -c "import opcal_mlt; from opcal_mlt.version import get_app_version; raise SystemExit(0 if get_app_version() == '1.2.0' else 1)" 2>$null
    return $LASTEXITCODE -eq 0
}

$PythonCommand = Get-PythonCommand

if ($Rebuild -and (Test-Path ".venv")) {
    Write-Host "Removing local Python environment..."
    Remove-Item ".venv" -Recurse -Force
}

if (-not (Test-Path ".venv")) {
    Write-Host "Creating local Python environment..."
    New-LocalVenv $PythonCommand
}

$VenvPython = Join-Path $RootDir ".venv\Scripts\python.exe"

if (-not (Test-LocalInstall $VenvPython)) {
    Write-Host "Installing/updating OPCAL-MLT dependencies..."
    & $VenvPython -m pip install --upgrade pip setuptools wheel
    & $VenvPython -m pip install -e .
}

if (-not (Test-LocalInstall $VenvPython)) {
    Write-Host ""
    Write-Host "The local .venv exists but OPCAL-MLT still cannot be imported correctly."
    Write-Host "Run this launcher again with --rebuild to recreate .venv from scratch:"
    Write-Host "powershell -ExecutionPolicy Bypass -File .\scripts\OPCAL-Labeler.ps1 --rebuild"
    Read-Host "Press Enter to close"
    exit 1
}

Write-Host "Launching OPCAL-Labeler..."
& (Join-Path $RootDir ".venv\Scripts\opcal-mlt.exe")
