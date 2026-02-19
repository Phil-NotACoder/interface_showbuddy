# src/core/state.py

import time
from dataclasses import dataclass, field
from typing import Optional
from .modes import READ

@dataclass
class AppState:
    """État global de l’application."""

    mode: str = READ
    connected: bool = False
    last_hello_ts: float = 0.0
    fps: float = 0.0
    msgs_per_sec: float = 0.0
    last_error: Optional[str] = None

    # ✅ Ajout Step 2b : sélection courante dans l’UI (None = rien)
    selected_fixture: Optional[int] = None

    # KPI message/s
    _count_msgs: int = field(default=0, init=False, repr=False)
    _last_msg_window_ts: float = field(default_factory=time.monotonic, init=False, repr=False)

    def on_msg_received(self):
        """Appelé à chaque message OSC reçu — calcule Msg/s."""
        self._count_msgs += 1
        now = time.monotonic()
        if now - self._last_msg_window_ts >= 1.0:
            self.msgs_per_sec = self._count_msgs / (now - self._last_msg_window_ts)
            self._count_msgs = 0
            self._last_msg_window_ts = now