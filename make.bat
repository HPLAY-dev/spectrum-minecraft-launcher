set PROJECT=main
set PYINSTALLER=C:\Users\magic\Documents\Programs\python310\Scripts\pyinstaller.exe

:Environment
if exist .\build rd /s /q .\build
if not exist .\builds mkdir builds
if not exist .\builds\build mkdir .\builds\build
mkdir build

:BUILD
cd build
%pyinstaller% --noconfirm --onedir --windowed .\..\%PROJECT%.py
xcopy .\dist .\..\builds\build /I /Q

:ARCHIVE
7z a -mx0 ".\..\builds\latest.7z" ".\..\builds\build\*"

cd ..