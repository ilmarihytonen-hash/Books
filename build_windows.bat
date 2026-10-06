@echo off
setlocal
cd /d "%~dp0"

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

echo Build complete: dist\Bookapp.exe
endlocal
