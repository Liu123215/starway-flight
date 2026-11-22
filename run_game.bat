@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
    python -B "%~dp0main.py"
) else (
    py -3 -B "%~dp0main.py"
)
if errorlevel 1 (
    echo.
    echo Starway Flight needs Python 3.10 or newer with Tcl/Tk support.
    pause
)
