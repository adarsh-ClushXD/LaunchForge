from __future__ import annotations

import threading
from collections.abc import Callable

import keyboard

from core.actions import execute_binding
from core.config_manager import ConfigManager
from core.logger import get_logger
from core.models import KeyBinding, Profile


log = get_logger(__name__)


class HotkeyManager:
    """
    Wraps `keyboard.add_hotkey` and manages registering/unregistering bindings
    for the currently active profile.

    Important: `keyboard` installs a global hook. In some setups it may require
    Administrator privileges or be blocked by security tools.
    """

    def __init__(self, cfg: ConfigManager) -> None:
        self._cfg = cfg
        self._lock = threading.RLock()
        self._registered: dict[str, int] = {}  # binding_id -> keyboard hotkey handle
        self._on_trigger: Callable[[KeyBinding, bool, str], None] | None = None

    def set_trigger_callback(self, cb: Callable[[KeyBinding, bool, str], None]) -> None:
        self._on_trigger = cb

    def stop(self) -> None:
        with self._lock:
            for _, handle in list(self._registered.items()):
                try:
                    keyboard.remove_hotkey(handle)
                except Exception:
                    pass
            self._registered.clear()

    def apply_active_profile(self) -> None:
        snap = self._cfg.snapshot()
        active_name = snap.active_profile
        profile = next((p for p in snap.profiles if p.name == active_name), None)
        if not profile:
            profile = Profile(name=active_name, bindings=[])

        self.apply_profile(profile)

    def apply_profile(self, profile: Profile) -> None:
        with self._lock:
            self.stop()

            used: set[str] = set()
            for b in profile.bindings:
                if not b.enabled:
                    continue
                hk = (b.hotkey or "").strip().lower()
                if not hk:
                    continue
                if hk in used:
                    log.warning("Duplicate hotkey in profile '%s': %s", profile.name, hk)
                    continue
                used.add(hk)

                try:
                    handle = keyboard.add_hotkey(hk, self._make_handler(b), suppress=False)
                    self._registered[b.id] = handle
                    log.info("Registered hotkey=%s (binding=%s)", hk, b.id)
                except Exception:
                    log.exception("Failed to register hotkey=%s (binding=%s)", hk, b.id)

    def _make_handler(self, binding: KeyBinding):
        def _handler() -> None:
            try:
                result = execute_binding(binding)
                if self._on_trigger:
                    self._on_trigger(binding, result.ok, result.message)
            except Exception as e:
                log.exception("Unhandled exception executing binding=%s", binding.id)
                if self._on_trigger:
                    self._on_trigger(binding, False, str(e))

        return _handler

