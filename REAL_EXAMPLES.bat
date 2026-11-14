@echo off
cd /d "%~dp0"
call python_run.bat main.py --package Serilog --version 3.1.1 --max-depth 2 --output output/Serilog.dot --png output/Serilog.png
if errorlevel 1 exit /b 1
start "" "output\Serilog.png"
call python_run.bat main.py --package Humanizer.Core --version 2.14.1 --max-depth 2 --output output/Humanizer.dot --png output/Humanizer.png
if errorlevel 1 exit /b 1
start "" "output\Humanizer.png"
call python_run.bat main.py --package Microsoft.Extensions.Logging --version 8.0.0 --max-depth 2 --output output/Logging.dot --png output/Logging.png
if errorlevel 1 exit /b 1
start "" "output\Logging.png"
pause
