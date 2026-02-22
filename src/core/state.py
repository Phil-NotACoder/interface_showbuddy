import time
from dataclasses import dataclass, field
from typing import Optional, Dict
from .modes import READ


@dataclass
class FixtureState:
    # Couleurs et Intensité (0-255)
    r: float = 0.0
    g: float = 0.0
    b: float = 0.0
    a: float = 0.0
    w: float = 0.0
    dimmer: float = 0.0
    strobe: float = 0.0

    # Position et Forme (Nouveaux attributs INDISPENSABLES)
    pos_x: float = 100.0
    pos_y: float = 100.0
    shape: str = "circle"  # "circle" ou "beam"
    size: float = 20.0  # Pour le mode ROUND

    # Paramètres Beam
    angle: float = 0.0
    beam_length: float = 100.0
    cone_angle: float = 45.0

    def set_color(self, r, g, b, a, w):
        self.r, self.g, self.b, self.a, self.w = float(r), float(g), float(b), float(a), float(w)

    def set_dimmer(self, value):
        self.dimmer = float(value)

    def set_strobe(self, value):
        self.strobe = float(value)


@dataclass
class AppState:
    mode: str = READ
    connected: bool = False
    last_hello_ts: float = 0.0
    fps: float = 0.0
    msgs_per_sec: float = 0.0
    last_error: Optional[str] = None

    # Renommé pour correspondre à l'interface (était selected_fixture)
    selected_fixture_id: Optional[int] = None

    fixtures: Dict[int, FixtureState] = field(default_factory=dict)

    # KPI internals
    _count_msgs: int = field(default=0, init=False, repr=False)
    _last_msg_window_ts: float = field(default_factory=time.monotonic, init=False, repr=False)

    def on_msg_received(self):
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