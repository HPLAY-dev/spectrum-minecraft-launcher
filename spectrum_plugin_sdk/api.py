import requests
import os
import threading

class LauncherAPI:
    def __init__(self, launcher):
        self.launcher = launcher

    # ========= 启动器信息 =========
    def get_version(self) -> str:
        return getattr(self.launcher, "version", "unknown")

    def get_minecraft_dir(self) -> str:
        return self.launcher.lineEdit.text()

    # ========= 日志 =========
    def log_info(self, msg: str):
        print(f"[INFO] {msg}")

    def log_warn(self, msg: str):
        print(f"[WARN] {msg}")

    def log_error(self, msg: str):
        print(f"[ERROR] {msg}")

    # ========= UI 操作 =========
    def set_launch_button_text(self, text: str):
        self.launcher.LaunchBtn.setText(text)

    # ========= 文件操作 =========
    def install_mod(self, mod_file: str, version_name: str):
        import shutil
        mc_dir = self.get_minecraft_dir()
        mod_dir = os.path.join(mc_dir, "versions", version_name, "mods")
        os.makedirs(mod_dir, exist_ok=True)
        shutil.copy(mod_file, mod_dir)
        self.log_info(f"已安装 Mod {mod_file} 到 {version_name}")

    def remove_mod(self, mod_name: str, version_name: str):
        mc_dir = self.get_minecraft_dir()
        mod_dir = os.path.join(mc_dir, "versions", version_name, "mods")
        target = os.path.join(mod_dir, mod_name)
        if os.path.exists(target):
            os.remove(target)
            self.log_info(f"已删除 Mod {mod_name} ({version_name})")

    # ========= 启动参数 =========
    def add_jvm_arg(self, arg: str):
        if not hasattr(self.launcher, "extra_jvm_args"):
            self.launcher.extra_jvm_args = []
        self.launcher.extra_jvm_args.append(arg)

    # ========= 事件系统 =========
    def on_event(self, event_name: str, callback):
        if not hasattr(self.launcher, "_event_hooks"):
            self.launcher._event_hooks = {}
        if event_name not in self.launcher._event_hooks:
            self.launcher._event_hooks[event_name] = []
        self.launcher._event_hooks[event_name].append(callback)

    def trigger_event(self, event_name: str, *args, **kwargs):
        if hasattr(self.launcher, "_event_hooks"):
            for cb in self.launcher._event_hooks.get(event_name, []):
                cb(*args, **kwargs)

    # ========= 网络 API =========
    def http_get(self, url: str, **kwargs):
        self.log_info(f"GET {url}")
        return requests.get(url, **kwargs)

    def http_post(self, url: str, data=None, json=None, **kwargs):
        self.log_info(f"POST {url}")
        return requests.post(url, data=data, json=json, **kwargs)

    def download_file(self, url: str, save_path: str, chunk_size: int = 8192):
        self.log_info(f"下载文件: {url} -> {save_path}")
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
        self.log_info(f"文件下载完成: {save_path}")
        return save_path

    def download_file_async(self, url: str, save_path: str,
                            chunk_size: int = 8192,
                            progress_callback=None,
                            finish_callback=None,
                            error_callback=None):
        """异步下载文件（带进度回调）"""
        def _download():
            try:
                self.log_info(f"[AsyncDownload] {url} -> {save_path}")
                with requests.get(url, stream=True) as r:
                    r.raise_for_status()
                    total = int(r.headers.get("content-length", 0))
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    downloaded = 0
                    with open(save_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=chunk_size):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                if progress_callback:
                                    progress_callback(downloaded, total)
                self.log_info(f"[AsyncDownload] 完成 {save_path}")
                if finish_callback:
                    finish_callback(save_path)
            except Exception as e:
                self.log_error(f"[AsyncDownload] 出错: {e}")
                if error_callback:
                    error_callback(e)

        thread = threading.Thread(target=_download, daemon=True)
        thread.start()
        return thread
class LauncherAPI:
    def __init__(self, launcher):
        self.launcher = launcher

    def log_info(self, msg):
        print(f"[Plugin][INFO] {msg}")

    def log_error(self, msg):
        print(f"[Plugin][ERROR] {msg}")
