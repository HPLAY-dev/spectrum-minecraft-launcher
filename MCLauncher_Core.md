# “mclauncher_core” 使用文档
`mclauncher_core`，以下简称`core`，通过Python3(3.13)实现了Minecraft (Java Edition)启动器的基本功能，可通过调用core的代码使用**启动 Minecraft**，**下载 Minecraft**等功能。兼容`Fabric Mod 加载器`。
## 1.0 Functions
要使用core，请先在你的python文件中`import mclauncher_core`，之后则可以使用其功能。
**注意: 获取 不等于 下载**
### 1.1 参数说明
此列表储存主要参数，次要参数请在单个Function的说明下查看
|参数名称|参数说明|参数类型|
|-----|-----|-----|
|minecraft_dir|以.minecraft为名称的文件夹(通常)，存放着Minecraft游戏文件，通常包含`versions`,`libraries`,`assets`等子文件夹，对于未启用版本分离的启动器，则已下载Minecraft版本名称将在此目录中。|str|
|version|版本id，通常为1.X.X格式|str|
|version_name|版本名称，在`.minecraft/versions`下查看|str|
|url|url链接|str|
|bmclapi|是否使用BMCLAPI下载，`True`使用bmclapi，`False`使用官方源|bool|
|java_binary_path|Java二进制文件目录，包含文件名称|str|
### 1.2 Minecraft版本卷宗 Functions
#### get\_version\_manifest(bmclapi=False) -> dict
获取Minecraft版本卷宗文件
#### get\_version\_list(show\_snapshot=False, show\_old=False, show\_release=True, bmclapi=False) -> list
获取Minecraft版本列表
#### get\_version\_json(version, bmclapi=False) -> dict
获取一个Minecraft版本的JSON文件
#### download\_version\_json(minecraft_dir, version, version_name, bmclapi=False) -> None
下载一个Minecraft版本的JSON文件
#### get_mainclass(minecraft_dir, version, version_name) -> str
获取Minecraft版本的`mainClass`
### Minecraft下载Functions
#### download\_jar(minecraft\_dir, version\_name, bmclapi=False) -> None
下载Minecraft版本的jar(主文件)
#### download\_libraries(minecraft\_dir, version, version\_name, print\_status=True, bmclapi=False, progress\_callback=None) -> None
下载Minecraft的libraries
#### download_assets(minecraft_dir, version_name, print_status=True, bmclapi=False, progress_callback=None) -> None
下载Minecraft的Assets
### Minecraft启动functions
#### remove\_version(minecraft\_dir, version\_name) -> None
删除一个Minecraft版本但不删除libraries与assets
#### get\_minecraft\_version(minecraft\_dir, version\_name) -> None
从版本名称获得版本号
#### launch(javaw, xmx, minecraft_dir, version, version_name, javawrapper=None, username="steve", xmn="256M") -> str
生成启动指令
`javaw` -- Java可执行文件目录(包含文件名)
`xmx` -- JVM内存最大分配大小
`javawrapper` -- JavaWrapper.jar文件目录(仅Windows)
`username` -- 玩家名称
`xmn` -- JVM -Xmn 参数
### 1.9 Fabric ModLoader Functions
此处包括Fabric ModLoader的一些代码使用
#### is\_fabric(minecraft\_dir, version\_name) -> bool
判断版本是否使用Fabric ModLoader
#### merge\_json(fabric\_json\_path, minecraft\_json\_path) -> None
合并fabric与minecraft版本的json
`fabric_json_path` -- Fabric的json文件目录(包含文件名)
`minecraft_json_path` -- Minecraft的版本json文件目录(包含文件名)
`modify` -- 兼容性，不需要填写
#### parse\_xml(url) -> dict
处理maven.fabricmc.net下各个子目录下的`maven-metadata.xml`。填入对应参数可获得FabricLoader与FabricInstaller的版本。
#### get\_fabric\_installer\_versions() -> str
**注意：此function将废弃**
获取FabricInstaller的最新版本号。
#### get\_latest\_fabric\_loader\_version() -> str
获取FabricLoader的最新版本号。
#### download\_fabric\_json(minecraft\_dir, version, version\_name, loader\_version='latest') -> None
下载Fabric的版本json到Minecraft版本目录
`loader_version` -- FabricLoader版本，填入`latest`或不填为最新版本