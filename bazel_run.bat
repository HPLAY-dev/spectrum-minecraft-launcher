@echo off
REM Build entire project and launch from bazel-bin/launcher
REM Requires: Bazel/Bazelisk, Python 3.12+, Rust (cargo)

setlocal
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build.ps1"
if errorlevel 1 goto :fail

echo [run] Starting Spectrum Launcher (bazel-bin/launcher)...
set SPECTRUM_USE_RUST=1
cd /d "%~dp0bazel-bin\launcher"
set PYTHONPATH=%CD%\python;%PYTHONPATH%
python main.py %*
goto :eof

:fail
echo Build failed
exit /b 1
