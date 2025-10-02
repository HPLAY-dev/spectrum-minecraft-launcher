class PluginBase:
    """插件开发者基类"""

    id = "unnamed"
    name = "Unnamed Plugin"
    version = "0.0.1"
    author = "Unknown"
    description = ""

    def on_load(self, launcher):
        raise NotImplementedError

    def on_unload(self):
        raise NotImplementedError
from .base import PluginBase
from .manager import PluginManager
from .loader import load_plugin, load_all_plugins
from .launcher_api import LauncherAPI   # ✅ 新增

__all__ = [
    "PluginBase",
    "PluginManager",
    "load_plugin",
    "load_all_plugins",
    "LauncherAPI"
]
