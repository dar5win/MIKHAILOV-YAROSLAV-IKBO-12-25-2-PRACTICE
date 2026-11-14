@echo off
cd /d "%~dp0"
call python_run.bat main.py --test --repository data/branch.json --package A --version 1.0.0 --max-depth 3 --png output/graph.png
if errorlevel 1 exit /b 1
start "" "output\graph.png"
pause
