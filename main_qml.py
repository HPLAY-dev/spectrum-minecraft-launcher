#!/usr/bin/env python3
"""Spectrum Launcher — QML + QSS + Vue 新 UI 入口。"""

from __future__ import annotations

import os
import sys

if getattr(sys, "frozen", False):
    APP_PATH = os.path.dirname(sys.executable)
else:
    APP_PATH = os.path.dirname(os.path.abspath(__file__))

for p in (
    os.path.join(APP_PATH, "bazel-bin", "python"),
    os.path.join(APP_PATH, "python"),
):
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

try:
    from PySide6.QtWebEngineQuick import QtWebEngineQuick

    QtWebEngineQuick.initialize()
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False

from app.bridge import AppBridge, WebBridge
from app.local_fonts import fonts_dir_url, register_local_fonts


def _load_qss(app: QApplication) -> None:
    qss_path = os.path.join(APP_PATH, "themes", "spectrum.qss")
    if os.path.isfile(qss_path):
        with open(qss_path, encoding="utf-8") as f:
            app.setStyleSheet(f.read())


def run_qml_ui() -> int:
    from main import MainWindow, log, l18n, lang_path

    l18n.load_lang(path=lang_path)

    app = QApplication(sys.argv)
    register_local_fonts(APP_PATH)
    QQuickStyle.setStyle("Basic")
    _load_qss(app)

    backend = MainWindow()
    backend.hide()

    bridge = AppBridge(backend)
    web_bridge = WebBridge(backend)

    engine = QQmlApplicationEngine()

    def _on_qml_warnings(warnings):
        for w in warnings:
            log(f"QML: {w.toString()}", "FATAL", 0)

    engine.warnings.connect(_on_qml_warnings)
    engine.rootContext().setContextProperty("App", bridge)
    engine.rootContext().setContextProperty("Web", web_bridge)
    engine.rootContext().setContextProperty("hasWebEngine", HAS_WEBENGINE)
    engine.rootContext().setContextProperty("fontsDir", fonts_dir_url(APP_PATH))

    qml_dir = os.path.join(APP_PATH, "qml")
    engine.addImportPath(qml_dir)

    main_qml = os.path.join(qml_dir, "main.qml")
    engine.load(QUrl.fromLocalFile(main_qml))

    if not engine.rootObjects():
        log("QML 加载失败", "FATAL", 0)
        return 1

    log("QML UI started", "INIT", 1)
    return app.exec()


if __name__ == "__main__":
    sys.exit(run_qml_ui())
