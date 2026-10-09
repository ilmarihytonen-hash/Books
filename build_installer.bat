@echo off
setlocal
cd /d "%~dp0"

if not exist "dist\Bookapp.exe" (
    call "build_windows.bat"
    if errorlevel 1 exit /b 1
)

set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
    echo Inno Setup 6 was not found. Install it from https://jrsoftware.org/isdl.php
    exit /b 1
)

"%ISCC%" /DMyAppVersion=0.2.0-beta.1 "Bookapp.iss"
if errorlevel 1 (
    echo Installer build failed. See the error output above.
    exit /b 1
)

echo Installer complete: dist\Bookapp-Setup.exe
endlocal
