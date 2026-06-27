#!/usr/bin/env python3
"""SerenaLauncher — PySide6 + Qt6 QML 入口。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from app.bridge import AppBridge
from app.branding import load_branding


def main() -> int:
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Fusion")

    branding = load_branding()
    app = QGuiApplication(sys.argv)
    app.setApplicationName(branding.name)
    app.setApplicationDisplayName(branding.display_title)
    app.setApplicationVersion(branding.full_version)

    engine = QQmlApplicationEngine()
    bridge = AppBridge()

    engine.rootContext().setContextProperty("App", bridge)
    engine.rootContext().setContextProperty("Branding", branding.to_dict())
    engine.addImportPath(str(ROOT / "qml"))
    engine.load(QUrl.fromLocalFile(str(ROOT / "qml" / "main.qml")))

    if not engine.rootObjects():
        print("Failed to load QML", file=sys.stderr)
        return 1
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
