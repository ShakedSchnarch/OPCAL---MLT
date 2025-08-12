@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
where py >NUL 2>&1 || (echo [ERROR] Python launcher not found. Install Python 3.10+ & pause & exit /b 1)
set VENV=.opcal-venv
if not exist "%VENV%" ( py -3 -m venv "%VENV%" )
call "%VENV%\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -e .
python -m streamlit run app\main.py