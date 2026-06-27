"""NeoForge ModLoader — BMCLAPI 版本列表（不依赖 mclauncher_core / bs4）"""

from __future__ import annotations

import importlib

import requests


def get_neoforge_version(mcversion):
    url = f"https://bmclapi2.bangbang93.com/neoforge/list/{mcversion}"
    resp = requests.get(url, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Request Fail: {resp.status_code}\nurl: {url}")
    return resp.json()


def _legacy():
    return importlib.import_module("mclauncher_core.modloader_neoforge")


def download_neoforge_json(*args, **kwargs):
    return _legacy().download_neoforge_json(*args, **kwargs)
