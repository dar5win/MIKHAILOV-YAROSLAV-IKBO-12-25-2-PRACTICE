@echo off
setlocal
cd /d "%~dp0"
if defined PYTHON_EXE goto configured
set "PYTHON_EXE=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%PYTHON_EXE%" goto configured
set "PYTHON_EXE=python"
:configured
"%PYTHON_EXE%" %*
set "_run_result=%errorlevel%"
if not "%_run_result%"=="0" pause
exit /b %_run_result%
