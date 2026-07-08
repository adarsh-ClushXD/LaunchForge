from __future__ import annotations

import threading

import keyboard
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


class CaptureHotkeyDialog(QDialog):
    captured = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Capture Hotkey")
        self.setModal(True)
        self.setMinimumWidth(380)

        self._label = QLabel("Press the desired hotkey now…\n(Press Esc to cancel)")
        self._label.setAlignment(Qt.AlignCenter)

        self._cancel = QPushButton("Cancel")
        self._cancel.clicked.connect(self.reject)

        btns = QHBoxLayout()
        btns.addStretch(1)
        btns.addWidget(self._cancel)

        layout = QVBoxLayout()
        layout.addWidget(self._label)
        layout.addLayout(btns)
        self.setLayout(layout)

        self._worker = threading.Thread(target=self._capture_worker, daemon=True)
        self._worker.start()

    def _capture_worker(self) -> None:
        try:
            hotkey = keyboard.read_hotkey(suppress=False)
            if hotkey:
                hk = str(hotkey).strip().lower()
                if hk == "esc":
                    return
                self.captured.emit(hk)
        except Exception:
            # Swallow capture errors; UI can still function.
            return

