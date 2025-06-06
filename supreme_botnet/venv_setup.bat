@echo off
setlocal EnableDelayedExpansion

:: ================================
:: Setup virtual environment
:: ================================

echo [*] Creating virtual environment...
C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe -m venv venv

if not exist venv\Scripts\activate.bat (
    echo [!] Failed to create virtual environment. Make sure Python is installed and on PATH.
    exit /b 1
)

echo [*] Activating virtual environment...
call venv\Scripts\activate.bat

echo [*] Upgrading pip, setuptools, and wheel...
python -m pip install --upgrade pip setuptools wheel

echo [*] Installing requirements...
if exist requirements.txt (
    pip install -r requirements.txt
) else (
    echo [!] requirements.txt not found. Creating a basic one...
    > requirements.txt echo undetected-chromedriver
    >> requirements.txt echo selenium
    >> requirements.txt echo selenium-wire
    >> requirements.txt echo requests
    >> requirements.txt echo beautifulsoup4
    >> requirements.txt echo tldextract
    >> requirements.txt echo flask
    >> requirements.txt echo blinker
    >> requirements.txt echo zstandard
    >> requirements.txt echo certifi
    >> requirements.txt echo lxml
    >> requirements.txt echo openpyxl
    >> requirements.txt echo colorama
    >> requirements.txt echo psutil
    >> requirements.txt echo pycryptodome
    pip install -r requirements.txt
)

echo [✓] Virtual environment setup complete.
echo ----------------------------------------
echo To activate it manually in the future:
echo   call venv\Scripts\activate.bat
echo ----------------------------------------

pause
