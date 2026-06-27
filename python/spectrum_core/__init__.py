"""Spectrum Launcher — Rust/Python 混合核心桥接层。

环境变量:
  SPECTRUM_USE_RUST=1   启用 Rust 核心（默认）
  SPECTRUM_USE_RUST=0   回退到 mclauncher_core
"""

from __future__ import annotations

import os
import sys

USE_RUST = os.environ.get("SPECTRUM_USE_RUST", "1").lower() not in ("0", "false", "no")

_native = None
if USE_RUST:
    try:
        import _spectrum_core as _native  # Bazel / maturin 产物
    except ImportError:
        try:
            # 开发: cargo build 输出的 cdylib 复制到 PYTHONPATH
            from spectrum_core import _spectrum_core as _native  # type: ignore
        except ImportError:
            _native = None
else:
    _native = None


def rust_available() -> bool:
    return _native is not None


def require_native():
    if _native is None:
        raise RuntimeError(
            "Rust 核心未加载。请运行: bazel build //python:spectrum_core_native "
            "或 cargo build --features python -p spectrum_core"
        )
    return _native
