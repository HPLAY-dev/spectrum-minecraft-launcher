"""SerenaLauncher 品牌与版本信息。

版本号规格：年份.季度.buildId.commitId
  例：26.2.129.fcd4827
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass

# --- 固定发布信息 ---
PROJECT_NAME = "SerenaLauncher"
DISPLAY_NAME = "Serena Launcher"
CODENAME = "Okra"
TAGLINE = "新的开始"

# 年份.季度（不含 buildId / commitId）
VERSION_RELEASE = "26.2"
VERSION_YEAR = 26
VERSION_QUARTER = 2

GITHUB_REPO = "HPLAY-dev/spectrum-minecraft-launcher"


def _run_git(*args: str) -> str | None:
    try:
        proc = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        if proc.returncode == 0:
            out = (proc.stdout or "").strip()
            if out:
                return out
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def build_id() -> str:
    env = os.environ.get("SERENA_BUILD_ID", "").strip()
    if env:
        return env
    return _run_git("rev-list", "--count", "HEAD") or "0"


def commit_id() -> str:
    env = os.environ.get("SERENA_COMMIT_ID", "").strip()
    if env:
        return env
    return _run_git("rev-parse", "--short", "HEAD") or "dev"


def full_version() -> str:
    """完整版本：年份.季度.buildId.commitId"""
    return f"{VERSION_RELEASE}.{build_id()}.{commit_id()}"


@dataclass(frozen=True)
class BrandingInfo:
    project_name: str
    display_name: str
    codename: str
    tagline: str
    version_release: str
    build_id: str
    commit_id: str
    full_version: str
    in_game_version_type: str


def get_branding() -> BrandingInfo:
    bid = build_id()
    cid = commit_id()
    release = VERSION_RELEASE
    full = f"{release}.{bid}.{cid}"
    return BrandingInfo(
        project_name=PROJECT_NAME,
        display_name=DISPLAY_NAME,
        codename=CODENAME,
        tagline=TAGLINE,
        version_release=release,
        build_id=bid,
        commit_id=cid,
        full_version=full,
        in_game_version_type=f"§lSerena§r · {CODENAME} {release}",
    )


def branding_dict() -> dict:
    b = get_branding()
    return {
        "projectName": b.project_name,
        "displayName": b.display_name,
        "codename": b.codename,
        "tagline": b.tagline,
        "versionRelease": b.version_release,
        "buildId": b.build_id,
        "commitId": b.commit_id,
        "fullVersion": b.full_version,
        "versionSpec": "年份.季度.buildId.commitId",
        "githubRepo": GITHUB_REPO,
    }
