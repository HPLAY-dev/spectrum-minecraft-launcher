"""Java — Rust 优先（tuna 与 GitHub Adoptium API）"""

from __future__ import annotations

import platform

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

    def get_url(
        java_major_version,
        java_type,
        arch=None,
        platform_name=None,
        file_type=".msi",
        tuna=False,
    ):
        url = _r.get_java_download_url(int(java_major_version), java_type, tuna)
        if url is None:
            raise RuntimeError(
                f"未找到 Java {java_major_version} {java_type} 下载地址"
            )
        return url

    def get_arch():
        arch = platform.machine().lower()
        replacer = {"amd64": "x64"}
        for key, value in replacer.items():
            arch = arch.replace(key, value)
        return arch

else:
    from spectrum_core.py_fallback.java import *  # noqa: F403
