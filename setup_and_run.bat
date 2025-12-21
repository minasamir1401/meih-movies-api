@echo off
echo Killing any existing Node/Python processes (optional, ignore errors)...
taskkill /F /IM node.exe /T 2>nul
taskkill /F /IM uvicorn.exe /T 2>nul
taskkill /F /IM python.exe /T 2>nul

echo Cleaning Vite Cache...
if exist meih-netflix-clone\node_modules\.vite rmdir /s /q meih-netflix-clone\node_modules\.vite

echo Setting up Backend...
if exist backend (
    cd backend
)
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt
start "FastAPI Backend" cmd /k "uvicorn main:app --reload --port 8000"

echo Setting up Frontend...
if exist ..\meih-netflix-clone (
    cd ..\meih-netflix-clone
) else if exist meih-netflix-clone (
    cd meih-netflix-clone
)
if not exist node_modules (
    call npm install
)
echo Starting Frontend...
start "React Frontend" cmd /k "npm run dev"

echo Done!
