@echo off
setlocal
cd /d "%~dp0"

if exist "Bookapp.exe" (
    start "" "Bookapp.exe"
    exit /b 0
)

if exist "dist\Bookapp.exe" (
    start "" "dist\Bookapp.exe"
    exit /b 0
)

echo Bookapp.exe was not built yet. The build script will download and install dependencies.
choice /C YN /N /M "Run the install and build script now? [Y/N] "
if errorlevel 2 exit /b 0

call "build_windows.bat"
if errorlevel 1 exit /b 1

if exist "dist\Bookapp.exe" (
    start "" "dist\Bookapp.exe"
    exit /b 0
)

echo Build completed, but dist\Bookapp.exe was not found.
exit /b 1
