import json
import dataclasses
from pythonosc import udp_client
from .state import AppState
from .modes import READ, WRITE


class App:
    def __init__(self):
        self.state = AppState()
        self.osc_client = None

        # Configuration OSC par défaut
        self.setup_osc("127.0.0.1", 9000)

    def setup_osc(self, ip, port):
        try:
            self.osc_client = udp_client.SimpleUDPClient(ip, port)
            print(f"OSC Client ready on {ip}:{port}")
        except Exception as e:
            print(f"Failed to init OSC Client: {e}")

    def set_mode(self, mode):
        self.state.mode = mode
        print(f"Mode changed to: {mode}")

    def set_fixture_count(self, count):
        # On ajuste le nombre de fixtures
        current_ids = list(self.state.fixtures.keys())

        # Si on en a trop, on supprime les dernières
        if len(current_ids) > count:
            for i in range(count + 1, len(current_ids) + 1):
                if i in self.state.fixtures:
                    del self.state.fixtures[i]

        # Si on en manque, on ajoute
        for i in range(1, count + 1):
            self.state.ensure_fixture(i)

    def select_fixture(self, fid):
        self.state.selected_fixture_id = fid
        print(f"Selected fixture: {fid}")

    def update_fixture(self, fid, **kwargs):
        """
        Met à jour n'importe quel paramètre d'une fixture.
        Accepte des arguments variables comme pos_x=120, dimmer=255, etc.
        """
        fix = self.state.ensure_fixture(fid)

        should_send_osc = False

        for param, value in kwargs.items():
            # 1. On met à jour l'état interne (Le Cerveau)
            if hasattr(fix, param):
                # Petit hack de sécurité : si le state attend un nombre mais reçoit une string, on convertit
                current_val = getattr(fix, param)
                if isinstance(current_val, (int, float)) and not isinstance(value, (int, float)):
                    try:
                        value = float(value)
                    except:
                        pass  # On garde la valeur telle quelle si conversion impossible

                setattr(fix, param, value)

                # 2. On décide si on doit envoyer du OSC
                # On n'envoie que si c'est un paramètre de lumière (pas la position sur l'écran)
                if param in ["r", "g", "b", "a", "w", "dimmer", "strobe"]:
                    should_send_osc = True
            else:
                # Optionnel : on pourrait afficher un warning ici, mais on l'ignore pour l'instant
                pass

        # 3. Envoi OSC si nécessaire et si on est en mode WRITE
        if should_send_osc and self.state.mode == WRITE and self.osc_client:
            self._send_osc(fid, fix)

    def _send_osc(self, fid, fix):
        # Exemple de protocole : /fixture/1/dimmer 255
        base = f"/fixture/{fid}"
        try:
            self.osc_client.send_message(f"{base}/dimmer", fix.dimmer)
            self.osc_client.send_message(f"{base}/rgb", [fix.r, fix.g, fix.b])
            self.osc_client.send_message(f"{base}/white", fix.w)
            self.osc_client.send_message(f"{base}/amber", fix.a)
            self.osc_client.send_message(f"{base}/strobe", fix.strobe)
        except Exception as e:
            print(f"OSC Error: {e}")

    def save_project(self, filename="show.json"):
        """Sauvegarde l'état actuel dans un fichier JSON spécifique."""
        data = {
            "fixtures": {
                str(fid): dataclasses.asdict(fix)
                for fid, fix in self.state.fixtures.items()
            }
        }
        try:
            with open(filename, "w") as f:
                json.dump(data, f, indent=4)
            print(f"Project saved to {filename}")
        except Exception as e:
            print(f"Error saving project: {e}")

    def load_project(self, filename="show.json"):
        """Charge l'état depuis un fichier JSON spécifique."""
        try:
            with open(filename, "r") as f:
                data = json.load(f)

            self.state.fixtures.clear()

            for fid_str, fix_data in data.get("fixtures", {}).items():
                fid = int(fid_str)
                fix = self.state.ensure_fixture(fid)

                for k, v in fix_data.items():
                    if hasattr(fix, k):
                        setattr(fix, k, v)

            print(f"Project loaded from {filename}")
        except Exception as e:
            print(f"Error loading project: {e}")