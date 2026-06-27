# 构建指南

## 依赖

- CMake >= 3.20
- C++17 编译器
- Qt 6.x（C++ GUI 与 PySide6）
- Python 3.10+
- Rust 1.70+（含 `pyo3` 扩展）

## Windows

```powershell
pip install -r requirements.txt
.\scripts\cargo_build.ps1
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
py .\src\core\GUI\py\main_qml.py
```

## Linux / macOS

```bash
pip install -r requirements.txt
./scripts/cargo_build.sh
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j$(nproc)
python3 src/core/GUI/py/main_qml.py
```

## 环境变量

| 变量 | 说明 | 默认 |
|------|------|------|
| `MC_USE_RUST` | 启用 Rust 核心 | `1` |
| `MC_USE_BMCLAPI` | 使用 BMCLAPI 镜像 | `1` |
