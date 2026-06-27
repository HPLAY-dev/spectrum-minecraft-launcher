@echo off
REM Spectrum Launcher — Nuitka + Makefile
REM   make.bat help
REM   make.bat all 1.0.0

if /i "%~1"=="__fallback__" goto batch_entry
if "%~1"=="" goto help

where mingw32-make >nul 2>&1
if not errorlevel 1 (
    mingw32-make %*
    exit /b %ERRORLEVEL%
)

where make.exe >nul 2>&1
if not errorlevel 1 (
    make.exe %*
    exit /b %ERRORLEVEL%
)

call "%~f0" __fallback__ %*
exit /b %ERRORLEVEL%

:batch_entry
setlocal EnableDelayedExpansion
shift
set "TARGET=%~1"
if /i "%TARGET%"=="help" goto help
if /i "%TARGET%"=="clean" goto clean
if /i "%TARGET%"=="rust" goto rust
if /i "%TARGET%"=="ui" goto ui
if /i "%TARGET%"=="nuitka" goto nuitka
if /i "%TARGET%"=="dist" goto dist
if /i "%TARGET%"=="archive" goto archive
if /i "%TARGET%"=="all" goto all
echo Unknown target: %TARGET%
exit /b 1

:parse_version
set "VERSION=1.0.0"
if not "%~2"=="" set "VERSION=%~2"
echo !VERSION! | findstr /r "^VERSION=" >nul && set "VERSION=!VERSION:VERSION==!"
exit /b 0

:rust
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0cargo_build.ps1"
exit /b %ERRORLEVEL%

:ui
python make_tools.py uic -o ui.py qt.ui
exit /b %ERRORLEVEL%

:nuitka
call :parse_version %*
call :rust
if errorlevel 1 exit /b 1
call :ui
if errorlevel 1 exit /b 1
echo [make] Nuitka VERSION=!VERSION!
set "NUITKA_PYD="
if exist python\spectrum_core\_spectrum_core.pyd (
    set "NUITKA_PYD=--include-data-files=python/spectrum_core/_spectrum_core.pyd=python/spectrum_core/_spectrum_core.pyd"
)
set "PYTHONPATH=%CD%\python;%PYTHONPATH%"
python make_tools.py nuitka --mingw64 --standalone --jobs=16 --enable-plugin=pyside6 ^
    --include-package=spectrum_core ^
    --include-package=modrinth_api_wrapper ^
    --include-data-dir=./assets=assets ^
    --include-data-dir=./languages=languages ^
    !NUITKA_PYD! ^
    --assume-yes-for-downloads ^
    --output-dir=build ^
    --show-progress ^
    --windows-console-mode=disable ^
    --windows-file-version=!VERSION! ^
    --windows-product-version=!VERSION! ^
    --windows-file-description=Spectrum Minecraft Launcher ^
    main.py
exit /b %ERRORLEVEL%

:dist
call :parse_version %*
if not exist build\main.dist (
    echo [make] build\main.dist not found — run: make.bat nuitka !VERSION!
    exit /b 1
)
if not exist builds mkdir builds
if exist builds\nuitka-!VERSION! rmdir /s /q builds\nuitka-!VERSION!
mkdir builds\nuitka-!VERSION!
xcopy /E /I /Q build\main.dist builds\nuitka-!VERSION!
xcopy /E /I /Q assets builds\nuitka-!VERSION!\assets
xcopy /E /I /Q languages builds\nuitka-!VERSION!\languages
if exist python\spectrum_core\_spectrum_core.pyd (
    if not exist builds\nuitka-!VERSION!\python\spectrum_core mkdir builds\nuitka-!VERSION!\python\spectrum_core
    copy /Y python\spectrum_core\_spectrum_core.pyd builds\nuitka-!VERSION!\python\spectrum_core\
)
echo [make] dist -^> builds\nuitka-!VERSION!
exit /b 0

:archive
call :dist %*
if errorlevel 1 exit /b 1
call :parse_version %*
7z a -mx0 builds\nuitka-!VERSION!-windows.7z builds\nuitka-!VERSION!
exit /b %ERRORLEVEL%

:all
call :archive %*
exit /b %ERRORLEVEL%

:clean
if exist build rmdir /s /q build
echo [make] cleaned build/
exit /b 0

:help
echo Spectrum Launcher — Nuitka build
echo.
echo   make.bat help
echo   make.bat clean
echo   make.bat rust
echo   make.bat ui
echo   make.bat nuitka [VERSION]
echo   make.bat dist [VERSION]
echo   make.bat archive [VERSION]
echo   make.bat all [VERSION]
echo.
echo Requires: Python 3.12+, Nuitka, MinGW64, PySide6, 7z
echo With GNU Make: make.bat all VERSION=1.0.0
exit /b 0
