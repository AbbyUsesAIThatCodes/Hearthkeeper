@echo off
setlocal
cd /d "%~dp0"
echo This opens the ORIGINAL BROWSER archive demo.
echo For the native desktop app, use Start-Hearthkeeper.bat or the packaged Hearthkeeper.exe.
where py >nul 2>nul
if errorlevel 1 goto use_python
py -3 -m hearthkeeper demo --open
goto result
:use_python
python -m hearthkeeper demo --open
:result
pause
