"""NeoForge ModLoader — BMCLAPI 版本列表 + Rust 安装"""

from __future__ import annotations

import requests

from spectrum_core import rust_available, require_native


def get_neoforge_version(mcversion):
    url = f"https://bmclapi2.bangbang93.com/neoforge/list/{mcversion}"
    resp = requests.get(url, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Request Fail: {resp.status_code}\nurl: {url}")
    return resp.json()


if rust_available():
    _r = require_native()

    def download_neoforge_json(
        minecraft_dir,
        mcversion,
        instance_name,
        neoforge_version="latest",
        bmclapi=False,
        java="java",
    ):
        nv = None if neoforge_version in ("latest", None) else neoforge_version
        return _r.download_neoforge_json(
            minecraft_dir,
            mcversion,
            instance_name,
            nv,
            bmclapi,
            java,
        )

else:

    def download_neoforge_json(*args, **kwargs):
        from spectrum_core.py_fallback.modloader_neoforge import (
            download_neoforge_json as _fn,
        )

        return _fn(*args, **kwargs)
