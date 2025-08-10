# Spectrum Minecraft Launcher
An open source Minecraft Launcher in Python3. Currently focusing on Modloaders.

## 1.0 Files
**mclauncher_core.py** Core Functions
**tkui.py**            UI
**JavaWrapper.jar**    see 1.1
**make.bat**           pack via PyInstaller

### 1.1 JavaWrapper
Fixes Unicode problems on Windows.
> 如果你的 Windows 系统启用了 Beta 版：使用Unicode UTF-8提供全球语言支持，Java 可能会在读取命令行参数时使用错误的编码进行解码，导致一系列问题。
> Bug 参考 JDK-8272352，已在 Java19 修复
> 使用此 Wrapper 可用于修复 Class Path, -D 参数 和 App 参数 中的乱码，解决大部分因此Bug无法运行的情况。
> From: [GitHub/00ll00/java_launch_wrapper](https://github.com/00ll00/java_launch_wrapper)

## 2.0 Launcher Core
Launcher functions. One day there will be a documentation. Forgive me for not writing comment.

## 3.0 3rd-party stuff
**BMCLAPI** download faster in China Mainland.
**JavaWrapper** fixed bugs on Windows with East-Asian language(zh_CN for me).
**PCL 2** Launch command referred.
**Fabric** Modloader.