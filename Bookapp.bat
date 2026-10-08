@echo off
setlocal
set "BOOKAPP_SHORTCUT=%~dp0Bookapp.lnk"
set "BOOKAPP_LAUNCHER=%~f0"
powershell -NoProfile -Command "$shell = New-Object -ComObject WScript.Shell; $shortcut = $shell.CreateShortcut($env:BOOKAPP_SHORTCUT); $shortcut.TargetPath = $env:BOOKAPP_LAUNCHER; $shortcut.WorkingDirectory = Split-Path -Parent $env:BOOKAPP_LAUNCHER; $shortcut.Description = 'Start Bookapp'; $shortcut.Save()"
if errorlevel 1 echo Warning: Could not create or update Bookapp.lnk.
set "BOOKAPP_SHORTCUT="
set "BOOKAPP_LAUNCHER="
call "%~dp0run_bookapp.bat"
exit /b %errorlevel%
