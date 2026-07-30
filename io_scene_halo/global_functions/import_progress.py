# Lightweight import-progress reporter.
#
# Prints phase markers + ETA to the system console (Window > Toggle System Console
# on Windows, or the terminal you launched Blender from on macOS/Linux), and
# drives Blender's cursor progress bar via WindowManager.progress_*.
#
# Blender's main thread still owns the import operator, so the UI itself stays
# blocked — this just makes it possible to tell whether the import is making
# progress and roughly how long it has left.

import time


class ImportProgress:
    def __init__(self, window_manager=None, label="Import"):
        self.wm = window_manager
        self.label = label
        self.t_start = time.monotonic()
        self.phase_label = None
        self.phase_start = self.t_start
        self.phase_total = 0
        self.last_print = 0.0
        self._wm_active = False

    def begin(self):
        self.t_start = time.monotonic()
        self.phase_start = self.t_start
        if self.wm is not None:
            try:
                self.wm.progress_begin(0.0, 1.0)
                self._wm_active = True
            except Exception:
                self._wm_active = False
        print("[%s] start" % self.label, flush=True)

    def phase(self, label, total=0):
        now = time.monotonic()
        if self.phase_label is not None:
            elapsed = now - self.phase_start
            print("[%s] %s: done in %.1fs" % (self.label, self.phase_label, elapsed), flush=True)
        self.phase_label = label
        self.phase_start = now
        self.phase_total = int(total) if total else 0
        self.last_print = 0.0
        if self.phase_total > 0:
            print("[%s] %s: 0 / %d" % (self.label, label, self.phase_total), flush=True)
        else:
            print("[%s] %s..." % (self.label, label), flush=True)
        if self._wm_active:
            try:
                self.wm.progress_update(0.0)
            except Exception:
                pass

    def step(self, value, force=False):
        if self.phase_total <= 0:
            return
        now = time.monotonic()
        # Throttle prints to once every 0.5s, but always emit on the final step.
        if not force and value < self.phase_total and now - self.last_print < 0.5:
            return
        self.last_print = now
        elapsed = now - self.phase_start
        rate = value / elapsed if elapsed > 0 else 0.0
        eta = (self.phase_total - value) / rate if rate > 0 else 0.0
        pct = value / self.phase_total if self.phase_total else 0.0
        if self._wm_active:
            try:
                self.wm.progress_update(min(max(pct, 0.0), 1.0))
            except Exception:
                pass
        print(
            "[%s] %s: %d / %d (%.1f%%) — %.1fs elapsed, ~%.1fs left" % (
                self.label, self.phase_label, value, self.phase_total,
                pct * 100.0, elapsed, eta,
            ),
            flush=True,
        )

    def end(self):
        now = time.monotonic()
        if self.phase_label is not None:
            elapsed = now - self.phase_start
            print("[%s] %s: done in %.1fs" % (self.label, self.phase_label, elapsed), flush=True)
            self.phase_label = None
        total = now - self.t_start
        print("[%s] total: %.1fs" % (self.label, total), flush=True)
        if self._wm_active:
            try:
                self.wm.progress_end()
            except Exception:
                pass
            self._wm_active = False
