"""启动 — Rust 优先，回退 mclauncher_core.launcher_funcs"""

from __future__ import annotations

from spectrum_core import rust_available, require_native

if rust_available():
    _r = require_native()

    def launch(
        javaw,
        xmx,
        minecraft_dir,
        instance_name,
        username="steve",
        xmn="256M",
        ms_login=False,
        access_token=None,
        width=854,
        height=480,
        version_type="Launcher",
        jvm_args="",
        game_args_extend="",
        uuid=None,
        **_ignored,
    ):
        return _r.build_launch_script(
            javaw,
            xmx,
            minecraft_dir,
            instance_name,
            username,
            xmn,
            ms_login,
            access_token,
            width,
            height,
            version_type,
            jvm_args,
            game_args_extend,
            uuid,
        )

    def get_minecraft_version(minecraft_dir, instance_name):
        return _r.get_minecraft_version(minecraft_dir, instance_name)

    def get_required_java_version(minecraft_dir, instance_name):
        return _r.get_required_java_version(minecraft_dir, instance_name)

    def remove_version(minecraft_dir, instance_name):
        return _r.remove_version(minecraft_dir, instance_name)

    def native():
        return _r.native_os_py()

else:
    from mclauncher_core.launcher_funcs import *  # noqa: F403
