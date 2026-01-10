# Spectrum Minecraft Launcher
开源且轻量的Minecraft启动器，基于Python3

## 2.0 模组加载器
Fabric，Forge与Neoforge支持。

## 3.0 多语言
中文(简体) 英语(美国)

## 4.0 问题
- 早期版本不能正确加载assets(素材)

## 5.0 已经支持
- [x] 启动任何Minecraft Java Edition版本
- [x] 微软登录
- [x] Fabric ModLoader
- [x] Forge ModLoader
- [x] Neoforge ModLoader
- [x] 版本文件管理
- [x] Modrinth Mods下载
- [x] BMCLAPI镜像
- [x] 所有Minecraft启动器应该提供的功能

......

## 6.0 开发与贡献
### 6.1 环境配置
- Python>=3.12 (3.12 被使用以用mingw64编译)
- 开发Qt 6 GUI的桌面环境(linux only)
- OAuth登录使用的浏览器(或手动获取输出并在浏览器中打开链接)

要使此程序完整工作，还需要安装以下包

- PySide6
- modrinth_api_wrapper
- requests
```
pip install PyQt6 PyQt6-Tools requests modrinth_api_wrapper
```
### 6.2 UI 修改
运行 `pyside6-designer qt.ui` 来修改 UI.
运行 `./buildui.bat`(Windows) 来构建. (在其它系统，执行 `pyside6-uic -o .\ui.py .\qt.ui`)