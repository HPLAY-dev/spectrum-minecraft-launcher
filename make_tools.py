"""Resolve PySide6/Nuitka CLI tools when Scripts/ is not on PATH."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import sysconfig

TOOLS = {
    "uic": {"cli": "pyside6-uic", "pip": "PySide6", "module": None},
    "nuitka": {"cli": "nuitka", "pip": "nuitka", "module": "nuitka"},
}


def find_tool(name: str) -> list[str]:
    spec = TOOLS[name]
    cli_name = spec["cli"]
    candidates = (f"{cli_name}.exe", cli_name) if os.name == "nt" else (cli_name,)
    for candidate in candidates:
        path = shutil.which(candidate)
        if path:
            return [path]
    scripts = sysconfig.get_path("scripts")
    for candidate in candidates:
        path = os.path.join(scripts, candidate)
        if os.path.isfile(path):
            return [path]
    if spec["module"]:
        try:
            __import__(spec["module"])
        except ImportError:
            pass
        else:
            return [sys.executable, "-m", spec["module"]]
    raise SystemExit(f"{cli_name} not found. Install: pip install {spec['pip']}")


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in TOOLS:
        names = ", ".join(TOOLS)
        raise SystemExit(f"usage: {sys.argv[0]} {{{names}}} [args...]")
    cmd = find_tool(sys.argv[1]) + sys.argv[2:]
    subprocess.check_call(cmd)


if __name__ == "__main__":
    main()
