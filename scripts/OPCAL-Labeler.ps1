$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot
$py = $env:PYTHON_BIN; if (-not $py) { $py = "py" }
$venv = ".opcal-venv"
if (-not (Test-Path $venv)) { & $py -3 -m venv $venv }
& "$venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip | Out-Null
python -m pip install -e .
python -m streamlit run app\main.py