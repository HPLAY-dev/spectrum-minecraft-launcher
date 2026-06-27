"""Java — Rust 优先；get_url 仍走 Python（清华镜像页面解析）"""

from __future__ import annotations

from spectrum_core import rust_available, require_native

if rust_available():
    _r = require_native()

    def get_java_version(java_binary_path, detailed=False):
        major = _r.get_java_version(java_binary_path)
        if detailed:
            return major, str(major)
        return major

    def find_javas():
        return _r.find_javas()

    def get_url(*args, **kwargs):
        from mclauncher_core.java import get_url as _get_url

        return _get_url(*args, **kwargs)

    def get_arch(*args, **kwargs):
        from mclauncher_core.java import get_arch as _get_arch

        return _get_arch(*args, **kwargs)

else:
    from mclauncher_core.java import *  # noqa: F403
