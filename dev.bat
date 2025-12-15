@echo off
REM Windows batch file to run dev.sh
REM Usage: dev.bat

echo 🚀 Starting AG-UI Development Server...
echo.
echo 📝 Fixing line endings...
wsl bash -c "perl -pi -e 's/\r\n/\n/g' /mnt/c/temp/AI/AGUI/agui/src/dev.sh && chmod +x /mnt/c/temp/AI/AGUI/agui/src/dev.sh"

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to fix line endings
    exit /b 1
)

echo ✅ Line endings fixed
echo.
echo Starting services...
echo   📱 Frontend: http://localhost:5173
echo   🔌 Runtime:  http://localhost:3001
echo   🐍 Backend:  http://localhost:8888
echo.
echo Press Ctrl+C to stop all services
echo.

wsl bash -c "cd /mnt/c/temp/AI/AGUI/agui/src && ./dev.sh"
