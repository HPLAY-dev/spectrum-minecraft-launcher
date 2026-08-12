# Spectrum Minecraft Launcher

An open-source, lightweight Minecraft Launcher written in Python 3 with a Rust core option for improved performance.

Language composition: Python ~42.1%, Rust ~39.6%, QML ~11.2% (plus PowerShell, HTML, JavaScript, and other small files).

## Quick highlights

- Cross-platform Minecraft Java Edition launcher
- Microsoft OAuth login
- Supports Fabric, Neoforge and Forge mod loaders
- Modrinth mod downloads and BMCLAPI mirror support
- Account management, version file management

## Supported ModLoaders

- Fabric
- Neoforge
- Forge

## Languages / Localization

Built-in languages: zh_CN, en_US. Add more by placing a `LANG.json` (e.g. `fr_FR.json`) in the `languages/` directory.

## Known issues

- Ancient Minecraft versions may be unable to load assets.

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

## Requirements

- Python >= 3.12 (development used 3.14). For compiling with MinGW64 + Nuitka use Python 3.12 compatibility.

Python packages required for development / running from source:

```
pip install PySide6 requests modrinth_api_wrapper
# Optional: for Modrinth search UI
pip install PySide6-WebEngine
```

For release builds with Nuitka:

```
pip install nuitka
```

## Run from source

```powershell
pip install PySide6 requests modrinth_api_wrapper
pip install PySide6-WebEngine   # Optional: Modrinth search page
python main.py
```

`main_qml.py` is an alias compatible with `main.py`.

The main program uses `spectrum_core` (Rust core + Python bridge) by default. To fallback to the pure-Python implementation, set:

```powershell
set SPECTRUM_USE_RUST=0   # Windows (PowerShell/CMD)
# or on Unix-like shells:
export SPECTRUM_USE_RUST=0
```

The pure-Python fallback lives under `python/spectrum_core/py_fallback/`.

## Building the Rust core (recommended for compilation)

Windows PowerShell helper:

```powershell
.\cargo_build.ps1
```

Output: `python/spectrum_core/_spectrum_core.pyd` (used by the Python package).

## Release build — Nuitka + Makefile + make.bat

Recommended for Windows (MinGW64 + Nuitka):

```bat
make.bat all 1.0.0
```

Or step-by-step:

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

## UI modification

To edit UI files use Qt Designer (from PySide6):

```
pyside6-designer qt.ui
```

On Windows, run the helper to rebuild UI files:

```bat
./buildui.bat
```

## Contributing

Contributions, bug reports and translations are welcome. Please open issues for problems or feature requests and submit pull requests for fixes and improvements.

- Follow the existing code style.
- If adding translations, add a `LANG.json` file under `languages/`.

## License

This project is open-source. Please check the repository LICENSE file for details.
