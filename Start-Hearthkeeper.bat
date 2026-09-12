@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto use_python
py -3 bootstrap_desktop.py
goto result
:use_python
where python >nul 2>nul
if errorlevel 1 goto missing_python
python bootstrap_desktop.py
:result
if errorlevel 1 goto failed
exit /b 0
:missing_python
echo Python 3.11 through 3.13 is required for the source launcher. See README.md.
pause
exit /b 1
:failed
echo.
echo The desktop could not launch. Read the error above and see README.md.
pause
exit /b 1
