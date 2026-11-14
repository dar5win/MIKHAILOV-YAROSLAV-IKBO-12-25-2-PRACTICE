@echo off
cd /d "%~dp0"
call python_run.bat -m unittest discover -s tests -v
pause
