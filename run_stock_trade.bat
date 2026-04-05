@echo off
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo Starting Stock Trade Application...
echo.

:: Start the Django server in the background
start /b cmd /c "stock_venv_01\Scripts\python.exe manage.py runserver"

:: Wait for a few seconds for the server to start
timeout /t 5 /nobreak > nul

:: Open the browser to the application
start http://127.0.0.1:8000/

echo.
echo The application is now running.
echo To close the application, close this window and then stop the server in the background.
echo (Or just close the terminal window that opened).
pause
