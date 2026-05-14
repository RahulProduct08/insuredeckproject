@echo off
REM Time Tracker Automation - Quick Setup Script

echo.
echo ================================
echo Time Tracker Automation Setup
echo ================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python found
echo.
echo Installing dependencies...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [OK] Dependencies installed successfully
echo.
echo ================================
echo NEXT STEPS:
echo ================================
echo.
echo 1. Open time_tracker_config.json in a text editor
echo.
echo 2. Update these fields:
echo    - "url": Your EMS/Time Tracker login page
echo    - "username": Your username
echo    - "password": Your password
echo.
echo 3. Customize daily_entries with your work tickets
echo.
echo 4. Test the script:
echo    python time_tracker_automation.py
echo.
echo 5. Schedule daily automation (Run as Administrator):
echo    powershell -ExecutionPolicy Bypass -File setup_scheduler.ps1
echo.
echo For detailed instructions, see AUTOMATION_GUIDE.md
echo.
pause
