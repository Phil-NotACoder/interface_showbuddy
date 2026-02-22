import tkinter as tk
from app import ShowBuddyApp
from src.ui.main_window import MainWindow

import sys
from src.core.state import FixtureState

if __name__ == "__main__":
    # 1. Création de la racine Tkinter (la fenêtre de base)
    root = tk.Tk()

    # 2. Création de la logique de l'application
    app = ShowBuddyApp()

    # 3. Création de l'interface principale
    # On doit passer 'root' (la fenêtre) ET 'app' (la logique)
    window = MainWindow(root, app)

    # 4. Lancement de la boucle principale
    root.mainloop()