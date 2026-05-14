@echo off
REM Temple Quest - Installation Helper for Windows
REM This script installs all dependencies

echo.
echo ============================================================
echo.
echo  🏛️  TEMPLE QUEST - Installation Helper 🏛️
echo.
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed!
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo ✅ Python found!
echo.
python --version
echo.

REM Install requirements
echo Installing dependencies...
echo.
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install dependencies!
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ Installation complete!
echo.
echo ============================================================
echo.
echo 🎮 CHOOSE YOUR VERSION:
echo.
echo 1. Web Version (Browser)
echo    Command: python mario_india_web.py
echo    Then open: http://localhost:5000
echo.
echo 2. Desktop Version
echo    Command: python mario_india_game_enhanced.py
echo.
echo ============================================================
echo.
pause
