class LauncherAPI:
    def __init__(self, launcher):
        self.launcher = launcher

    def log_info(self, msg):
        print(f"[Plugin][INFO] {msg}")

    def log_error(self, msg):
        print(f"[Plugin][ERROR] {msg}")
