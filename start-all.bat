@echo off
title MEIH Streaming Platform
echo ========================================
echo   MEIH Streaming Platform
echo   بدء تشغيل الموقع...
echo ========================================
echo.

REM Start Stealth Proxy
echo [1/3] بدء تشغيل Stealth Proxy...
cd /d "%~dp0backend\proxy-service"
start "Stealth Proxy" cmd /k "node server.js"

REM Start Backend Server
echo [2/3] بدء تشغيل Backend Server...
cd /d "%~dp0backend"
start "Backend Server" cmd /k "call venv\Scripts\activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM Wait for backend and proxy to start
echo ⏳ انتظار تشغيل الخدمات...
timeout /t 5 /nobreak > nul

REM Start Frontend Server
echo [3/3] بدء تشغيل Frontend Server...
cd /d "%~dp0meih-netflix-clone"
start "Frontend Server" cmd /k "npm run dev"

echo.
echo ✅ تم تشغيل الموقع بنجاح!
echo.
echo 🌐 الروابط:
echo    - Frontend: http://localhost:5173
echo    - Backend:  http://localhost:8000
echo.
echo ℹ️  ملاحظة: سيتم فتح نافذتين منفصلتين
echo    يمكنك إغلاق هذه النافذة الآن.
echo.
pause
