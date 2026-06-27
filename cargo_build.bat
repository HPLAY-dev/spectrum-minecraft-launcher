@echo off
setlocal
cd /d "%~dp0\spectrum-core"

set PYO3_PYTHON=python
cargo build --release --features python
if errorlevel 1 exit /b 1

set OUT=target\release
if exist "%OUT%\spectrum_core.dll" (
    copy /Y "%OUT%\spectrum_core.dll" "..\python\spectrum_core\_spectrum_core.pyd"
    echo Copied to python\spectrum_core\_spectrum_core.pyd
    goto :done
)
if exist "%OUT%\_spectrum_core.dll" (
    copy /Y "%OUT%\_spectrum_core.dll" "..\python\spectrum_core\_spectrum_core.pyd"
    echo Copied to python\spectrum_core\_spectrum_core.pyd
    goto :done
)
if exist "%OUT%\_spectrum_core.pyd" (
    copy /Y "%OUT%\_spectrum_core.pyd" "..\python\spectrum_core\_spectrum_core.pyd"
    echo Copied to python\spectrum_core\_spectrum_core.pyd
    goto :done
)

echo Build output not found in %OUT%
exit /b 1

:done
echo Done. Run: python main.py
endlocal
