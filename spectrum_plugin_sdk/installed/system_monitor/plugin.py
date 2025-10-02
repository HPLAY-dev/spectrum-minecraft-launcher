from spectrum_plugin_sdk.base import PluginBase
from PyQt5.QtWidgets import QLabel, QPushButton, QDialog, QGridLayout, QAction
from PyQt5.QtCore import QTimer
import psutil


class SystemMonitorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系统监控")
        self.resize(400, 250)

        layout = QGridLayout(self)

        self.label_cpu = QLabel("CPU 占用: ")
        self.label_mem = QLabel("内存占用: ")
        self.label_gpu = QLabel("GPU 占用: ")
        self.label_net = QLabel("网络收发: ")
        self.label_disk = QLabel("磁盘占用: ")

        layout.addWidget(self.label_cpu, 0, 0)
        layout.addWidget(self.label_mem, 1, 0)
        layout.addWidget(self.label_gpu, 2, 0)
        layout.addWidget(self.label_net, 3, 0)
        layout.addWidget(self.label_disk, 4, 0)

        self.setLayout(layout)

        # 定时刷新
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)

    def update_stats(self):
        # CPU
        cpu = psutil.cpu_percent()
        self.label_cpu.setText(f"CPU 占用: {cpu}%")

        # 内存
        mem = psutil.virtual_memory()
        self.label_mem.setText(f"内存占用: {mem.percent}% "
                               f"({mem.used // (1024**3)}G / {mem.total // (1024**3)}G)")

        # GPU（可选）
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                self.label_gpu.setText(
                    f"GPU 占用: {gpu.load*100:.1f}% 显存 {gpu.memoryUsed}MB / {gpu.memoryTotal}MB"
                )
            else:
                self.label_gpu.setText("GPU 占用: 未检测到")
        except Exception:
            self.label_gpu.setText("GPU 占用: 未启用")

        # 网络
        net = psutil.net_io_counters()
        self.label_net.setText(f"网络收发: {net.bytes_recv//1024//1024}MB ↓ / "
                               f"{net.bytes_sent//1024//1024}MB ↑")

        # 磁盘
        disk = psutil.disk_usage("/")
        self.label_disk.setText(f"磁盘占用: {disk.percent}% "
                                f"({disk.used // (1024**3)}G / {disk.total // (1024**3)}G)")


class SystemMonitorPlugin(PluginBase):
    id = "system_monitor"
    name = "系统监控"
    version = "1.0.0"
    author = "Spectrum Team"
    description = "显示 CPU、内存、GPU、网络和硬盘占用情况"

    def on_load(self, launcher):
        """加载插件时，在菜单栏增加一个入口"""
        if hasattr(launcher, "menuBar"):
            menu = launcher.menuBar().addMenu("插件")
            self.action = QAction("系统监控", launcher)
            self.action.triggered.connect(self.open_monitor)
            menu.addAction(self.action)
            print("[Plugin] 系统监控插件已挂载")

    def on_unload(self):
        if hasattr(self, "action"):
            self.action.deleteLater()

    def open_monitor(self):
        dialog = SystemMonitorDialog()
        dialog.exec_()
