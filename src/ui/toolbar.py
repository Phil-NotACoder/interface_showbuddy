import tkinter as tk
from tkinter import ttk
from core.modes import READ, WRITE, normalize_mode

class Toolbar(ttk.Frame):
    """
    Barre d’outils en haut :
    - Boutons READ / WRITE
    - Indicateur de connexion (rond rouge/vert)
    - Texte d’état
    """

    def __init__(self, master, on_mode_changed):
        super().__init__(master)
        self.on_mode_changed = on_mode_changed

        # Indicateur de connexion (petit rond)
        self.conn_indicator = tk.Canvas(self, width=14, height=14, highlightthickness=0)
        self.conn_dot = self.conn_indicator.create_oval(2, 2, 12, 12,
                                                        fill="#777777",
                                                        outline="#555555")
        self.conn_indicator.pack(side=tk.LEFT, padx=(6, 4), pady=6)

        ttk.Label(self, text="Mode:").pack(side=tk.LEFT, padx=(2, 4))
        self.mode_var = tk.StringVar(value=READ)

        rb_read = ttk.Radiobutton(self, text="READ", value=READ,
                                  variable=self.mode_var,
                                  command=self._on_mode_click)
        rb_write = ttk.Radiobutton(self, text="WRITE", value=WRITE,
                                   variable=self.mode_var,
                                   command=self._on_mode_click)

        rb_read.pack(side=tk.LEFT, padx=2)
        rb_write.pack(side=tk.LEFT, padx=2)

        self.status_var = tk.StringVar(value="Not connected")
        ttk.Label(self, textvariable=self.status_var).pack(side=tk.RIGHT, padx=8)

    def _on_mode_click(self):
        mode = normalize_mode(self.mode_var.get())
        if callable(self.on_mode_changed):
            self.on_mode_changed(mode)

    def set_connected(self, connected: bool):
        color = "#2ecc71" if connected else "#c0392b"
        self.conn_indicator.itemconfig(self.conn_dot, fill=color)

    def set_status_text(self, text: str):
        self.status_var.set(text)

    def set_mode_value(self, mode: str):
        self.mode_var.set(normalize_mode(mode))