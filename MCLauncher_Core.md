# “mclauncher_core” 使用文档
`mclauncher_core`，以下简称`core`，通过Python3(3.13)实现了Minecraft (Java Edition)启动器的基本功能，可通过调用core的代码使用**启动 Minecraft**，**下载 Minecraft**等功能。兼容`Fabric Mod 加载器`。
## 1.0 Functions
要使用core，请先在你的python文件中`import mclauncher_core`，之后则可以使用其功能。

**注意**: 函数说明中获取指将文件获取并当作dict(如果是json)或str读取。下载指将文件下载到minecraft目录的对应文件夹中
### 1.1 参数说明
此列表储存主要参数，次要参数请在单个Function的说明下查看
|参数名称|参数说明|参数类型|
|-----|-----|-----|
|minecraft_dir|以.minecraft为名称的文件夹(通常)，存放着Minecraft游戏文件，通常包含`versions`,`libraries`,`assets`等子文件夹，对于未启用版本分离的启动器，则已下载Minecraft版本名称将在此目录中。|str|
|version|版本id，通常为1.X.X(rd-xxxxxx, b1.x.x, a1.x.x, rd-2019xxxx......)格式|str|
|version_name|版本名称，在`.minecraft/versions`下查看|str|
|url|url链接|str|
|bmclapi|是否使用BMCLAPI下载，`True`使用bmclapi，`False`使用官方源|bool|
|java_binary_path|Java二进制文件目录，包含文件名称|str|
