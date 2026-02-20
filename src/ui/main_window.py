# fichier: src/ui/main_window.py

import tkinter as tk
from tkinter import ttk
import queue
from pathlib import Path
import yaml

from core.scheduler import Scheduler
from utils.log import get_logger
from ui.fixtures_view import FixturesView
from ui.toolbar import Toolbar
from ui.controls import ControlsPanel
from ui.controls_list import ControlsListView
from core.modes import READ, normalize_mode
from core.state import AppState
from io_.osc_client import OscClient  # IMPORTANT : 'io_' (et non 'io')

logger = get_logger(__name__)

class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Lighting Viz — Views & Fixture Count')
        self.root.minsize(1100, 650)

        # État global
        self.state = AppState()
        self._view_mode = "color"   # "color" | "sliders"

        # --- Toolbar ---
        self.toolbar = Toolbar(
            self.root,
            on_mode_changed=self.on_mode_changed,
            on_send_test=self.on_send_test,
            on_apply_fixture_count=self.on_apply_fixture_count,
            on_view_mode_changed=self.on_view_mode_changed,
        )
        self.toolbar.pack(fill=tk.X, side=tk.TOP)

        # --- Zone principale ---
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Grille de fixtures (aperçu couleur / barres)
        self.fixtures_view = FixturesView(self.main_frame, on_select=self.on_fixture_select)

        # Panneau sliders par fixture sélectionnée (droite)
        self.controls_panel = ControlsPanel(self.main_frame, on_change=self.on_controls_change)

        # Vue sliders "toutes fixtures"
        self.controls_list = ControlsListView(self.main_frame, on_change=self.on_controls_list_change)

        # Layout par défaut (mode color): grille à gauche + sliders sélection à droite
        self._layout_color_mode()

        # --- Status bar ---
        self.status_var = tk.StringVar(
            value='Mode: READ | Status: Idle | FPS: -- | Msg/s: -- | Fixtures: 0'
        )
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, anchor='w')
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # Queue pour événements OSC
        self.event_queue = queue.Queue()

        # Charger configs
        self._io_cfg = self._load_io_config()
        self._fx_cfg = self._load_fixtures_config()

        # Client OSC
        self.osc = OscClient(
            listen_port=self._io_cfg["listen_port"],
            remote_ip=self._io_cfg["remote_ip"],
            send_port=self._io_cfg["send_port"],
            event_queue=self.event_queue
        )
        self.osc.start()

        # Fréquence d'envoi
        try:
            self.osc._max_rate_hz = int(self._io_cfg.get("max_rate_hz", 60))
        except Exception:
            self.osc._max_rate_hz = 60

        # READY + mode initial
        self.osc.send_app_ready()
        self.osc.send_mode(self.state.mode)
        self.controls_panel.set_mode(self.state.mode)
        self.toolbar.set_fixture_count_value(int(self._fx_cfg.get("count", 4)))
        self.toolbar.set_view_mode_value(self._view_mode)

        # Pré-allouer des fixtures
        self._ensure_fixture_count(int(self._fx_cfg.get("count", 4)))

        # Scheduler (~30 FPS)
        self.scheduler = Scheduler(self.root, interval_ms=33, on_tick=self.on_tick)
        self.scheduler.start()

        self.root.protocol('WM_DELETE_WINDOW', self.on_close)

    # ----------------------------------------------------------------------
    # Layout helpers
    # ----------------------------------------------------------------------
    def _clear_main(self):
        for w in (self.fixtures_view, self.controls_panel, self.controls_list):
            try:
                w.pack_forget()
            except Exception:
                pass

    def _layout_color_mode(self):
        # Grille (expand) + panneau sliders sélection à droite
        self._clear_main()
        self.fixtures_view.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.controls_panel.pack(fill=tk.Y, side=tk.RIGHT, padx=(6,6), pady=(6,6))

    def _layout_sliders_mode(self):
        # Vue sliders "toutes fixtures" en plein
        self._clear_main()
        self.controls_list.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

    # ----------------------------------------------------------------------
    # Tick
    # ----------------------------------------------------------------------
    def on_tick(self):
        self._drain_events()

        # Redessiner selon le mode d'affichage
        if self._view_mode == "color":
            self.fixtures_view.render(self.state)
        else:
            self.controls_list.render(self.state)

        # WRITE: envoi automatique d'un /frame (throttle côté OscClient)
        if self.state.mode == "write":
            try:
                t, fixtures_flat = self._build_frame_from_state()
                if fixtures_flat:
                    self.osc.send_frame(t, fixtures_flat, throttle=True)
            except Exception as e:
                logger.error("send_frame failed: %s", e)

        # KPIs + statut
        self.state.fps = self.scheduler.fps
        connected_text = "Connected" if self.state.connected else "Not connected"
        self.toolbar.set_connected(self.state.connected)
        self.toolbar.set_status_text(connected_text)
        nb_fixtures = len(self.state.fixtures)
        self.status_var.set(
            f"Mode: {self.state.mode.upper()} | "
            f"{connected_text} | "
            f"FPS: {self.state.fps:.0f} | "
            f"Msg/s: {self.state.msgs_per_sec:.0f} | "
            f"Fixtures: {nb_fixtures}"
        )

    def _drain_events(self):
        try:
            while True:
                etype, payload = self.event_queue.get_nowait()

                if etype == "hello":
                    self.state.connected = True
                    self.state.last_hello_ts = self._now()

                elif etype == "error":
                    msg = payload.get("message", "")
                    self.state.last_error = msg
                    logger.error("OSC error: %s", msg)

                elif etype == "fixture_color":
                    fid = int(payload["id"])
                    r = float(payload["r"]); g = float(payload["g"]); b = float(payload["b"])
                    a = float(payload["a"]); w = float(payload["w"])
                    fx = self.state.ensure_fixture(fid)
                    fx.set_color(r, g, b, a, w)
                    if self.state.selected_fixture == fid and self._view_mode == "color":
                        self.controls_panel.load_from_fixture(fid, fx)

                elif etype == "fixture_dimmer":
                    fid = int(payload["id"])
                    val = float(payload["value"])
                    fx = self.state.ensure_fixture(fid)
                    fx.set_dimmer(val)
                    if self.state.selected_fixture == fid and self._view_mode == "color":
                        self.controls_panel.load_from_fixture(fid, fx)

                elif etype == "fixture_strobe":
                    fid = int(payload["id"])
                    rate = float(payload["rate"])
                    fx = self.state.ensure_fixture(fid)
                    fx.set_strobe(rate)
                    if self.state.selected_fixture == fid and self._view_mode == "color":
                        self.controls_panel.load_from_fixture(fid, fx)

                elif etype == "frame":
                    for item in payload.get("fixtures", []):
                        fid = int(item["id"])
                        fx = self.state.ensure_fixture(fid)
                        fx.set_color(float(item["r"]), float(item["g"]), float(item["b"]), float(item["a"]), float(item["w"]))
                        fx.set_dimmer(float(item["dimmer"]))
                        fx.set_strobe(float(item["strobe"]))
                        if self.state.selected_fixture == fid and self._view_mode == "color":
                            self.controls_panel.load_from_fixture(fid, fx)

                self.state.on_msg_received()
        except queue.Empty:
            pass

    # ----------------------------------------------------------------------
    # Construction d'un /frame
    # ----------------------------------------------------------------------
    def _build_frame_from_state(self):
        import time as _t
        t = _t.perf_counter()
        flat = []
        for fid in sorted(self.state.fixtures.keys()):
            fx = self.state.fixtures[fid]
            flat.extend([
                int(fid),
                float(fx.r), float(fx.g), float(fx.b), float(fx.a), float(fx.w),
                float(fx.dimmer), float(fx.strobe),
            ])
        return t, flat

    # ----------------------------------------------------------------------
    # Toolbar callbacks
    # ----------------------------------------------------------------------
    def on_mode_changed(self, mode: str):
        mode = normalize_mode(mode)
        if self.state.mode != mode:
            self.state.mode = mode
            try:
                self.osc.send_mode(mode)
            except Exception as e:
                logger.exception("Failed to send mode: %s", e)
        self.controls_panel.set_mode(mode)

    def on_send_test(self):
        import time as _t
        t = _t.perf_counter()
        fixtures_flat = [
            1, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.2,
            2, 0.0, 1.0, 0.0, 0.0, 0.0, 0.8, 0.0,
            3, 0.0, 0.0, 1.0, 0.0, 0.0, 0.6, 0.1,
            4, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0,
        ]
        try:
            self.osc.send_frame(t, fixtures_flat, throttle=False)
            self.toolbar.set_status_text("Test frame sent")
        except Exception as e:
            self.toolbar.set_status_text("Send failed")
            logger.exception("Send test frame failed: %s", e)

    def on_apply_fixture_count(self, count: int):
        # Ajuste l'état à 'count' fixtures
        self._ensure_fixture_count(count)
        # MàJ interface
        if self._view_mode == "color" and self.state.selected_fixture:
            # Relire sliders de la fixture sélectionnée si elle existe toujours
            if self.state.selected_fixture in self.state.fixtures:
                fx = self.state.ensure_fixture(self.state.selected_fixture)
                self.controls_panel.load_from_fixture(self.state.selected_fixture, fx)
            else:
                self.state.selected_fixture = None
                self.controls_panel.set_selected_id(None)

    def on_view_mode_changed(self, view_mode: str):
        vm = (view_mode or "color").lower()
        if vm not in ("color","sliders"):
            vm = "color"
        if vm == self._view_mode:
            return
        self._view_mode = vm
        # Ajuster le layout
        if self._view_mode == "color":
            self._layout_color_mode()
        else:
            self._layout_sliders_mode()

    # ----------------------------------------------------------------------
    # Sélection & sliders callbacks
    # ----------------------------------------------------------------------
    def on_fixture_select(self, fixture_id):
        if self._view_mode != "color":
            return  # en vue "sliders (toutes)", le clic sur la grille n'est pas utilisé
        if fixture_id is None:
            self.state.selected_fixture = None
            self.controls_panel.set_selected_id(None)
            try:
                self.osc.send_select(-1)
            except Exception as e:
                logger.error("send_select(-1) failed: %s", e)
        else:
            self.state.selected_fixture = int(fixture_id)
            self.controls_panel.set_selected_id(self.state.selected_fixture)
            try:
                self.osc.send_select(self.state.selected_fixture)
            except Exception as e:
                logger.error("send_select(%s) failed: %s", self.state.selected_fixture, e)
            fx = self.state.ensure_fixture(self.state.selected_fixture)
            self.controls_panel.load_from_fixture(self.state.selected_fixture, fx)

    def on_controls_change(self, name: str, value: float):
        if self._view_mode != "color":
            return
        fid = self.state.selected_fixture
        if fid is None:
            return
        self._apply_param_to_fixture(fid, name, value)

    def on_controls_list_change(self, fid: int, name: str, value: float):
        if fid not in self.state.fixtures:
            return
        self._apply_param_to_fixture(fid, name, value)

    def _apply_param_to_fixture(self, fid: int, name: str, value: float):
        fx = self.state.ensure_fixture(fid)
        v = max(0.0, min(1.0, float(value)))
        if name == "r":   fx.r = v
        elif name == "g": fx.g = v
        elif name == "b": fx.b = v
        elif name == "a": fx.a = v
        elif name == "w": fx.w = v
        elif name == "dimmer": fx.dimmer = v
        elif name == "strobe": fx.strobe = v
        # Si la fixture est sélectionnée en mode color, refléter sur le panneau
        if self._view_mode == "color" and self.state.selected_fixture == fid:
            self.controls_panel.load_from_fixture(fid, fx)

    # ----------------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------------
    def _ensure_fixture_count(self, count: int):
        count = max(4, min(20, int(count)))
        # Ajouter les manquantes
        for fid in range(1, count + 1):
            self.state.ensure_fixture(fid)
        # Supprimer celles au-delà
        to_remove = [fid for fid in self.state.fixtures.keys() if fid > count]
        for fid in to_remove:
            try:
                del self.state.fixtures[fid]
            except Exception:
                pass
        # MàJ spin si besoin
        try:
            self.toolbar.set_fixture_count_value(count)
        except Exception:
            pass

    def _load_io_config(self):
        path = Path(__file__).resolve().parents[2] / "config" / "io.yml"
        defaults = {"listen_port": 9000, "send_port": 9001, "remote_ip": "127.0.0.1"}
        try:
            if path.exists():
                with path.open("r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                return {
                    "listen_port": int(data.get("listen_port", defaults["listen_port"])),
                    "send_port": int(data.get("send_port", defaults["send_port"])),
                    "remote_ip": str(data.get("remote_ip", defaults["remote_ip"])),
                    "max_rate_hz": int(data.get("max_rate_hz", 60)),
                }
            else:
                return defaults
        except Exception:
            return defaults

    def _load_fixtures_config(self):
        path = Path(__file__).resolve().parents[2] / "config" / "fixtures.yml"
        defaults = {
            "count": 4,
            "defaults": {"color": [0, 0, 0, 0, 0], "dimmer": 0.0, "strobe": 0.0},
        }
        try:
            if path.exists():
                with path.open("r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                fx = data.get("fixtures", {}) or {}
                return {
                    "count": int(fx.get("count", defaults["count"])),
                    "defaults": fx.get("defaults", defaults["defaults"]) or defaults["defaults"],
                }
            else:
                return defaults
        except Exception:
            return defaults

    def _now(self):
        import time
        return time.monotonic()

    def on_close(self):
        try:
            self.scheduler.stop()
        except Exception:
            pass
        try:
            self.osc.stop()
        except Exception:
            pass
        self.root.destroy()

    def run(self):
        self.root.mainloop()

def run_app():
    app = MainWindow()
    app.run()