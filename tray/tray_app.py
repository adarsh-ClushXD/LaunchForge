from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtGui import QAction, QActionGroup, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon

from core.app_info import APP_NAME
from core.config_manager import ConfigManager
from core.icons import load_icon
from core.hotkey_manager import HotkeyManager
from core.logger import get_logger
from ui.bindings_window import BindingsWindow
from ui.profiles_window import ProfilesWindow
from ui.settings_window import SettingsWindow
from ui.theme import apply_dark_palette, apply_light_palette


log = get_logger(__name__)


class TrayApp(QObject):
    def __init__(self, cfg: ConfigManager, hotkeys: HotkeyManager, tray_icon: QIcon) -> None:
        super().__init__()
        self._cfg = cfg
        self._hotkeys = hotkeys
        if tray_icon is None or tray_icon.isNull():
            style = QApplication.style()
            tray_icon = style.standardIcon(QStyle.SP_ComputerIcon) if style else QIcon()
        self._tray = QSystemTrayIcon(tray_icon)
        self._tray.setToolTip(APP_NAME)
        self._tray.activated.connect(self._on_tray_activated)

        self._settings_win: SettingsWindow | None = None
        self._bindings_win: BindingsWindow | None = None
        self._profiles_win: ProfilesWindow | None = None

        self._menu = QMenu()
        self._action_open_settings = QAction("Open Settings")
        self._action_manage_bindings = QAction("Manage Key Bindings")
        self._action_manage_profiles = QAction("Manage Profiles")
        self._switch_profile_menu = QMenu("Switch Profile")
        self._action_exit = QAction("Exit")
        self._profile_action_group = QActionGroup(self)
        self._profile_action_group.setExclusive(True)

        self._action_open_settings.triggered.connect(self.open_settings)
        self._action_manage_bindings.triggered.connect(self.open_bindings)
        self._action_manage_profiles.triggered.connect(self.open_profiles)
        self._action_exit.triggered.connect(self.exit_app)

        # Optional custom menu icons (fallbacks are fine)
        self._action_open_settings.setIcon(load_icon("settings.png"))
        self._action_manage_bindings.setIcon(load_icon("mappings.png"))
        self._action_manage_profiles.setIcon(load_icon("profiles.png"))

        self._menu.addAction(self._action_open_settings)
        self._menu.addAction(self._action_manage_bindings)
        self._menu.addAction(self._action_manage_profiles)
        self._menu.addMenu(self._switch_profile_menu)
        self._menu.addSeparator()
        self._menu.addAction(self._action_exit)
        self._tray.setContextMenu(self._menu)

        self._hotkeys.set_trigger_callback(self._on_binding_triggered)

        self._apply_theme()
        self._rebuild_profiles_menu()

    def start(self) -> None:
        self._tray.show()
        self._maybe_notify(APP_NAME, "Running in system tray.")

    def stop(self) -> None:
        self._tray.hide()

    def open_settings(self) -> None:
        if not self._settings_win:
            self._settings_win = SettingsWindow(self._cfg)
            self._settings_win.config_imported.connect(self._on_config_imported)
            self._settings_win.destroyed.connect(lambda: setattr(self, "_settings_win", None))
        self._settings_win.show()
        self._settings_win.raise_()
        self._settings_win.activateWindow()

    def open_bindings(self) -> None:
        if not self._bindings_win:
            self._bindings_win = BindingsWindow(self._cfg)
            self._bindings_win.saved.connect(self._on_bindings_saved)
            self._bindings_win.destroyed.connect(lambda: setattr(self, "_bindings_win", None))
        self._bindings_win.show()
        self._bindings_win.raise_()
        self._bindings_win.activateWindow()

    def open_profiles(self) -> None:
        if not self._profiles_win:
            self._profiles_win = ProfilesWindow(self._cfg)
            self._profiles_win.changed.connect(self._on_profiles_changed)
            self._profiles_win.destroyed.connect(lambda: setattr(self, "_profiles_win", None))
        self._profiles_win.show()
        self._profiles_win.raise_()
        self._profiles_win.activateWindow()

    def exit_app(self) -> None:
        from PySide6.QtWidgets import QApplication

        QApplication.quit()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.DoubleClick:
            self.open_bindings()

    def _rebuild_profiles_menu(self) -> None:
        self._switch_profile_menu.clear()
        snap = self._cfg.snapshot()

        for p in snap.profiles:
            act = QAction(p.name)
            act.setCheckable(True)
            act.setChecked(p.name == snap.active_profile)
            act.setData(p.name)
            self._profile_action_group.addAction(act)
            act.triggered.connect(lambda checked=False, a=act: self._switch_profile(str(a.data())))
            self._switch_profile_menu.addAction(act)

    def _switch_profile(self, name: str) -> None:
        try:
            self._cfg.set_active_profile(name)
            self._cfg.save()
            self._hotkeys.apply_active_profile()
            self._rebuild_profiles_menu()
            if self._bindings_win:
                self._bindings_win.sync_from_config()
            self._maybe_notify("Profile switched", f"Active profile: {name}")
        except Exception as e:
            log.exception("Failed switching profile")
            self._maybe_notify("Error", f"Failed switching profile: {e}")

    def _on_bindings_saved(self) -> None:
        self._hotkeys.apply_active_profile()
        self._rebuild_profiles_menu()
        if self._bindings_win:
            self._bindings_win.sync_from_config()

    def _on_profiles_changed(self) -> None:
        self._hotkeys.apply_active_profile()
        self._rebuild_profiles_menu()
        if self._bindings_win:
            self._bindings_win.sync_from_config()

    def _on_config_imported(self) -> None:
        self._hotkeys.apply_active_profile()
        self._rebuild_profiles_menu()
        if self._bindings_win:
            self._bindings_win.sync_from_config()
        if self._profiles_win:
            self._profiles_win._reload()
        self._apply_theme()

    def _on_binding_triggered(self, binding, ok: bool, message: str) -> None:
        snap = self._cfg.snapshot()
        if not bool(snap.settings.get("show_notifications", True)):
            return
        title = binding.name or binding.hotkey
        body = "Triggered" if ok else f"Failed: {message}"
        self._tray.showMessage(title, body)

    def _maybe_notify(self, title: str, body: str) -> None:
        snap = self._cfg.snapshot()
        if bool(snap.settings.get("show_notifications", True)):
            self._tray.showMessage(title, body)

    def _apply_theme(self) -> None:
        from PySide6.QtWidgets import QApplication

        snap = self._cfg.snapshot()
        theme = str(snap.settings.get("theme", "dark"))
        app = QApplication.instance()
        if not app:
            return

        if theme == "light":
            app.setPalette(apply_light_palette(app.palette()))
        else:
            app.setPalette(apply_dark_palette(app.palette()))

