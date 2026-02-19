# src/ui/main_window.py

import tkinter as tk
from tkinter import ttk
import queue
from pathlib import Path
import yaml

from core.scheduler import Scheduler
from utils.log import get_logger
from ui.fixtures_view import FixturesView
from ui.toolbar import Toolbar
from core.modes import READ, normalize_mode
from core.state import AppState
from io_.osc_client import OscClient  # IMPORTANT : 'io_' (et non 'io')

logger = get_logger(__name__)

class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Lighting Viz — Step 2b')
        self.root.minsize(820, 560)

        # État global
        self.state = AppState()

        # --- Toolbar (READ/WRITE + connexion) ---
        self.toolbar = Toolbar(self.root, on_mode_changed=self.on_mode_changed)
        self.toolbar.pack(fill=tk.X, side=tk.TOP)

        # --- Zone principale (fixtures) ---
        # ✅ Step 2b : on passe le callback on_select
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.fixtures_view = FixturesView(self.main_frame, on_select=self.on_fixture_select)
        self.fixtures_view.pack(fill=tk.BOTH, expand=True)

        # --- Status bar ---
        self.status_var = tk.StringVar(
            value='Mode: READ | Status: Idle | FPS: -- | Msg/s: --'
        )
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, anchor='w')
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # Queue pour recevoir les events OSC
        self.event_queue = queue.Queue()

        # Charger config I/O
        self._io_cfg = self._load_io_config()

        # Client OSC
        self.osc = OscClient(
            listen_port=self._io_cfg["listen_port"],
            remote_ip=self._io_cfg["remote_ip"],
            send_port=self._io_cfg["send_port"],
            event_queue=self.event_queue
        )
        self.osc.start()

        # Envoyer READY et mode initial
        self.osc.send_app_ready()
        self.osc.send_mode(self.state.mode)

        # Scheduler (~30 FPS)
        self.scheduler = Scheduler(self.root, interval_ms=33, on_tick=self.on_tick)
        self.scheduler.start()

        self.root.protocol('WM_DELETE_WINDOW', self.on_close)

    # ----------------------------------------------------------------------
    # Boucle UI
    # ----------------------------------------------------------------------
    def on_tick(self):
        self._drain_events()

        # KPIs
        self.state.fps = self.scheduler.fps

        connected_text = "Connected" if self.state.connected else "Not connected"
        self.toolbar.set_connected(self.state.connected)
        self.toolbar.set_status_text(connected_text)

        self.status_var.set(
            f"Mode: {self.state.mode.upper()} | "
            f"{connected_text} | "
            f"FPS: {self.state.fps:.0f} | "
            f"Msg/s: {self.state.msgs_per_sec:.0f}"
        )

    def _drain_events(self):
        """Lit les événements envoyés par le thread OSC."""
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

                # Futur : fixture states, cues...
                self.state.on_msg_received()

        except queue.Empty:
            pass

    # ----------------------------------------------------------------------
    # Toolbar
    # ----------------------------------------------------------------------
    def on_mode_changed(self, mode: str):
        mode = normalize_mode(mode)
        if self.state.mode != mode:
            self.state.mode = mode
            try:
                self.osc.send_mode(mode)
            except Exception as e:
                logger.exception("Failed to send mode: %s", e)

    # ----------------------------------------------------------------------
    # ✅ Step 2b — Sélection d’un fixture (clic dans la vue)
    # ----------------------------------------------------------------------
    def on_fixture_select(self, fixture_id):
        """
        fixture_id = int ou None
        - Met à jour l'état sélectionné
        - Envoie /ui/select {id} à Max (ou -1 si None)
        """
        if fixture_id is None:
            self.state.selected_fixture = None
            try:
                self.osc.send_select(-1)
            except Exception as e:
                logger.error("send_select(-1) failed: %s", e)
        else:
            self.state.selected_fixture = int(fixture_id)
            try:
                self.osc.send_select(self.state.selected_fixture)
            except Exception as e:
                logger.error("send_select(%s) failed: %s", self.state.selected_fixture, e)

    # ----------------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------------
    def _load_io_config(self):
        """
        Charge config/io.yml si présent, sinon retourne des valeurs par défaut.
        """
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
        """Boucle principale Tkinter."""
        self.root.mainloop()

def run_app():
    app = MainWindow()
    app.run()