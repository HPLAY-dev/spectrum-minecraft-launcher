"""下载 — Rust 优先，回退 mclauncher_core.download_funcs"""

from __future__ import annotations

from spectrum_core import _native, rust_available, require_native

if rust_available():
    _r = require_native()

    def get_version_list(
        show_snapshot=False,
        show_old_alpha=False,
        show_old_beta=False,
        bmclapi=False,
    ):
        return _r.get_version_list(show_snapshot, show_old_alpha, show_old_beta, bmclapi)

    def auto_download(
        minecraft_dir,
        mcversion,
        instance_name,
        modloader="vanilla",
        bmclapi=False,
        modloader_version="latest",
        progress_callback=None,
        java="java",
    ):
        _r.auto_download(
            minecraft_dir,
            mcversion,
            instance_name,
            modloader,
            modloader_version if modloader_version != "latest" else None,
            bmclapi,
            progress_callback,
        )

    def native():
        return _r.native_os_py()

    def get_version_json(mcversion, bmclapi=False):
        return _r.get_version_json(mcversion, bmclapi)

else:
    from mclauncher_core.download_funcs import *  # noqa: F403
