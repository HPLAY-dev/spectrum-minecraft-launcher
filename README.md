# SerenaLauncher

跨平台 Minecraft 启动器，支持多版本管理、Mod 管理、多实例隔离等功能。

| 项 | 值 |
|---|---|
| **产品名** | SerenaLauncher |
| **版本格式** | `26Q2.BuildID.commitid` |
| **大版本** | 26 |
| **开发代号** | Okra |

技术栈：**C++ 核心引擎** + **Rust 高性能模块 (PyO3)** + **Python 桥接** + **Qt6 (PySide6 / C++ QML)**

## 项目结构

```
serena-launcher/
├── CMakeLists.txt
├── config/
│   ├── default.json
│   └── version.json          # 版本元数据（构建时更新 commit）
├── src/
│   ├── core/                 # C++ 核心引擎
│   │   ├── rs/mc-core/       # Rust 高性能核心
│   │   └── GUI/
│   │       ├── py/           # PySide6 + QML（主 GUI）
│   │       ├── cpp/          # Qt6 C++ GUI
│   │       └── rs/           # Rust 原生 GUI
│   ├── common/
│   └── launcher/             # CLI 入口
├── resources/
├── docs/
├── tests/
└── scripts/
    ├── gen_version.ps1       # 生成 26Q2.BuildID.commitid
    └── cargo_build.ps1
```

## 快速开始

```powershell
pip install -r requirements.txt
.\scripts\gen_version.ps1
.\scripts\cargo_build.ps1
py .\src\core\GUI\py\main_qml.py
```

### 构建 C++ 核心

```powershell
.\scripts\build.ps1
.\build\Release\serena_launcher_cli.exe
```

## 版本号

完整版本号：`26Q2.{BuildID}.{commitid}`

- **26** — 大版本
- **Q2** — 2026 第二季度渠道
- **BuildID** — 构建编号（环境变量 `SERENA_BUILD_ID`，默认 `0`）
- **commitid** — Git 短 SHA（`scripts/gen_version.ps1` 自动写入）

```powershell
$env:SERENA_BUILD_ID = "2025062801"
.\scripts\gen_version.ps1
# => 26Q2.2025062801.a3f2c1d
```

## 环境变量

| 变量 | 说明 | 默认 |
|------|------|------|
| `MC_USE_RUST` | 启用 Rust 核心 | `1` |
| `MC_USE_BMCLAPI` | 使用 BMCLAPI 镜像 | `1` |
| `SERENA_BUILD_ID` | 构建编号 | `0` |

## 许可

GNU General Public License v3.0 — 见 [LICENSE](LICENSE)
