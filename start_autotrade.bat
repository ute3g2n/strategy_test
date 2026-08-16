@echo off
setlocal EnableExtensions

rem Double-click entry point for the local AutoTrade app.
rem Delegate the actual startup work to PowerShell in this repository.
set "PROJECT_ROOT=%~dp0"

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%scripts\start_autotrade.ps1" %*
set "EXIT_CODE=%ERRORLEVEL%"

endlocal & exit /b %EXIT_CODE%
