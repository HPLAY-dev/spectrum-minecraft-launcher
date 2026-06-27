"""Minecraft 版本 ↔ Java 运行时策略（最低版本、架构、模组兼容警告）。"""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from typing import Iterable, Literal

ModLoaderKind = Literal["vanilla", "fabric", "forge", "neoforge"]

LTS_MAJORS = frozenset({8, 11, 17, 21, 25})


@dataclass
class JavaRuntimeInfo:
    path: str
    major: int
    full_version: str = ""
    is_64bit: bool = True
    is_jre: bool = False

    @property
    def is_lts(self) -> bool:
        return self.major in LTS_MAJORS


@dataclass
class InstanceJavaContext:
    mc_version: str
    modloader: ModLoaderKind
    java8_only: bool = False
    uses_launchwrapper: bool = False
    min_java: int = 8


def normalize_mc_version(raw: str) -> str:
    """从实例 id / 版本 id 中提取可比较的 Minecraft 版本号。"""
    if not raw:
        return raw
    v = raw.strip()
    v = re.split(r"[-+]", v, maxsplit=1)[0]
    lower = v.lower()
    for suffix in ("neoforge", "fabric", "forge", "optifine", "nf"):
        if lower.endswith(suffix) and len(v) > len(suffix):
            base = v[: -len(suffix)]
            if base and base[-1].isdigit():
                v = base
                break
    m = re.match(
        r"^(\d+w\d+[a-z]?|\d+\.\d+(?:\.\d+)?|\d{2,}(?:\.\d+)*)",
        v.lower(),
    )
    return m.group(1) if m else v.strip()


@dataclass
class JavaValidation:
    blocked: bool = False
    block_reason: str = ""
    warning: str = ""


