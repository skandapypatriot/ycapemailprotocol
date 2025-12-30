@echo off
setlocal enabledelayedexpansion

REM YCAP Protocol - Initial Setup

echo.
echo ========================================
echo YCAP Email Protocol - Setup
echo ========================================
echo.

REM Check Python installation
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3 is required but not installed
    echo Please install Python 3 from https://www.python.org/
    echo and make sure it's added to PATH
    pause
    exit /b 1
)

echo Python found:
python --version
echo.

REM Install required packages
echo Installing required Python packages...
echo.

pip install cryptography
if errorlevel 1 (
    echo ERROR: Failed to install cryptography
    pause
    exit /b 1
)

echo.
echo All dependencies installed successfully!
echo.

REM Generate and set YCAP_KEY
echo Generating YCAP_KEY environment variable...
for /f "delims=" %%A in ('python -c "from cryptography import fernet; print(fernet.Fernet.generate_key().decode())"') do (
    set "YCAP_KEY=%%A"
)

setx YCAP_KEY "!YCAP_KEY!"
echo YCAP_KEY has been set globally in Windows environment

echo.
echo ========================================
echo Setup Complete
echo ========================================
echo.
echo YCAP_KEY (saved to environment): !YCAP_KEY!
echo.
echo Next steps:
echo 1. Run "run_servers.bat" to start mail and file servers
echo 2. Run "run_client_example.bat" to test the client
echo.

pause
endlocal
