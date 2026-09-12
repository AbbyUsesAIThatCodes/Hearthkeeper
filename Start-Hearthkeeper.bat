@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto use_python
py -3 -m hearthkeeper demo --open
goto result
:use_python
where python >nul 2>nul
if errorlevel 1 goto missing_python
python -m hearthkeeper demo --open
:result
if errorlevel 1 goto failed
echo.
echo The fictional archive is ready. Its location is printed above.
pause
exit /b 0
:missing_python
echo Python 3.11 or newer is required. See README.md for setup.
pause
exit /b 1
:failed
echo.
echo The demo could not finish. Read the error above and see README.md.
pause
exit /b 1
