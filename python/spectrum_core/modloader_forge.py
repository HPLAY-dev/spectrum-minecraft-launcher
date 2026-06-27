"""Forge ModLoader — BMCLAPI 版本列表（不依赖 mclauncher_core / bs4）"""

from __future__ import annotations

import importlib

import requests

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


def _legacy():
    return importlib.import_module("mclauncher_core.modloader_forge")


def download_forge_json(*args, **kwargs):
    return _legacy().download_forge_json(*args, **kwargs)
