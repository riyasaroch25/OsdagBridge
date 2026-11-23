"""
Experiment E3: verify results_data.member_internal_forces against OpenSees.

For every element of the analysed model, rotate OpenSees' global end forces
('forces') into member-local axes and compare with OpenSees' own local end
forces ('localForces'). Also checks the transverse-member map.
"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_design import designed_window
from harness import RESULTS_DIR
import openseespy.opensees as ops
from osdagbridge.core.bridge_types.plate_girder.results_data import (
    member_local_axes, build_transverse_member_map, classify_members)

skew = sys.argv[1] if len(sys.argv) > 1 else None
app, win, b = designed_window(skew=skew)
nodes, members = b.get_nodes_members()
report = {"skew": skew, "per_kind": {}}
tmap = build_transverse_member_map(b.result_data)
kinds = {"end_diaphragms": {int(i["member"]) for i in tmap["end_diaphragms"]},
         "cross_bracings": {int(i["member"]) for i in tmap["cross_bracings"]}}
for kind, ids in [("girder/edge (longitudinal)", None), *kinds.items()]:
    errs, mags, n = [], [], 0
    for e, (n1, n2) in members.items():
        if ids is None and not abs(nodes[n1][2]-nodes[n2][2]) < 1e-6: continue
        if ids is not None and e not in ids: continue
        g = np.array(ops.eleResponse(e, "forces"), float)
        loc = np.array(ops.eleResponse(e, "localForces"), float)
        R = np.vstack(member_local_axes(nodes[n1], nodes[n2]))
        mine = np.concatenate([R @ g[0:3], R @ g[3:6], R @ g[6:9], R @ g[9:12]])
        # OpenSees local y/z may be oriented differently (vecxz); compare per component
        # allowing a sign flip of the transverse axes, report the best match.
        best = min((np.max(np.abs(mine*s - loc)), s.tolist()) for s in
                   [np.tile(np.array([1,a,c,1,a,c]),2) for a in (1,-1) for c in (1,-1)])
        errs.append(best[0]); mags.append(np.max(np.abs(loc))); n += 1
        sign = best[1][:6]
    report["per_kind"][kind] = {"n_elements": n, "max_abs_error": float(max(errs)),
                                "max_force_magnitude": float(max(mags)), "axis_sign_pattern": sign}
report["transverse_map_counts"] = {k: len(v) for k, v in tmap.items()}
report["example_end_diaphragm"] = tmap["end_diaphragms"][:2]
report["n_girders"] = len(b.result_data.get("girders", {}))
print(json.dumps(report, indent=1, default=str))
(RESULTS_DIR / f"E3_local_force_check_skew{skew or 0}.json").write_text(json.dumps(report, indent=1, default=str))
