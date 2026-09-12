@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto use_python
py -3 -m hearthkeeper demo --open
goto result
:use_python
python -m hearthkeeper demo --open
:result
pause
