# fichier: src/core/state.py

import time
from dataclasses import dataclass, field
from typing import Optional, Dict
from .modes import READ

@dataclass
class FixtureState:
    r: float = 0.0
    g: float = 0.0
    b: float = 0.0
    a: float = 0.0
    w: float = 0.0
    dimmer: float = 0.0
    strobe: float = 0.0

    def set_color(self, r: float, g: float, b: float, a: float, w: float):
        self.r, self.g, self.b, self.a, self.w = float(r), float(g), float(b), float(a), float(w)

    def set_dimmer(self, value: float):
        self.dimmer = float(value)

    def set_strobe(self, value: float):
        self.strobe = float(value)

@dataclass
class AppState:
    """État global de l’application."""
    mode: str = READ
    connected: bool = False
    last_hello_ts: float = 0.0
    fps: float = 0.0
    msgs_per_sec: float = 0.0
    last_error: Optional[str] = None

    # Sélection courante dans l’UI (None = rien)
    selected_fixture: Optional[int] = None

    # État des fixtures (clé = id de fixture)
    fixtures: Dict[int, FixtureState] = field(default_factory=dict)

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

    def ensure_fixture(self, fid: int) -> FixtureState:
        if fid not in self.fixtures:
            self.fixtures[fid] = FixtureState()
        return self.fixtures[fid]