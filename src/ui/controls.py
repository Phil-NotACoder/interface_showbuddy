
# fichier: src/ui/controls.py
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

PARAMS = [
    ("R", "r", "#ff4040"),
    ("G", "g", "#40ff40"),
    ("B", "b", "#4040ff"),
    ("A", "a", "#aaaaaa"),
    ("W", "w", "#ffffff"),
    ("Dimmer", "dimmer", "#ffffff"),
    ("Strobe", "strobe", "#b36bff"),
]

def _clamp01(x: float) -> float:
    try:
        return max(0.0, min(1.0, float(x)))
    except Exception:
        return 0.0

class ControlsPanel(ttk.Frame):
    """
    Panneau de sliders pour la fixture sélectionnée (R,G,B,A,W,Dimmer,Strobe).
    - on_change(param_name: str, value: float) est appelé à chaque changement.
    - set_mode(write: bool) active/désactive les contrôles selon le mode.
    - load_from_fixture(fid, fx) affiche les valeurs de la fixture sélectionnée.
    """

    def __init__(self, parent, on_change: Optional[Callable[[str, float], None]] = None):
        super().__init__(parent, padding=10)
        self._on_change = on_change
        self._selected_id: Optional[int] = None
        self._updating = False  # évite boucle lors du chargement

        # Titre
        self._title_var = tk.StringVar(value="No fixture selected")
        title = ttk.Label(self, textvariable=self._title_var, font=("Segoe UI", 10, "bold"))
        title.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        # Construire les lignes (label, scale, valeur)
        self._vars = {}     # name -> tk.DoubleVar
        self._value_labels = {}  # name -> tk.StringVar

        row = 1
        for label_txt, name, color in PARAMS:
            ttk.Label(self, text=label_txt, width=8).grid(row=row, column=0, sticky="w", pady=4)

            var = tk.DoubleVar(value=0.0)
            self._vars[name] = var

            scale = ttk.Scale(
                self, from_=0.0, to=1.0, orient=tk.HORIZONTAL, variable=var,
                command=lambda _v, n=name: self._on_scale(n)
            )
            scale.grid(row=row, column=1, sticky="ew", padx=6, pady=4)
            self.columnconfigure(1, weight=1)

            val_var = tk.StringVar(value="0.00")
            self._value_labels[name] = val_var
            ttk.Label(self, textvariable=val_var, width=6).grid(row=row, column=2, sticky="e", pady=4)

            row += 1

        # Séparateur & info mode
        ttk.Separator(self, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=3, sticky="ew", pady=(8, 6))
        row += 1
        self._mode_var = tk.StringVar(value="Mode: READ (sliders disabled)")
        ttk.Label(self, textvariable=self._mode_var, foreground="#888").grid(row=row, column=0, columnspan=3, sticky="w")

        # État d'activation
        self._enabled = False
        self._set_enabled(False)

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------
    def set_mode(self, mode: str):
        write = (mode.lower() == "write")
        self._mode_var.set(f"Mode: {'WRITE' if write else 'READ'} ({'sliders enabled' if write else 'sliders disabled'})")
        self._set_enabled(write)

    def set_selected_id(self, fid: Optional[int]):
        self._selected_id = fid
        if fid is None:
            self._title_var.set("No fixture selected")
        else:
            self._title_var.set(f"Fixture {fid}")

    def load_from_fixture(self, fid: int, fx) -> None:
        """Charge les valeurs de la fixture dans les sliders (sans déclencher les callbacks)."""
        self._selected_id = fid
        self._title_var.set(f"Fixture {fid}")
        self._updating = True
        try:
            # Met à jour les seven vars
            self._vars["r"].set(_clamp01(getattr(fx, "r", 0.0)))
            self._vars["g"].set(_clamp01(getattr(fx, "g", 0.0)))
            self._vars["b"].set(_clamp01(getattr(fx, "b", 0.0)))
            self._vars["a"].set(_clamp01(getattr(fx, "a", 0.0)))
            self._vars["w"].set(_clamp01(getattr(fx, "w", 0.0)))
            self._vars["dimmer"].set(_clamp01(getattr(fx, "dimmer", 0.0)))
            self._vars["strobe"].set(_clamp01(getattr(fx, "strobe", 0.0)))
            self._refresh_value_labels()
        finally:
            self._updating = False

    # ------------------------------------------------------------------
    # Internes
    # ------------------------------------------------------------------
    def _set_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for child in self.winfo_children():
            if isinstance(child, ttk.Scale):
                child.configure(state=state)
        self._enabled = enabled

    def _refresh_value_labels(self):
        for name, var in self._vars.items():
            self._value_labels[name].set(f"{var.get():.2f}")

    def _on_scale(self, name: str):
        if self._updating:
            return
        v = _clamp01(self._vars[name].get())
        self._vars[name].set(v)
        self._value_labels[name].set(f"{v:.2f}")
        if self._on_change:
            self._on_change(name, v)