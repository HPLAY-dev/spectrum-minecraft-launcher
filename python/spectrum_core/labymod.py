"""LabyMod 4 — Rust 优先"""

from __future__ import annotations

from spectrum_core import rust_available, require_native

if rust_available():
    _r = require_native()

    def get_versions():
        return _r.get_labymod_versions()

    def download(minecraftDirectory, version, mcversion: str, instance_name):
        return _r.labymod_download(
            minecraftDirectory, int(version), mcversion, instance_name
        )

else:
    from spectrum_core.py_fallback.labymod import *  # noqa: F403
