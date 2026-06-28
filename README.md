# Spectrum Minecraft Launcher

An open-source lightweight Minecraft Launcher written in Python3.

## ModLoader Support
Fabric, Neoforge, and Forge are currently supported.

## Multi-Language
zh_CN & en_US are available. You can add your own language by creating a file named `LANG.json` (where LANG is the language string) in the `languages/` directory.

## Known Issues
- *Ancient versions* are unable to load assets.

## Features
- [x] Launch any version of Minecraft Java Edition
- [x] Microsoft Login (OAuth)
- [x] Fabric ModLoader
- [x] Forge ModLoader
- [x] Neoforge ModLoader
- [x] Version file management
- [x] Download Mods from Modrinth
- [x] BMCLAPI Mirror support
- [x] Account Management
- [x] Cross Platform
......

## Developing & Contributing

### Requirements
- Python >= 3.12 (3.14 used for development; 3.12 for compiling via mingw64 + Nuitka)

To make all parts of this application work, you need to install the following packages:
- PySide6
- modrinth_api_wrapper
- requests
- nuitka (for release builds; Nuitka 4.x uses `python -m nuitka`)

```
pip install PySide6 requests modrinth_api_wrapper nuitka
```

### Run from source
```powershell
pip install PySide6 requests modrinth_api_wrapper
pip install PySide6-WebEngine   # For Modrinth search page (optional)
python main.py
```

`main_qml.py` is an alias compatible with `main.py`.

The main program has switched to `spectrum_core` (Rust core + Python bridge). Set `SPECTRUM_USE_RUST=0` to fall back to the pure Python implementation (`python/spectrum_core/py_fallback/`).

### Rust Core (recommended for compilation)
```powershell
.\cargo_build.ps1
```
Output: `python/spectrum_core/_spectrum_core.pyd`

### Release build — Nuitka + Makefile + make.bat
Recommended for Windows (MinGW64 + Nuitka):
```bat
make.bat all 1.0.0
```
Or step by step:
```bat
make.bat clean
make.bat nuitka 1.0.0
make.bat dist 1.0.0
make.bat archive 1.0.0
```

If GNU Make is installed, `make.bat` will delegate to `Makefile`:
```bat
make.bat all VERSION=1.0.0
```

Output directory: `builds/nuitka-<VERSION>/`  
Archive: `builds/nuitka-<VERSION>-windows.7z`

### UI Modification
Run `pyside6-designer qt.ui` to modify the UI.  
Run `./buildui.bat` (Windows only) to build the UI.