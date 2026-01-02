@echo off

set nuitka=nuitka

if '%1' neq '' goto CHECKARG 

:HELP
    echo this is a build script for Spectrum Launcher using Nuitka.
    echo Usage: .\make_ntk.bat [clean^|dist^|make]
    echo.
    goto EOF

:CHECKARG
    if '%1'=='clean' goto clean
    set /p VERSION=V: 
    if '%1'=='make' goto make
    if '%1'=='dist' goto dist

:clean
    if exist .\build rd /s /q .\build
    goto EOF

:make
    if exist .\upx set upx=.\upx
    
    echo Starting Nuitka
    %nuitka% --mingw64 ^
             --standalone ^
             --jobs=16 ^
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