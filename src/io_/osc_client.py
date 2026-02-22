from pythonosc import udp_client
from pythonosc import dispatcher
from pythonosc import osc_server
import threading
import queue


class OSCClient:
    def __init__(self, ip="127.0.0.1", send_port=9000, listen_port=8000):
        self.ip = ip
        self.send_port = send_port
        self.listen_port = listen_port

        # Client pour envoyer vers MAX
        self.client = udp_client.SimpleUDPClient(ip, send_port)

        # Serveur pour recevoir de MAX
        self.dispatcher = dispatcher.Dispatcher()
        self.dispatcher.set_default_handler(self._default_handler)

        self.server = osc_server.ThreadingOSCUDPServer((ip, listen_port), self.dispatcher)

        self.server_thread = None
        self.msg_queue = queue.Queue()
        self.running = False

    def start(self):
        """Démarre le serveur d'écoute en arrière-plan."""
        if not self.running:
            self.running = True
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            print(f"OSC: Écoute sur {self.ip}:{self.listen_port}, Envoi vers {self.ip}:{self.send_port}")

    def stop(self):
        """Arrête le serveur."""
        if self.running:
            self.running = False
            self.server.shutdown()
            self.server.server_close()

    def get_queue(self):
        return self.msg_queue

    def _default_handler(self, address, *args):
        """Met les messages reçus dans la file d'attente."""
        self.msg_queue.put((address, args))

    # --- Méthodes d'envoi ---

    def send_mode(self, mode):
        """Envoie le mode (read/write) à MAX."""
        self.client.send_message("/mode", mode)

    def send_fixture_values(self, fixture_id, r, g, b, a, w, dimmer, strobe):
        """Envoie les valeurs d'une fixture à MAX."""
        addr = f"/fixture/{fixture_id}/values"
        self.client.send_message(addr, [r, g, b, a, w, dimmer, strobe])