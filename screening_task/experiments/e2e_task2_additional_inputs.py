"""
End-to-end check of Task II in the real Additional Inputs dialog.
Writes results/task2_e2e.json and screenshots.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import build_main_window, pump, grab, RESULTS_DIR  # noqa: E402

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QComboBox, QLineEdit

import osdagbridge.desktop.ui.dialogs.additional_input.additional_inputs as ai_mod
from osdagbridge.core.utils.common import (
    KEY_SPAN, KEY_CARRIAGEWAY_WIDTH, KEY_WL_GUST_FACTOR, KEY_CB_TYPE, KEY_CB_WIDTH, KEY_TS_DECK_THICKNESS,
)

DIALOGS, ANSWERS = [], []


class FakeBox:
    def __init__(self, title="", text="", buttons=None, dialogType=None, **kw):
        self.entry = {"title": title, "text": text, "buttons": buttons, "type": dialogType}

    def exec(self):
        answer = ANSWERS.pop(0) if ANSWERS else "OK"
        self.entry["answer"] = answer
        DIALOGS.append(self.entry)
        return answer


ai_mod.CustomMessageBox = FakeBox

app, win = build_main_window()
for key, val in ((KEY_SPAN, "20"), (KEY_CARRIAGEWAY_WIDTH, "5")):
    w = win.input_dock.input_widget.findChild(QLineEdit, key)
    w.setText(val)
    win.input_dock._on_field_edited(key, w)
pump(app, 0.3)

results = []


def log(case, **extra):
    entry = {"case": case, "is_modified": dlg.is_modified, "visible": dlg.isVisible(),
             "dialogs": list(DIALOGS), **extra}
    DIALOGS.clear()
    results.append(entry)
    print(json.dumps(entry))


def user_pick(combo: QComboBox, text: str):
    """Mimic a user selection: change index and emit the user-only `activated` signal."""
    idx = combo.findText(text)
    combo.setCurrentIndex(idx)
    combo.activated.emit(idx)
    pump(app, 0.2)


win._show_additional_inputs()
dlg = win._additional_inputs_dialog
pump(app, 0.8)
log("open dialog (no user edits)")

# Close with no changes -> no warning
dlg.close(); pump(app, 0.3)
log("close without changes")

win._show_additional_inputs(); pump(app, 0.8)
gust_mode = dlg.findChild(QComboBox, KEY_WL_GUST_FACTOR + ".mode")
gust_val = dlg.findChild(QLineEdit, KEY_WL_GUST_FACTOR + ".value")
dlg._reveal_widget(gust_mode); pump(app, 0.3)
user_pick(gust_mode, "Custom")
gust_val.clear()
log("gust factor -> Custom (empty)")

dlg._save_inputs(); pump(app, 0.3)
log("save with empty custom value", error_style=bool(gust_val.property("error")))
grab(dlg, "task2_save_blocked.png")

cb_type = dlg.findChild(QComboBox, KEY_CB_TYPE)
dlg._reveal_widget(cb_type); pump(app, 0.3)
user_pick(cb_type, "Custom")
cb_w = dlg.findChild(QLineEdit, KEY_CB_WIDTH)
cb_w.clear()
dlg._save_inputs(); pump(app, 0.3)
log("save with two empty custom values")

# Fill both -> save succeeds
dlg._reveal_widget(gust_val); QTest.keyClicks(gust_val, "0.85")
dlg._reveal_widget(cb_w); QTest.keyClicks(cb_w, "0.5")
pump(app, 0.2)
dlg._save_inputs(); pump(app, 0.3)
log("save after filling values")

# Edit -> close -> Cancel keeps dialog open; Discard closes and rolls back
deck = dlg.findChild(QLineEdit, KEY_TS_DECK_THICKNESS)
dlg._reveal_widget(deck)
deck.selectAll(); QTest.keyClicks(deck, "300"); pump(app, 0.2)
ANSWERS.append("Cancel")
dlg.close(); pump(app, 0.3)
log("edit then close -> Cancel")
ANSWERS.append("Cancel")
QTest.keyClick(dlg, Qt.Key_Escape); pump(app, 0.3)
log("edit then Esc -> Cancel")
ANSWERS.append("Discard")
dlg.close(); pump(app, 0.3)
log("edit then close -> Discard", deck_in_input_dict=win.input_dict.get(KEY_TS_DECK_THICKNESS))

win._show_additional_inputs(); pump(app, 0.8)
log("reopen after discard", deck_widget=dlg.findChild(QLineEdit, KEY_TS_DECK_THICKNESS).text())

(RESULTS_DIR / "task2_e2e.json").write_text(json.dumps(results, indent=2))
