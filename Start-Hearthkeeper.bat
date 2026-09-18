@echo off
setlocal
cd /d "%~dp0"
set "HEARTHKEEPER_PY_VERSION="
set "PYLAUNCHER_ALLOW_INSTALL="
where py >nul 2>nul
if errorlevel 1 goto use_python
rem Select an installed, supported interpreter, even when the default is newer.
for %%V in (3.12 3.13 3.11) do call :try_py %%V
if not defined HEARTHKEEPER_PY_VERSION goto use_python
py %HEARTHKEEPER_PY_VERSION% bootstrap_desktop.py %*
goto result
:try_py
if defined HEARTHKEEPER_PY_VERSION exit /b 0
py -%1 -c "import sys; raise SystemExit(not ((3, 11) <= sys.version_info < (3, 14)))" >nul 2>nul
if not errorlevel 1 set "HEARTHKEEPER_PY_VERSION=-%1"
exit /b 0
:use_python
where python >nul 2>nul
if errorlevel 1 goto missing_python
python -c "import sys; raise SystemExit(not ((3, 11) <= sys.version_info < (3, 14)))" >nul 2>nul
if errorlevel 1 goto missing_python
python bootstrap_desktop.py %*
:result
if errorlevel 1 goto failed
exit /b 0
:missing_python
echo No supported Python installation was found for the SOURCE launcher.
echo Hearthkeeper's desktop toolkit needs Python 3.11, 3.12, or 3.13.
echo.
echo The packaged Windows app needs NO Python:
echo   Run Download-Windows-Preview.bat to open the current release.
echo   Download Hearthkeeper-0.1.0a8-Windows.zip under Assets.
echo   Extract ALL files, and run Hearthkeeper.exe with _internal beside it.
echo.
echo To run from source, install a supported Python alongside your existing version.
echo You do not need to uninstall Python or change your system default.
if /i "%~1"=="--check-python" exit /b 1
pause
exit /b 1
:failed
echo.
echo The desktop could not launch. Read the error above and see README.md.
if /i "%~1"=="--check-python" exit /b 1
pause
exit /b 1
