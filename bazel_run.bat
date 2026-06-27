@echo off
REM Build entire project and launch
REM Requires: Bazel/Bazelisk, Python 3.12+, Rust (cargo), MSVC Build Tools

setlocal
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build.ps1"
if errorlevel 1 goto :fail

echo [run] Starting Spectrum Launcher...
set SPECTRUM_USE_RUST=1
set PYTHONPATH=%CD%\python;%PYTHONPATH%
python main.py %*
goto :eof

:fail
echo Build failed
exit /b 1
