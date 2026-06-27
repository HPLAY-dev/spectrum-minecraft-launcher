"""集成测试公共工具。"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def setup_rust_env() -> None:
    os.environ.setdefault("SPECTRUM_USE_RUST", "1")
    bridge = str(ROOT / "python")
    if bridge not in sys.path:
        sys.path.insert(0, bridge)


def load_fixture(name: str) -> dict:
    with open(FIXTURES / name, encoding="utf-8") as f:
        return json.load(f)


def make_minecraft_dir(
    instance_name: str = "test-1.20.1",
    *,
    version_json: dict | None = None,
) -> Path:
    """创建临时 .minecraft 目录结构。"""
    tmp = Path(tempfile.mkdtemp(prefix="spectrum_it_"))
    inst = tmp / "versions" / instance_name
    inst.mkdir(parents=True)

    data = version_json if version_json is not None else load_fixture("test_instance.json")
    data.setdefault("id", instance_name)
    json_path = inst / f"{instance_name}.json"
    json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    (inst / "saves" / "world_alpha").mkdir(parents=True)
    (inst / "mods").mkdir(parents=True)
    (inst / "resourcepacks").mkdir(parents=True)
    (inst / "shaderpacks").mkdir(parents=True)
    (inst / "mods" / "example-mod.jar").write_bytes(b"")
    (inst / "resourcepacks" / "pack.zip").write_bytes(b"")
    (inst / "shaderpacks" / "shader.zip").write_bytes(b"")
    return tmp


def cleanup_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def network_enabled() -> bool:
    return os.environ.get("SPECTRUM_INTEGRATION_NETWORK", "1") != "0"
