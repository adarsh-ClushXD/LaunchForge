from __future__ import annotations

import os
import sys

from PySide6.QtGui import QIcon


def _icons_dir() -> str:
    # PyInstaller sets sys._MEIPASS to the temp extracted dir
    if hasattr(sys, '_MEIPASS'):
        root = sys._MEIPASS
    else:
        # assets/icons/ relative to project root
        here = os.path.dirname(os.path.abspath(__file__))
        root = os.path.abspath(os.path.join(here, ".."))
    return os.path.join(root, "assets", "icons")


def icon_path(filename: str) -> str:
    return os.path.join(_icons_dir(), filename)


def load_icon(filename: str) -> QIcon:
    p = icon_path(filename)
    if os.path.exists(p):
        return QIcon(p)
    return QIcon()

