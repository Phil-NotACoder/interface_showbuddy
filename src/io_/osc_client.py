# src/io_/osc_client.py

import threading
import queue
from typing import Optional
from pythonosc import dispatcher, osc_server, udp_client


class OscClient:
    """
    Thread OSC pour :
    - écouter Max (Max → App)
    - envoyer à Max (App → Max)
    - pousser des événements vers l’UI via une Queue thread-safe
    """

    def __init__(self, listen_port: int, remote_ip: str, send_port: int, event_queue: queue.Queue):
        self.listen_port = listen_port
        self.remote_ip = remote_ip
        self.send_port = send_port
        self._event_queue = event_queue

        self._server: Optional[osc_server.ThreadingOSCUDPServer] = None
        self._server_thread: Optional[threading.Thread] = None

        # Client OSC pour envoyer vers Max
        self._client = udp_client.SimpleUDPClient(remote_ip, send_port)

        self._running = False

    # --------------------------------------------------------------------------
    # ENVOIS (App → Max)
    # --------------------------------------------------------------------------

    def send_app_ready(self):
        """Envoyé automatiquement au démarrage"""
        try:
            self._client.send_message("/app/ready", [])
        except Exception as e:
            self._push_error(f"send_app_ready failed: {e}")

    def send_mode(self, mode: str):
        """Quand tu bascules READ/WRITE dans la toolbar"""
        try:
            self._client.send_message("/ui/mode", [mode])
        except Exception as e:
            self._push_error(f"send_mode failed: {e}")

    def send_select(self, fixture_id: int):
        """Step 2b — Envoie la sélection courante (-1 pour désélection)."""
        try:
            self._client.send_message("/ui/select", [int(fixture_id)])
        except Exception as e:
            self._push_error(f"send_select failed: {e}")

    # --------------------------------------------------------------------------
    # RÉCEPTION (Max → App)
    # --------------------------------------------------------------------------

    def _setup_dispatcher(self) -> dispatcher.Dispatcher:
        disp = dispatcher.Dispatcher()

        def on_hello(addr, *args):
            # Max envoie : /app/hello
            self._event_queue.put(("hello", {}))

        disp.map("/app/hello", on_hello)
        return disp

    # --------------------------------------------------------------------------
    # DÉMARRAGE DU SERVEUR OSC
    # --------------------------------------------------------------------------

    def start(self):
        if self._running:
            return

        self._running = True

        try:
            disp = self._setup_dispatcher()
            self._server = osc_server.ThreadingOSCUDPServer(
                ("0.0.0.0", self.listen_port), disp
            )
        except Exception as e:
            self._push_error(f"OSC server start error: {e}")
            self._running = False
            return

        # Thread « non bloquant »
        def server_loop():
            try:
                self._server.serve_forever()
            except Exception as e:
                self._push_error(f"OSC server fatal error: {e}")

        self._server_thread = threading.Thread(
            target=server_loop,
            name="OSC-Server",
            daemon=True
        )
        self._server_thread.start()

    # --------------------------------------------------------------------------
    # ARRÊT
    # --------------------------------------------------------------------------

    def stop(self):
        self._running = False
        try:
            if self._server:
                self._server.shutdown()
        except Exception:
            pass

    # --------------------------------------------------------------------------
    # UTILITAIRE
    # --------------------------------------------------------------------------

    def _push_error(self, message: str):
        self._event_queue.put(("error", {"message": message}))