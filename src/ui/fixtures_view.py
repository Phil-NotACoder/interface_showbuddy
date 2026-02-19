# src/ui/fixtures_view.py

import tkinter as tk
from math import ceil
from typing import Callable, Dict, Tuple, Optional

class FixturesView(tk.Canvas):
    """
    Step 2b :
    - Dessine 12 fixtures en grille
    - Détection de clic (sélection)
    - Affiche un halo bleu autour de la sélection
    - Appelle un callback on_select(fixture_id) fourni par MainWindow
    """

    def __init__(self, master, on_select: Callable[[Optional[int]], None] = None, **kwargs):
        super().__init__(master, background='#111319', highlightthickness=0, **kwargs)
        self.placeholder_count = 12
        self.on_select = on_select

        # mapping: fixture_id -> (cx, cy, r, body_id, label_id, halo_id)
        self._items: Dict[int, Tuple[float, float, float, int, int, Optional[int]]] = {}
        self._selected_id: Optional[int] = None

        # Bind events
        self.bind('<Configure>', self._on_resize)
        self.bind('<Button-1>', self._on_click)

        self._draw()

    # ----------------------------------------------------------------------
    # EVENT : Redessiner lors d'un resize
    # ----------------------------------------------------------------------
    def _on_resize(self, event):
        self._draw()

    # ----------------------------------------------------------------------
    # API : sélection commandée par MainWindow
    # ----------------------------------------------------------------------
    def set_selected(self, fixture_id: Optional[int]):
        """Met à jour l'affichage en fonction d'un id sélectionné (ou None)."""
        self._selected_id = fixture_id

        # Effacer tous les halos existants
        for fid, (cx, cy, r, body_id, label_id, halo_id) in list(self._items.items()):
            if halo_id is not None:
                self.delete(halo_id)
                self._items[fid] = (cx, cy, r, body_id, label_id, None)

        # Dessiner le halo sur le fixture sélectionné
        if fixture_id is not None and fixture_id in self._items:
            cx, cy, r, body_id, label_id, _ = self._items[fixture_id]
            halo = self.create_oval(
                cx - r*1.35, cy - r*1.35, cx + r*1.35, cy + r*1.35,
                outline='#4da3ff', width=3
            )
            self._items[fixture_id] = (cx, cy, r, body_id, label_id, halo)

    # ----------------------------------------------------------------------
    # EVENT : clic souris
    # ----------------------------------------------------------------------
    def _on_click(self, event):
        fid = self._hit_test(event.x, event.y)

        if fid is None:
            # clic dans le vide -> désélection
            self.set_selected(None)
            if callable(self.on_select):
                self.on_select(None)
        else:
            self.set_selected(fid)
            if callable(self.on_select):
                self.on_select(fid)

    # ----------------------------------------------------------------------
    # Dessin complet
    # ----------------------------------------------------------------------
    def _draw(self):
        self.delete('all')

        previous_selected = self._selected_id
        self._items.clear()

        w = max(self.winfo_width(), 1)
        h = max(self.winfo_height(), 1)

        title = 'Fixtures — Click to select (Step 2b)\n/ui/select {id}'
        self.create_text(
            w/2, 24, text=title,
            fill='#9aa3b2', font=('Segoe UI', 12),
            justify='center'
        )

        # grille calculée
        count = self.placeholder_count
        cols = 4
        rows = ceil(count / cols)
        margin = 40
        title_h = 24

        grid_w = w - 2*margin
        grid_h = h - 2*margin - title_h

        if grid_w <= 0 or grid_h <= 0:
            return

        cell_w = grid_w / cols
        cell_h = grid_h / rows
        radius = min(cell_w, cell_h) * 0.3

        idx = 0
        for r_idx in range(rows):
            for c_idx in range(cols):
                if idx >= count:
                    break

                fid = idx + 1
                cx = margin + c_idx*cell_w + cell_w/2
                cy = margin + title_h + r_idx*cell_h + cell_h/2

                # corps du projecteur
                body = self.create_oval(
                    cx - radius, cy - radius,
                    cx + radius, cy + radius,
                    fill='#243042', outline='#3a4a64', width=2
                )

                # étiquette
                text_id = self.create_text(
                    cx, cy, text=str(fid),
                    fill='#d1d7e0', font=('Segoe UI', 11, 'bold')
                )

                self._items[fid] = (cx, cy, radius, body, text_id, None)
                idx += 1

        # si un fixture était sélectionné avant redessin
        if previous_selected is not None:
            self.set_selected(previous_selected)

    # ----------------------------------------------------------------------
    # Détection de clic
    # ----------------------------------------------------------------------
    def _hit_test(self, x, y) -> Optional[int]:
        for fid, (cx, cy, r, *_rest) in self._items.items():
            dx = x - cx
            dy = y - cy
            if dx*dx + dy*dy <= r*r:
                return fid
        return None