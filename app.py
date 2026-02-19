"""
Lighting Viz — Step 2a
Point d’entrée de l’application.

- Ajoute le dossier src/ au sys.path pour permettre les imports "ui.*", "core.*", "utils.*", "io_.*"
- Lance la fenêtre principale (MainWindow)
"""

import sys
from pathlib import Path

# S'assurer que src/ est bien dans le chemin des modules Python
here = Path(__file__).resolve()
src_path = here.parent / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Démarrer l'app
from ui.main_window import run_app

if __name__ == '__main__':
    run_app()