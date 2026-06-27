# MC Launcher

一个跨平台 Minecraft 启动器，支持多版本管理、Mod 管理、多实例隔离等功能。

技术栈：**C++ 核心引擎** + **Rust 高性能模块 (PyO3)** + **Python 桥接** + **Qt6 (PySide6 / C++ QML)**

## 项目结构

```
mc-launcher/
├── CMakeLists.txt              # 根构建配置
├── pyproject.toml              # Python 项目配置
├── requirements.txt            # Python 依赖
├── src/
│   ├── core/                   # 核心引擎 (C++)
│   │   ├── include/mc/         # 公共头文件
│   │   ├── src/                # 核心实现
│   │   ├── CMakeLists.txt
│   │   ├── rs/
│   │   │   └── mc-core/        # Rust 高性能核心 (PyO3)
│   │   └── GUI/
│   │       ├── cpp/            # C++ GUI (Qt6)
│   │       ├── py/             # Python GUI (PySide6 + QML)
│   │       │   ├── app/        # 应用层 / QML 桥接
│   │       │   ├── mc_core/    # Python ↔ Rust 桥接包
│   │       │   ├── qml/        # Qt6 QML 界面
│   │       │   ├── main.py
│   │       │   └── main_qml.py
│   │       └── rs/
│   │           └── gui-native/ # Rust 原生 GUI (Slint/Tauri 占位)
│   ├── common/                 # 通用工具库 (C++)
│   └── launcher/               # CLI 启动器入口 (C++)
├── resources/
│   ├── icons/
│   ├── fonts/
│   ├── lang/                   # en_us.json / zh_cn.json
│   └── themes/                 # default.qss
├── docs/
│   ├── architecture.md
│   └── build.md
├── tests/
│   ├── cpp/
│   ├── python/
│   └── rust/
├── scripts/
│   ├── build.ps1 / build.sh
│   └── cargo_build.ps1 / cargo_build.sh
└── config/
    └── default.json
```

## 功能特性

- 多版本 Minecraft 支持 (正式版 / 快照版 / Forge / Fabric / NeoForge)
- 多实例管理，完全隔离
- 微软 / Mojang 账户认证
- Mod / 资源包 / 光影管理
- Java 运行时自动检测与管理
- 游戏日志实时查看
- 多语言支持 (zh_CN / en_US)
- 主题定制

## 快速开始

### 依赖

- CMake >= 3.20
- C++17 编译器
- Qt 6.x
- Python 3.10+ & PySide6
- Rust 1.70+

### 运行 Python GUI（推荐）

```powershell
pip install -r requirements.txt
.\scripts\cargo_build.ps1
py .\src\core\GUI\py\main_qml.py
```

### 构建 C++ 核心

```powershell
.\scripts\build.ps1
.\build\Release\mc_launcher_cli.exe
```

## 环境变量

| 变量 | 说明 | 默认 |
|------|------|------|
| `MC_USE_RUST` | 启用 Rust 核心 | `1` |
| `MC_USE_BMCLAPI` | 使用 BMCLAPI 镜像 | `1` |

## 许可

GNU General Public License v3.0 — 见 [LICENSE](LICENSE)
