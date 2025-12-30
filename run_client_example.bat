@echo off
setlocal enabledelayedexpansion

REM YCAP Client Example Launcher

echo.
echo ========================================
echo YCAP Email Protocol - Client Launcher
echo ========================================
echo.

REM Check YCAP_KEY environment variable
if not defined YCAP_KEY (
    echo ERROR: YCAP_KEY not set. Please run run_servers.bat first.
    pause
    exit /b 1
)

echo YCAP_KEY is set.
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

REM Create client example script if it doesn't exist
if not exist "client_example.py" (
    echo Creating client_example.py...
    (
        echo from client import Client, sign_up
        echo import time
        echo.
        echo # Example usage
        echo if __name__ == "__main__":
        echo     try:
        echo         # Sign up a new user
        echo         print("Signing up test user...")
        echo         sign_up("testuser", "testpass123", "localhost", 1200)
        echo         print("Sign up successful!")
        echo.
        echo         # Connect as client
        echo         print("\nConnecting to YCAP server...")
        echo         client = Client("localhost", 1200, "testuser^ycap.com", "testpass123")
        echo         print("Connected successfully!")
        echo.
        echo         # Example: Get mails
        echo         print("\nFetching mails...")
        echo         mails = client.get_mail(sent=False, no=5)
        echo         print(f"Got {len(mails) if mails else 0} mails")
        echo.
        echo         # Example: Send text mail
        echo         print("\nSending test mail...")
        echo         result = client.send_mail("testuser2^ycap.com", "text", "Hello, this is a test!")
        echo         print(f"Mail sent: {result}")
        echo.
        echo         # Example: Send file
        echo         print("\nTo send a file, use: client.send_file('recipient@ycap.com', 'path/to/file')")
        echo         print("To download file, use: client.download_file('file_hash', 'save_path')")
        echo.
        echo         print("\nClient session active. Press Ctrl+C to exit.")
        echo         while True:
        echo             time.sleep(1)
        echo.
        echo     except Exception as e:
        echo         print(f"Error: {e}")
        echo         import traceback
        echo         traceback.print_exc()
        echo     finally:
        echo         print("\nDisconnecting...")
    ) > client_example.py
    echo client_example.py created.
)

echo.
echo ========================================
echo Starting Client Example
echo ========================================
echo.

python client_example.py

pause
endlocal
