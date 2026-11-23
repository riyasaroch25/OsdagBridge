"""
Scripted demo of the three screening-task features, for the screen recording.

Drives the real OsdagBridge window: smooth (eased) cursor motion, real mouse
clicks/double-clicks and per-character typing via QTest. Modal message boxes
are left on screen for a moment, then their button is clicked.
Frames are rendered from the application's own windows (main window, dialogs,
tooltips) with a drawn cursor, so nothing outside OsdagBridge is captured and
the real system mouse is never moved. Output: screening_task/media/demo_video.mp4
"""
import math, sys, time, faulthandler
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import build_main_window, pump  # noqa: E402

from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtGui import QCursor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLineEdit, QComboBox, QPushButton, QDialog, QTabWidget

from osdagbridge.core.utils.common import *

def main():
    app, win = build_main_window()
    win.showMaximized(); pump(app, 1.5)

    import os, shutil, subprocess, tempfile
    from PySide6.QtGui import QPainter, QPolygonF, QColor, QPen, QBrush, QImage, QFont
    from PySide6.QtCore import QPointF

    FPS = 15
    FRAMES = Path(tempfile.mkdtemp(prefix="osdag_demo_"))
    _cursor = {"pos": win.mapToGlobal(win.rect().center()), "click": 0}
    _caption = {"text": ""}
    _n = {"i": 0}


    def _frame():
        origin = win.mapToGlobal(QPoint(0, 0))
        img = QImage(win.size(), QImage.Format_RGB32); img.fill(QColor("white"))
        p = QPainter(img)
        p.drawPixmap(0, 0, win.grab())
        from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox

        def _layer(w):                                      # paint order: dialogs < message boxes < popups/tooltips
            if isinstance(w, CustomMessageBox):
                return 1
            if w.windowFlags() & (Qt.ToolTip | Qt.Popup) == (Qt.ToolTip | Qt.Popup) or \
                    type(w).__name__ in ("QTipLabel", "QComboBoxPrivateContainer"):
                return 2
            return 0
        tops = [w for w in QApplication.topLevelWidgets()
                if w is not win and w.isVisible() and w.width() > 2]
        for w in sorted(tops, key=_layer):                  # dialogs, message boxes, tooltips
                g = w.mapToGlobal(QPoint(0, 0)) - origin
                p.drawPixmap(g, w.grab())
        c = _cursor["pos"] - origin
        p.setRenderHint(QPainter.Antialiasing)
        if _caption["text"]:
            p.setFont(QFont("Arial", 15, QFont.Bold))
            m = p.fontMetrics(); tw = m.horizontalAdvance(_caption["text"]) + 40
            box = (img.width() - tw) // 2
            p.setPen(Qt.NoPen); p.setBrush(QColor(47, 61, 10, 225))
            p.drawRoundedRect(box, img.height() - 70, tw, 44, 8, 8)
            p.setPen(QColor("white")); p.drawText(box + 20, img.height() - 40, _caption["text"])
        p.setFont(QFont("Arial", 10)); p.setPen(QColor(120, 120, 120))
        p.drawText(img.width() - 470, 18, "OsdagBridge screening task - scripted demo (inputs driven by a script)")
        if _cursor["click"] > 0:
            p.setPen(QPen(QColor(144, 175, 19), 3)); p.setBrush(Qt.NoBrush)
            r = 26 - _cursor["click"] * 2
            p.drawEllipse(QPointF(c), r, r); _cursor["click"] -= 1
        arrow = QPolygonF([QPointF(0, 0), QPointF(0, 22), QPointF(6, 17), QPointF(10, 26),
                           QPointF(14, 24), QPointF(10, 16), QPointF(17, 16)])
        arrow.translate(QPointF(c))
        p.setPen(QPen(QColor("white"), 1.5)); p.setBrush(QBrush(QColor("black"))); p.drawPolygon(arrow)
        p.end()
        img.scaledToWidth(1600, Qt.SmoothTransformation).save(str(FRAMES / f"f{_n['i']:05d}.jpg"), "JPG", 90)
        _n["i"] += 1


    _timer = QTimer(); _timer.timeout.connect(_frame); _timer.start(int(1000 / FPS))


    def wait(s): pump(app, s)


    def move_to(widget, local=None, duration=0.7):
        """Ease-in-out glide of the drawn cursor to a point on `widget`."""
        target = widget.mapToGlobal(local if local is not None else widget.rect().center())
        start = QPoint(_cursor["pos"])
        steps = max(12, int(duration * 60))
        for k in range(1, steps + 1):
            e = 0.5 - 0.5 * math.cos(math.pi * k / steps)
            _cursor["pos"] = QPoint(int(start.x() + (target.x() - start.x()) * e),
                                    int(start.y() + (target.y() - start.y()) * e))
            app.processEvents(); time.sleep(duration / steps)
        return widget.mapFromGlobal(target)


    def click(widget, local=None, double=False):
        p = move_to(widget, local); wait(0.15)
        _cursor["click"] = 8
        (QTest.mouseDClick if double else QTest.mouseClick)(widget, Qt.LeftButton, Qt.NoModifier, p)
        wait(0.3)


    def type_text(widget, text, clear=True):
        if clear:
            widget.selectAll() if hasattr(widget, "selectAll") else None
        for ch in text:
            QTest.keyClicks(widget, ch); wait(0.09)


    _answers = []          # queued button texts; default "OK"
    _seen = {}


    def answer_next_dialog(button_text="OK", delay=2.5):
        if button_text != "OK":
            _answers.append(button_text)


    def _auto_answer():
        """Keep each message box on screen ~2.5 s, then press the queued (or OK) button."""
        from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox
        for w in QApplication.topLevelWidgets():
            if isinstance(w, CustomMessageBox) and w.isVisible():
                if w.property("_demo_done"):
                    continue
                t = w.property("_demo_t") or time.time()
                w.setProperty("_demo_t", t)
                if time.time() - t > 2.5:
                    labels = [b.text().strip() for b in w.findChildren(QPushButton)]
                    want = _answers[0] if _answers and _answers[0] in labels else "OK"
                    if want in labels and want != "OK" or want == "OK" and "OK" in labels:
                        if _answers and want == _answers[0]:
                            _answers.pop(0)
                        w.setProperty("_demo_done", True)
                        b = next(b for b in w.findChildren(QPushButton) if b.text().strip() == want)
                        QTimer.singleShot(0, lambda b=b: (_cursor.update(click=8), b.click()))


    _answer_timer = QTimer(); _answer_timer.timeout.connect(_auto_answer); _answer_timer.start(200)


    dock = win.input_dock
    # Project location (custom-data form values; test fixture)
    win.input_dict[KEY_PROJECT_LOCATION] = {
        "method": "custom_data", "data": {},
        "weather_data": {"wind_speed": 44, "zone": "III", "z_value": 0.16, "max_temp": 45, "min_temp": 5},
        "display_text": "", "show_display": False,
    }
    # ── Basic inputs
    print('STAGE: Basic inputs', flush=True)
    _caption['text'] = 'Basic inputs: span 20 m, carriageway 5 m'
    for key, val in ((KEY_SPAN, "20"), (KEY_CARRIAGEWAY_WIDTH, "5")):
        f = dock.input_widget.findChild(QLineEdit, key)
        click(f); type_text(f, val); QTest.keyClick(f, Qt.Key_Tab); wait(0.6)
    wait(1.0)

    # ── Task I: double-click CAD labels
    print('STAGE: Task I: double-click CAD labels', flush=True)
    _caption['text'] = 'Task I - double-click a CAD dimension label to edit it (derived labels are locked)'
    cross = win.cad_comp_widget.cross_section_widget
    top = win.cad_comp_widget.top_view_widget


    def label_point(view, key):
        view.repaint(); wait(0.1)
        for rect, spec in view._label_registry:
            if spec.key == key:
                return rect.center().toPoint()


    def cad_edit(view, key, text, error=False):
        p = label_point(view, key)
        move_to(view, p, 0.9); wait(0.6)                  # hover shows edit cursor/tooltip
        click(view, p, double=True); wait(0.5)
        ed = view._label_editor
        if ed is None:
            wait(2.0); return
        ed.selectAll(); type_text(ed, text, clear=False); wait(0.4)
        if error:
            answer_next_dialog("OK", 2.5)
        QTest.keyClick(ed, Qt.Key_Return); wait(3.2 if error else 1.5)


    cad_edit(cross, KEY_TS_GIRDER_SPACING, "1.80")
    cad_edit(cross, KEY_TS_DECK_THICKNESS, "220")
    cad_edit(top, KEY_SPAN, "25")
    cad_edit(cross, KEY_TS_DECK_OVERHANG, "")            # locked: tooltip, no editor
    cad_edit(cross, KEY_TS_DECK_THICKNESS, "50", error=True)
    wait(1.0)

    # ── Task II: Additional Inputs
    print('STAGE: Task II: Additional Inputs', flush=True)
    _caption['text'] = "Task II - empty 'Custom' value blocks Save; unsaved changes ask Discard / Cancel"
    btn = next(b for b in win.findChildren(QPushButton) if b.text().strip() == "Additional Inputs")
    click(btn); wait(1.5)
    dlg = win._additional_inputs_dialog


    def open_tab(widget):
        """Click through the nested tab bars that lead to `widget`."""
        chain, w = [], widget
        while w is not None and w is not dlg:
            par = w.parentWidget()
            if par is not None and isinstance(par.parentWidget(), QTabWidget) and par.parentWidget().indexOf(w) >= 0:
                chain.append((par.parentWidget(), w))
            w = par
        for tabs, page in reversed(chain):
            bar = tabs.tabBar(); i = tabs.indexOf(page)
            click(bar, bar.tabRect(i).center()); wait(0.6)


    gust_mode = dlg.findChild(QComboBox, KEY_WL_GUST_FACTOR + ".mode")
    open_tab(gust_mode); wait(0.8)
    click(gust_mode); wait(0.6)
    popup_idx = gust_mode.findText("Custom")
    gust_mode.hidePopup(); gust_mode.setCurrentIndex(popup_idx); gust_mode.activated.emit(popup_idx); wait(1.0)
    answer_next_dialog("OK", 3.0)
    click(dlg.save_button); wait(3.8)

    gust_val = dlg.findChild(QLineEdit, KEY_WL_GUST_FACTOR + ".value")
    click(gust_val); type_text(gust_val, "2.5"); wait(0.5)
    answer_next_dialog("OK", 2.0)
    click(dlg.save_button); wait(2.8)

    deck = dlg.findChild(QLineEdit, KEY_TS_DECK_THICKNESS)
    open_tab(deck); click(deck); deck.selectAll(); type_text(deck, "300", clear=False); wait(0.8)
    answer_next_dialog("Discard", 3.0)
    click(dlg.title_bar.btn_close); wait(4.0)

    # ── Task III: design, then transverse plots
    print('STAGE: Task III: design, then transverse plots', flush=True)
    _caption['text'] = 'Task III - transverse members (end diaphragms, cross bracings) in result plots'
    design_btn = dock.design_btn
    click(design_btn)
    t0 = time.time()
    while time.time() - t0 < 120 and not getattr(win.plots_widget, "_ds_all", None) is not None:
        wait(0.5)
    wait(2.0)
    for dlgw in QApplication.topLevelWidgets():          # dismiss any completion notice
        if isinstance(dlgw, QDialog) and dlgw.isVisible() and dlgw is not dlg:
            for b in dlgw.findChildren(QPushButton):
                if b.text().strip() == "OK":
                    click(b)
    click(win.plots_control, None); wait(1.5)
    if not win.output_dock.isVisible() or win.output_dock.width() < 50:
        win.output_dock_toggle(); wait(1.5)

    od = win.output_dock.output_widget
    member = od.findChild(QComboBox, "analysis.member")
    from osdagbridge.desktop.ui.utils.custom_widgets import CustomRadioButton
    radios = {rb.text(): rb for rb in od.findChildren(CustomRadioButton)}
    lc = od.findChild(QComboBox, "analysis.load_combination")


    def choose(combo, text):
        click(combo); wait(0.6); combo.hidePopup()
        combo.setCurrentText(text); wait(2.0)


    choose(member, VALUE_ANALYSIS_END_DIAPHRAGMS)
    click(radios["M<sub>z</sub>"]); wait(2.5)
    click(radios["V<sub>y</sub>"]); wait(2.5)
    choose(member, VALUE_ANALYSIS_CROSS_BRACINGS)
    click(radios["M<sub>z</sub>"]); wait(2.5)
    click(radios["D<sub>y</sub>"]); wait(2.5)
    choose(member, VALUE_ANALYSIS_ALL_TRANSVERSE)
    click(radios["M<sub>z</sub>"]); wait(2.5)
    if lc.findText("Case1 1xClassA") >= 0:
        choose(lc, "Case1 1xClassA"); wait(2.0)
    choose(member, "G1"); wait(2.5)
    _timer.stop()
    out = Path(__file__).resolve().parents[1] / "media" / "demo_video.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(FRAMES / "f%05d.jpg"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", str(out)], check=True)
    shutil.rmtree(FRAMES)
    _caption['text'] = ''
    print("DEMO DONE", out, _n["i"], "frames")


if __name__ == "__main__":
    faulthandler.dump_traceback_later(400, exit=True)
    main()
