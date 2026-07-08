"""
GUI launcher for LaunchForge.

Double-clicking a .py file usually runs under python.exe (console).
Double-clicking a .pyw file runs under pythonw.exe (no console),
so the tray app keeps running without a terminal window.
"""

from main import main

raise SystemExit(main())

