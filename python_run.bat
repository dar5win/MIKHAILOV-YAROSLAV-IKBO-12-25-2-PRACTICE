@echo off
setlocal
cd /d "%~dp0"
if defined PYTHON_EXE goto configured
set "PYTHON_EXE=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%PYTHON_EXE%" goto configured
set "PYTHON_EXE=python"
:configured
"%PYTHON_EXE%" %*
if errorlevel 1 pause
