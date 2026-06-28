@echo off
echo ========================================
echo   MRI AI Tumor Detection System
echo   Starting All Services...
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Starting Backend (port 8000)...
start "Backend Server" cmd /k "cd /d "%~dp0backend" && call ..\.venv\Scripts\Activate && uvicorn app.main:app --reload --port 8000"

timeout /t 3 /nobreak >nul

echo [2/3] Starting Frontend (port 5173)...
start "Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

timeout /t 3 /nobreak >nul

echo [3/3] Starting AI Service (port 8001)...
start "AI Service" cmd /k "cd /d "%~dp0ai" && call ..\.venv\Scripts\Activate && python service.py"

echo.
echo ========================================
echo   All Services Started!
echo ========================================
echo.
echo   Backend:   http://localhost:8000
echo   Frontend:  http://localhost:5173
echo   AI Service: http://localhost:8001
echo.
echo   Press any key to exit this window...
pause >nul