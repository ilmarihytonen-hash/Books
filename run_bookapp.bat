@echo off
setlocal
cd /d "%~dp0"

if exist "dist\Bookapp.exe" (
    start "" "dist\Bookapp.exe"
    exit /b 0
)

echo Bookapp.exe was not built yet. Run build_windows.bat first.
exit /b 1
