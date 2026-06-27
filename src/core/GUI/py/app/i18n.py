"""国际化工具。"""

from __future__ import annotations

import json
from pathlib import Path


class I18n:
    def __init__(self, lang_dir: Path, locale: str = "zh_cn") -> None:
        self._strings: dict[str, str] = {}
        path = lang_dir / f"{locale}.json"
        if path.exists():
            self._strings = json.loads(path.read_text(encoding="utf-8"))

    def string(self, key: str, default: str = "") -> str:
        return self._strings.get(key, default or key)
