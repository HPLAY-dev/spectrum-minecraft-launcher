"""后台网络任务 — 避免阻塞 Qt 主线程。"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QObject, Qt, Signal


class _MainThreadDeliverer(QObject):
    """将线程池结果投递回 Qt 主线程。"""

    delivered = Signal(object)

    def __init__(self, callback: Callable, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._callback = callback
        self.delivered.connect(self._invoke, type=Qt.ConnectionType.QueuedConnection)

    def emit_result(self, result) -> None:
        self.delivered.emit(result)

    def _invoke(self, result) -> None:
        try:
            self._callback(result if result is not None else [])
        except TypeError:
            self._callback(result)
        self.deleteLater()


def fetch_labymod_versions() -> list:
    import spectrum_core.labymod as labymod

    try:
        return list(labymod.get_versions())
    except Exception:
        return []


def fetch_minecraft_versions(
    show_snapshot: bool,
    show_old: bool,
    show_release: bool,
    bmclapi: bool,
) -> list:
    import spectrum_core.download_funcs as downloader

    try:
        return list(
            downloader.get_version_list(
                show_snapshot,
                show_old,
                show_release,
                bmclapi,
            )
        )
    except Exception:
        return []


def run_in_pool(
    executor,
    fn: Callable,
    on_result: Callable,
    parent: QObject | None = None,
) -> None:
    """在线程池执行 fn，完成后于 Qt 主线程调用 on_result。"""

    deliverer = _MainThreadDeliverer(on_result, parent=parent)

    def _done(future) -> None:
        try:
            result = future.result()
        except Exception:
            result = None
        deliverer.emit_result(result)

    executor.submit(fn).add_done_callback(_done)
