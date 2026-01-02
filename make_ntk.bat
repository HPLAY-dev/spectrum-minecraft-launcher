@echo off

REM this is a build script for Spectrum Launcher using Nuitka.
REM Usage: make_ntk.bat [clean|dist]
REM 

set nuitka=.\.venv\Scripts\nuitka


REM .\.venv\Scripts\activate

set /p VERSION=V: 
if '%1'=='clean' goto clean
if '%1'=='dist' goto dist
goto make

:clean
    if exist .\build rd /s /q .\build
    goto EOF

:make
    echo Starting Nuitka
    %nuitka% --mingw64 ^
             --standalone ^
             --enable-plugin=pyside6 ^
             --assume-yes-for-downloads ^
             --output-dir=build ^
             --show-progress ^
             main.py
    goto EOF
:dist
    echo Copying Files
    mkdir .\..\builds\build-%Version%
    mkdir .\..\builds\build-%Version%\assets
    xcopy .\build\main.dist .\builds\nuitka-%VERSION% /E /I /Q
    xcopy .\assets .\builds\nuitka-%VERSION%\assets /E /I /Q
    xcopy .\languages .\builds\nuitka-%VERSION%\languages /E /I /Q
    echo Creating Archive
    7z a -mx0 .\builds\nuitka-%VERSION%-windows.7z .\builds\nuitka-%VERSION%
    goto EOF

:EOF