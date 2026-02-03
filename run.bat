@echo off
echo ==========================================
echo BIST Analytics - Launcher
echo ==========================================

echo [1/3] Checking dependencies...
python -m pip install -r backend/requirements.txt >nul 2>&1

echo [2/3] Starting Backend Server...
cd backend
start "BIST Backend" python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
cd ..

echo [3/3] Opening Dashboard...
timeout /t 2 >nul
start "" "frontend\index.html"

echo.
echo ==========================================
echo Success! 
echo 1. The black window is the Server (Keep it open).
echo 2. The website should be open in your browser.
echo ==========================================
pause
