# Spectrum Minecraft Launcher

基于 **Python 3 + PySide6** 的轻量级开源 Minecraft 启动器，核心下载/启动/OAuth 逻辑由 **Rust (`spectrum-core`)** 加速，通过 PyO3 暴露给 Python。

## 功能概览

| 类别 | 支持内容 |
|------|----------|
| 游戏版本 | 正式版、快照版（可选显示 Alpha/Beta） |
| Mod 加载器 | Vanilla、Fabric、Forge、NeoForge |
| 客户端 | **LabyMod 4**（独立下载页） |
| 账户 | 离线账户、Microsoft OAuth |
| 镜像 | BMCLAPI（版本清单、资源、库文件） |
| 其他 | Modrinth 模组安装、版本管理、多语言 (zh_CN / en_US) |

## 架构

```
main.py                 # PySide6 GUI 入口
python/spectrum_core/   # Python 桥接层（优先调用 Rust，失败回退 mclauncher_core）
spectrum-core/          # Rust 异步核心（下载、启动参数、OAuth、Java 检测等）
mclauncher_core/        # 旧版 Python 实现（回退 / LabyMod 等尚未迁移模块）
```

- 默认启用 Rust 核心：`SPECTRUM_USE_RUST=1`（可设为 `0` 回退纯 Python）
- 原生扩展产物：`python/spectrum_core/_spectrum_core.pyd`（Windows）或对应平台的 `.so`

## 快速开始

### 依赖

- **Python** ≥ 3.12（开发环境使用 3.14；Nuitka 编译建议 3.12）
- **Rust** toolchain（编译 `spectrum-core`）
- Python 包：

```bash
pip install PySide6 requests modrinth_api_wrapper beautifulsoup4
```

### 编译 Rust 核心

**Windows（推荐）：**

```powershell
.\cargo_build.ps1
```

**手动：**

```bash
cd spectrum-core
cargo build --release --features python
# 将 target/release/spectrum_core.dll 复制为 ../python/spectrum_core/_spectrum_core.pyd
```

**Bazel（可选）：**

```bash
bazel build //python:spectrum_core_native
bazel run //:launcher   # 若已配置 bazel_run.bat
```

### 运行

```bash
python main.py
```

首次运行前请确认 `_spectrum_core.pyd` 已存在；若启动日志出现 `Rust core unavailable`，请先执行编译步骤。

## 配置说明

配置文件位于启动器目录：

| 文件 | 说明 |
|------|------|
| `cfg.json` | Minecraft 路径、内存、JVM 参数、已保存 Java 列表等 |
| `accounts.json` | 账户信息 |
| `versions.json` | 各实例的 Java 覆盖等 |

### Minecraft 目录

- 留空或填写 `.minecraft` 时，Windows 自动解析为 `%APPDATA%\.minecraft`
- 支持 `~`、相对路径；下载前会规范化为绝对路径并自动创建 `versions/` 目录

### Java 多版本管理（设置页）

- **启动时自动扫描**：注册表 + `PATH` 中的 Java 安装
- **「扫描」按钮**：手动重新检测
- **下拉列表**：显示 `Java {主版本} — {路径}`，可手动添加/删除
- **选 Java 策略**：优先精确匹配所需主版本，否则选用 `>=` 要求的最低版本
- **下载 Java**：「下载 Java 8 / 17」为快捷入口；「下载 Java...」可输入任意主版本号 (8–99)，从清华 Adoptium 镜像拉取安装包

## LabyMod 下载

1. 切换到 **「下载 LabyMod」** 标签页
2. 选择 LabyMod 支持的 MC 版本，填写实例名称
3. 点击下载：后台线程执行 LabyMod 安装，完成后自动调用 Rust 核心补全 client / libraries / assets

实现位于 `mclauncher_core/labymod.py`（仅下载当前 MC 版本所需库，避免拉取全量依赖）。

## 开发

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SPECTRUM_USE_RUST` | `1` | `0` / `false` 时使用纯 Python 核心 |
| `PYO3_PYTHON` | — | 编译 PyO3 扩展时指定 Python 解释器 |
| `VERBOSE` | — | 集成测试详细输出 |

### 集成测试

```bash
python run_integration_tests.py
# 或
python -m unittest discover -s tests -p "test_*.py"
```

需要已编译的 Rust 核心；部分用例依赖网络（BMCLAPI / Mojang）。

### UI 修改

```bash
pyside6-designer qt.ui    # 编辑界面
./buildui.bat             # 生成 ui.py（Windows）
```

### 项目结构（核心）

```
spectrum-core/src/
  download.rs      # 异步下载引擎（JAR / LIB / AST）
  python.rs        # PyO3 绑定（含 GIL 安全的 progress 回调）
  oauth.rs         # Microsoft / Xbox / MC 认证
  launcher.rs      # 启动命令拼装
  java.rs          # Java 检测
  manifest.rs      # 版本清单与 version.json 合并
  modloader/       # Fabric / Forge / NeoForge / LabyMod 安装器
```

## 已知问题

- 远古版本（Alpha/Beta）资源加载可能不完整
- Java 在线安装依赖清华镜像页面结构，偶发 403 需更换镜像或手动安装
- 修改 `_spectrum_core.pyd` 后需**关闭**正在运行的 `main.py` 再重新编译，否则文件被占用无法覆盖

## 路线图 / 已完成

- [x] 任意 Java 版启动
- [x] Microsoft OAuth 登录
- [x] Fabric / Forge / NeoForge
- [x] LabyMod 4 下载
- [x] Rust 异步下载核心 + BMCLAPI
- [x] 多 JDK 扫描与管理
- [x] 版本与存档管理
- [x] Modrinth 模组安装
- [x] 跨平台（Windows / Linux / macOS，Rust 核心）

## 多语言

在 `languages/` 下新增 `LANG.json`（`LANG` 为语言代码，如 `ja_JP.json`）即可扩展语言。参考现有 `zh_CN.json` / `en_US.json`。

## 许可证

见 [LICENSE](LICENSE)。