def _run_java_version(java_path: str) -> str:
    try:
        proc = subprocess.run(
            [java_path, "-version"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        return (proc.stderr or "") + (proc.stdout or "")
    except OSError:
        return ""


def inspect_java(java_path: str, major: int | None = None) -> JavaRuntimeInfo | None:
    from spectrum_core import java as java_mod

    output = _run_java_version(java_path)
    if major is None:
        try:
            major = java_mod.get_java_version(java_path)
        except Exception:
            return None
    if not major:
        return None

    low = output.lower()
    if "64-bit" in low or "64-bit" in output or "64-Bit" in output:
        is_64bit = True
    elif "32-bit" in low or "32-Bit" in output:
        is_64bit = False
    elif "x86_64" in low or "amd64" in low:
        is_64bit = True
    elif re.search(r"\bx86\b", low) and "x86_64" not in low:
        is_64bit = False
    else:
        is_64bit = "programfiles(x86)" not in java_path.lower()

    full = ""
    m = re.search(r'"([\d._]+)"', output)
    if m:
        full = m.group(1)

    is_jre = "jre" in low or "runtime environment" in low
    return JavaRuntimeInfo(
        path=java_path,
        major=int(major),
        full_version=full,
        is_64bit=is_64bit,
        is_jre=is_jre,
    )


def parse_mc_version_key(mc_version: str) -> tuple:
    """返回可比较的 5 元组。type: 0=1.x, 1=weekly snapshot, 2=26+。"""
    v = mc_version.strip().lower()
    if not v:
        return (0, 0, 0, 0, 0)

    m = re.match(r"^(\d+)w(\d+)([a-z])?$", v)
    if m:
        letter = ord(m.group(3)) if m.group(3) else ord("a")
        return (1, int(m.group(1)), int(m.group(2)), letter, 0)

    m = re.match(r"^(\d+)\.(\d+)", v)
    if m and int(m.group(1)) >= 26:
        return (2, int(m.group(1)), int(m.group(2)), 0, 0)

    pre_num = 0
    is_pre = False
    pre_m = re.search(r"-pre(\d+)", v)
    if pre_m:
        is_pre = True
        pre_num = int(pre_m.group(1))

    base = re.split(r"[-+]", v)[0]
    parts = base.split(".")
    if parts[0] == "1" and len(parts) >= 2:
        try:
            minor = int(parts[1])
        except ValueError:
            return (0, 0, 0, 0, 0)
        patch = 0
        if len(parts) > 2:
            pm = re.match(r"^(\d+)", parts[2])
            patch = int(pm.group(1)) if pm else 0
        release_rank = 1 if is_pre else 2
        return (0, minor, patch, release_rank, pre_num)

    return (0, 0, 0, 0, 0)


def mc_version_ge(a: str, b: str) -> bool:
    return parse_mc_version_key(a) >= parse_mc_version_key(b)


def get_min_java(mc_version: str) -> int:
    v = normalize_mc_version(mc_version.strip())
    if not v:
        return 8

    if mc_version_ge(v, "26.1") or re.match(r"^26\.", v.lower()):
        return 25

    if mc_version_ge(v, "24w14a") or mc_version_ge(v, "1.20.5"):
        return 21

    if mc_version_ge(v, "1.18-pre2"):
        return 17

    if mc_version_ge(v, "21w19a") or mc_version_ge(v, "1.17"):
        return 16

    return 8


def requires_64bit_java(mc_version: str) -> bool:
    return mc_version_ge(mc_version, "24w14a") or mc_version_ge(mc_version, "1.20.5")


def detect_modloader(minecraft_dir: str, instance_name: str) -> ModLoaderKind:
    data = _read_instance_json(minecraft_dir, instance_name)
    if data:
        main_class = str(data.get("mainClass", "")).lower()
        lib_text = " ".join(
            lib if isinstance(lib, str) else lib.get("name", "")
            for lib in data.get("libraries", [])
            if isinstance(lib, (str, dict))
        ).lower()
        if "bootstraplauncher" in main_class or "net.neoforged" in lib_text:
            return "neoforge"
        if "knotclient" in main_class or "fabric-loader" in lib_text:
            return "fabric"
        if "modlauncher" in main_class or "launchwrapper" in main_class:
            return "forge"
        if "labymod" in lib_text:
            return "labymod"  # type: ignore[return-value]

    name = instance_name.lower()
    if "neoforge" in name or name.endswith("nf"):
        return "neoforge"
    if "forge" in name:
        return "forge"
    try:
        from spectrum_core import modloader_fabric as fabric

        if fabric.is_fabric(minecraft_dir, instance_name):
            return "fabric"
    except Exception:
        pass
    return "vanilla"


def _read_instance_json(minecraft_dir: str, instance_name: str) -> dict | None:
    base = os.path.join(minecraft_dir, "versions", instance_name)
    for name in (f"{instance_name}.json", "version.json"):
        path = os.path.join(base, name)
        if os.path.isfile(path):
            try:
                with open(path, encoding="utf-8") as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError):
                pass
    return None


def instance_uses_launchwrapper(minecraft_dir: str, instance_name: str) -> bool:
    data = _read_instance_json(minecraft_dir, instance_name)
    if not data:
        return False

    main_class = str(data.get("mainClass", "")).lower()
    if "launchwrapper" in main_class:
        return True

    libraries = data.get("libraries", [])
    for lib in libraries:
        if isinstance(lib, str):
            name = lib
        elif isinstance(lib, dict):
            name = lib.get("name", "")
        else:
            name = ""
        if "launchwrapper" in name.lower():
            return True
    return False


def requires_java8_only(
    minecraft_dir: str,
    instance_name: str,
    mc_version: str,
    modloader: ModLoaderKind,
) -> bool:
    if instance_uses_launchwrapper(minecraft_dir, instance_name):
        return True
    if not mc_version_ge(mc_version, "1.13"):
        return True
    if modloader == "forge" and _forge_java8_only(mc_version):
        return True
    return False


def build_instance_context(minecraft_dir: str, instance_name: str) -> InstanceJavaContext:
    mc_version = normalize_mc_version(instance_name)
    json_min: int | None = None
    try:
        import spectrum_core.launcher_funcs as launcher

        mc_version = normalize_mc_version(
            launcher.get_minecraft_version(minecraft_dir, instance_name)
        )
        try:
            json_min = int(launcher.get_required_java_version(minecraft_dir, instance_name))
            if json_min <= 0:
                json_min = None
        except Exception:
            json_min = None
    except Exception:
        pass

    modloader = detect_modloader(minecraft_dir, instance_name)
    uses_lw = instance_uses_launchwrapper(minecraft_dir, instance_name)
    java8_only = requires_java8_only(minecraft_dir, instance_name, mc_version, modloader)
    if java8_only:
        min_java = 8
    else:
        min_java = max(get_min_java(mc_version), json_min or 0)
    return InstanceJavaContext(
        mc_version=mc_version,
        modloader=modloader,
        java8_only=java8_only,
        uses_launchwrapper=uses_lw,
        min_java=min_java,
    )


def _forge_java8_only(mc_version: str) -> bool:
    if not mc_version_ge(mc_version, "1.12"):
        return mc_version_ge(mc_version, "1.7.10") or mc_version_ge(mc_version, "1.7")
    return mc_version_ge(mc_version, "1.12") and not mc_version_ge(mc_version, "1.17")


def validate_java(
    ctx: InstanceJavaContext,
    runtime: JavaRuntimeInfo,
) -> JavaValidation:
    mc_version = ctx.mc_version
    modloader = ctx.modloader
    min_java = ctx.min_java
    result = JavaValidation()

    if ctx.java8_only and runtime.major != 8:
        reason = (
            f"此实例（MC {mc_version}）仅支持 Java 8。"
            if not ctx.uses_launchwrapper
            else (
                f"此实例使用 LaunchWrapper（MC {mc_version}），"
                f"Java {runtime.major} 无法启动（与旧版 ClassLoader 不兼容）。"
                "请安装 Java 8 并在设置中添加 java.exe。"
            )
        )
        result.blocked = True
        result.block_reason = reason
        return result

    if runtime.major < min_java:
        result.blocked = True
        result.block_reason = (
            f"Java 版本过低：当前 Java {runtime.major}，"
            f"运行 Minecraft {mc_version} 至少需要 Java {min_java}。"
        )
        return result

    if requires_64bit_java(mc_version) and not runtime.is_64bit:
        result.blocked = True
        result.block_reason = (
            f"Minecraft {mc_version} 不支持 32 位 Java，请安装并使用 64 位 Java {min_java} 或更高版本。"
        )
        return result

    if (
        modloader == "forge"
        and _forge_java8_only(mc_version)
        and runtime.major > 8
        and not ctx.java8_only
    ):
        result.warning = (
            f"Forge 模组包（MC {mc_version}）通常仅兼容 Java 8，"
            f"使用 Java {runtime.major} 可能导致启动失败。"
        )
    elif (
        modloader == "forge"
        and mc_version_ge(mc_version, "1.7.10")
        and not mc_version_ge(mc_version, "1.12")
        and runtime.major > 8
    ):
        result.warning = (
            f"Forge 1.7.10–1.11 在 Java 8 上最稳定，Java {runtime.major} 存在崩溃风险。"
        )
    elif mc_version_ge(mc_version, "1.17") and not mc_version_ge(mc_version, "1.18-pre2") and runtime.major > 16:
        result.warning = (
            "部分 1.17 旧 Fabric 模组仅适配 Java 16，使用更高版本 Java 可能闪退。"
        )

    if not runtime.is_64bit:
        warn32 = "32 位 Java 最大堆内存通常仅约 1024MB，游戏极易卡顿。"
        result.warning = f"{result.warning}\n{warn32}".strip() if result.warning else warn32

    return result


def _sort_key_for_mc(ctx: InstanceJavaContext, runtime: JavaRuntimeInfo) -> tuple:
    if ctx.java8_only:
        return (
            0 if runtime.major == 8 else 1,
            0 if runtime.is_64bit else 1,
            runtime.path.lower(),
        )
    min_java = ctx.min_java
    lts_rank = 0 if runtime.is_lts else 1
    match_dist = abs(runtime.major - min_java)
    arch_rank = 0 if runtime.is_64bit else 1
    return (arch_rank, lts_rank, match_dist, runtime.major)


def rank_javas(
    ctx: InstanceJavaContext,
    runtimes: Iterable[JavaRuntimeInfo],
) -> list[tuple[JavaRuntimeInfo, JavaValidation]]:
    items: list[tuple[JavaRuntimeInfo, JavaValidation]] = []
    for rt in runtimes:
        items.append((rt, validate_java(ctx, rt)))
    items.sort(key=lambda x: (_sort_key_for_mc(ctx, x[0]), x[0].path.lower()))
    return items


def format_java_label(
    runtime: JavaRuntimeInfo,
    *,
    recommended: bool = False,
    blocked: bool = False,
    block_reason: str = "",
) -> str:
    bits = "64位" if runtime.is_64bit else "32位"
    lts = " LTS" if runtime.is_lts else ""
    tag = " [推荐]" if recommended else ""
    ver = runtime.full_version or str(runtime.major)
    if blocked:
        short = block_reason.split("。")[0] if block_reason else "不兼容"
        return f"Java {runtime.major} ({bits}) — 不可用：{short}"
    return f"Java {runtime.major} ({bits}{lts}) — {ver}{tag}"


def pick_java(
    ctx: InstanceJavaContext,
    runtimes: Iterable[JavaRuntimeInfo],
    preferred_path: str | None = None,
) -> tuple[JavaRuntimeInfo | None, JavaValidation | None]:
    ranked = rank_javas(ctx, runtimes)
    if not ranked:
        need = ctx.min_java
        return None, JavaValidation(
            blocked=True,
            block_reason=(
                f"未找到 Java 8。此实例仅支持 Java 8，请安装并在设置中添加 java.exe。"
                if ctx.java8_only
                else f"未找到任何 Java 安装。运行 Minecraft {ctx.mc_version} 至少需要 Java {need}。"
            ),
        )

    if preferred_path:
        pref = preferred_path.replace("\\", "/")
        for rt, val in ranked:
            if rt.path.replace("\\", "/") == pref and not val.blocked:
                return rt, val

    for rt, val in ranked:
        if not val.blocked:
            return rt, val

    return ranked[0][0], ranked[0][1]


def java_options_payload(
    ctx: InstanceJavaContext,
    runtimes: Iterable[JavaRuntimeInfo],
) -> list[dict]:
    min_java = ctx.min_java
    ranked = rank_javas(ctx, runtimes)
    options: list[dict] = []
    best_path = None
    for rt, val in ranked:
        if not val.blocked and best_path is None:
            best_path = rt.path
        is_rec = rt.path == best_path and not val.blocked
        options.append(
            {
                "path": rt.path,
                "major": rt.major,
                "label": format_java_label(
                    rt,
                    recommended=is_rec,
                    blocked=val.blocked,
                    block_reason=val.block_reason,
                ),
                "is64bit": rt.is_64bit,
                "isLts": rt.is_lts,
                "recommended": is_rec,
                "enabled": not val.blocked,
                "blocked": val.blocked,
                "blockReason": val.block_reason,
                "warning": val.warning,
                "java8Only": ctx.java8_only,
                "minJava": min_java,
                "modloader": ctx.modloader,
            }
        )
    if options and all(o["blocked"] for o in options):
        hint = (
            "此实例仅支持 Java 8（LaunchWrapper/旧版 Forge）。"
            if ctx.java8_only
            else f"未检测到满足 Java {min_java}+ 的运行时。"
        )
        options.append(
            {
                "path": "",
                "major": min_java,
                "label": "需要 Java 8" if ctx.java8_only else f"需要 Java {min_java}+",
                "enabled": False,
                "blocked": True,
                "blockReason": hint + " 请安装后在设置中扫描或添加 java.exe。",
                "warning": "",
                "recommended": False,
                "is64bit": True,
                "isLts": min_java in LTS_MAJORS,
                "java8Only": ctx.java8_only,
            }
        )
    elif not options:
        options.append(
            {
                "path": "",
                "major": min_java,
                "label": f"需要 Java {min_java}+",
                "enabled": False,
                "blocked": True,
                "blockReason": f"未检测到可用 Java，请安装 Java {min_java} 或更高版本。",
                "warning": "",
                "recommended": False,
                "is64bit": True,
                "isLts": min_java in LTS_MAJORS,
                "java8Only": ctx.java8_only,
            }
        )
    return options
