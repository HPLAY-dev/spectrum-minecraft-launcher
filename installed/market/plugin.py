from spectrum_plugin_sdk import PluginBase, LauncherAPI
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QPushButton, QListWidgetItem,
    QMessageBox, QLineEdit, QLabel, QHBoxLayout
)
import requests
import os
import zipfile
import io

SERVER_URL = "http://127.0.0.1:8000"   # ⚠️ 修改成你的服务器地址


class PluginMarket(PluginBase):
    id = "plugin_market"
    name = "插件市场"
    version = "1.0.0"
    author = "Spectrum Team"
    description = "提供插件市场界面，支持登录、浏览和下载插件"

    def on_load(self, launcher):
        self.api = LauncherAPI(launcher)
        self.api.log_info("✅ 插件市场已加载！")

        self.token = None

        # 在插件管理Tab加按钮
        if hasattr(launcher, "horizontalLayout_plugins"):
            self.btn_market = QPushButton("打开插件市场")
            launcher.horizontalLayout_plugins.addWidget(self.btn_market)
            self.btn_market.clicked.connect(self.open_market)

    def on_unload(self):
        self.api.log_info("❌ 插件市场已卸载")

    # 打开插件市场界面
    def open_market(self):
        dialog = QDialog(self.api.launcher)
        dialog.setWindowTitle("插件市场")
        layout = QVBoxLayout(dialog)

        # 登录区
        login_layout = QHBoxLayout()
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("用户名")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.btn_login = QPushButton("登录")
        login_layout.addWidget(QLabel("账号:"))
        login_layout.addWidget(self.username_input)
        login_layout.addWidget(QLabel("密码:"))
        login_layout.addWidget(self.password_input)
        login_layout.addWidget(self.btn_login)
        layout.addLayout(login_layout)

        # 插件列表
        self.list = QListWidget(dialog)
        layout.addWidget(self.list)

        # 操作按钮
        self.btn_refresh = QPushButton("刷新插件列表")
        self.btn_download = QPushButton("下载选中插件")
        layout.addWidget(self.btn_refresh)
        layout.addWidget(self.btn_download)

        # 绑定事件
        self.btn_login.clicked.connect(self.login)
        self.btn_refresh.clicked.connect(self.fetch_plugins)
        self.btn_download.clicked.connect(self.download_plugin)

        dialog.setLayout(layout)
        dialog.resize(600, 400)
        dialog.exec_()

    # 登录
    def login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self.api.launcher, "提示", "请输入账号和密码")
            return
        try:
            r = requests.post(f"{SERVER_URL}/auth/login", json={
                "username": username,
                "password": password
            })
            if r.status_code == 200:
                self.token = r.json()["access_token"]
                QMessageBox.information(self.api.launcher, "成功", f"登录成功，Token 已保存")
            else:
                QMessageBox.critical(self.api.launcher, "错误", f"登录失败: {r.text}")
        except Exception as e:
            QMessageBox.critical(self.api.launcher, "错误", f"请求失败: {e}")

    # 获取插件列表
    def fetch_plugins(self):
        try:
            r = requests.get(f"{SERVER_URL}/plugins/list")
            if r.status_code == 200:
                self.list.clear()
                plugins = r.json()
                for p in plugins:
                    item = QListWidgetItem(f"{p['name']} v{p['version']} - {p['author']}")
                    item.setData(1000, p)
                    self.list.addItem(item)
            else:
                QMessageBox.critical(self.api.launcher, "错误", f"获取插件失败: {r.text}")
        except Exception as e:
            QMessageBox.critical(self.api.launcher, "错误", f"请求失败: {e}")

    # 下载并安装插件
    def download_plugin(self):
        item = self.list.currentItem()
        if not item:
            QMessageBox.warning(self.api.launcher, "提示", "请选择插件")
            return

        plugin_data = item.data(1000)
        plugin_id = plugin_data["id"]

        try:
            r = requests.get(f"{SERVER_URL}/plugins/download/{plugin_id}")
            if r.status_code != 200:
                QMessageBox.critical(self.api.launcher, "错误", f"下载失败: {r.text}")
                return

            download_url = SERVER_URL + r.json()["download_url"]
            r_file = requests.get(download_url)
            r_file.raise_for_status()

            # 解压到 plugins/installed/<id>/
            target_dir = os.path.join("plugins", "installed", plugin_data["name"])
            os.makedirs(target_dir, exist_ok=True)
            with zipfile.ZipFile(io.BytesIO(r_file.content)) as zf:
                zf.extractall(target_dir)

            QMessageBox.information(self.api.launcher, "成功", f"插件 {plugin_data['name']} 已安装")
            if hasattr(self.api.launcher, "refresh_plugin_list"):
                self.api.launcher.refresh_plugin_list()

        except Exception as e:
            QMessageBox.critical(self.api.launcher, "错误", f"请求失败: {e}")
