"""MC Launcher — Python 桥接层（Rust 优先，py_fallback 回退）。"""

from __future__ import annotations

import importlib
import os
from typing import Any

_USE_RUST = os.environ.get("MC_USE_RUST", "1").lower() not in ("0", "false", "no")
_native: Any | None = None


def rust_available() -> bool:
    if not _USE_RUST:
        return False
    try:
        import mc_core._mc_core  # noqa: F401

        return True
    except ImportError:
        return False


def require_native() -> Any:
    global _native
    if _native is None:
        _native = importlib.import_module("mc_core._mc_core")
    return _native
