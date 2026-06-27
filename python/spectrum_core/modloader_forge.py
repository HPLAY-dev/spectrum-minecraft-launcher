"""Forge ModLoader — BMCLAPI 版本列表 + Rust 安装"""

from __future__ import annotations

import requests

from spectrum_core import rust_available, require_native

_FORGE_BASE = "https://bmclapi2.bangbang93.com/forge/minecraft"


def get_all_forgeable_versions():
    resp = requests.get(_FORGE_BASE, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Request Fail: {resp.status_code}\nurl: {_FORGE_BASE}")
    return resp.json()


def get_forge_version(mcversion):
    url = f"{_FORGE_BASE}/{mcversion}"
    resp = requests.get(url, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Request Fail: {resp.status_code}\nurl: {url}")
    return resp.json()


if rust_available():
    _r = require_native()

    def download_forge_json(
        minecraft_dir,
        mcversion,
        instance_name,
        forge_version="latest",
        bmclapi=False,
        java="java",
    ):
        fv = None if forge_version in ("latest", None) else forge_version
        return _r.download_forge_json(
            minecraft_dir,
            mcversion,
            instance_name,
            fv,
            bmclapi,
            java,
        )

else:

    def download_forge_json(*args, **kwargs):
        from spectrum_core.py_fallback.modloader_forge import (
            download_forge_json as _fn,
        )

        return _fn(*args, **kwargs)
