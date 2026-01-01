    @echo off
    setlocal
    echo ==========================================
    echo NITRO SYSTEM INITIALIZING
    echo ==========================================

    REM Killing existing processes
    echo Killing any existing Node/Python/Chrome processes...
    taskkill /F /IM node.exe /T 2>nul
    taskkill /F /IM uvicorn.exe /T 2>nul
    taskkill /F /IM python.exe /T 2>nul
    taskkill /F /IM chromedriver.exe /T 2>nul
    taskkill /F /IM chrome.exe /T 2>nul

    REM Cleaning caches
    echo Cleaning corrupted driver and Vite cache...
    if exist "%APPDATA%\undetected_chromedriver" rmdir /s /q "%APPDATA%\undetected_chromedriver"
    if exist meih-netflix-clone\node_modules\.vite rmdir /s /q meih-netflix-clone\node_modules\.vite

    REM Backend Setup
    echo Setting up Backend...
    set ROOT_DIR=%~dp0
    cd /d "%ROOT_DIR%backend"
    if not exist venv (
        python -m venv venv
    )
    call venv\Scripts\activate
    pip install -r requirements.txt
    
    REM Ensure Playwright Browsers are installed
    if not exist "%LOCALAPPDATA%\ms-playwright" (
        echo [!] Installing Playwright browsers...
        venv\Scripts\playwright install chromium
    )

    REM Start FlareSolverr in Ghost Mode
    echo Starting FlareSolverr Local Engine (Ghost Mode)...
    set PORT=8191
    set SKIP_BROWSER_TEST=true
    set HEADLESS=true
    set LOG_LEVEL=error
    start /B "FlareSolverr" cmd /c "cd flaresolverr && ..\venv\Scripts\python flaresolverr.py"

    REM Give FlareSolverr a moment to wake up
    timeout /t 5 /nobreak >nul

    REM Start FastAPI Backend
    echo Starting FastAPI Backend (Turbo Mode)...
    start /B "Backend" cmd /c "venv\Scripts\uvicorn main:app --port 8000 --workers 1"

    REM Frontend Setup
    echo Setting up Frontend...
    cd /d "%ROOT_DIR%meih-netflix-clone"
    if not exist node_modules (
        echo [!] First time setup: Installing node modules...
        call npm install
    )

    REM Start Frontend
    echo Starting Frontend (Vite)...
    set VITE_CJS_IGNORE_WARNING=true
    start "Frontend" cmd /k "npm run dev"

    echo.
    echo ==========================================
    echo NITRO SYSTEM DEPLOYED SUCCESSFULLY MINA SAMIR
    echo ==========================================
    echo Backend: http://localhost:8000
    echo Frontend: http://localhost:5173
    echo FlareSolverr: http://localhost:8191
    echo ==========================================
    echo.
    pause
