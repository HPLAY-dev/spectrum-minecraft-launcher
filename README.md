# Spectrum Minecraft Launcher
An open-source lightweight Minecraft Launcher in Python3.

## 2.0 ModLoader Support
Fabric, Neoforge and Forge is currently supported.

## 3.0 Multi-Language
zh_CN & en_US.

## 4.0 Problems
- 1.0 *and other ancient versions too* is unable to load assets.

## 5.0 What can we do
- [x] Launch any version of Minecraft Java Edition
- [x] Microsoft Login
- [x] Fabric ModLoader
- [x] Forge ModLoader
- [x] Neoforge ModLoader
- [x] Version file managing
- [x] Download Mods on Modrinth
- [x] BMCLAPI mirror
- [x] Everything you need (mostly)

......

## 6.0 Developing & Contributing
### 6.1 Requirements
- Python>=3.12 (3.14 used by developing)(3.12 for compiling via mingw64)
- A environment for developing Qt 6 GUI (Linux only)
- A Browser for developing OAuth Login (Alternatively, you can open the link in your browser.)

To make all parts of this application work, you need to install the following packages.

- PyQt6
- modrinth_api_wrapper
- requests
```
pip install PyQt6 PyQt6-Tools requests modrinth_api_wrapper
```
### 6.2 UI Modification 
Run `pyside6-designer qt.ui` to modify UI.
Run `./buildui.bat`(Windows only) to build the ui.
