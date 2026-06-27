"""Modrinth API v2 — https://docs.modrinth.com/api/"""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote

import requests

BASE_URL = "https://api.modrinth.com/v2"
USER_AGENT = (
    "CHENs/spectrum-minecraft-launcher/1.0 "
    "(https://github.com/hplay-dev/spectrum-minecraft-launcher)"
)


def _headers() -> dict[str, str]:
    return {"User-Agent": USER_AGENT, "Accept": "application/json"}


def _get(path: str, **params: Any) -> Any:
    resp = requests.get(
        f"{BASE_URL}{path}",
        params=params or None,
        headers=_headers(),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def search(
    query: str,
    *,
    loader: str | None = None,
    game_version: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """GET /v2/search — 搜索模组项目。"""
    query = (query or "").strip()
    if len(query) <= 2:
        return []

    facets: list[list[str]] = [["project_type:mod"]]
    if loader:
        facets.append([f"categories:{loader.lower()}"])
    if game_version:
        facets.append([f"versions:{game_version}"])

    data = _get(
        "/search",
        query=query,
        limit=limit,
        index="relevance",
        facets=json.dumps(facets, separators=(",", ":")),
    )
    return list(data.get("hits", []))


def list_compatible_versions(
    project_id: str,
    *,
    loader: str,
    game_version: str,
) -> list[dict[str, Any]]:
    """GET /v2/project/{id}/version — 按加载器与游戏版本筛选。"""
    loaders = json.dumps([loader.lower()])
    versions = json.dumps([game_version])
    return _get(
        f"/project/{quote(project_id, safe='')}/version",
        loaders=loaders,
        game_versions=versions,
    )


def install_mod(
    project_id: str,
    *,
    loader: str,
    game_version: str,
    mods_dir: str,
) -> str:
    """下载并安装与实例兼容的最新 Modrinth 版本，返回文件名。"""
    import os

    versions = list_compatible_versions(
        project_id, loader=loader, game_version=game_version
    )
    if not versions:
        raise RuntimeError("未找到兼容的 Modrinth 版本")

    ver = versions[0]
    files = ver.get("files") or []
    if not files:
        raise RuntimeError("Modrinth 版本没有可下载文件")

    primary = next((f for f in files if f.get("primary")), files[0])
    url = primary.get("url")
    filename = primary.get("filename")
    if not url or not filename:
        raise RuntimeError("Modrinth 文件信息不完整")

    os.makedirs(mods_dir, exist_ok=True)
    dest = os.path.join(mods_dir, filename)
    with requests.get(url, headers=_headers(), stream=True, timeout=120) as resp:
        resp.raise_for_status()
        with open(dest, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=65536):
                if chunk:
                    fh.write(chunk)
    return filename
