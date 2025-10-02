class PluginBase:
    """插件开发者必须继承的基类（启动器内部用）"""

    id = "unnamed"
    name = "Unnamed Plugin"
    version = "0.0.1"
    author = "Unknown"
    description = ""

    def on_load(self, launcher):
        raise NotImplementedError

    def on_unload(self):
        raise NotImplementedError
