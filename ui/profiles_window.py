from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.config_manager import ConfigManager
from core.models import Profile
from core.icons import load_icon
from ui.common import show_error, show_info


class ProfilesWindow(QWidget):
    changed = Signal()

    def __init__(self, cfg: ConfigManager, parent=None) -> None:
        super().__init__(parent)
        self._cfg = cfg

        self.setWindowTitle("Manage Profiles")
        ico = load_icon("profiles.png")
        if not ico.isNull():
            self.setWindowIcon(ico)
        self.setMinimumWidth(520)
        self.setMinimumHeight(380)

        self._list = QListWidget()
        self._list.setSelectionMode(QAbstractItemView.SingleSelection)

        self._active_label = QLabel("")

        self._add = QPushButton("New…")
        self._rename = QPushButton("Rename…")
        self._delete = QPushButton("Delete")
        self._set_active = QPushButton("Set Active")

        self._add.clicked.connect(self._on_add)
        self._rename.clicked.connect(self._on_rename)
        self._delete.clicked.connect(self._on_delete)
        self._set_active.clicked.connect(self._on_set_active)

        btns = QHBoxLayout()
        btns.addWidget(self._add)
        btns.addWidget(self._rename)
        btns.addWidget(self._delete)
        btns.addStretch(1)
        btns.addWidget(self._set_active)

        layout = QVBoxLayout()
        layout.addWidget(self._active_label)
        layout.addWidget(self._list, 1)
        layout.addLayout(btns)
        self.setLayout(layout)

        self._reload()

    def _reload(self) -> None:
        snap = self._cfg.snapshot()
        self._list.clear()
        self._active_label.setText(f"Active profile: {snap.active_profile}")

        for p in snap.profiles:
            item = QListWidgetItem(p.name)
            item.setData(0, p.name)
            self._list.addItem(item)

        # Select active by default
        for i in range(self._list.count()):
            if self._list.item(i).text() == snap.active_profile:
                self._list.setCurrentRow(i)
                break

    def _current_name(self) -> str | None:
        item = self._list.currentItem()
        return item.text() if item else None

    def _on_add(self) -> None:
        name, ok = _text_prompt(self, "New Profile", "Profile name:")
        if not ok:
            return
        name = name.strip()
        if not name:
            show_error(self, "Invalid", "Profile name cannot be empty.")
            return
        snap = self._cfg.snapshot()
        if any(p.name.lower() == name.lower() for p in snap.profiles):
            show_error(self, "Duplicate", "A profile with that name already exists.")
            return

        self._cfg.raw.setdefault("profiles", [])
        self._cfg.raw["profiles"].append(Profile(name=name, bindings=[]).to_dict())
        self._cfg.save()
        self.changed.emit()
        self._reload()

    def _on_rename(self) -> None:
        current = self._current_name()
        if not current:
            return
        new, ok = _text_prompt(self, "Rename Profile", "New name:", initial=current)
        if not ok:
            return
        new = new.strip()
        if not new:
            show_error(self, "Invalid", "Profile name cannot be empty.")
            return

        snap = self._cfg.snapshot()
        if any(p.name.lower() == new.lower() for p in snap.profiles if p.name != current):
            show_error(self, "Duplicate", "A profile with that name already exists.")
            return

        # Update profile name in raw config
        for p in self._cfg.raw.get("profiles", []):
            if isinstance(p, dict) and p.get("name") == current:
                p["name"] = new

        if snap.active_profile == current:
            self._cfg.set_active_profile(new)

        self._cfg.save()
        self.changed.emit()
        self._reload()

    def _on_delete(self) -> None:
        current = self._current_name()
        if not current:
            return
        snap = self._cfg.snapshot()
        if len(snap.profiles) <= 1:
            show_error(self, "Not allowed", "You must keep at least one profile.")
            return

        # Remove from raw config
        self._cfg.raw["profiles"] = [
            p for p in (self._cfg.raw.get("profiles") or []) if not (isinstance(p, dict) and p.get("name") == current)
        ]

        # If deleting active, set active to first remaining
        remaining = [p.get("name") for p in self._cfg.raw.get("profiles", []) if isinstance(p, dict) and p.get("name")]
        if snap.active_profile == current and remaining:
            self._cfg.set_active_profile(str(remaining[0]))

        self._cfg.save()
        self.changed.emit()
        self._reload()

    def _on_set_active(self) -> None:
        current = self._current_name()
        if not current:
            return
        self._cfg.set_active_profile(current)
        self._cfg.save()
        self.changed.emit()
        show_info(self, "Active profile", f"Active profile set to: {current}")
        self._reload()


def _text_prompt(parent: QWidget, title: str, label: str, initial: str = "") -> tuple[str, bool]:
    dlg = QDialog(parent)
    dlg.setWindowTitle(title)
    edit = QLineEdit()
    edit.setText(initial)
    form = QFormLayout()
    form.addRow(label, edit)
    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    buttons.accepted.connect(dlg.accept)
    buttons.rejected.connect(dlg.reject)
    layout = QVBoxLayout()
    layout.addLayout(form)
    layout.addWidget(buttons)
    dlg.setLayout(layout)
    ok = dlg.exec() == QDialog.Accepted
    return edit.text(), ok

