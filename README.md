# Spectrum Minecraft Launcher
An open-source lightweight Minecraft Launcher in Python3.

## 2.0 ModLoader Support
Fabric is currently supported. Forge & Neoforge is currently partly working, see 4.0

## 3.0 Multi-Language
Only zh_CN is supported.

## 4.0 Problems
- 1.0 *and other ancient versions too* is unable to load assets.
- Cannot install forge when a `url` string is blank.
- Login via Microsoft is currently not working(403).

## 5.0 What can we do
- [x] Launch any version of Minecraft Java Edition
- [x] Fabric ModLoader
- [ ] Forge ModLoader (50%)
- [ ] Neoforge ModLoader (50%)
- [x] Version file managing
- [x] Download Mods on Modrinth

......

## 6.0 Developing & Contributing
### 6.1 Requirements
- Python 3.x (3.13 used by us)
- A environment for developing Qt 5 GUI
- A Browser for developing OAuth Login (Alternatively, you can open the link in your browser without the webbrowser.)

To make all parts of this application work, you need to install the following packages.

- PyQt6
- Qt Creator
- requests
```
pip install PyQt6 PyQt6-Tools requests modrinth_api_wrapper
```
### 6.2 UI Modification 
Run `./buildui.bat`(Windows only) to build the ui. (On *nix OSes, run `pyuic6 -o .\ui.py .\qt.ui`)
