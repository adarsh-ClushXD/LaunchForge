from __future__ import annotations

import json
import os
import shutil
import uuid
from dataclasses import dataclass
from typing import Any

from core.models import Profile
from core.paths import AppPaths, get_app_paths


DEFAULT_CONFIG_VERSION = 1


def _default_config() -> dict[str, Any]:
    return {
        "version": DEFAULT_CONFIG_VERSION,
        "settings": {
            "run_on_startup": False,
            "theme": "dark",  # "dark" | "light"
            "show_notifications": True,
        },
        "active_profile": "Default",
        "profiles": [
            {
                "name": "Default",
                "bindings": [
                    # example (disabled by default)
                    {
                        "id": str(uuid.uuid4()),
                        "name": "Launch Notepad",
                        "hotkey": "ctrl+alt+n",
                        "enabled": False,
                        "action": "launch_apps",
                        "delay_ms": 250,
                        "apps": [{"path": "notepad.exe", "args": "", "cwd": None}],
                    }
                ],
            }
        ],
    }


@dataclass
class ConfigSnapshot:
    version: int
    settings: dict[str, Any]
    active_profile: str
    profiles: list[Profile]


class ConfigManager:
    def __init__(self, paths: AppPaths | None = None, app_name: str = "LaunchForge") -> None:
        self.paths = paths or get_app_paths(app_name=app_name)
        self._raw: dict[str, Any] = _default_config()

    @property
    def raw(self) -> dict[str, Any]:
        return self._raw

    def load(self) -> None:
        if not os.path.exists(self.paths.config_path):
            self.save()
            return

        with open(self.paths.config_path, "r", encoding="utf-8") as f:
            self._raw = json.load(f)

        self._raw = self._coerce_and_repair(self._raw)

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.paths.config_path), exist_ok=True)
        if os.path.exists(self.paths.config_path):
            try:
                shutil.copy2(self.paths.config_path, self.paths.config_path + ".bak")
            except Exception:
                pass
        with open(self.paths.config_path, "w", encoding="utf-8") as f:
            json.dump(self._raw, f, indent=2)

    def snapshot(self) -> ConfigSnapshot:
        repaired = self._coerce_and_repair(self._raw)
        profiles = [Profile.from_dict(p) for p in (repaired.get("profiles") or [])]
        return ConfigSnapshot(
            version=int(repaired.get("version", DEFAULT_CONFIG_VERSION)),
            settings=dict(repaired.get("settings") or {}),
            active_profile=str(repaired.get("active_profile") or "Default"),
            profiles=profiles,
        )

    def set_active_profile(self, name: str) -> None:
        self._raw["active_profile"] = name

    def set_setting(self, key: str, value: Any) -> None:
        self._raw.setdefault("settings", {})
        self._raw["settings"][key] = value

    def import_from_path(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._raw = self._coerce_and_repair(data)
        self.save()

    def export_to_path(self, path: str) -> None:
        repaired = self._coerce_and_repair(self._raw)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(repaired, f, indent=2)

    def _coerce_and_repair(self, data: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(data, dict):
            data = _default_config()

        out = _default_config()
        out["version"] = int(data.get("version", DEFAULT_CONFIG_VERSION))

        settings = data.get("settings") if isinstance(data.get("settings"), dict) else {}
        out["settings"].update(settings)

        profiles = data.get("profiles") if isinstance(data.get("profiles"), list) else []
        out["profiles"] = []
        for p in profiles:
            if not isinstance(p, dict):
                continue
            name = str(p.get("name") or "Profile")
            bindings = p.get("bindings") if isinstance(p.get("bindings"), list) else []
            fixed_bindings: list[dict[str, Any]] = []
            seen_hotkeys: set[str] = set()
            for b in bindings:
                if not isinstance(b, dict):
                    continue
                hotkey = str(b.get("hotkey") or "").strip().lower()
                if not hotkey:
                    continue
                if hotkey in seen_hotkeys:
                    # prevent duplicates within a profile by disabling later ones
                    b = dict(b)
                    b["enabled"] = False
                seen_hotkeys.add(hotkey)

                if not b.get("id"):
                    b = dict(b)
                    b["id"] = str(uuid.uuid4())
                b["hotkey"] = hotkey
                fixed_bindings.append(b)
            out["profiles"].append({"name": name, "bindings": fixed_bindings})

        active = str(data.get("active_profile") or out["profiles"][0]["name"])
        existing_names = {p["name"] for p in out["profiles"]} or {"Default"}
        out["active_profile"] = active if active in existing_names else next(iter(existing_names))
        return out

