from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.app_info import APP_NAME
from core.config_manager import ConfigManager
from core.startup import is_startup_enabled, set_startup_enabled
from core.icons import load_icon
from ui.common import show_error, show_info


class SettingsWindow(QWidget):
    def __init__(self, cfg: ConfigManager, app_name: str = APP_NAME, parent=None) -> None:
        super().__init__(parent)
        self._cfg = cfg
        self._app_name = app_name

        self.setWindowTitle("Settings")
        ico = load_icon("settings.png")
        if not ico.isNull():
            self.setWindowIcon(ico)
        self.setMinimumWidth(520)

        snap = self._cfg.snapshot()

        self._run_startup = QCheckBox("Run on Windows startup")
        self._run_startup.setChecked(is_startup_enabled(self._app_name))

        self._theme = QComboBox()
        self._theme.addItems(["dark", "light"])
        self._theme.setCurrentText(str(snap.settings.get("theme", "dark")))

        self._notify = QCheckBox("Show tray notifications when a shortcut triggers")
        self._notify.setChecked(bool(snap.settings.get("show_notifications", True)))

        prefs = QGroupBox("Preferences")
        form = QFormLayout()
        form.addRow(self._run_startup)
        form.addRow("Theme", self._theme)
        form.addRow(self._notify)
        prefs.setLayout(form)

        self._import_btn = QPushButton("Import Config…")
        self._export_btn = QPushButton("Export Config…")
        self._save_btn = QPushButton("Save")
        self._save_btn.setDefault(True)

        self._import_btn.clicked.connect(self._on_import)
        self._export_btn.clicked.connect(self._on_export)
        self._save_btn.clicked.connect(self._on_save)

        row = QHBoxLayout()
        row.addWidget(self._import_btn)
        row.addWidget(self._export_btn)
        row.addStretch(1)
        row.addWidget(self._save_btn)

        layout = QVBoxLayout()
        layout.addWidget(prefs)
        layout.addStretch(1)
        layout.addLayout(row)
        self.setLayout(layout)

        self.setWindowFlag(Qt.Window, True)

    def _on_save(self) -> None:
        try:
            set_startup_enabled(self._app_name, self._run_startup.isChecked())
            self._cfg.set_setting("run_on_startup", self._run_startup.isChecked())
            self._cfg.set_setting("theme", self._theme.currentText())
            self._cfg.set_setting("show_notifications", self._notify.isChecked())
            self._cfg.save()
            show_info(self, "Saved", "Settings saved.")
        except Exception as e:
            show_error(self, "Error", f"Failed to save settings: {e}")

    def _on_import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import Config", "", "JSON Files (*.json)")
        if not path:
            return
        try:
            self._cfg.import_from_path(path)
            show_info(self, "Imported", "Config imported. Restart app to ensure all changes apply.")
        except Exception as e:
            show_error(self, "Import failed", str(e))

    def _on_export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export Config", "config.json", "JSON Files (*.json)")
        if not path:
            return
        try:
            self._cfg.export_to_path(path)
            show_info(self, "Exported", "Config exported.")
        except Exception as e:
            show_error(self, "Export failed", str(e))

