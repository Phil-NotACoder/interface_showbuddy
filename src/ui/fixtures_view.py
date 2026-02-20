# fichier: src/ui/fixtures_view.py
import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, Optional

BAR_HEIGHT = 10          # hauteur d'une barre (rgba, w, dimmer, strobe)
BAR_SPACING = 4          # espace vertical entre barres
CELL_PADDING = 8         # marge intérieure d'une cellule
CELL_W = 160             # largeur d'une cellule (fixe, grille auto)
CELL_H = 140             # hauteur d'une cellule
COLS = 5                 # nombre de colonnes pour l'auto-grid

# Couleurs de barres
COLOR_R = "#ff4040"
COLOR_G = "#40ff40"
COLOR_B = "#4040ff"
COLOR_A = "#aaaaaa"      # alpha = gris pour la visu
COLOR_W = "#ffffff"
COLOR_DIMMER_BG = "#2a2a2a"
COLOR_DIMMER = "#ffffff"
COLOR_STROBE = "#b36bff"  # violet

# Contour sélection
SELECT_OUTLINE = "#00c8ff"
SELECT_WIDTH = 3

def _clamp01(x: float) -> float:
    try:
        return max(0.0, min(1.0, float(x)))
    except Exception:
        return 0.0

class FixturesView(ttk.Frame):
    """
    Vue principale qui dessine les fixtures en grille.
    Chaque fixture est une cellule avec 7 barres : R G B A W | Dimmer | Strobe
    - on_select(fid: int | None) est appelé quand l'utilisateur clique une cellule
    - render(state) est appelé depuis la boucle UI pour redessiner.
    """
    def __init__(self, parent, on_select: Optional[Callable[[Optional[int]], None]] = None):
        super().__init__(parent)
        self._on_select = on_select

        # Canvas pour dessiner la grille
        self.canvas = tk.Canvas(self, bg="#151515", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Données de placement (id -> bbox)
        self._cell_bbox: Dict[int, tuple[int, int, int, int]] = {}
        self._selected_id: Optional[int] = None

        # Binding clic
        self.canvas.bind("<Button-1>", self._on_click)

        # Mise à l'échelle responsive
        self.bind("<Configure>", self._on_resize)

        # Cache dernière taille
        self._last_w = 0
        self._last_h = 0

        # Dernier état rendu (référence non conservée, on copie ce qu'il faut)
        self._last_fixture_ids = []

    # ----------------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------------
    def render(self, state) -> None:
        """
        Redessine toutes les cellules à partir de `state.fixtures`.
        `state` est une instance de core.state.AppState.
        """
        # Calcule la grille à partir des ids actuels
        fixture_ids = sorted(state.fixtures.keys())
        if not fixture_ids:
            # Si aucun fixture reçu pour le moment, on efface et affiche un message
            self.canvas.delete("all")
            self.canvas.create_text(
                self.canvas.winfo_width() // 2,
                self.canvas.winfo_height() // 2,
                text="En attente de données...\n(/app/hello, /fixture/*, /frame)",
                fill="#888",
                font=("Segoe UI", 12),
                justify="center"
            )
            return

        # Redessiner si la liste d'ids a changé, ou si la taille a changé,
        # ou tout simplement à chaque frame (on garde simple).
        self.canvas.delete("all")
        self._cell_bbox.clear()

        # Calcul grille
        cols = max(1, COLS)
        # cell width/height peuvent rester fixes pour garder la lisibilité.
        cell_w = CELL_W
        cell_h = CELL_H

        # Calcul du décalage pour centrer la grille
        W = max(1, self.canvas.winfo_width())
        H = max(1, self.canvas.winfo_height())

        rows = (len(fixture_ids) + cols - 1) // cols
        grid_w = cols * cell_w
        grid_h = rows * cell_h

        offset_x = max(0, (W - grid_w) // 2)
        offset_y = max(0, (H - grid_h) // 2)

        # Dessin des cellules
        for idx, fid in enumerate(fixture_ids):
            r = idx // cols
            c = idx % cols
            x0 = offset_x + c * cell_w
            y0 = offset_y + r * cell_h
            x1 = x0 + cell_w
            y1 = y0 + cell_h

            self._draw_cell(fid, (x0, y0, x1, y1), state)
            self._cell_bbox[fid] = (x0, y0, x1, y1)

        # Sélection visuelle si existante
        self._selected_id = state.selected_fixture
        if self._selected_id in self._cell_bbox:
            x0, y0, x1, y1 = self._cell_bbox[self._selected_id]
            self.canvas.create_rectangle(
                x0 + 2, y0 + 2, x1 - 2, y1 - 2,
                outline=SELECT_OUTLINE, width=SELECT_WIDTH
            )

        self._last_fixture_ids = fixture_ids

    # ----------------------------------------------------------------------
    # Dessin d'une cellule
    # ----------------------------------------------------------------------
    def _draw_cell(self, fid: int, bbox: tuple[int, int, int, int], state) -> None:
        x0, y0, x1, y1 = bbox

        # Fond cellule
        self.canvas.create_rectangle(x0, y0, x1, y1, fill="#1b1b1b", outline="#2c2c2c")

        # Titre (id)
        title = f"Fixture {fid}"
        self.canvas.create_text(
            x0 + CELL_PADDING, y0 + CELL_PADDING,
            text=title, anchor="nw", fill="#d0d0d0", font=("Segoe UI", 10, "bold")
        )

        # Récupération des valeurs
        fx = state.fixtures.get(fid)
        if fx is None:
            # Placeholder si pas encore reçu quoi que ce soit
            return

        # Zone des barres
        bx0 = x0 + CELL_PADDING
        bx1 = x1 - CELL_PADDING
        by = y0 + CELL_PADDING + 20  # sous le titre

        # Barres couleur RGBAW
        self._draw_bar(bx0, by, bx1, by + BAR_HEIGHT, fx.r, COLOR_R, "R")
        by += BAR_HEIGHT + BAR_SPACING
        self._draw_bar(bx0, by, bx1, by + BAR_HEIGHT, fx.g, COLOR_G, "G")
        by += BAR_HEIGHT + BAR_SPACING
        self._draw_bar(bx0, by, bx1, by + BAR_HEIGHT, fx.b, COLOR_B, "B")
        by += BAR_HEIGHT + BAR_SPACING
        self._draw_bar(bx0, by, bx1, by + BAR_HEIGHT, fx.a, COLOR_A, "A")
        by += BAR_HEIGHT + BAR_SPACING
        self._draw_bar(bx0, by, bx1, by + BAR_HEIGHT, fx.w, COLOR_W, "W", outline="#3a3a3a")
        by += BAR_HEIGHT + BAR_SPACING

        # Dimmer (fond sombre + remplissage blanc)
        self._draw_bar(bx0, by, bx1, by + BAR_HEIGHT, fx.dimmer, COLOR_DIMMER, "Dim", bg=COLOR_DIMMER_BG)
        by += BAR_HEIGHT + BAR_SPACING

        # Strobe (violet)
        self._draw_bar(bx0, by, bx1, by + BAR_HEIGHT, fx.strobe, COLOR_STROBE, "Strb")
        # by += ...

    def _draw_bar(
        self,
        x0: int, y0: int, x1: int, y1: int,
        value: float,
        color: str,
        label: str,
        bg: Optional[str] = None,
        outline: Optional[str] = None,
    ) -> None:
        v = _clamp01(value)
        # fond
        if bg:
            self.canvas.create_rectangle(x0, y0, x1, y1, fill=bg, outline=outline or bg)
        else:
            self.canvas.create_rectangle(x0, y0, x1, y1, fill="#252525", outline=outline or "#303030")

        # remplissage proportionnel
        width = x1 - x0
        fill_w = int(width * v)
        if fill_w > 0:
            self.canvas.create_rectangle(x0, y0, x0 + fill_w, y1, fill=color, outline=color)

        # label (à gauche)
        self.canvas.create_text(x0 - 4, (y0 + y1) // 2, text=label, anchor="e", fill="#8a8a8a", font=("Segoe UI", 9))

    # ----------------------------------------------------------------------
    # Interaction
    # ----------------------------------------------------------------------
    def _on_click(self, event) -> None:
        # Trouver la cellule cliquée
        x, y = event.x, event.y
        clicked_id = None
        for fid, (x0, y0, x1, y1) in self._cell_bbox.items():
            if x0 <= x <= x1 and y0 <= y <= y1:
                clicked_id = fid
                break

        # Toggle si on reclique la même cellule -> désélection
        if clicked_id is not None:
            if self._selected_id == clicked_id:
                self._selected_id = None
                if self._on_select:
                    self._on_select(None)
            else:
                self._selected_id = clicked_id
                if self._on_select:
                    self._on_select(clicked_id)

    def _on_resize(self, _event) -> None:
        # Redessiner lors de changements de taille (le prochain render mettra à jour)
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w != self._last_w or h != self._last_h:
            # Pas de redraw immédiat ici pour éviter de dessiner 2x,
            # le prochain run de on_tick() fera un render actualisé.
            self._last_w, self._last_h = w, h