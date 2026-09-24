# -*- coding: utf-8 -*-
#  app/utils/debounce.py
#  Debounce utility for reducing excessive signal emissions (Task 7)
# ============================================================
from PySide6.QtCore import QTimer, QObject, Signal
from functools import wraps


class Debouncer(QObject):
    """Debounce rapid signal emissions to reduce re-renders."""
    triggered = Signal()

    def __init__(self, delay_ms: int = 500):
        """
        Args:
            delay_ms: Milliseconds to wait after last signal before emitting
        """
        super().__init__()
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._emit)
        self._delay_ms = delay_ms

    def signal_received(self):
        """Call this when the debounced signal is received."""
        self._timer.stop()
        self._timer.start(self._delay_ms)

    def _emit(self):
        """Emit the debounced signal."""
        self._timer.stop()
        self.triggered.emit()

    def cancel(self):
        """Cancel pending debounce."""
        self._timer.stop()
