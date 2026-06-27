"""工具函数 — Rust 优先"""

from __future__ import annotations

from spectrum_core import rust_available, require_native

if rust_available():
    _r = require_native()

    def native():
        return _r.native_os_py()

    def maven_to_path(maven_str):
        return _r.maven_to_path_py(maven_str)

    def get_architecture(*args, **kwargs):
        from mclauncher_core.tool_funcs import get_architecture as _fn

        return _fn(*args, **kwargs)

    def get_architecture_key(*args, **kwargs):
        from mclauncher_core.tool_funcs import get_architecture_key as _fn

        return _fn(*args, **kwargs)

    def get_system_bits(*args, **kwargs):
        from mclauncher_core.tool_funcs import get_system_bits as _fn

        return _fn(*args, **kwargs)

    def get_file_path(*args, **kwargs):
        from mclauncher_core.tool_funcs import get_file_path as _fn

        return _fn(*args, **kwargs)

else:
    from mclauncher_core.tool_funcs import *  # noqa: F403
