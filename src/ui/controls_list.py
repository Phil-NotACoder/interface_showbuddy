# fichier: src/ui/controls_list.py
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

PARAMS = [
    ("R", "r"), ("G", "g"), ("B", "b"), ("A", "a"), ("W", "w"),
    ("Dim", "dimmer"), ("Strb", "strobe"),
]

def _clamp01(x: float) -> float:
    try:
        return max(0.0, min(1.0, float(x)))
    except Exception:
        return 0.0

class ControlsListView(ttk.Frame):
    """
    Panneau scrollable contenant un groupe de 7 sliders pour chaque fixture.
    - Appeler render(state) à chaque tick (léger).
    - Callback on_change(fid:int, name:str, value:float) pour propager les modifications.
    - La vue se régénère si l'ensemble des fixture IDs a changé.
    """

    def __init__(self, parent, on_change: Optional[Callable[[int,str,float], None]] = None):
        super().__init__(parent)
        self._on_change = on_change

        # Scrollable area
        self.canvas = tk.Canvas(self, bg="#141414", highlightthickness=0)
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)

        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0,0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.canvas.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.vsb.pack(fill=tk.Y, side=tk.RIGHT)

        # state
        self._built_for_ids = []
        self._widgets = {}   # fid -> { name -> (scale, var, labelVar) }

    # ------------------------------------------------------------------
    def render(self, state) -> None:
        ids = sorted(state.fixtures.keys())
        if ids != self._built_for_ids:
            self._rebuild(ids, state)

        # Update values from state (no callback loop)
        for fid in ids:
            fx = state.fixtures.get(fid)
            if not fx:
                continue
            wmap = self._widgets.get(fid, {})
            for short, name in PARAMS:
                var = wmap.get(name, {}).get("var")
                valLabel = wmap.get(name, {}).get("val")
                if var is None or valLabel is None:
                    continue
                cur = getattr(fx, name if name != "dim" else "dimmer", getattr(fx, name, 0.0))
                cur = _clamp01(cur)
                if abs(var.get() - cur) > 1e-6:
                    var.set(cur)
                    valLabel.set(f"{cur:.2f}")

    # ------------------------------------------------------------------
    def _rebuild(self, ids, state):
        for child in self.inner.winfo_children():
            child.destroy()
        self._widgets.clear()

        row = 0
        for fid in ids:
            group = ttk.LabelFrame(self.inner, text=f"Fixture {fid}", padding=8)
            group.grid(row=row, column=0, sticky="ew", padx=8, pady=6)
            group.columnconfigure(1, weight=1)
            self._widgets[fid] = {}

            fx = state.fixtures.get(fid)

            r2 = 0
            for short, name in PARAMS:
                ttk.Label(group, text=short, width=6).grid(row=r2, column=0, sticky="w", pady=2)
                var = tk.DoubleVar(value=_clamp01(getattr(fx, name if name!="dim" else "dimmer", getattr(fx, name, 0.0)) if fx else 0.0))
                scale = ttk.Scale(group, from_=0.0, to=1.0, orient=tk.HORIZONTAL, variable=var,
                                  command=lambda _v, _fid=fid, _n=name, _var=var: self._on_scale(_fid, _n, _var))
                scale.grid(row=r2, column=1, sticky="ew", padx=6, pady=2)
                valVar = tk.StringVar(value=f"{var.get():.2f}")
                ttk.Label(group, textvariable=valVar, width=6).grid(row=r2, column=2, sticky="e", pady=2)

                self._widgets[fid][name] = {"scale": scale, "var": var, "val": valVar}
                r2 += 1

            row += 1

        self._built_for_ids = ids

    def _on_scale(self, fid: int, name: str, var: tk.DoubleVar):
        v = _clamp01(var.get())
        var.set(v)
        if self._on_change:
            self._on_change(fid, name, v)