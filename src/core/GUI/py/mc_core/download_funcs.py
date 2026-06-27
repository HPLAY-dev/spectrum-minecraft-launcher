"""下载模块 — Rust 优先。"""

from __future__ import annotations

from mc_core import rust_available, require_native

if rust_available():
    _r = require_native()

    def get_version_list(show_snapshot=False, show_release=True, bmclapi=True):
        return _r.get_version_list(show_snapshot, show_release, bmclapi)

else:
    from mc_core.py_fallback.download_funcs import get_version_list  # noqa: F401
