# fichier: src/ui/toolbar.py
import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
from core.modes import READ

class Toolbar(ttk.Frame):
    """
    Barre d'outils avec :
    - Mode READ/WRITE
    - Contrôle "Fixture count" (4..20) + bouton Apply
    - Toggle d'affichage: "Color preview" / "All sliders"
    - Bouton "Send test frame"
    - Indicateur de connexion + texte statut

    Callbacks attendus (MainWindow):
      - on_mode_changed(mode:str)
      - on_send_test()
      - on_apply_fixture_count(count:int)
      - on_view_mode_changed(view_mode:str)  # "color" | "sliders"
    """

    def __init__(
        self,
        parent,
        on_mode_changed: Optional[Callable[[str], None]] = None,
        on_send_test: Optional[Callable[[], None]] = None,
        on_apply_fixture_count: Optional[Callable[[int], None]] = None,
        on_view_mode_changed: Optional[Callable[[str], None]] = None,
    ):
        super().__init__(parent)
        self._on_mode_changed = on_mode_changed
        self._on_send_test = on_send_test
        self._on_apply_fixture_count = on_apply_fixture_count
        self._on_view_mode_changed = on_view_mode_changed

        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        # Colonnes
        for c in range(0, 9):
            self.columnconfigure(c, weight=0)
        self.columnconfigure(9, weight=1)  # push status to the right
        self.columnconfigure(10, weight=0)
        self.columnconfigure(11, weight=0)

        # Mode
        ttk.Label(self, text="Mode:").grid(row=0, column=0, padx=(8,4), pady=6, sticky="w")
        self.mode_var = tk.StringVar(value=READ)
        self.mode_combo = ttk.Combobox(self, textvariable=self.mode_var, values=("read","write"), width=8, state="readonly")
        self.mode_combo.grid(row=0, column=1, padx=(0,8), pady=6, sticky="w")
        self.mode_combo.bind("<<ComboboxSelected>>", self._on_mode_combo)

        # View mode (Color preview / All sliders)
        ttk.Label(self, text="View:").grid(row=0, column=2, padx=(8,4), pady=6, sticky="w")
        self.view_mode_var = tk.StringVar(value="color")
        self.view_combo = ttk.Combobox(self, textvariable=self.view_mode_var, values=("color","sliders"), width=9, state="readonly")
        self.view_combo.grid(row=0, column=3, padx=(0,8), pady=6, sticky="w")
        self.view_combo.bind("<<ComboboxSelected>>", self._on_view_combo)

        # Fixture count + Apply
        ttk.Label(self, text="Fixtures:").grid(row=0, column=4, padx=(8,4), pady=6, sticky="w")
        self.count_var = tk.IntVar(value=4)
        self.count_spin = ttk.Spinbox(self, from_=4, to=20, textvariable=self.count_var, width=5)
        self.count_spin.grid(row=0, column=5, padx=(0,6), pady=6, sticky="w")
        self.apply_btn = ttk.Button(self, text="Apply", command=self._on_apply_click)
        self.apply_btn.grid(row=0, column=6, padx=(0,8), pady=6, sticky="w")

        # Send test frame
        self.btn_send = ttk.Button(self, text="Send test frame", command=self._on_send_btn)
        self.btn_send.grid(row=0, column=7, padx=8, pady=6, sticky="w")

        # Indicateur de connexion + statut (à droite)
        self._conn_var = tk.StringVar(value="●")
        self._conn_label = ttk.Label(self, textvariable=self._conn_var, foreground="#888")
        self._conn_label.grid(row=0, column=10, padx=(8, 4), pady=6, sticky="e")

        self._status_var = tk.StringVar(value="Idle")
        self._status_label = ttk.Label(self, textvariable=self._status_var)
        self._status_label.grid(row=0, column=11, padx=(0, 8), pady=6, sticky="e")

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def _on_mode_combo(self, _evt=None):
        mode = (self.mode_var.get() or "").strip().lower()
        if mode not in ("read","write"):
            mode = READ
            self.mode_var.set(mode)
        if self._on_mode_changed:
            self._on_mode_changed(mode)

    def _on_view_combo(self, _evt=None):
        vm = (self.view_mode_var.get() or "").strip().lower()
        if vm not in ("color","sliders"):
            vm = "color"
            self.view_mode_var.set(vm)
        if self._on_view_mode_changed:
            self._on_view_mode_changed(vm)

    def _on_apply_click(self):
        try:
            val = int(self.count_var.get())
        except Exception:
            val = 4
        val = min(20, max(4, val))
        self.count_var.set(val)
        if self._on_apply_fixture_count:
            self._on_apply_fixture_count(val)

    def _on_send_btn(self):
        if self._on_send_test:
            self._on_send_test()

    # ------------------------------------------------------------------
    # API pour MainWindow
    # ------------------------------------------------------------------
    def set_connected(self, connected: bool):
        if connected:
            self._conn_label.configure(foreground="#28c840")
            self._conn_var.set("●")
        else:
            self._conn_label.configure(foreground="#888")
            self._conn_var.set("●")

    def set_status_text(self, text: str):
        self._status_var.set(text or "")

    def set_fixture_count_value(self, count: int):
        self.count_var.set(int(count))

    def set_view_mode_value(self, mode: str):
        mode = (mode or "color").lower()
        if mode not in ("color","sliders"):
            mode = "color"
        self.view_mode_var.set(mode)