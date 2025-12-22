@echo off
title MEIH Streaming Platform
echo ========================================
echo   MEIH Streaming Platform
echo   بدء تشغيل الموقع...
echo ========================================
echo.

REM Start Backend Server
echo [1/2] بدء تشغيل Backend Server...
cd /d "%~dp0backend"
start "Backend Server" cmd /k "call venv\Scripts\activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM Wait for backend to start
echo ⏳ انتظار تشغيل Backend Server...
timeout /t 5 /nobreak > nul

REM Start Frontend Server
echo [2/2] بدء تشغيل Frontend Server...
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
