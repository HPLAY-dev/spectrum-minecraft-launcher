
set PROJECT=tkui

if "%1"=="postonly" goto postonly
if exist build goto build
:MakeBuildDir
    mkdir build
:build
    cd build
    :DetectIfPyinstallerExists
        pyinstaller > nul
        if %ERRORLEVEL% == 9009 goto PyInstallerNotFound
    :DetectIf7zExists
        pyinstaller > nul
        if %ERRORLEVEL% == 9009 goto 7zNotFound
    :PyInstaller
    rem Execute Pyinstaller Scripts
        pyinstaller --noconfirm --onedir --windowed .\..\%PROJECT%.py
    goto post
    :postonly
    rem Post-only script
        cd build
    :post
    rem Copy Files and Remove Directories
        mkdir .\builds\build
        mkdir .\builds\build\_internal
        xcopy .\dist\%PROJECT%\ .\..\builds\build /E
        rd /s /q .\dist
        rd /s /q .\build
        mkdir .\..\builds\build\unzip
        xcopy .\..\unzip\*.* .\..\builds\build\unzip
        copy .\..\JavaWrapper.jar .\..\builds\build
    :7z
    rem 7zip to distribution
        7z a -mx0 ".\..\builds\build.7z" ".\..\builds\build\*"
    :src
    rem create src archive
        mkdir src
        copy .\..\%PROJECT%.py .\src
        copy .\..\mclauncher_core.py .\src
        copy .\..\make.bat .\src
    :src7z
        7z a -mx0 ".\..\builds\src.7z" ".\src\*"
    cd ..
    echo MAKE finish
    goto EOF
:PyInstallerNotFound
echo Cannot find pyinstaller
:7zNotFound
echo Cannot find pyinstaller
:EOF