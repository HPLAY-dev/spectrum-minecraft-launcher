from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "src" / "core" / "GUI" / "py"
sys.path.insert(0, str(ROOT))

from mc_core.py_fallback import download_funcs  # noqa: E402


def test_get_version_list_fallback():
    versions = download_funcs.get_version_list(show_release=True, bmclapi=True)
    assert isinstance(versions, list)
    assert len(versions) > 0
