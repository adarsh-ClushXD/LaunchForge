from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppPaths:
    app_dir: str
    config_path: str
    log_path: str


def get_app_paths(app_name: str = "SmartKeyRemapper") -> AppPaths:
    appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
    app_dir = os.path.join(appdata, app_name)
    os.makedirs(app_dir, exist_ok=True)

    return AppPaths(
        app_dir=app_dir,
        config_path=os.path.join(app_dir, "config.json"),
        log_path=os.path.join(app_dir, "app.log"),
    )

