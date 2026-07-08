from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AppLaunchItem:
    kind: str = "path"  # "path" | "shortcut" | "aumid"
    path: str = ""  # exe/command, or .lnk/.url path, or AUMID depending on kind
    args: str = ""
    cwd: str | None = None

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "AppLaunchItem":
        kind = str(d.get("kind") or "").strip().lower()
        if not kind:
            # Backward compatibility: old configs only stored `path`
            kind = "path"
        return AppLaunchItem(
            kind=kind,
            path=str(d.get("path", "")),
            args=str(d.get("args", "")),
            cwd=d.get("cwd") if d.get("cwd") else None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "path": self.path, "args": self.args, "cwd": self.cwd}


@dataclass
class KeyBinding:
    id: str
    hotkey: str
    name: str = ""
    enabled: bool = True
    action: str = "launch_apps"  # currently only this action
    delay_ms: int = 0
    apps: list[AppLaunchItem] = field(default_factory=list)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "KeyBinding":
        apps = [AppLaunchItem.from_dict(x) for x in (d.get("apps") or [])]
        return KeyBinding(
            id=str(d.get("id", "")),
            hotkey=str(d.get("hotkey", "")),
            name=str(d.get("name", "")),
            enabled=bool(d.get("enabled", True)),
            action=str(d.get("action", "launch_apps")),
            delay_ms=int(d.get("delay_ms", 0) or 0),
            apps=apps,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "hotkey": self.hotkey,
            "name": self.name,
            "enabled": self.enabled,
            "action": self.action,
            "delay_ms": self.delay_ms,
            "apps": [a.to_dict() for a in self.apps],
        }


@dataclass
class Profile:
    name: str
    bindings: list[KeyBinding] = field(default_factory=list)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "Profile":
        bindings = [KeyBinding.from_dict(x) for x in (d.get("bindings") or [])]
        return Profile(name=str(d.get("name", "Default")), bindings=bindings)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "bindings": [b.to_dict() for b in self.bindings]}

