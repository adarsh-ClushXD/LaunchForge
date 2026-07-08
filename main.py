import os
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from core.app_info import APP_NAME, ORG_NAME
from core.config_manager import ConfigManager
from core.icons import load_icon
from core.hotkey_manager import HotkeyManager
from core.logger import configure_logging, get_logger
from tray.tray_app import TrayApp


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    app.setQuitOnLastWindowClosed(False)

    # Optional: allow running without working dir assumptions
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    cfg = ConfigManager(app_name=APP_NAME)
    configure_logging(cfg.paths.log_path)
    log = get_logger(__name__)

    try:
        cfg.load()
    except Exception:
        # If config is corrupt, keep app alive with defaults.
        log.exception("Failed to load config; continuing with defaults.")

    hotkeys = HotkeyManager(cfg)
    hotkeys.apply_active_profile()

    app_icon = load_icon("app.ico")
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)

    tray_icon = load_icon("tray.ico")
    tray = TrayApp(cfg, hotkeys, tray_icon=tray_icon)
    tray.start()

    exit_code = app.exec()

    tray.stop()
    hotkeys.stop()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

