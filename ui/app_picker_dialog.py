from __future__ import annotations

import os
from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from core.app_catalog import CatalogApp, build_catalog


@dataclass(frozen=True)
class AppShortcut:
    name: str
    shortcut_path: str


def _start_menu_roots() -> list[str]:
    roots: list[str] = []
    program_data = os.environ.get("PROGRAMDATA")
    app_data = os.environ.get("APPDATA")

    if program_data:
        roots.append(os.path.join(program_data, "Microsoft", "Windows", "Start Menu", "Programs"))
    if app_data:
        roots.append(os.path.join(app_data, "Microsoft", "Windows", "Start Menu", "Programs"))
    return [r for r in roots if os.path.isdir(r)]


def list_start_menu_apps() -> list[AppShortcut]:
    """
    Returns a list of Start Menu app shortcuts (.lnk / .url).
    We store shortcut paths and let Windows resolve them on launch.
    """
    shortcuts: list[AppShortcut] = []
    for root in _start_menu_roots():
        for dirpath, _, filenames in os.walk(root):
            for fn in filenames:
                lower = fn.lower()
                if not (lower.endswith(".lnk") or lower.endswith(".url")):
                    continue
                full = os.path.join(dirpath, fn)
                name = os.path.splitext(fn)[0]
                shortcuts.append(AppShortcut(name=name, shortcut_path=full))

    # Sort for stable UX (name, then path)
    shortcuts.sort(key=lambda s: (s.name.lower(), s.shortcut_path.lower()))
    return shortcuts


class AppPickerDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Pick an App (Installed Apps)")
        self.setMinimumWidth(720)
        self.setMinimumHeight(520)

        shortcuts = list_start_menu_apps()
        self._all: list[CatalogApp] = build_catalog([(s.name, s.shortcut_path) for s in shortcuts])
        self._selected: CatalogApp | None = None

        self._filter = QLineEdit()
        self._filter.setPlaceholderText("Search apps… (e.g. Chrome, VS Code, Spotify)")
        self._filter.textChanged.connect(self._apply_filter)

        self._list = QListWidget()
        self._list.itemSelectionChanged.connect(self._on_selection_changed)
        self._list.itemDoubleClicked.connect(lambda _: self.accept())

        self._hint = QLabel(
            "This list combines Start Menu shortcuts + Windows installed-app registry (Get-StartApps).\n"
            "If an app still isn’t listed, you can use “Add App…” to browse for an .exe."
        )
        self._hint.setStyleSheet("color: #9ca3af;")
        self._hint.setWordWrap(True)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        top = QHBoxLayout()
        top.addWidget(QLabel("Search"), 0)
        top.addWidget(self._filter, 1)

        layout = QVBoxLayout()
        layout.addLayout(top)
        layout.addWidget(self._list, 1)
        layout.addWidget(self._hint)
        layout.addWidget(buttons)
        self.setLayout(layout)

        self._apply_filter()

    def selected_app(self) -> CatalogApp | None:
        return self._selected

    def _apply_filter(self) -> None:
        text = self._filter.text().strip().lower()
        self._list.clear()

        for s in self._all:
            if text and text not in s.name.lower():
                continue
            suffix = " (Store/Packaged)" if s.kind == "aumid" else ""
            item = QListWidgetItem(f"{s.name}{suffix}")
            item.setToolTip(s.value)
            item.setData(Qt.UserRole, {"kind": s.kind, "value": s.value, "name": s.name})
            self._list.addItem(item)

        if self._list.count() > 0:
            self._list.setCurrentRow(0)

    def _on_selection_changed(self) -> None:
        items = self._list.selectedItems()
        if not items:
            self._selected = None
            return
        data = items[0].data(Qt.UserRole) or {}
        if not isinstance(data, dict):
            self._selected = None
            return
        kind = str(data.get("kind") or "")
        value = str(data.get("value") or "")
        name = str(data.get("name") or "")
        if kind and value and name:
            self._selected = CatalogApp(name=name, kind=kind, value=value)
        else:
            self._selected = None

