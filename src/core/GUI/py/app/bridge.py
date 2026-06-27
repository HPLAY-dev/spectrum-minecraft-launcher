from __future__ import annotations

import json

from PySide6.QtCore import QObject, Signal, Slot

from app.branding import load_branding
from mc_core import download_funcs


class AppBridge(QObject):
    toast = Signal(str, str)
    versionsChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._branding = load_branding()

    @Slot(result=str)
    def getBranding(self) -> str:
        return json.dumps(self._branding.to_dict(), ensure_ascii=False)

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
