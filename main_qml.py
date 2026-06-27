#!/usr/bin/env python3
"""兼容入口 — 请使用 python main.py。"""

from __future__ import annotations

import sys

from main import run_qml_ui

if __name__ == "__main__":
    sys.exit(run_qml_ui())
