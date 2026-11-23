"""
End-to-end check of Task I in the real template page.

Simulates: fill span/carriageway -> double-click a CAD label -> type -> Enter,
for every editable label, plus locked-label and invalid-input cases.
Writes results/task1_e2e.json and screenshots.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import build_main_window, pump, grab, RESULTS_DIR  # noqa: E402

from PySide6.QtCore import Qt, QPointF
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QLineEdit, QApplication

import osdagbridge.desktop.ui.template_page as tp
from osdagbridge.core.utils.common import (
    KEY_SPAN, KEY_CARRIAGEWAY_WIDTH, KEY_TS_GIRDER_SPACING, KEY_TS_DECK_THICKNESS,
    KEY_TS_DECK_OVERHANG, KEY_TS_OVERALL_WIDTH, KEY_TS_NO_OF_GIRDERS,
)

# Record error dialogs instead of blocking on them.
DIALOGS = []


class _FakeBox:
    def __init__(self, title="", text="", **kw):
        DIALOGS.append({"title": title, "text": text})

    def exec(self):
        return "OK"


tp.CustomMessageBox = _FakeBox
import osdagbridge.desktop.ui.docks.input_dock as idock  # noqa: E402
idock.CustomMessageBox = _FakeBox

app, win = build_main_window()
dock = win.input_dock


def set_field(key, text):
    w = dock.input_widget.findChild(QLineEdit, key)
    w.setText(text)
    dock._on_field_edited(key, w)
    pump(app, 0.3)


set_field(KEY_SPAN, "20")
set_field(KEY_CARRIAGEWAY_WIDTH, "5")
pump(app, 0.5)
cross = win.cad_comp_widget.cross_section_widget
top = win.cad_comp_widget.top_view_widget
cross.update(); top.update(); pump(app, 0.5)
grab(win.cad_comp_widget, "task1_before.png")


def find_label(view, key):
    for rect, spec in view._label_registry:
        if spec.key == key:
            return rect
    return None


def edit(view, key, text, press=Qt.Key_Return):
    view.repaint(); pump(app, 0.2)
    rect = find_label(view, key)
    if rect is None:
        return {"found_label": False}
    t0 = time.perf_counter()
    QTest.mouseDClick(view, Qt.LeftButton, Qt.NoModifier, rect.center().toPoint())
    pump(app, 0.1)
    editor = getattr(view, "_label_editor", None)
    opened = editor is not None and editor.isVisible()
    open_ms = (time.perf_counter() - t0) * 1000
    if opened:
        editor.selectAll()
        QTest.keyClicks(editor, text)
        QTest.keyClick(editor, press)
    pump(app, 0.6)
    return {"found_label": True, "editor_opened": opened, "open_ms": round(open_ms, 1)}


results = []


def record(name, info, expect_ok):
    snap = {k: win.input_dict.get(k) for k in
            [KEY_SPAN, KEY_CARRIAGEWAY_WIDTH, KEY_TS_GIRDER_SPACING, KEY_TS_DECK_THICKNESS,
             KEY_TS_DECK_OVERHANG, KEY_TS_OVERALL_WIDTH, KEY_TS_NO_OF_GIRDERS]}
    entry = {"case": name, **info, "dialogs": list(DIALOGS), "input_dict": snap}
    DIALOGS.clear()
    results.append(entry)
    print(json.dumps(entry, default=str))


record("girder spacing 1.80 (cross-section)", edit(cross, KEY_TS_GIRDER_SPACING, "1.80"), True)
record("deck thickness 220 mm", edit(cross, KEY_TS_DECK_THICKNESS, "220"), True)
grab(win.cad_comp_widget, "task1_after_spacing_deck.png")
record("carriageway width 7.5 m", edit(cross, KEY_CARRIAGEWAY_WIDTH, "7.5"), True)
record("span length 30 m (plan view)", edit(top, KEY_SPAN, "30"), True)
record("girder spacing 2.2 (plan view)", edit(top, KEY_TS_GIRDER_SPACING, "2.2"), True)
record("deck thickness 50 mm (out of range)", edit(cross, KEY_TS_DECK_THICKNESS, "50"), False)
record("girder spacing 99 (infeasible)", edit(cross, KEY_TS_GIRDER_SPACING, "99"), False)
record("overhang (locked)", edit(cross, KEY_TS_DECK_OVERHANG, "1"), False)
record("overall width (locked)", edit(cross, KEY_TS_OVERALL_WIDTH, "1"), False)
record("deck thickness Esc cancels", edit(cross, KEY_TS_DECK_THICKNESS, "300", press=Qt.Key_Escape), False)
grab(win.cad_comp_widget, "task1_final.png")

# Locked input dock -> editing refused
dock.is_locked = True
record("edit while dock locked", edit(cross, KEY_TS_DECK_THICKNESS, "240"), False)
dock.is_locked = False

(RESULTS_DIR / "task1_e2e.json").write_text(json.dumps(results, indent=2, default=str))
print("written", RESULTS_DIR / "task1_e2e.json")
