@echo off
cd /d "%~dp0"
call python_run.bat main.py --package Serilog --version 3.1.1 --max-depth 2 --output output/Serilog.dot --html output/Serilog.html
call python_run.bat main.py --package Humanizer.Core --version 2.14.1 --max-depth 2 --output output/Humanizer.dot --html output/Humanizer.html
call python_run.bat main.py --package Microsoft.Extensions.Logging --version 8.0.0 --max-depth 2 --output output/Logging.dot --html output/Logging.html
pause
