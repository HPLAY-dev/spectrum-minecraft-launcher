"""SerenaLauncher 品牌与版本信息。"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[5]
_VERSION_FILE = _REPO_ROOT / "config" / "version.json"


@dataclass(frozen=True)
class Branding:
    name: str
    codename: str
    major: int
    quarter: str
    build_id: str
    commit: str

    @property
    def full_version(self) -> str:
        return f"{self.major}{self.quarter}.{self.build_id}.{self.commit}"

    @property
    def display_title(self) -> str:
        return f"{self.name} {self.full_version}"

    @property
    def subtitle(self) -> str:
        return f"开发代号 {self.codename} · 大版本 {self.major}"

    def to_dict(self) -> dict[str, str | int]:
        return {
            "name": self.name,
            "codename": self.codename,
            "major": self.major,
            "quarter": self.quarter,
            "build_id": self.build_id,
            "commit": self.commit,
            "full_version": self.full_version,
            "display_title": self.display_title,
            "subtitle": self.subtitle,
        }


def _git_commit_short() -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(_REPO_ROOT), "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        value = result.stdout.strip()
        return value or None
    except (OSError, subprocess.CalledProcessError):
        return None


def load_branding() -> Branding:
    data: dict = {}
    if _VERSION_FILE.exists():
        data = json.loads(_VERSION_FILE.read_text(encoding="utf-8-sig"))

    commit = _git_commit_short() or data.get("commit", "dev")
    return Branding(
        name=data.get("name", "SerenaLauncher"),
        codename=data.get("codename", "Okra"),
        major=int(data.get("major", 26)),
        quarter=str(data.get("quarter", "Q2")),
        build_id=str(data.get("build_id", "0")),
        commit=str(commit),
    )
