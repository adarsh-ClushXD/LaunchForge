from __future__ import annotations

import os
import sys
import winreg


RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _app_executable_command() -> str:
    """
    Returns a command suitable for HKCU\\...\\Run.
    - In dev: uses python.exe + main.py
    - In PyInstaller: uses the frozen exe path
    """
    if getattr(sys, "frozen", False):
        return f"\"{sys.executable}\""

    main_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "main.py")
    main_py = os.path.abspath(main_py)
    return f"\"{sys.executable}\" \"{main_py}\""


def is_startup_enabled(app_name: str) -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, app_name)
            return bool(value)
    except FileNotFoundError:
        return False
    except OSError:
        return False


def set_startup_enabled(app_name: str, enabled: bool) -> None:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, _app_executable_command())
        else:
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                pass

