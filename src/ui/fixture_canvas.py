import tkinter as tk
import math


class FixtureCanvas(tk.Canvas):
    def __init__(self, parent, state, on_select=None, on_move=None):
        super().__init__(parent, bg="#111", highlightthickness=0)
        self.state = state
        self.on_select = on_select
        self.on_move = on_move

        self.bind("<Button-1>", self._on_click)
        self.bind("<B1-Motion>", self._on_drag)

        self._drag_data = {"x": 0, "y": 0, "item": None}

    def render(self, state):
        self.delete("all")

        w = self.winfo_width()
        h = self.winfo_height()
        for i in range(0, w, 50):
            self.create_line(i, 0, i, h, fill="#222")
        for i in range(0, h, 50):
            self.create_line(0, i, w, i, fill="#222")

        for fid, fix in state.fixtures.items():
            self._draw_fixture(fid, fix, state.selected_fixture_id == fid)

    def _draw_fixture(self, fid, fix, is_selected):
        # --- PROTECTION ANTI-CRASH (ZOMBIE DATA) ---
        # On utilise getattr pour donner une valeur par défaut si l'attribut manque.
        x = getattr(fix, "pos_x", 100 + (fid * 50))
        y = getattr(fix, "pos_y", 100)
        shape = getattr(fix, "shape", "circle")
        angle = getattr(fix, "angle", 0.0)
        beam_len = getattr(fix, "beam_length", 100.0)
        cone_angle = getattr(fix, "cone_angle", 45.0)
        size = getattr(fix, "size", 20.0)

        # Couleurs (supporte les vieux noms red/green/blue au cas où)
        r = getattr(fix, "r", getattr(fix, "red", 0))
        g = getattr(fix, "g", getattr(fix, "green", 0))
        b = getattr(fix, "b", getattr(fix, "blue", 0))
        dimmer = getattr(fix, "dimmer", 0)

        if dimmer > 0:
            fill_color = self._rgb_to_hex(r, g, b)
            outline_color = "white" if is_selected else ""
        else:
            fill_color = ""
            outline_color = "white" if is_selected else "#555"

        tags = (f"fixture_{fid}", "fixture")

        if shape == "beam":
            # --- BEAM ---
            angle_rad = math.radians(angle - 90)
            cone_width_rad = math.radians(cone_angle / 2)

            p1_x, p1_y = x, y
            p2_x = x + beam_len * math.cos(angle_rad - cone_width_rad)
            p2_y = y + beam_len * math.sin(angle_rad - cone_width_rad)
            p3_x = x + beam_len * math.cos(angle_rad + cone_width_rad)
            p3_y = y + beam_len * math.sin(angle_rad + cone_width_rad)

            self.create_polygon(p1_x, p1_y, p2_x, p2_y, p3_x, p3_y,
                                fill=fill_color if fill_color else "#333",
                                outline=outline_color,
                                stipple="gray50" if dimmer < 255 else "",
                                tags=tags)

            self.create_oval(x - 5, y - 5, x + 5, y + 5, fill="white", tags=tags)

        else:
            # --- ROUND ---
            rad = size / 2
            self.create_oval(x - rad, y - rad, x + rad, y + rad,
                             fill=fill_color,
                             outline=outline_color,
                             width=2 if is_selected else 1,
                             tags=tags)

            self.create_text(x, y, text=str(fid), fill="white" if dimmer < 128 else "black", font=("Arial", 8, "bold"),
                             tags=tags)

    def _rgb_to_hex(self, r, g, b):
        return f"#{int(r):02x}{int(g):02x}{int(b):02x}"

    def _on_click(self, event):
        item = self.find_closest(event.x, event.y)
        tags = self.gettags(item)
        for tag in tags:
            if tag.startswith("fixture_"):
                fid = int(tag.split("_")[1])
                if self.on_select:
                    self.on_select(fid)
                self._drag_data["item"] = fid
                self._drag_data["x"] = event.x
                self._drag_data["y"] = event.y
                return

        if self.on_select:
            self.on_select(None)

    def _on_drag(self, event):
        fid = self._drag_data["item"]
        if fid is not None and self.on_move:
            dx = event.x - self._drag_data["x"]
            dy = event.y - self._drag_data["y"]

            # On récupère la fixture
            fix = self.state.fixtures[fid]

            # CORRECTION ICI : On utilise la même formule que dans render()
            # pour éviter le saut si la position n'est pas encore enregistrée.
            default_x = 100 + (fid * 50)

            curr_x = getattr(fix, "pos_x", default_x)
            curr_y = getattr(fix, "pos_y", 100)

            new_x = curr_x + dx
            new_y = curr_y + dy

            self.on_move(fid, "pos_x", new_x)
            self.on_move(fid, "pos_y", new_y)

            self._drag_data["x"] = event.x
            self._drag_data["y"] = event.y