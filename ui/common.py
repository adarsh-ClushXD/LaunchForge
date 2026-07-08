from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget


def show_error(parent: QWidget | None, title: str, message: str) -> None:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Critical)
    box.setWindowTitle(title)
    box.setText(message)
    box.exec()


def show_info(parent: QWidget | None, title: str, message: str) -> None:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Information)
    box.setWindowTitle(title)
    box.setText(message)
    box.exec()

