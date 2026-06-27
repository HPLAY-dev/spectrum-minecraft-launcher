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
- nuitka (release build; Nuitka 4.x uses `python -m nuitka`)
```
pip install PySide6 requests modrinth_api_wrapper nuitka
```

### Run from source
```powershell
pip install PySide6 requests modrinth_api_wrapper
pip install PySide6-WebEngine   # 模组页 Modrinth 搜索（可选）
python main.py
```

`main_qml.py` 为兼容别名，等价于 `main.py`。

主程序已切换至 `spectrum_core`（Rust 核心 + Python 桥接）。`SPECTRUM_USE_RUST=0` 可回退纯 Python 实现（`python/spectrum_core/py_fallback/`）。

### Rust 核心（推荐编译）
```powershell
.\cargo_build.ps1
```
产物：`python/spectrum_core/_spectrum_core.pyd`

### Release build — Nuitka + Makefile + make.bat

Windows 推荐（MinGW64 + Nuitka）：

```bat
make.bat all 1.0.0
```

或分步：

```bat
make.bat clean
make.bat nuitka 1.0.0
make.bat dist 1.0.0
make.bat archive 1.0.0
```

已安装 GNU Make 时，`make.bat` 会委托给 `Makefile`：

```bat
make.bat all VERSION=1.0.0
```

产物目录：`builds/nuitka-<VERSION>/`，压缩包：`builds/nuitka-<VERSION>-windows.7z`

### UI Modification 
Run `pyside6-designer qt.ui` to modify UI.
Run `./buildui.bat`(Windows only) to build the ui.
