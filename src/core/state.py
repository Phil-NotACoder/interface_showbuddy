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

        # --- Layout / affichage (positions normalisées 0..1, formes & tailles) ---
        # Valeurs par défaut raisonnables; seront remplacées par le YAML quand chargé
        x: float = 0.5
        y: float = 0.5
        shape: str = "circle"  # "circle" | "beam"

        # Circle
        circle_size: float = 0.08  # rayon relatif à la plus petite dimension du canvas

        # Beam (utilisé en PR#2)
        beam_length: float = 0.15
        beam_width: float = 0.10
        beam_angle_deg: float = 0.0

        label: str = ""

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

    # UI flags
    edit_mode: bool = False
    show_indexes: bool = False  # par défaut: indices masqués

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

# --- Persistance du layout (YAML) ---
import os
import yaml

def load_layout_from_yaml(app_state: 'AppState', path: str = "config/fixtures.yml") -> None:
    """Charge positions/formes/tailles depuis config/fixtures.yml (si présent)."""
    try:
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        fx_cfg = data.get("fixtures", {}) or {}
        count = int(fx_cfg.get("count", 0) or 0)
        items = fx_cfg.get("items", []) or []

        # Assure le nombre de fixtures dans l'état (MainWindow a aussi sa propre méthode)
        # Ici on ne supprime pas — on ne fait que remplir ce qui existe.
        if count:
            for fid in range(1, count + 1):
                app_state.ensure_fixture(fid)

        # Applique layout si présent
        by_id = {int(it.get("id")): it for it in items if isinstance(it, dict) and "id" in it}
        for fid, fx in app_state.fixtures.items():
            it = by_id.get(fid)
            if not it:
                continue
            fx.x = float(it.get("x", fx.x))
            fx.y = float(it.get("y", fx.y))
            fx.shape = str(it.get("shape", fx.shape))
            fx.circle_size = float(it.get("circle_size", fx.circle_size))
            fx.beam_length = float(it.get("beam_length", fx.beam_length))
            fx.beam_width = float(it.get("beam_width", fx.beam_width))
            fx.beam_angle_deg = float(it.get("beam_angle_deg", fx.beam_angle_deg))
            fx.label = str(it.get("label", fx.label))

    except Exception as e:
        # On ne plante pas l'app si le YAML est mal formé
        app_state.last_error = f"load_layout_from_yaml error: {e}"

def save_layout_to_yaml(app_state: 'AppState', path: str = "config/fixtures.yml") -> None:
    """Sauvegarde positions/formes/tailles dans config/fixtures.yml (conserve defaults existants)."""
    try:
        # Lis YAML existant pour conserver fixtures.defaults
        base = {}
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                base = yaml.safe_load(f) or {}

        fx_cfg = base.get("fixtures", {}) or {}
        fx_cfg["count"] = len(app_state.fixtures)

        items = []
        for fid in sorted(app_state.fixtures.keys()):
            fx = app_state.fixtures[fid]
            items.append({
                "id": int(fid),
                "x": round(float(fx.x), 6),
                "y": round(float(fx.y), 6),
                "shape": str(fx.shape),
                "circle_size": round(float(fx.circle_size), 6),
                "beam_length": round(float(fx.beam_length), 6),
                "beam_width": round(float(fx.beam_width), 6),
                "beam_angle_deg": round(float(fx.beam_angle_deg), 3),
                "label": fx.label or "",
            })
        fx_cfg["items"] = items
        base["fixtures"] = fx_cfg

        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(base, f, sort_keys=False, allow_unicode=True)
    except Exception as e:
        app_state.last_error = f"save_layout_to_yaml error: {e}"
``