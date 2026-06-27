"""工具函数 — Rust 优先"""

from __future__ import annotations

import os
import sys

from spectrum_core import rust_available, require_native

if rust_available():
    _r = require_native()

    def native():
        return _r.native_os_py()

    def maven_to_path(maven_str):
        return _r.maven_to_path_py(maven_str)

    def get_architecture():
        return _r.get_architecture_py()

    def get_architecture_key():
        return _r.get_architecture_key_py()

    def get_system_bits():
        return _r.get_system_bits_py()

    def get_file_path() -> str:
        if getattr(sys, "frozen", False):
            return os.path.dirname(sys.executable).replace("\\", "/")
        return os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")

else:
    from spectrum_core.py_fallback.tool_funcs import *  # noqa: F403
