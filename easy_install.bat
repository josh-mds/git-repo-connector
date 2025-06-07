@echo off
echo GitHub Account Manager - Easy Installer
echo =======================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7 or later from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo Detected Python installation: 
python --version

echo.
echo What would you like to do?
echo [1] Build executable from source
echo [2] Install already-built executable
echo [3] Just install Python dependencies
echo.
set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" (
    echo.
    echo Building executable from Python source...
    echo This will create a Windows .exe file
    echo.
    python setup.py
    if %errorlevel% equ 0 (
        echo.
        echo Build completed! Now installing...
        python install.py
    )
) else if "%choice%"=="2" (
    echo.
    echo Installing already-built executable...
    python install.py
) else if "%choice%"=="3" (
    echo.
    echo Installing Python dependencies only...
    pip install -r requirements.txt
    echo.
    echo Dependencies installed. You can now run: python github_account_manager.py
) else (
    echo Invalid choice. Please run the script again.
)

echo.
pause