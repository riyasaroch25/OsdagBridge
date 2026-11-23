"""
Headless harness for the OsdagBridge desktop UI.

Builds the real `CustomWindow` (template page) exactly as
`python -m osdagbridge.desktop` does, but without entering the blocking event
loop, so that scripted experiments and tests can drive it and grab screenshots.

Usage (from the repository root, with the conda env active):

    QT_QPA_PLATFORM=offscreen python screening_task/experiments/harness.py

Running the module directly performs a smoke test: it builds the window,
pumps the event loop for a moment and writes a screenshot to
screening_task/experiments/results/smoke_template_page.png.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = REPO_ROOT / "screening_task" / "experiments" / "results"
SRC_DIR = REPO_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def pump(app, seconds: float = 0.3) -> None:
    """Process Qt events for roughly `seconds` (lets deferred timers fire)."""
    end = time.perf_counter() + seconds
    while time.perf_counter() < end:
        app.processEvents()
        time.sleep(0.01)


def build_main_window(width: int = 1600, height: int = 950):
    """Create QApplication + CustomWindow the same way desktop/__main__.py does."""
    # Importing the desktop package runs its start-up side effects
    # (sqlite creation, osdag_core DB build) exactly like the real launcher.
    import osdagbridge.desktop.__main__ as desktop_main  # noqa: F401
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    stylesheet = desktop_main.load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)

    window = desktop_main.CustomWindow("OsdagBridge", desktop_main.PlateGirderBridge)
    window.resize(width, height)
    window.show()
    pump(app, 0.8)
    return app, window


def grab(widget, name: str) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / name
    widget.grab().save(str(path))
    return path


if __name__ == "__main__":
    t0 = time.perf_counter()
    app, window = build_main_window()
    print(f"[harness] window built in {time.perf_counter() - t0:.2f} s")
    print(f"[harness] screenshot -> {grab(window, 'smoke_template_page.png')}")
