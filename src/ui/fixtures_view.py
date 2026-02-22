import tkinter as tk
from tkinter import ttk
import math


class FixturesView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # --- GESTION DE LA SOURIS ---
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)

        self.drag_data = {"x": 0, "y": 0, "item": None}

    def render(self, state):
        self.state = state  # On garde une référence pour les events
        self.canvas.delete("all")

        for fixture_id in sorted(state.fixtures.keys()):
            fixture = state.fixtures[fixture_id]
            self._draw_fixture(self.canvas, fixture_id, fixture, state)

    def _draw_fixture(self, canvas, fixture_id, fixture, state):
        # On utilise les coordonnées stockées
        x, y = fixture.x, fixture.y

        # Couleur
        intensity = fixture.dimmer / 255.0
        r = int(fixture.r * intensity)
        g = int(fixture.g * intensity)
        b = int(fixture.b * intensity)
        color_hex = f"#{r:02x}{g:02x}{b:02x}"

        radius = getattr(fixture, "radius", 20)

        # Contours
        is_selected = (state.selected_fixture_id == fixture_id)
        if is_selected:
            outline_color = "white"
            outline_width = 3
        else:
            outline_color = "#444444"
            outline_width = 2

        # On dessine le cercle avec un tag unique "fixture_ID"
        tag = f"fixture_{fixture_id}"
        canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill=color_hex,
            outline=outline_color,
            width=outline_width,
            tags=(tag, "movable")  # "movable" nous aidera à savoir ce qu'on peut bouger
        )

        if state.show_indexes:
            brightness = (r + g + b) / 3
            text_color = "black" if brightness > 100 else "white"
            canvas.create_text(x, y, text=str(fixture_id), fill=text_color, font=("Arial", 10, "bold"), tags=tag)

    # --- LOGIQUE SOURIS ---

    def _on_click(self, event):
        # On cherche l'objet sous la souris
        item = self.canvas.find_closest(event.x, event.y)
        tags = self.canvas.gettags(item)

        # On cherche le tag qui ressemble à "fixture_123"
        fixture_id = None
        for tag in tags:
            if tag.startswith("fixture_"):
                fixture_id = int(tag.split("_")[1])
                break

        if fixture_id is not None:
            # On sélectionne la fixture dans l'état global
            self.state.selected_fixture_id = fixture_id

            # On prépare le déplacement
            self.drag_data["item"] = fixture_id
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
        else:
            # Si on clique dans le vide, on désélectionne
            self.state.selected_fixture_id = None

    def _on_drag(self, event):
        # On ne bouge que si on est en mode WRITE
        if self.state.mode != "write":
            return

        fixture_id = self.drag_data["item"]
        if fixture_id is not None and fixture_id in self.state.fixtures:
            # Calcul du déplacement (delta)
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]

            # Mise à jour de la position dans l'état
            fixture = self.state.fixtures[fixture_id]
            fixture.x += dx
            fixture.y += dy

            # On met à jour la référence pour le prochain mouvement
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y

            # Note: L'affichage se mettra à jour au prochain 'render' (automatique)