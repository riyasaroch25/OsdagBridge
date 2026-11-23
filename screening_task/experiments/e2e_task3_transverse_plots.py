"""
End-to-end check of Task III: select transverse members in the real output
dock, cycle all nine components, record render time and summary values.
"""
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_design import designed_window
from harness import pump, grab, RESULTS_DIR

from PySide6.QtWidgets import QComboBox
from osdagbridge.desktop.ui.utils.custom_widgets import CustomRadioButton
from osdagbridge.core.utils.common import ANALYSIS_TRANSVERSE_SELECTIONS

skew = sys.argv[1] if len(sys.argv) > 1 else None
app, win, b = designed_window(skew=skew)
win.plots_view_toggle(); pump(app, 0.5)
od = win.output_dock.output_widget
member = od.findChild(QComboBox, "analysis.member")
lc = od.findChild(QComboBox, "analysis.load_combination")
radios = {rb.text(): rb for rb in od.findChildren(CustomRadioButton)}
items = [member.itemText(i) for i in range(member.count())]
out = {"skew": skew, "member_dropdown": items, "runs": []}
for case in ("1.0 DL", "Case1 1xClassA"):
    if lc.findText(case) >= 0:
        lc.setCurrentText(case); pump(app, 0.2)
    for sel in ANALYSIS_TRANSVERSE_SELECTIONS:
        member.setCurrentText(sel); pump(app, 0.2)
        for label in ["F<sub>x</sub>","V<sub>y</sub>","V<sub>z</sub>","T<sub>x</sub>","M<sub>y</sub>","M<sub>z</sub>",
                      "D<sub>x</sub>","D<sub>y</sub>","D<sub>z</sub>"]:
            t0 = time.perf_counter()
            radios[label].setChecked(True); pump(app, 0.05)
            ms = (time.perf_counter() - t0) * 1000
            w = win.plots_widget
            title = w._fig.axes[0].get_title() if w._fig.axes else ""
            out["runs"].append({"loadcase": lc.currentText(), "selection": sel, "component": label,
                                "render_ms": round(ms, 1), "summary": w._summary_data})
            if label in ("M<sub>z</sub>", "V<sub>y</sub>", "D<sub>y</sub>") and case == "Case1 1xClassA":
                pump(app, 0.3)
                tag = label.replace("<sub>", "").replace("</sub>", "")
                grab(w, f"task3_{sel.replace(' ', '_')}_{tag}_skew{skew or 0}.png")
# girder plot still works after transverse selection
member.setCurrentText("G1"); radios["M<sub>z</sub>"].setChecked(True); pump(app, 0.3)
out["girder_plot_after"] = win.plots_widget._fig.axes[0].get_title() if win.plots_widget._fig.axes else None
(RESULTS_DIR / f"task3_e2e_skew{skew or 0}.json").write_text(json.dumps(out, indent=1, default=float))
print(json.dumps({"dropdown": items, "n_runs": len(out["runs"]),
                  "render_ms_max": max(r["render_ms"] for r in out["runs"]),
                  "render_ms_median": sorted(r["render_ms"] for r in out["runs"])[len(out["runs"])//2],
                  "girder_after": out["girder_plot_after"]}))
