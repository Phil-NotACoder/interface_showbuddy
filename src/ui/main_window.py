import tkinter as tk
from tkinter import ttk, filedialog  # <--- L'import manquant est ici !
from .fixture_canvas import FixtureCanvas
from .controls_list import ControlsListView
from .beam_list import BeamListView


class MainWindow:
    def __init__(self, root, app):
        self.root = root
        self.app = app
        self.root.title("Interface ShowBuddy")
        self.root.geometry("1200x800")
        self.root.configure(bg="#1e1e1e")

        # --- TOOLBAR ---
        toolbar = tk.Frame(root, bg="#333", height=40)
        toolbar.pack(fill="x", side="top")

        # Bouton SAVE (corrigé pour utiliser save_show)
        tk.Button(toolbar, text="SAVE", command=self.save_show,
                  bg="#444", fg="white", relief="flat").pack(side="left", padx=2, pady=2)

        # Bouton LOAD (corrigé pour utiliser load_show)
        tk.Button(toolbar, text="LOAD", command=self.load_show,
                  bg="#444", fg="white", relief="flat").pack(side="left", padx=2, pady=2)

        # Entrée pour le nombre de fixtures
        tk.Label(toolbar, text="FIXTURES:", bg="#333", fg="#aaa").pack(side="left", padx=(10, 2))
        self.entry_count = tk.Entry(toolbar, width=5, bg="#222", fg="white", insertbackground="white")
        self.entry_count.pack(side="left", padx=2)
        self.entry_count.bind("<Return>", self._on_count_change)
        self.entry_count.insert(0, str(len(self.app.state.fixtures)))

        # Boutons READ / WRITE
        self.btn_read = tk.Button(toolbar, text="READ", command=lambda: self._set_mode("READ"), width=8)
        self.btn_read.pack(side="right", padx=2, pady=2)

        self.btn_write = tk.Button(toolbar, text="WRITE", command=lambda: self._set_mode("WRITE"), width=8)
        self.btn_write.pack(side="right", padx=2, pady=2)

        # --- MAIN LAYOUT ---
        main_container = tk.Frame(root, bg="#1e1e1e")
        main_container.pack(fill="both", expand=True)

        # 1. Colonne Gauche : Contrôles (Couleurs)
        self.controls_list = ControlsListView(main_container, on_change=self._on_param_change)
        self.controls_list.pack(side="left", fill="y", padx=5, pady=5)

        # 2. Centre : Canevas (Plan de feu)
        center_frame = tk.Frame(main_container, bg="#111")
        center_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.canvas = FixtureCanvas(center_frame, self.app.state,
                                    on_select=self._on_select_fixture,
                                    on_move=self._on_fixture_move)
        self.canvas.pack(fill="both", expand=True)

        # 3. Colonne Droite : Beam List (Formes et Angles)
        # On fixe une largeur de 400px pour avoir de la place
        right_frame = tk.Frame(main_container, bg="#1e1e1e", width=400)
        right_frame.pack(side="right", fill="y", padx=5, pady=5)
        right_frame.pack_propagate(False)

        self.beam_list = BeamListView(right_frame, on_change=self._on_param_change)
        self.beam_list.pack(fill="both", expand=True)

        # Initialisation de l'affichage
        self._update_mode_buttons()
        self.render(self.app.state)

    def render(self, state):
        self.canvas.render(state)
        self.controls_list.render(state)
        self.beam_list.render(state)

    def save_show(self):
        """Ouvre l'explorateur pour sauvegarder."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="Save Show As..."
        )
        if filename:
            self.app.save_project(filename)
            print(f"Sauvegardé sous : {filename}")

    def load_show(self):
        """Ouvre l'explorateur pour charger."""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="Load Show"
        )
        if filename:
            self.app.load_project(filename)
            # On rafraîchit tout l'affichage
            self.render(self.app.state)
            # On met à jour le champ nombre de fixtures
            self.entry_count.delete(0, tk.END)
            self.entry_count.insert(0, str(len(self.app.state.fixtures)))
            print(f"Chargé depuis : {filename}")

    def _set_mode(self, mode):
        self.app.set_mode(mode)
        self._update_mode_buttons()

    def _update_mode_buttons(self):
        mode = self.app.state.mode
        if mode == "READ":
            self.btn_read.configure(bg="#d4af37", fg="black", relief="sunken")
            self.btn_write.configure(bg="#444", fg="white", relief="raised")
        else:
            self.btn_read.configure(bg="#444", fg="white", relief="raised")
            self.btn_write.configure(bg="#d4af37", fg="black", relief="sunken")

    def _on_count_change(self, event):
        try:
            count = int(self.entry_count.get())
            self.app.set_fixture_count(count)
            self.render(self.app.state)
        except ValueError:
            pass

    def _on_select_fixture(self, fid):
        self.app.select_fixture(fid)
        self.render(self.app.state)

    def _on_fixture_move(self, fid, param, value):
        # Mouvement sur le canevas (drag & drop)
        self.app.update_fixture(fid, **{param: value})
        # On ne redessine pas tout le canevas pour éviter de laguer pendant le drag
        # Mais on pourrait mettre à jour les listes si besoin

    def _on_param_change(self, fid, param, value, **kwargs):
        # Changement via les sliders ou boutons
        self.app.update_fixture(fid, **{param: value})
        self.render(self.app.state)