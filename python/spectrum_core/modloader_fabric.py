"""Fabric ModLoader — Rust 优先"""

from __future__ import annotations

from spectrum_core import rust_available, require_native

if rust_available():
    _r = require_native()

    def get_fabric_versions():
        return _r.get_fabric_versions()

    def get_fabric_installer_versions():
        return get_fabric_versions()

    def get_latest_fabric_loader_version():
        versions = get_fabric_versions()
        return versions[-1] if versions else ""

    def download_fabric_api(
        minecraft_dir, mcversion, instance_name, mod_version="latest"
    ):
        mv = None if mod_version in ("latest", None) else mod_version
        return _r.download_fabric_api(
            minecraft_dir, mcversion, instance_name, mv
        )

    def is_fabric(minecraft_dir, instance_name) -> bool:
        import os

        path = os.path.join(
            minecraft_dir, "versions", instance_name, f"{instance_name}.json"
        )
        with open(path, encoding="utf-8") as f:
            return "fabric-loader" in f.read()

else:
    from spectrum_core.py_fallback.modloader_fabric import *  # noqa: F403
