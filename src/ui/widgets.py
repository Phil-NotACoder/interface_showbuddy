import tkinter as tk
from tkinter import ttk
import math


# --- ATTENTION : Pas d'import de .widgets ici ! ---

class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)

        self.canvas = tk.Canvas(self, bg="#141414", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Gestion souris
        self.bind("<Enter>", self._bind_mouse)
        self.bind("<Leave>", self._unbind_mouse)
        self.canvas.bind("<Enter>", self._bind_mouse)
        self.canvas.bind("<Leave>", self._unbind_mouse)
        self.scrollable_frame.bind("<Enter>", self._bind_mouse)
        self.scrollable_frame.bind("<Leave>", self._unbind_mouse)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _bind_mouse(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mouse(self, event):
        under_mouse = self.winfo_containing(event.x_root, event.y_root)
        if under_mouse is not None and str(under_mouse).startswith(str(self)):
            return
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        # On ne scroll que si le contenu dépasse la hauteur visible
        if self.scrollable_frame.winfo_height() <= self.canvas.winfo_height():
            return

        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class RotaryDial(tk.Canvas):
    def __init__(self, parent, size=50, min_val=0, max_val=360, initial_val=0, command=None, bg="#141414"):
        super().__init__(parent, width=size, height=size, bg=bg, highlightthickness=0)
        self.size = size
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.command = command
        self.center = size / 2
        self.radius = (size / 2) - 5

        self.bind("<Button-1>", self._on_click)
        self.bind("<B1-Motion>", self._on_drag)

        self.draw()

    def draw(self):
        self.delete("all")
        self.create_oval(5, 5, self.size - 5, self.size - 5, outline="#444", width=2)

        angle_rad = math.radians(self.value - 90)
        x = self.center + self.radius * math.cos(angle_rad)
        y = self.center + self.radius * math.sin(angle_rad)

        self.create_line(self.center, self.center, x, y, fill="#d4af37", width=3)
        self.create_oval(x - 3, y - 3, x + 3, y + 3, fill="#d4af37", outline="")

    def _on_click(self, event):
        self._update_from_mouse(event.x, event.y)

    def _on_drag(self, event):
        self._update_from_mouse(event.x, event.y)

    def _update_from_mouse(self, x, y):
        dx = x - self.center
        dy = y - self.center
        rad = math.atan2(dy, dx)
        deg = math.degrees(rad) + 90
        if deg < 0: deg += 360

        self.value = deg
        self.draw()
        if self.command:
            self.command(self.value)

    def set_value(self, val):
        self.value = val
        self.draw()