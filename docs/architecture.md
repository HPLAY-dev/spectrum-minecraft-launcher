# MC Launcher 架构

## 技术栈

| 层级 | 技术 | 路径 |
|------|------|------|
| 核心引擎 | C++17 | `src/core/` |
| 高性能核心 | Rust (PyO3) | `src/core/rs/mc-core/` |
| GUI (主) | Python + PySide6 + Qt6 QML | `src/core/GUI/py/` |
| GUI (备选) | C++ + Qt6 QML | `src/core/GUI/cpp/` |
| GUI (备选) | Rust native | `src/core/GUI/rs/gui-native/` |
| 通用库 | C++ | `src/common/` |
| CLI 入口 | C++ | `src/launcher/` |

## 数据流

```
Qt6 QML UI  ←→  Python AppBridge  ←→  mc_core (Rust / py_fallback)
                      ↓
               C++ mc_core (实例管理、启动参数)
```

## 构建顺序

1. `scripts/cargo_build.ps1` — 编译 Rust PyO3 扩展
2. `cmake -B build` — 编译 C++ 核心与 CLI
3. `py src/core/GUI/py/main_qml.py` — 运行 Python GUI
