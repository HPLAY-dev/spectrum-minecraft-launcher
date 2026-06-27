"""本地 fonts/ 目录字体注册。"""

from __future__ import annotations

import os

from PySide6.QtCore import QUrl
from PySide6.QtGui import QFontDatabase

# 相对 fonts/ 的路径
LOCAL_FONT_FILES = (
    "Playfair_Display/static/PlayfairDisplay-Bold.ttf",
    "Lora/static/Lora-Regular.ttf",
    "SiYuanSongTiRegular/SourceHanSerifCN-Regular-1.otf",
    "SiYuanSongTiRegular/SourceHanSerifCN-SemiBold-7.otf",
    "SiYuanSongTiRegular/SourceHanSerifCN-Bold-2.otf",
)


def fonts_directory(app_path: str) -> str:
    return os.path.join(app_path, "fonts")


def fonts_dir_url(app_path: str) -> str:
    return QUrl.fromLocalFile(fonts_directory(app_path) + os.sep).toString()


def register_local_fonts(app_path: str) -> int:
    """注册 fonts/ 下的 TTF/OTF，供 QSS / Widget 使用。返回成功数量。"""
    loaded = 0
    for rel in LOCAL_FONT_FILES:
        path = os.path.join(fonts_directory(app_path), rel.replace("/", os.sep))
        if os.path.isfile(path) and QFontDatabase.addApplicationFont(path) >= 0:
            loaded += 1
    return loaded
