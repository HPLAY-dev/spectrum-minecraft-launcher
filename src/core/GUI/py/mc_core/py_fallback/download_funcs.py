"""纯 Python 回退实现。"""

from __future__ import annotations

import json
import urllib.request

_MANIFEST = "https://bmclapi2.bangbang93.com/mc/game/version_manifest_v2.json"


def get_version_list(show_snapshot=False, show_release=True, bmclapi=True):
    url = _MANIFEST if bmclapi else "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json"
    with urllib.request.urlopen(url, timeout=30) as resp:
        data = json.load(resp)
    versions = []
    for entry in data.get("versions", []):
        t = entry.get("type", "")
        if t == "release" and show_release:
            versions.append(entry["id"])
        elif t == "snapshot" and show_snapshot:
            versions.append(entry["id"])
    return versions
