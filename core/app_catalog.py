from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass

from core.logger import get_logger


log = get_logger(__name__)


@dataclass(frozen=True)
class CatalogApp:
    name: str
    kind: str  # "shortcut" | "aumid"
    value: str  # shortcut path or AUMID


def _powershell_get_start_apps() -> list[CatalogApp]:
    """
    Uses Get-StartApps to list apps that appear in Windows Start search/menu,
    including many Microsoft Store apps that do not expose normal .exe/.lnk.
    """
    try:
        # ConvertTo-Json output can be either object or array depending on count,
        # so we normalize after parsing.
        cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            "Get-StartApps | Select-Object Name,AppID | ConvertTo-Json -Depth 3",
        ]
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT, encoding="utf-8")
        data = json.loads(out) if out.strip() else []
        rows = data if isinstance(data, list) else [data]
        apps: list[CatalogApp] = []
        for r in rows:
            if not isinstance(r, dict):
                continue
            name = str(r.get("Name") or "").strip()
            app_id = str(r.get("AppID") or "").strip()
            if name and app_id:
                apps.append(CatalogApp(name=name, kind="aumid", value=app_id))
        return apps
    except Exception:
        log.exception("Failed to query Get-StartApps")
        return []


def build_catalog(shortcuts: list[tuple[str, str]]) -> list[CatalogApp]:
    """
    shortcuts: list of (name, shortcut_path)
    """
    items: list[CatalogApp] = [CatalogApp(name=n, kind="shortcut", value=p) for n, p in shortcuts]
    items.extend(_powershell_get_start_apps())

    # De-duplicate by (name.lower(), kind, value.lower()) and sort.
    seen: set[tuple[str, str, str]] = set()
    out: list[CatalogApp] = []
    for i in items:
        key = (i.name.lower(), i.kind, i.value.lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(i)

    out.sort(key=lambda x: (x.name.lower(), x.kind, x.value.lower()))
    return out

