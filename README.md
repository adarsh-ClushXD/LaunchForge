# LaunchForge (Windows Tray App)

A lightweight Windows **system tray** app that runs in the background and lets you:

- Remap global hotkeys
- Assign one hotkey to launch multiple apps (with optional delay)
- Maintain multiple **profiles** (Gaming / Study / Editing) and switch quickly from the tray

Built with **Python 3.10+**, **PySide6**, and `keyboard`.

---

## Requirements

- Windows 10/11
- Python 3.10+
- `pip install -r requirements.txt`

Notes about `keyboard`:
- Global hooks sometimes require **Administrator** privileges depending on your environment / antivirus policy.
- Some reserved system combos (e.g., `Win+L`) cannot be overridden by design.

---

## How to run (dev)

From this folder:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

The app starts **silently** and appears in the system tray (hidden icons).

---

## How to use

- Right‑click tray icon:
  - **Open Settings**
  - **Manage Key Bindings**
  - **Switch Profile**
  - **Exit**

In **Manage Key Bindings**:
- Click **Add**
- Capture a hotkey (global)
- Add one or more apps (path + optional args)
- Optional launch delay between apps

---

## Config & Logs

Config is stored at:
- `%APPDATA%\LaunchForge\config.json`

Logs are stored at:
- `%APPDATA%\LaunchForge\app.log`

You can **Import/Export** config from the Settings window.

---

## Build to `.exe` (PyInstaller)

Install:

```bash
py -m pip install pyinstaller
```

Build (console-less tray app):

```bash
py -m pyinstaller --noconsole --name LaunchForge --onefile run_launchforge.pyw
```

Output exe will be in `dist\SmartKeyRemapper.exe`.

Tip: For a custom icon, add `--icon assets\tray.ico` once you have an `.ico`.

---

## Future Improvements

- Per-binding action types (send text, run scripts, window management)
- Better key capture UX (show currently held keys live)
- Per-profile “enabled/disabled” toggles per binding
- Auto-update mechanism
- Conflict detection across profiles and OS-reserved key warnings

