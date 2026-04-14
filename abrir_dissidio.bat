@echo off
set SCRIPT_DIR=%~dp0
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%abrir_dissidio.ps1"
if errorlevel 1 (
    echo.
    echo O app nao conseguiu abrir. Veja a mensagem acima.
    pause
)
