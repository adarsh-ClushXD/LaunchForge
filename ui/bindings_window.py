from __future__ import annotations

import uuid

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.config_manager import ConfigManager
from core.models import AppLaunchItem, KeyBinding, Profile
from core.icons import load_icon
from ui.app_picker_dialog import AppPickerDialog
from ui.capture_hotkey_dialog import CaptureHotkeyDialog
from ui.common import show_error, show_info
from ui.profiles_window import ProfilesWindow


class BindingEditorDialog(QDialog):
    def __init__(self, parent=None, binding: KeyBinding | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Key Binding")
        self.setMinimumWidth(640)

        self._binding = binding or KeyBinding(id=str(uuid.uuid4()), hotkey="")

        self._name = QLineEdit(self._binding.name)
        self._hotkey = QLineEdit(self._binding.hotkey)
        self._hotkey.setPlaceholderText("e.g. win+c, ctrl+alt+n")
        self._enabled = QCheckBox("Enabled")
        self._enabled.setChecked(self._binding.enabled)

        self._delay = QSpinBox()
        self._delay.setRange(0, 10000)
        self._delay.setSingleStep(50)
        self._delay.setValue(int(self._binding.delay_ms))

        self._apps = QListWidget()
        self._apps.setSelectionMode(QAbstractItemView.SingleSelection)
        for app in self._binding.apps:
            self._apps.addItem(self._make_app_item(app))

        self._add_app = QPushButton("Add App…")
        self._add_start_menu = QPushButton("Add from Start Menu…")
        self._remove_app = QPushButton("Remove")
        self._capture = QPushButton("Capture Hotkey…")

        self._add_app.clicked.connect(self._on_add_app)
        self._add_start_menu.clicked.connect(self._on_add_from_start_menu)
        self._remove_app.clicked.connect(self._on_remove_app)
        self._capture.clicked.connect(self._on_capture)

        form = QFormLayout()
        form.addRow("Name", self._name)

        hotkey_row = QHBoxLayout()
        hotkey_row.addWidget(self._hotkey, 1)
        hotkey_row.addWidget(self._capture)
        form.addRow("Hotkey", hotkey_row)

        form.addRow("", self._enabled)
        form.addRow("Delay between apps (ms)", self._delay)

        apps_box = QVBoxLayout()
        apps_box.addWidget(QLabel("Apps to launch (in order)"))
        apps_box.addWidget(self._apps, 1)

        apps_btns = QHBoxLayout()
        apps_btns.addWidget(self._add_app)
        apps_btns.addWidget(self._add_start_menu)
        apps_btns.addWidget(self._remove_app)
        apps_btns.addStretch(1)
        apps_box.addLayout(apps_btns)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(apps_box, 1)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def _format_app(self, app: AppLaunchItem) -> str:
        args = f" {app.args}" if app.args.strip() else ""
        return f"{app.path}{args}"

    def _make_app_item(self, app: AppLaunchItem) -> QListWidgetItem:
        item = QListWidgetItem(self._format_app(app))
        item.setData(Qt.UserRole, app.to_dict())
        item.setToolTip(app.path)
        return item

    def _on_add_app(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select App", "", "Executables (*.exe);;All Files (*.*)")
        if not path:
            return
        args, ok = _simple_text_prompt(self, "Arguments", "Optional arguments (leave blank if none):")
        if not ok:
            return
        app = AppLaunchItem(path=path, args=args.strip())
        self._apps.addItem(self._make_app_item(app))

    def _on_add_from_start_menu(self) -> None:
        dlg = AppPickerDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return
        s = dlg.selected_app()
        if not s:
            return
        if s.kind == "aumid":
            app = AppLaunchItem(kind="aumid", path=s.value, args="")
        else:
            # Launching .lnk/.url directly is supported by our action runner.
            app = AppLaunchItem(kind="shortcut", path=s.value, args="")
        self._apps.addItem(self._make_app_item(app))

    def _on_remove_app(self) -> None:
        row = self._apps.currentRow()
        if row >= 0:
            self._apps.takeItem(row)

    def _on_capture(self) -> None:
        dlg = CaptureHotkeyDialog(self)

        def _set(hk: str) -> None:
            self._hotkey.setText(hk)
            dlg.accept()

        dlg.captured.connect(_set)
        dlg.exec()

    def get_binding(self) -> KeyBinding:
        apps: list[AppLaunchItem] = []
        for i in range(self._apps.count()):
            item = self._apps.item(i)
            data = item.data(Qt.UserRole)
            if isinstance(data, dict):
                apps.append(AppLaunchItem.from_dict(data))
            else:
                # Backward compatible fallback if older items exist
                text = item.text()
                apps.append(AppLaunchItem(path=text.split(" ")[0], args=" ".join(text.split(" ")[1:])))

        return KeyBinding(
            id=self._binding.id,
            name=self._name.text().strip(),
            hotkey=self._hotkey.text().strip().lower(),
            enabled=self._enabled.isChecked(),
            action="launch_apps",
            delay_ms=int(self._delay.value()),
            apps=apps,
        )


def _simple_text_prompt(parent: QWidget, title: str, label: str) -> tuple[str, bool]:
    dlg = QDialog(parent)
    dlg.setWindowTitle(title)
    edit = QLineEdit()
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


class BindingsWindow(QWidget):
    saved = Signal()

    def __init__(self, cfg: ConfigManager, parent=None) -> None:
        super().__init__(parent)
        self._cfg = cfg

        self.setWindowTitle("Manage Key Bindings")
        ico = load_icon("mappings.png")
        if not ico.isNull():
            self.setWindowIcon(ico)
        self.setMinimumWidth(860)
        self.setMinimumHeight(460)

        self._profile = QComboBox()
        self._profile.currentTextChanged.connect(self._on_profile_changed)
        self._manage_profiles = QPushButton("Manage Profiles…")
        self._manage_profiles.clicked.connect(self._on_manage_profiles)

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(["Enabled", "Name", "Hotkey", "# Apps", "Delay (ms)"])
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self._add = QPushButton("Add")
        self._edit = QPushButton("Edit")
        self._delete = QPushButton("Delete")
        self._save = QPushButton("Save")

        self._add.clicked.connect(self._on_add)
        self._edit.clicked.connect(self._on_edit)
        self._delete.clicked.connect(self._on_delete)
        self._save.clicked.connect(self._on_save)

        btns = QHBoxLayout()
        btns.addWidget(self._add)
        btns.addWidget(self._edit)
        btns.addWidget(self._delete)
        btns.addStretch(1)
        btns.addWidget(self._save)

        layout = QVBoxLayout()
        top = QHBoxLayout()
        top.addWidget(QLabel("Profile"), 0)
        top.addWidget(self._profile, 0)
        top.addWidget(self._manage_profiles, 0)
        top.addStretch(1)
        layout.addLayout(top)
        layout.addWidget(self._table, 1)
        layout.addLayout(btns)
        self.setLayout(layout)

        self._reload_from_config()

    def sync_from_config(self) -> None:
        """
        Called by tray actions. Ensures the UI always shows the active profile's bindings,
        so switching profiles also "clears" any previous profile's mappings from view.
        """
        self._reload_from_config()

    def _active_profile(self) -> Profile:
        snap = self._cfg.snapshot()
        active_name = snap.active_profile
        p = next((x for x in snap.profiles if x.name == active_name), None)
        return p or Profile(name=active_name, bindings=[])

    def _reload_from_config(self) -> None:
        snap = self._cfg.snapshot()
        self._profile.blockSignals(True)
        self._profile.clear()
        for p in snap.profiles:
            self._profile.addItem(p.name)
        self._profile.setCurrentText(snap.active_profile)
        self._profile.blockSignals(False)

        profile = self._active_profile()
        self._bindings = list(profile.bindings)
        self._render()

    def _on_profile_changed(self, name: str) -> None:
        if not name:
            return
        # "Set profile": selecting from dropdown makes it active immediately.
        self._cfg.set_active_profile(name)
        self._cfg.save()
        self.saved.emit()  # tray will refresh hotkeys + profile menu
        self._reload_from_config()

    def _on_manage_profiles(self) -> None:
        # Lightweight modal wrapper
        dlg = QDialog(self)
        dlg.setWindowTitle("Manage Profiles")
        dlg.setMinimumWidth(560)
        dlg.setMinimumHeight(420)

        w = ProfilesWindow(self._cfg, parent=dlg)
        w.changed.connect(self.saved.emit)
        w.changed.connect(self._reload_from_config)

        layout = QVBoxLayout()
        layout.addWidget(w, 1)
        dlg.setLayout(layout)
        dlg.exec()

    def _render(self) -> None:
        self._table.setRowCount(0)
        for b in self._bindings:
            row = self._table.rowCount()
            self._table.insertRow(row)

            enabled_item = QTableWidgetItem("Yes" if b.enabled else "No")
            enabled_item.setData(Qt.UserRole, b.id)
            self._table.setItem(row, 0, enabled_item)

            self._table.setItem(row, 1, QTableWidgetItem(b.name))
            self._table.setItem(row, 2, QTableWidgetItem(b.hotkey))
            self._table.setItem(row, 3, QTableWidgetItem(str(len(b.apps))))
            self._table.setItem(row, 4, QTableWidgetItem(str(b.delay_ms)))

    def _current_index(self) -> int:
        row = self._table.currentRow()
        return row if 0 <= row < len(self._bindings) else -1

    def _on_add(self) -> None:
        dlg = BindingEditorDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return
        b = dlg.get_binding()
        if not b.hotkey:
            show_error(self, "Invalid", "Hotkey cannot be empty.")
            return
        if any(x.hotkey == b.hotkey for x in self._bindings):
            show_error(self, "Conflict", "This hotkey already exists in the active profile.")
            return
        self._bindings.append(b)
        self._render()

    def _on_edit(self) -> None:
        idx = self._current_index()
        if idx < 0:
            return
        current = self._bindings[idx]
        dlg = BindingEditorDialog(self, binding=current)
        if dlg.exec() != QDialog.Accepted:
            return
        updated = dlg.get_binding()
        if not updated.hotkey:
            show_error(self, "Invalid", "Hotkey cannot be empty.")
            return
        if any((x.hotkey == updated.hotkey and x.id != updated.id) for x in self._bindings):
            show_error(self, "Conflict", "This hotkey already exists in the active profile.")
            return
        self._bindings[idx] = updated
        self._render()

    def _on_delete(self) -> None:
        idx = self._current_index()
        if idx < 0:
            return
        self._bindings.pop(idx)
        self._render()

    def _on_save(self) -> None:
        snap = self._cfg.snapshot()
        active = snap.active_profile

        profiles = []
        for p in snap.profiles:
            if p.name == active:
                profiles.append(Profile(name=p.name, bindings=self._bindings).to_dict())
            else:
                profiles.append(p.to_dict())

        self._cfg.raw["profiles"] = profiles
        self._cfg.save()
        self.saved.emit()
        show_info(self, "Saved", "Bindings saved. Hotkeys will update immediately from the tray.")

