"""JavaWrapper.jar 下载 — Rust 未覆盖时的 Python 实现"""

from __future__ import annotations

from spectrum_core import rust_available

if rust_available():
    import requests

    def download_javawrapper() -> None:
        url = (
            "https://gitlab.com/HPLAY-dev/javawrapper-binary/-/raw/main/"
            "JavaWrapper.jar?inline=false"
        )
        resp = requests.get(url, timeout=60)
        if resp.status_code != 200:
            raise RuntimeError("Connection error while downloading javawrapper")
        with open("JavaWrapper.jar", "wb") as f:
            f.write(resp.content)

else:
    from spectrum_core.py_fallback.javawrapper import download_javawrapper  # noqa: F401
