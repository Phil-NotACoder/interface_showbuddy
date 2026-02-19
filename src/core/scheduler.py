import time

class Scheduler:
    """
    Simple Tk-based scheduler for UI ticks. Computes an approximate FPS.
    """
    def __init__(self, tk_root, interval_ms=33, on_tick=None):
        self.root = tk_root
        self.interval_ms = int(interval_ms)
        self.on_tick = on_tick
        self._running = False
        self._last_tick_time = None
        self._fps = 0.0
        self._sec_accum = 0.0
        self._sec_frames = 0

    @property
    def fps(self) -> float:
        return self._fps

    def start(self):
        if self._running:
            return
        self._running = True
        self._last_tick_time = time.monotonic()
        self.root.after(self.interval_ms, self._tick)

    def stop(self):
        self._running = False

    def _tick(self):
        if not self._running:
            return
        now = time.monotonic()
        dt = max(1e-6, now - self._last_tick_time)
        self._last_tick_time = now

        # Accumulate frames for 1-second FPS window
        self._sec_accum += dt
        self._sec_frames += 1
        if self._sec_accum >= 1.0:
            self._fps = self._sec_frames / self._sec_accum
            self._sec_accum = 0.0
            self._sec_frames = 0

        if callable(self.on_tick):
            try:
                self.on_tick()
            except Exception:
                # Keep UI alive even if callback errors
                pass

        self.root.after(self.interval_ms, self._tick)