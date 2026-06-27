from __future__ import annotations

import json

from PySide6.QtCore import QObject, Signal, Slot

from mc_core import download_funcs


class AppBridge(QObject):
    toast = Signal(str, str)
    versionsChanged = Signal()

    @Slot(result=str)
    def getVersionList(self) -> str:
        try:
            versions = download_funcs.get_version_list(show_release=True, bmclapi=True)
            return json.dumps(versions[:50])
        except Exception as exc:
            self.toast.emit(str(exc), "error")
            return "[]"

    @Slot()
    def refreshVersionList(self) -> None:
        self.versionsChanged.emit()
