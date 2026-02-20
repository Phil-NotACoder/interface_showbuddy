# fichier: src/ui/layout_canvas.py
import math
import time
import tkinter as tk
from tkinter import ttk

def _clamp01(x: float) -> float:
    try:
        return max(0.0, min(1.0, float(x)))
    except Exception:
        return 0.0

def _rgbaw_to_rgb255(r,g,b,a,w, dimmer, phase_on: bool):
    # Amber approx
    ar, ag, ab = 1.0, 0.75, 0.0
    R = r + w + a * ar
    G = g + w + a * ag
    B = b + w + a * ab
    R = max(0.0, min(1.0, R))
    G = max(0.0, min(1.0, G))
    B = max(0.0, min(1.0, B))
    mul = _clamp01(dimmer) * (1.0 if phase_on else 0.12)  # 12% visible en off-phase (outline)
    return (int(R*255*mul), int(G*255*mul), int(B*255*mul))

def _strobe_phase_on(strobe_val: float, fid: int, t_sec: float) -> bool:
    f = _clamp01(strobe_val) * 12.0  # 0..12 Hz
    if f <= 0.01:
        return True
    phase = (t_sec * f + (fid * 0.173)) % 1.0  # décalage par id
    return phase < 0.5  # duty 50%

class LayoutCanvas(ttk.Frame):
    """
    Canvas central (vue 'layout'):
      - Affiche les fixtures sous forme de cercles (fade approximé)
      - Drag & drop en mode EDIT (positions normalisées 0..1)
      - Outline: cyan si sélection, gris clair si off-phase
      - Indices: toggle via app_state.show_indexes
    """
    def __init__(self, parent, app_state, on_select_fixture=None):
        super().__init__(parent)
        self.app_state = app_state
        self.on_select_fixture = on_select_fixture

        self.canvas = tk.Canvas(self, bg="#111111", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # map: fid -> {"cx":int,"cy":int,"r":int}
        self._items = {}
        self._drag_id = None
        self._drag_offset = (0,0)

        # Bindings
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

    # Public: appelé depuis main_window.on_tick()
    def redraw(self, state):
        self.canvas.delete("all")
        self._items.clear()

        w = max(1, self.canvas.winfo_width())
        h = max(1, self.canvas.winfo_height())
        t = time.time()

        base = min(w, h)
        for fid in sorted(state.fixtures.keys()):
            fx = state.fixtures[fid]

            px = int(_clamp01(fx.x) * w)
            py = int(_clamp01(fx.y) * h)
            radius = int(max(4, _clamp01(fx.circle_size) * base))

            phase_on = _strobe_phase_on(fx.strobe, fid, t)
            r,g,b = _rgbaw_to_rgb255(fx.r, fx.g, fx.b, fx.a, fx.w, fx.dimmer, phase_on)

            # --- "fade" approximatif: plusieurs disques concentriques ---
            # 6 anneaux du plus grand (plus sombre) au plus petit (plus clair)
            rings = 6
            for i in range(rings, 0, -1):
                rr = int(radius * i / rings)
                if rr <= 0:
                    continue
                # éclaircir progressivement (simple interpolation vers blanc)
                k = i / rings
                cr = int(r + (255 - r) * (1 - k) * 0.15)
                cg = int(g + (255 - g) * (1 - k) * 0.15)
                cb = int(b + (255 - b) * (1 - k) * 0.15)
                color = f"#{cr:02x}{cg:02x}{cb:02x}"
                self.canvas.create_oval(px-rr, py-rr, px+rr, py+rr, fill=color, outline=color)

            # Outline
            if state.selected_fixture == fid:
                outline = "#00D1FF"
                width = 3
            else:
                outline = "#BBBBBB" if (not phase_on or fx.dimmer <= 0.001) else "#303030"
                width = 2
            self.canvas.create_oval(px-radius, py-radius, px+radius, py+radius, outline=outline, width=width)

            # Index (option)
            if state.show_indexes:
                self.canvas.create_text(px, py, text=str(fid), fill="#FFFFFF", font=("Segoe UI", 10, "bold"))

            # Petit boîtier (aide en EDIT)
            if state.edit_mode:
                self.canvas.create_rectangle(px-6, py-6, px+6, py+6, outline="#888888", width=1)

            self._items[fid] = {"cx": px, "cy": py, "r": radius}

    # --- Events ---
    def _pick(self, x, y):
        for fid, it in self._items.items():
            dx = x - it["cx"]
            dy = y - it["cy"]
            if dx*dx + dy*dy <= it["r"]*it["r"]:
                return fid
        return None

    def _on_click(self, ev):
        fid = self._pick(ev.x, ev.y)
        if fid is not None:
            self.app_state.selected_fixture = fid
            if callable(self.on_select_fixture):
                self.on_select_fixture(fid)
            if self.app_state.edit_mode:
                it = self._items.get(fid, {})
                self._drag_id = fid
                self._drag_offset = (ev.x - it.get("cx", ev.x), ev.y - it.get("cy", ev.y))
        else:
            self._drag_id = None

    def _on_drag(self, ev):
        if not self.app_state.edit_mode or self._drag_id is None:
            return
        w = max(1, self.canvas.winfo_width())
        h = max(1, self.canvas.winfo_height())
        nx = (ev.x - self._drag_offset[0]) / w
        ny = (ev.y - self._drag_offset[1]) / h
        nx = max(0.0, min(1.0, nx))
        ny = max(0.0, min(1.0, ny))
        fx = self.app_state.fixtures.get(self._drag_id)
        if fx:
            fx.x, fx.y = nx, ny

    def _on_release(self, _ev):
        self._drag_id = None