# Spectrum Minecraft Launcher
An open-source lightweight Minecraft Launcher in Python3.

## ModLoader Support
Fabric, Neoforge and Forge is currently supported.

## Multi-Language
zh_CN & en_US. You can add your language by creating a file named `LANG.json`(LANG=language string) in `languages/`.

## Problems
- *Ancient versions* are unable to load assets.

## What can we do
- [x] Launch any version of Minecraft Java Edition
- [x] Microsoft Login (OAuth)
- [x] Fabric ModLoader
- [x] Forge ModLoader
- [x] Neoforge ModLoader
- [x] Version file managing
- [x] Download Mods on Modrinth
- [x] BMCLAPI Mirror
- [x] Account Management
- [x] Cross Platform

......

## Developing & Contributing
### Requirements
- Python>=3.12 (3.14 used by developing)(3.12 for compiling via mingw64+nuitka)

To make all parts of this application work, you need to install the following packages.

- PySide6
- modrinth_api_wrapper
- requests
```
pip install PySide6 requests modrinth_api_wrapper
```
### UI Modification 
Run `pyside6-designer qt.ui` to modify UI.
Run `./buildui.bat`(Windows only) to build the ui.
