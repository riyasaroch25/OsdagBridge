"""
Run a full OsdagBridge design through the real template page, on the main
thread, following the same steps as CustomWindow.common_design_func, then wire
the result plots exactly as the UI does after a successful design.
"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import build_main_window, pump  # noqa: E402

from PySide6.QtWidgets import QLineEdit
from osdagbridge.core.bridge_types.plate_girder.defaults import solve_extend_basic_input_dict
from osdagbridge.core.utils.common import *


def designed_window(span="20", carriageway="5", skew=None, location=None):
    app, win = build_main_window()
    dock = win.input_dock
    fields = [(KEY_SPAN, span), (KEY_CARRIAGEWAY_WIDTH, carriageway)]
    if skew is not None:
        fields.append((KEY_SKEW_ANGLE, skew))
    for key, val in fields:
        w = dock.input_widget.findChild(QLineEdit, key)
        w.setText(str(val)); dock._on_field_edited(key, w)
    # Same structure ProjectLocation.get_selected_location() returns for
    # "custom data". Fixture values (Mumbai-like): Vb = 44 m/s, zone III.
    win.input_dict[KEY_PROJECT_LOCATION] = location or {
        "method": "custom_data", "data": {},
        "weather_data": {"wind_speed": 44, "zone": "III", "z_value": 0.16,
                         "max_temp": 45, "min_temp": 5},
        "display_text": "", "show_display": False,
    }
    pump(app, 0.3)
    dock._prime_material_inputs()
    solve_extend_basic_input_dict(win.input_dict); dock.is_require_field_changed = False
    dlg = win._get_additional_inputs(); dlg.set_input_dictionary(win.input_dict)
    win._sync_compute_results_to_input_dict()
    b = win.backend
    t0 = time.perf_counter()
    b.set_input(win.input_dict); b.design()
    b._design_seconds = time.perf_counter() - t0
    win.output_dock.refresh_loadcase_dropdowns()
    win.output_dock.refresh_member_dropdown()
    win.plots_widget.setup(b.get_results_dataset(), b.get_available_loadcases(),
                           *b.get_nodes_members(), edge_dist=b.get_edge_dist(),
                           transverse_map=b.get_transverse_member_map())
    win.plots_widget.link_output_dock(win.output_dock)
    return app, win, b


if __name__ == "__main__":
    app, win, b = designed_window()
    print("design s:", round(b._design_seconds, 1))
    print("loadcases:", b.get_available_loadcases()[:15])
