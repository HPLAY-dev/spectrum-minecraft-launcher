class PluginBase:
    """插件开发者必须继承的基类（启动器内部用）"""

    # 插件元信息
    id = "unnamed"
    name = "Unnamed Plugin"
    version = "0.0.1"
    author = "Unknown"
    description = ""

    def on_load(self, launcher):
        """
        插件被加载时调用。
        :param launcher: 启动器主对象（一般传 MainWindow 或管理器实例）
        """
        raise NotImplementedError("插件必须实现 on_load 方法")

    def on_unload(self):
        """
        插件被卸载时调用。
        用于清理资源、移除事件绑定等。
        """
        raise NotImplementedError("插件必须实现 on_unload 方法")
