@echo off
REM 使用 Bazel 构建 PyO3 扩展并运行启动器
REM 依赖: bazelisk 或 bazel, Python 3.12, MSVC (Windows)

setlocal

cd /d "%~dp0"

echo [1/3] Repin crate universe (若 Cargo.toml 已变更)...
set CARGO_BAZEL_REPIN=1
bazel run //:crates
if errorlevel 1 goto :fail

echo [2/3] 构建 Rust Python 扩展...
bazel build //python:spectrum_core
if errorlevel 1 goto :fail

echo [3/3] 启动 GUI (Rust 核心)...
set SPECTRUM_USE_RUST=1
set PYTHONPATH=%CD%\bazel-bin\python;%CD%\python;%PYTHONPATH%
python main.py %*
goto :eof

:fail
echo 构建失败
exit /b 1
