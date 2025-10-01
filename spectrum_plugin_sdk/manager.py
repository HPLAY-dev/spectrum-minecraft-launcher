import os
import shutil
import zipfile
from .loader import load_all_plugins

class PluginManager:
    def __init__(self, launcher, plugin_path):
        self.launcher = launcher
        self.plugin_path = plugin_path
        self.plugins = []

    def load(self):
        """加载所有插件"""
        self.plugins = load_all_plugins(self.launcher)

    def unload_all(self):
        """卸载所有插件"""
        for plugin in self.plugins:
            try:
                plugin.on_unload()
                print(f"[Plugin] Unloaded {plugin.name}")
            except Exception as e:
                print(f"[Plugin] Error unloading {plugin.name}: {e}")
        self.plugins.clear()

    def install(self, plugin_zip, plugin_id):
        """安装插件（ZIP 解压）"""
        target_dir = os.path.join(self.plugin_path, plugin_id)
        os.makedirs(target_dir, exist_ok=True)
        with zipfile.ZipFile(plugin_zip, "r") as zf:
            zf.extractall(target_dir)
        print(f"[Plugin] Installed {plugin_id}")

    def remove(self, plugin_id):
        """卸载插件"""
        target_dir = os.path.join(self.plugin_path, plugin_id)
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
            print(f"[Plugin] Removed {plugin_id}")
