"""Compare geometric member classification with ospgrillage group membership."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_design import designed_window
from harness import RESULTS_DIR

GROUPS = ["edge_beam", "exterior_main_beam_1", "exterior_main_beam_2", "interior_main_beam",
          "start_edge", "end_edge", "transverse_slab"]
skew = sys.argv[1] if len(sys.argv) > 1 else None
app, win, b = designed_window(skew=skew)
model = b.grillage_model.model
nodes, members = b.get_nodes_members()
grp = {}
for g in GROUPS:
    try: grp[g] = sorted(int(e) for e in model.get_element(member=g, options="elements"))
    except Exception as e: grp[g] = f"ERR {e}"
long_g = set().union(*[set(grp[g]) for g in GROUPS[:4]])
trans_g = set().union(*[set(grp[g]) for g in GROUPS[4:]])
geo_long = {t for t, (n1, n2) in members.items()
            if abs(nodes[n1][2]-nodes[n2][2]) < 1e-3 and abs(nodes[n1][1]-nodes[n2][1]) < 1e-3}
geo_trans = set(members) - geo_long
out = {
  "skew": skew, "n_elements": len(members), "n_nodes": len(nodes),
  "group_sizes": {g: len(v) if isinstance(v, list) else v for g, v in grp.items()},
  "overlap_long_trans_groups": len(long_g & trans_g),
  "unassigned_by_groups": sorted(set(members) - long_g - trans_g)[:20],
  "geo_long_but_group_trans": sorted(geo_long & trans_g)[:20],
  "geo_trans_but_group_long": sorted(geo_trans & long_g)[:20],
  "all_y_zero": all(abs(c[1]) < 1e-9 for c in nodes.values()),
  "result_data_keys": sorted(b.result_data.keys()),
  "n_crossbracings_in_result_data": len(b.result_data.get("crossbracings", [])),
  "girders": list(b.result_data.get("girders", {}).keys()),
  "edge_dist": b.get_edge_dist(),
}
print(json.dumps(out, indent=1))
(RESULTS_DIR / f"member_groups_skew{skew or 0}.json").write_text(json.dumps(out, indent=1))
