@echo off
setlocal

set "GIT_BASH=%ProgramFiles%\Git\bin\bash.exe"
if exist "%GIT_BASH%" (
  "%GIT_BASH%" "%~dp0auto-commit.sh"
  exit /b %ERRORLEVEL%
)

bash "%~dp0auto-commit.sh"
