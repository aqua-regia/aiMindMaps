@echo off
REM AI Mind Map Generator - Setup Script for Windows
REM This script automates the installation process

echo ==========================================
echo AI Mind Map Generator - Setup
echo ==========================================
echo.

REM Check Python version
echo Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)

python --version
echo.

REM Create virtual environment
echo Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo Virtual environment created
) else (
    echo Virtual environment already exists
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo Virtual environment activated
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip --quiet
echo pip upgraded
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet
echo Dependencies installed
echo.

REM Create output directory
echo Creating output directory...
if not exist "output" mkdir output
echo Output directory created
echo.

REM Check for .env file
echo Checking environment configuration...
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo Created .env file from template
        echo.
        echo IMPORTANT: Please edit .env and add your DEEPSEEK_API_KEY
        echo You can get your API key from: https://platform.deepseek.com/
    ) else (
        echo WARNING: .env.example not found. Please create .env manually
    )
) else (
    echo .env file already exists
)
echo.

echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo Next steps:
echo 1. If not done already, edit .env and add your DEEPSEEK_API_KEY
echo 2. Activate the virtual environment: venv\Scripts\activate
echo 3. Run the application: python main.py
echo.
echo To activate the virtual environment in the future:
echo   venv\Scripts\activate
echo.
pause

