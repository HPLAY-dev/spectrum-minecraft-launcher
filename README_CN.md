# Spectrum Minecraft Launcher
开源且轻量的Minecraft启动器，基于Python3

## 2.0 模组加载器
Fabric已经完整支持，Forge与Neoforge基本支持，见4.0

## 3.0 多语言
中文(简体) 英语(美国)

## 4.0 问题
- 早期版本不能正确加载assets(素材)
- 在 `url` 为空时，无法安装Forge(Neoforge也是)

## 5.0 已经支持
- [x] 启动任何Minecraft Java Edition版本
- [x] 微软登录
- [x] Fabric ModLoader
- [x] Forge ModLoader
- [x] Neoforge ModLoader
- [x] 版本文件管理
- [x] Modtinth Mods下载

......

## 6.0 开发与贡献
### 6.1 环境配置
- Python 3.x (3.13 被使用)
- 开发Qt 6 GUI的桌面环境(linux only)
- OAuth登录使用的浏览器

要使此程序完整工作，还需要安装以下包

- PySide6
- modrinth_api_wrapper
- requests
```
pip install PyQt6 PyQt6-Tools requests modrinth_api_wrapper
```
### 6.2 UI 修改
运行 `designer qt.ui` 来修改 UI.
运行 `./buildui.bat`(Windows) 来构建. (在其它系统，执行 `pyuic6 -o .\ui.py .\qt.ui`)