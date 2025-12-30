@echo off
setlocal enabledelayedexpansion

REM YCAP Email Protocol Server Launcher
REM This batch file initializes all necessary environment variables and starts the servers

echo.
echo ========================================
echo YCAP Email Protocol - Server Launcher
echo ========================================
echo.

REM Generate YCAP_KEY if not set
if not defined YCAP_KEY (
    echo Generating YCAP_KEY...
    for /f "delims=" %%A in ('python -c "from cryptography import fernet; print(fernet.Fernet.generate_key().decode())"') do (
        set "YCAP_KEY=%%A"
    )
    setx YCAP_KEY "!YCAP_KEY!"
    echo YCAP_KEY generated and saved: !YCAP_KEY!
) else (
    echo YCAP_KEY already set
)

echo.
echo ========================================
echo Environment Variables Initialized
echo ========================================
echo YCAP_KEY: !YCAP_KEY!
echo Current Directory: %CD%
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo Python found:
python --version
echo.

REM Check if required Python packages are installed
echo Checking required packages...
python -c "import cryptography, sqlite3" >nul 2>&1
if errorlevel 1 (
    echo WARNING: cryptography package not found. Installing...
    pip install cryptography
)

echo.
echo ========================================
echo Starting YCAP Servers
echo ========================================
echo.

REM Create output logs directory
if not exist "logs" mkdir logs

REM Get current date/time for log files
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a-%%b)

set LOGFILE=logs\server_%mydate%_%mytime%.log

echo Log file: %LOGFILE%
echo.

REM Start Mail Server in new window
echo Starting Mail Server on localhost:1200...
start "YCAP Mail Server" /D "%CD%" cmd /k python server.py
timeout /t 2 /nobreak

REM Start File Server in new window
echo Starting File Server on localhost:5124...
start "YCAP File Server" /D "%CD%" cmd /k python file_server.py
timeout /t 2 /nobreak

echo.
echo ========================================
echo Servers Started Successfully
echo ========================================
echo.
echo Mail Server:    localhost:1200
echo File Server:    localhost:5124
echo.
echo Press Ctrl+B in Mail Server window to shutdown
echo Close File Server window to stop it
echo.
echo To stop all servers, close the server windows or press:
echo - Ctrl+C in any server window
echo.

pause
endlocal
