@echo off
setlocal
cd /d "%~dp0"

set "ISCC=ISCC.exe"
where ISCC.exe >nul 2>&1
if errorlevel 1 (
    set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
    if not exist "%ISCC%" (
        echo Inno Setup is required to build the installer.
        echo Install it from https://jrsoftware.org/isinfo.php, then run this script again.
        exit /b 1
    )
)

py -m pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install Python dependencies.
    exit /b 1
)

py -m PyInstaller --clean --noconfirm --onefile --windowed ^
    --name Bookapp ^
    --add-data "urls.yaml;." ^
    --add-data "config.json;." ^
    --add-data "languages\en.json;languages" ^
    --add-data "languages\fi.json;languages" ^
    --add-data "languages\sv.json;languages" ^
    launcher.py
if errorlevel 1 (
    echo Build failed. See the error output above.
    exit /b 1
)

copy /Y config.json dist\config.json >nul
if errorlevel 1 (
    echo Failed to copy config.json beside the executable.
    exit /b 1
)

copy /Y urls.yaml dist\urls.yaml >nul
if errorlevel 1 (
    echo Failed to copy urls.yaml beside the executable.
    exit /b 1
)

"%ISCC%" setup.iss
if errorlevel 1 (
    echo Installer build failed. See the error output above.
    exit /b 1
)

echo Build complete: dist\Bookapp-Setup.exe
endlocal
