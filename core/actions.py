from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass

from core.logger import get_logger
from core.models import KeyBinding


log = get_logger(__name__)


@dataclass(frozen=True)
class ActionResult:
    ok: bool
    message: str = ""

def _launch_path(path: str, args: str, cwd: str | None) -> None:
    """
    Launches either:
    - an exe/command directly, or
    - a Start Menu shortcut (.lnk/.url) via `cmd /c start`.
    """
    p = (path or "").strip()
    if not p:
        raise ValueError("Empty launch path")

    lower = p.lower()
    if lower.endswith(".lnk") or lower.endswith(".url"):
        # Let Windows resolve the shortcut target.
        # `start` requires a title argument; we pass "".
        subprocess.Popen(["cmd", "/c", "start", "", p], cwd=cwd or None)
        return

    cmd = [p]
    if args.strip():
        # Simple arg splitting for usability; advanced quoting is left to future improvement.
        cmd.extend(args.split())
    subprocess.Popen(cmd, cwd=cwd or None)


def _launch_aumid(aumid: str) -> None:
    """
    Launch Microsoft Store / packaged apps by AppUserModelID (AppID from Get-StartApps).
    """
    a = (aumid or "").strip()
    if not a:
        raise ValueError("Empty AUMID")
    subprocess.Popen(["explorer.exe", f"shell:AppsFolder\\{a}"])


def execute_binding(binding: KeyBinding) -> ActionResult:
    if not binding.enabled:
        return ActionResult(ok=False, message="Binding disabled")

    if binding.action != "launch_apps":
        return ActionResult(ok=False, message=f"Unsupported action: {binding.action}")

    if not binding.apps:
        return ActionResult(ok=False, message="No apps configured")

    delay_s = max(0, int(binding.delay_ms)) / 1000.0
    for i, app in enumerate(binding.apps):
        try:
            kind = (getattr(app, "kind", "path") or "path").strip().lower()
            if kind == "aumid":
                _launch_aumid(app.path)
            else:
                _launch_path(app.path, app.args, app.cwd)
            log.info("Launched app for binding=%s: (%s) %s", binding.id, kind, app.path)
        except Exception as e:
            log.exception("Failed launching app '%s' (binding=%s)", app.path, binding.id)
            return ActionResult(ok=False, message=str(e))

        if delay_s and i < len(binding.apps) - 1:
            time.sleep(delay_s)

    return ActionResult(ok=True, message="Launched")

