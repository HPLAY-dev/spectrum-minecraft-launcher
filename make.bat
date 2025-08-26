set PROJECT=main
set PYINSTALLER=C:\Users\magic\Documents\Programs\python310\Scripts\pyinstaller.exe
set 7ZFILENAMEPREFIX=build
set 7ZFILENAMESUFFIX=py310-x86_64
set /p VERSION=Version: 

:Environment
if exist .\build rd /s /q .\build
if not exist .\builds mkdir builds
if not exist .\builds\build-%VERSION% mkdir .\builds\build-%VERSION%
mkdir build

:BUILD
cd build
%pyinstaller% --noconfirm --onedir --windowed .\..\%PROJECT%.py
xcopy .\dist .\..\builds\build /I /Q

:ARCHIVE
7z a -mx0 ".\..\builds\%7zFilenamePrefix%-%Version%-%7zFilenameSuffix%.7z" ".\..\builds\build\*"

cd ..