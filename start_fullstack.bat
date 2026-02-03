@echo off
echo ==========================================
echo Wolfee Analytics - Full Stack Launcher
echo ==========================================
echo.

:: Start Backend
echo [1/2] Starting Backend Server on port 8000...
cd backend
start "Wolfee Backend" python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
cd ..

:: Wait for backend
timeout /t 3 /nobreak >nul

:: Start Frontend Server on port 8080
echo [2/2] Starting Frontend Server on port 8080...
cd frontend
start "Wolfee Frontend" python -m http.server 8080
cd ..

timeout /t 2 /nobreak >nul

:: Open Browser
echo.
echo Opening browser...
start "" "http://127.0.0.1:8080"

echo.
echo ==========================================
echo ✓ Success! 
echo Backend: http://127.0.0.1:8000
echo Frontend: http://127.0.0.1:8080
echo.
echo Keep both terminal windows open!
echo ==========================================
pause
