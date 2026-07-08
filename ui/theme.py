from __future__ import annotations

from PySide6.QtGui import QPalette, QColor


def apply_dark_palette(palette: QPalette) -> QPalette:
    p = QPalette(palette)
    base = QColor("#0b0f14")
    alt_base = QColor("#111827")
    text = QColor("#e5e7eb")
    disabled_text = QColor("#6b7280")
    accent = QColor("#22d3ee")

    p.setColor(QPalette.Window, base)
    p.setColor(QPalette.WindowText, text)
    p.setColor(QPalette.Base, QColor("#0f172a"))
    p.setColor(QPalette.AlternateBase, alt_base)
    p.setColor(QPalette.Text, text)
    p.setColor(QPalette.Button, QColor("#0f172a"))
    p.setColor(QPalette.ButtonText, text)
    p.setColor(QPalette.ToolTipBase, QColor("#111827"))
    p.setColor(QPalette.ToolTipText, text)
    p.setColor(QPalette.Highlight, accent)
    p.setColor(QPalette.HighlightedText, QColor("#001018"))

    p.setColor(QPalette.Disabled, QPalette.Text, disabled_text)
    p.setColor(QPalette.Disabled, QPalette.WindowText, disabled_text)
    p.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_text)

    return p


def apply_light_palette(palette: QPalette) -> QPalette:
    # Keep it simple; default light palette is fine.
    return QPalette(palette)

