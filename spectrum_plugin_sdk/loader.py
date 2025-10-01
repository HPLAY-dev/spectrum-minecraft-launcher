import importlib.util
import json
import os
import subprocess
import sys
from .base import PluginBase


# 插件默认安装目录
PLUGIN_PATH = os.path.join(os.path.dirname(__file__), "installed")

def install_requirements(req_path):
    """严格模式：每次更新依赖"""
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "-r", req_path, "--upgrade"
    ])
    print(f"[Plugin] Installed/Updated requirements from {req_path}")

def load_plugin(manifest_path, launcher):
    """加载单个插件"""
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    root = os.path.dirname(manifest_path)

    # 安装依赖
    req_path = os.path.join(root, "requirements.txt")
    if os.path.exists(req_path):
        install_requirements(req_path)

    # 动态导入插件
    plugin_path = os.path.join(root, "plugin.py")
    spec = importlib.util.spec_from_file_location(manifest["id"], plugin_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    plugin_class = getattr(module, manifest["entry"], None)
    if plugin_class and issubclass(plugin_class, PluginBase):
        plugin_instance = plugin_class()
        plugin_instance.on_load(launcher)
        print(f"[Plugin] Loaded {manifest['name']} v{manifest['version']}")
        return plugin_instance
    else:
        raise RuntimeError(f"Invalid plugin entry in {manifest['id']}")

def load_all_plugins(launcher):
    """加载所有插件"""
    plugins = []
    if not os.path.exists(PLUGIN_PATH):
        os.makedirs(PLUGIN_PATH)

    for root, dirs, files in os.walk(PLUGIN_PATH):
        if "manifest.json" in files:
            try:
                plugins.append(load_plugin(os.path.join(root, "manifest.json"), launcher))
            except Exception as e:
                print(f"[Plugin] Failed to load plugin at {root}: {e}")

    return plugins
