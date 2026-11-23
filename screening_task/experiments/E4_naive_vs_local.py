"""
Experiment E4 (baseline vs proposed): for transverse members, compare the
naive approach (plot raw global component with the girder label, e.g. "Mz" =
global Mz) with member-local internal forces. Reports, per UI component, the
peak magnitude each approach would show and what physical quantity the naive
value actually is.
"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_design import designed_window
from harness import RESULTS_DIR
from osdagbridge.core.bridge_types.plate_girder.results_data import transverse_member_results

skew = sys.argv[1] if len(sys.argv) > 1 else None
app, win, b = designed_window(skew=skew)
ds_all = b.get_results_dataset(); nodes, members = b.get_nodes_members()
tmap = b.get_transverse_member_map()
items = tmap["end_diaphragms"] + tmap["cross_bracings"]
naive_comp = {"Fx": "Vx", "Fy": "Vy", "Fz": "Vz", "Mx": "Mx", "My": "My", "Mz": "Mz"}
out = {"skew": skew, "n_members": len(items), "loadcases": {}}
for lc in ("1.0 DL", "Case1 1xClassA"):
    ds = ds_all.sel(Loadcase=lc); row = {}
    for key, gc in naive_comp.items():
        local = transverse_member_results(ds, nodes, members, items, key)
        p_local = max(max(abs(r["value_i"]), abs(r["value_j"])) for r in local)
        naive = [abs(float(ds["forces"].sel(Element=int(it["member"]), Component=f"{gc}_{e}").values)) / 1000
                 for it in items for e in "ij"]
        row[key] = {"peak_local": round(p_local, 3), "peak_naive_global": round(max(naive), 3)}
    out["loadcases"][lc] = row
print(json.dumps(out, indent=1))
(RESULTS_DIR / f"E4_naive_vs_local_skew{skew or 0}.json").write_text(json.dumps(out, indent=1))
