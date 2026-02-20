# InterfaceShowbuddy — Lighting Viz (Max/Max for Live)

Visualiseur et outil de composition pour un système lumière **RGBAW + Dimmer + Strobe** avec **aller/retour OSC** entre Python et **Max / Max for Live**.

- **READ** : Python **reçoit** depuis Max et affiche l’état des luminaires (fixtures).
- **WRITE** : Python **envoie** en continu vers Max (à ~60 Hz, configurable) l’état courant des fixtures.
- **UI** : grille de fixtures + **sliders** (R, G, B, A, W, Dimmer, Strobe) pour éditer une fixture en WRITE.
- **Test rapide** : bouton **“Send test frame”** qui envoie un `/frame` de démonstration vers Max.

---

## ⚙️ Prérequis & installation

- Python 3.11+ recommandé (Windows/macOS OK).
- Dépendances :
  ```txt
  python-osc==1.8.3
  PyYAML==6.0.2
  
Installation :
pip install -r requirements.txt

💡 Windows : au premier lancement, autorisez Python dans le Pare‑feu.

📁 Structure du projet
config/
  io.yml            # ports OSC & IP
  fixtures.yml      # nombre de fixtures (+ valeurs par défaut)
src/
  core/
    modes.py        # READ / WRITE
    state.py        # AppState + FixtureState (RGBAW + Dimmer + Strobe)
  io_/
    osc_client.py   # OSC Read/Write + thread expéditeur + throttle
  ui/
    main_window.py  # fenêtre principale (grille + sliders + toolbar)
    fixtures_view.py# grille + barres RGBAW/Dimmer/Strobe
    toolbar.py      # mode READ/WRITE + bouton "Send test frame"
    controls.py     # sliders R,G,B,A,W,Dimmer,Strobe (WRITE)
utils/
  log.py            # logger simple
app.py              # point d'entrée
requirements.txt
README.md


🔌 Configuration OSC
Fichier : config/io.yml


listen_port: 9000     # Max -> Python (Python écoute ici)
send_port: 9001       # Python -> Max (Max écoute ici)
remote_ip: 127.0.0.1  # IP de Max (localhost si même machine)
max_rate_hz: 60       # fréquence max d'envoi de /frame en WRITE

Dans Max :

Pour ENVOYER vers Python (READ côté app) : udpsend 127.0.0.1 9000
Pour RECEVOIR depuis Python (WRITE côté app) : udpreceive 9001

💡 Déclarer les fixtures (autogrid)
Fichier : config/fixtures.yml

fixtures:
  count: 4          # minimum 4 (augmentez à 5–20 si souhaité)
  defaults:
    color: [0.0, 0.0, 0.0, 0.0, 0.0]   # r,g,b,a,w
    dimmer: 0.0
    strobe: 0.0

Au démarrage, l’app pré‑alloue count fixtures pour afficher la grille immédiatement.
Les valeurs reçues de Max (READ) ou éditées via les sliders (WRITE) mettent l’affichage à jour en temps réel.



