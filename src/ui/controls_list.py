import tkinter as tk
from tkinter import ttk
from .widgets import ScrollableFrame


class ControlsListView(ttk.Frame):
    def __init__(self, parent, on_change=None):
        super().__init__(parent)
        self.on_change = on_change

        # Dictionnaire pour stocker les widgets existants {fixture_id: {param: variable, frame: widget}}
        self.rows = {}

        self.scroll_frame = ScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True)
        self.inner = self.scroll_frame.scrollable_frame

    def render(self, state):
        current_ids = set(state.fixtures.keys())
        existing_ids = set(self.rows.keys())

        # 1. Supprimer les fixtures qui n'existent plus
        for fid in existing_ids - current_ids:
            self.rows[fid]["frame"].destroy()
            del self.rows[fid]

        # 2. Créer les nouvelles fixtures
        for fid in current_ids - existing_ids:
            self._create_fixture_row(fid, state.fixtures[fid])

        # 3. Mettre à jour les valeurs (sans rien détruire)
        for fid in current_ids:
            self._update_fixture_values(fid, state.fixtures[fid], state.selected_fixture_id)

    def _create_fixture_row(self, fid, fixture):
        # Cadre principal pour une fixture
        frame = tk.Frame(self.inner, bg="#141414", bd=1, relief="solid")
        frame.pack(fill="x", padx=5, pady=5)

        # En-tête
        header = tk.Label(frame, text=f"FIXTURE {fid}", fg="white", bg="#222", font=("Arial", 10, "bold"), anchor="w")
        header.pack(fill="x", padx=2, pady=2)

        row_data = {"frame": frame, "vars": {}}

        # Liste des sliders
        controls = [
            ("r", "R", "#ff4444"),
            ("g", "G", "#44ff44"),
            ("b", "B", "#4444ff"),
            ("amber", "A", "#ffaa00"),
            ("white", "W", "#ffffff"),
            ("dimmer", "D", "#aaaaaa"),
            ("strobe", "S", "#cccccc")
        ]

        for param, label, color in controls:
            sub_frame = tk.Frame(frame, bg="#141414")
            sub_frame.pack(fill="x", padx=2, pady=1)

            tk.Label(sub_frame, text=label, fg=color, bg="#141414", width=2, font=("Arial", 8, "bold")).pack(
                side="left")

            var = tk.DoubleVar(value=getattr(fixture, param, 0))
            row_data["vars"][param] = var

            scale = tk.Scale(sub_frame, variable=var, from_=0, to=255, orient="horizontal",
                             bg="#141414", fg="white", troughcolor="#333",
                             activebackground=color, highlightthickness=0, showvalue=0)
            scale.pack(side="left", fill="x", expand=True)

            # Callback
            var.trace_add("write", lambda *args, p=param, v=var, f=fid: self._on_val_change(f, p, v))

        self.rows[fid] = row_data

    def _update_fixture_values(self, fid, fixture, selected_id):
        row_data = self.rows[fid]

        # Mise en évidence visuelle si sélectionné
        bg_color = "#444" if fid == selected_id else "#141414"
        # On pourrait changer la couleur de fond du header ici si on voulait

        # Mise à jour des sliders si la valeur a changé (ex: via load ou autre)
        for param, var in row_data["vars"].items():
            target_val = getattr(fixture, param, 0)
            if abs(var.get() - target_val) > 0.5:
                var.set(target_val)

    def _on_val_change(self, fid, param, var):
        try:
            val = var.get()
            if self.on_change:
                self.on_change(fid, param, val)
        except:
            pass