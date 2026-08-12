# Spectrum Minecraft Launcher

**Version 26Q3.8 — "Pacific"** (released 2026-08-12)

An open-source, lightweight Minecraft Launcher written in Python 3 with a Rust core option for improved performance.

Language composition: Python ~42.1%, Rust ~39.6%, QML ~11.2% (plus PowerShell, HTML, JavaScript, and other small files).

## Quick highlights

- Cross-platform Minecraft Java Edition launcher
- Microsoft OAuth login
- Supports Fabric, Neoforge and Forge mod loaders
- Modrinth mod downloads and BMCLAPI mirror support
- Account management, version file management

## Release 26Q3.8 "Pacific" — Summary

This release (26Q3.8, codename "Pacific") packages the major improvements made over the last development cycle into a stable release. Key highlights:

- spectrum_core (Rust/PyO3) is the recommended runtime core for better performance and stability; a pure-Python fallback remains available.
- New QML/Web UI improvements and updated Spectrum theme for a modern look and smoother UX.
- Added mojang API helper for UUID resolution and related fixes.
- Multiple bug fixes and stability improvements: async/threading fixes, BMCLAPI/Forge/Neoforge fixes, LabyMod support, and Java detection improvements.
- Release/build improvements: updated Nuitka build flow, Makefile helpers and Cargo/Bazel integrations for reproducible builds.

For a concise list of changes and all commits, see the project commits page: https://github.com/HPLAY-dev/spectrum-minecraft-launcher/commits

## Recent changes (high level)

- 2026-06-27 — Introduced spectrum_core (Rust/PyO3) as the recommended core, new QML/Web UI, and Bazel/Cargo build integration. This moves heavy work into a Rust extension with a pure-Python fallback.
- 2026-06-28 — Added mojang API helper, multiple bug fixes, and English README improvements.
- 2026-01 → 2026-06 — Many UI improvements, bug fixes, async/threading stability fixes, BMCLAPI and Forge/Neoforge fixes, LabyMod support, and improvements to Java detection/management and Nuitka release scripts.
- Ongoing — Localization (zh_CN / en_US) improvements and community contributions.

(For full commit history see: https://github.com/HPLAY-dev/spectrum-minecraft-launcher/commits)

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
