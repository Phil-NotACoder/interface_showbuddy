import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class Toolbar(ttk.Frame):
    def __init__(self, parent,
                 on_fixture_count_changed: Optional[Callable[[int], None]] = None):
        super().__init__(parent)
        self.on_fixture_count_changed = on_fixture_count_changed
        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(1, weight=1)

        # Titre
        ttk.Label(self, text="ShowBuddy", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, padx=10, pady=5)

        # Spacer
        ttk.Frame(self).grid(row=0, column=1)

        # Nombre de fixtures
        ttk.Label(self, text="Fixtures:").grid(row=0, column=2, padx=(10, 5))

        self.spin_var = tk.IntVar(value=4)
        spin = ttk.Spinbox(self, from_=1, to=512, textvariable=self.spin_var, width=5, command=self._on_spin)
        spin.grid(row=0, column=3, padx=5)
        spin.bind("<Return>", self._on_spin)

    def _on_spin(self, _evt=None):
        try:
            val = self.spin_var.get()
            if self.on_fixture_count_changed:
                self.on_fixture_count_changed(val)
        except ValueError:
            pass

    def set_fixture_count(self, count: int):
        self.spin_var.set(count)