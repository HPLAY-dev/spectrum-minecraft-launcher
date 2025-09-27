if "%1"=="clean" goto clean

set PROJECT=main
set PYINSTALLER=pyinstaller
set PREFIX=build
set SUFFIX=python-x86_64
set /p VERSION=Version: 

:Environment
if exist .\build rd /s /q .\build
if not exist .\builds mkdir builds
if not exist .\builds\build-%VERSION% mkdir .\builds\build-%VERSION%
mkdir build

:BUILD
cd build
rem %pyinstaller% --noconfirm --onedir --windowed .\..\%PROJECT%.py
%pyinstaller% --noconfirm --onedir .\..\%PROJECT%.py
xcopy .\dist\%PROJECT% .\..\builds\build-%Version% /E /I /Q
mkdir .\..\builds\build-%Version%\assets
xcopy .\..\assets .\..\builds\build-%Version%\assets /E /I /Q

:ARCHIVE
7z a -mx0 .\..\builds\%Prefix%-%Version%-%Suffix%.7z .\..\builds\build-%Version%\*

cd ..
goto EOF

:clean
rd /s /q .\build
goto EOF

:EOF