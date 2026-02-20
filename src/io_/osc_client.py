# fichier: src/io_/osc_client.py

import threading
import queue
import time
from typing import Optional, List, Any, Tuple
from pythonosc import dispatcher, osc_server, udp_client


class OscClient:
    """
    Thread OSC pour :
    - écouter Max (Max → App)
    - envoyer à Max (App → Max) via une file + thread expéditeur (non-bloquant)
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

        # Envoi non-bloquant
        self._outbox: "queue.Queue[Tuple[str, List[Any]]]" = queue.Queue(maxsize=1000)
        self._sender_thread: Optional[threading.Thread] = None
        self._max_rate_hz: int = 60
        self._last_frame_sent_ts: float = 0.0

        self._running = False

    # --------------------------------------------------------------------------
    # ENVOIS (App → Max)
    # --------------------------------------------------------------------------

    def _enqueue(self, addr: str, args: List[Any]) -> None:
        try:
            self._outbox.put_nowait((addr, args))
        except queue.Full:
            try:
                self._outbox.get_nowait()
                self._outbox.put_nowait((addr, args))
            except Exception:
                self._push_error("OSC outbox overflow")

    def send_app_ready(self):
        self._enqueue("/app/ready", [])

    def send_mode(self, mode: str):
        self._enqueue("/ui/mode", [mode])

    def send_select(self, fixture_id: int):
        self._enqueue("/ui/select", [int(fixture_id)])

    def send_fixture_values(
        self,
        fixture_id: int,
        r: float, g: float, b: float, a: float, w: float,
        dimmer: float,
        strobe: float,
    ) -> None:
        """Envoi détaillé par fixture (facultatif si tu utilises /frame)."""
        self._enqueue(f"/fixture/{int(fixture_id)}/color", [float(r), float(g), float(b), float(a), float(w)])
        self._enqueue(f"/fixture/{int(fixture_id)}/dimmer", [float(dimmer)])
        self._enqueue(f"/fixture/{int(fixture_id)}/strobe", [float(strobe)])

    def send_frame(self, t: float, fixtures_flat: List[float], throttle: bool = True) -> None:
        """
        Envoi groupé: /frame t (id r g b a w dimmer strobe) * N
        fixtures_flat: concaténation de blocs de 8 valeurs:
            [id, r, g, b, a, w, dimmer, strobe, id, r, g, ...]
        """
        if throttle:
            now = time.perf_counter()
            min_dt = 1.0 / float(max(1, self._max_rate_hz))
            if (now - self._last_frame_sent_ts) < min_dt:
                return
            self._last_frame_sent_ts = now

        self._enqueue("/frame", [float(t), *fixtures_flat])

    # --------------------------------------------------------------------------
    # RÉCEPTION (Max → App)
    # --------------------------------------------------------------------------

    def _setup_dispatcher(self) -> dispatcher.Dispatcher:
        disp = dispatcher.Dispatcher()

        def on_hello(addr, *args):
            self._event_queue.put(("hello", {}))

        # /fixture/<id>/color r g b a w
        def on_color(addr, *args):
            try:
                parts = addr.split("/")
                fixture_id = int(parts[2])
                r, g, b, a, w = (float(x) for x in args[:5])
                self._event_queue.put((
                    "fixture_color",
                    {"id": fixture_id, "r": r, "g": g, "b": b, "a": a, "w": w}
                ))
            except Exception as e:
                self._push_error(f"on_color error: {e}")

        # /fixture/<id>/dimmer value
        def on_dimmer(addr, *args):
            try:
                parts = addr.split("/")
                fixture_id = int(parts[2])
                value = float(args[0])
                self._event_queue.put(("fixture_dimmer", {"id": fixture_id, "value": value}))
            except Exception as e:
                self._push_error(f"on_dimmer error: {e}")

        # /fixture/<id>/strobe rate
        def on_strobe(addr, *args):
            try:
                parts = addr.split("/")
                fixture_id = int(parts[2])
                rate = float(args[0])
                self._event_queue.put(("fixture_strobe", {"id": fixture_id, "rate": rate}))
            except Exception as e:
                self._push_error(f"on_strobe error: {e}")

        # /frame t id r g b a w dimmer strobe [id r g ...]
        def on_frame(addr, *args):
            try:
                if not args:
                    return
                t = float(args[0])
                flat = list(args[1:])
                block = 8
                if len(flat) % block != 0:
                    self._push_error("on_frame: payload length not multiple of 8")
                    return
                fixtures = []
                for i in range(0, len(flat), block):
                    fid = int(flat[i + 0])
                    r, g, b, a, w, dimmer, strobe = (
                        float(flat[i + 1]),
                        float(flat[i + 2]),
                        float(flat[i + 3]),
                        float(flat[i + 4]),
                        float(flat[i + 5]),
                        float(flat[i + 6]),
                        float(flat[i + 7]),
                    )
                    fixtures.append(
                        {"id": fid, "r": r, "g": g, "b": b, "a": a, "w": w, "dimmer": dimmer, "strobe": strobe}
                    )
                self._event_queue.put(("frame", {"t": t, "fixtures": fixtures}))
            except Exception as e:
                self._push_error(f"on_frame error: {e}")

        disp.map("/app/hello", on_hello)
        disp.map("/fixture/*/color", on_color)
        disp.map("/fixture/*/dimmer", on_dimmer)
        disp.map("/fixture/*/strobe", on_strobe)
        disp.map("/frame", on_frame)

        disp.set_default_handler(lambda addr, *args: None)
        return disp

    # --------------------------------------------------------------------------
    # DÉMARRAGE / ARRÊT
    # --------------------------------------------------------------------------

    def start(self):
        if self._running:
            return
        self._running = True

        # Serveur réception
        try:
            disp = self._setup_dispatcher()
            self._server = osc_server.ThreadingOSCUDPServer(
                ("0.0.0.0", self.listen_port), disp
            )
        except Exception as e:
            self._push_error(f"OSC server start error: {e}")
            self._running = False
            return

        def server_loop():
            try:
                self._server.serve_forever()
            except Exception as e:
                self._push_error(f"OSC server fatal error: {e}")

        self._server_thread = threading.Thread(target=server_loop, name="OSC-Server", daemon=True)
        self._server_thread.start()

        # Thread d'envoi (non-bloquant)
        def sender_loop():
            while self._running:
                try:
                    addr, args = self._outbox.get(timeout=0.1)
                except queue.Empty:
                    continue
                try:
                    self._client.send_message(addr, args)
                except Exception as e:
                    self._push_error(f"send_message({addr}) failed: {e}")

        self._sender_thread = threading.Thread(target=sender_loop, name="OSC-Sender", daemon=True)
        self._sender_thread.start()

    def stop(self):
        self._running = False
        try:
            if self._server:
                self._server.shutdown()
        except Exception:
            pass

        # On purge rapidement la file pour ne pas bloquer la fermeture
        try:
            if self._sender_thread and self._sender_thread.is_alive():
                while not self._outbox.empty():
                    try:
                        self._outbox.get_nowait()
                    except Exception:
                        break
        except Exception:
            pass

    # --------------------------------------------------------------------------
    # UTILITAIRES
    # --------------------------------------------------------------------------
    def _push_error(self, message: str):
        self._event_queue.put(("error", {"message": message}))