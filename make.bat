@echo off

:Environment
echo [make] Setting up environment
set PROJECT=main
set PYINSTALLER=pyinstaller
set Prefix=build
set Suffix=python-x86_64
set seven_zip=7z

:: Check what to do
if "%1"=="clean" goto clean
if "%1"=="build" goto BUILD_ALL
if "%1"=="7z" goto ARCHIVE_ALL
goto HELP

:BUILD_ALL
	
	:CLEAN
	if exist .\build rd /s /q .\build
	if not exist .\builds mkdir builds
	if not exist .\builds\build-%VERSION% mkdir .\builds\build-%VERSION%
	mkdir build
	goto EOF

	:BUILD
	set /p VERSION=Version: 
	cd build
	%pyinstaller% --noconfirm --onedir .\..\%PROJECT%.py
	xcopy .\dist\%PROJECT% .\..\builds\build-%Version% /E /I /Q
	mkdir .\..\builds\build-%Version%\assets
	xcopy .\..\assets .\..\builds\build-%Version%\assets /E /I /Q

	cd ..
	goto EOF
	
	
:ARCHIVE_ALL
	if defined VERSION goto archive
		set /p VERSION=Version: 
	:archive
	echo %seven_zip% a -mx0 .\builds\%Prefix%-%Version%-%Suffix%.7z .\builds\build-%Version%\*
	%seven_zip% a -mx0 .\builds\%Prefix%-%Version%-%Suffix%.7z .\builds\build-%Version%\*
	goto EOF

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
echo [make] cleaning environment
set PROJECT=
set PYINSTALLER=
set Prefix=
set Suffix=
set seven_zip=