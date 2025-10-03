@echo off

:: Check what to do
if "%1"=="clean" goto clean
if "%1"=="build" goto BUILD_ADD
if "%1"=="7z" goto ARCHIVE
goto HELP

:BUILD_ALL
	:Environment
	echo [make] Setting up environment
	set PROJECT=main
	set PYINSTALLER=pyinstaller
	set PREFIX=build
	set SUFFIX=python-x86_64
	set 7z=7z
	set /p VERSION=Version: 
	
	:CLEAN
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

	cd ..
	goto EOF
	
	
:ARCHIVE
	%7z% a -mx0 .\..\builds\%Prefix%-%Version%-%Suffix%.7z .\..\builds\build-%Version%\*

:clean
	rd /s /q .\build
	goto EOF

:HELP
	echo Make batfile for spectrum launcher
	echo generates binaries from pyinstaller and move it to ./builds/build-VERSION
	echo.
	echo     Usage: ./make clean  - Clean build folder
	echo     Usage: ./make build  - Build via PyInstaller
	echo     Usage: ./make 7z     - Create 7z archive for distributing (7z needed)
	echo     Usage: ./make help   - Display this infomation
	echo.
	echo to specify binaries path, edit this batch file.
	goto EOF
:EOF