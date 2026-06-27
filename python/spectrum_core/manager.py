"""实例管理 — Rust 优先"""

from __future__ import annotations

import os

from spectrum_core import rust_available, require_native

if rust_available():
    _r = require_native()

    get_saves = _r.get_saves
    get_mods = _r.get_mods
    get_resourcepacks = _r.get_resourcepacks
    get_shaderpacks = _r.get_shaderpacks
    remove_save = _r.remove_save
    remove_mod = _r.remove_mod
    remove_resourcepack = _r.remove_resourcepack
    remove_shaderpack = _r.remove_shaderpack
    rename_version = _r.rename_version
    list_instances = _r.list_instances

else:
    from spectrum_core.py_fallback.manager import *  # noqa: F403

    def list_instances(minecraft_dir):
        versions_dir = os.path.join(minecraft_dir, "versions")
        if not os.path.exists(versions_dir):
            return []
        return sorted(os.listdir(versions_dir))
