"""Tests for Task III data layer in results_data.py (no analysis needed)."""
import math

import numpy as np
import pytest

from osdagbridge.core.bridge_types.plate_girder.results_data import (
    classify_members, member_local_axes, member_internal_forces, build_transverse_member_map,
)
from osdagbridge.core.bridge_types.plate_girder.results_data_post_processing import build_crossbracings

# 3 girder lines (z = 0, 2, 4) + edge lines (z = -1, 5), two stations x = 0, 5
NODES = {}
tag = 1
for x in (0.0, 5.0):
    for z in (-1.0, 0.0, 2.0, 4.0, 5.0):
        NODES[tag] = [x, 0.0, z]; tag += 1
# transverse at x=0: 1-2 (edge->G1), 2-3, 3-4 (girder pairs), 4-5 (G3->edge)
MEMBERS = {1: [1, 2], 2: [2, 3], 3: [3, 4], 4: [4, 5],
           5: [6, 7], 6: [7, 8], 7: [8, 9], 8: [9, 10],      # transverse at x=5
           9: [1, 6], 10: [2, 7], 11: [3, 8], 12: [4, 9], 13: [5, 10]}   # longitudinal


def test_groups_take_precedence_and_geometry_is_fallback():
    groups = {"exterior_main_beam_1": [10], "exterior_main_beam_2": [12], "interior_main_beam": [11],
              "edge_beam": [9],                       # second edge beam (13) deliberately ungrouped
              "start_edge": [1, 2, 3, 4], "end_edge": [5, 6, 7, 8], "transverse_slab": []}
    longi, trans = classify_members(NODES, MEMBERS, groups)
    assert sorted(longi) == [9, 10, 11, 12, 13]       # 13 recovered by geometry
    assert sorted(trans) == [1, 2, 3, 4, 5, 6, 7, 8]


def test_group_membership_overrides_geometry():
    # A "longitudinal" member that is not parallel to X (e.g. curved girder chord)
    nodes = {1: [0, 0, 0], 2: [5, 0, 0.3]}
    longi, trans = classify_members(nodes, {1: [1, 2]}, {"interior_main_beam": [1]})
    assert longi == [1] and trans == []


def test_local_axes_girder_equals_global():
    ex, ey, ez = member_local_axes([0, 0, 0], [3, 0, 0])
    assert np.allclose(np.vstack([ex, ey, ez]), np.eye(3))


def test_local_axes_transverse_member():
    ex, ey, ez = member_local_axes([0, 0, 0], [0, 0, 2])
    assert np.allclose(ex, [0, 0, 1]) and np.allclose(ey, [0, 1, 0]) and np.allclose(ez, [-1, 0, 0])
    assert math.isclose(np.linalg.det(np.vstack([ex, ey, ez])), 1.0)   # right-handed


def _end_forces(Fi, Mi, Fj, Mj):
    d = {}
    for a, v in zip("xyz", Fi): d[f"V{a}_i"] = v
    for a, v in zip("xyz", Mi): d[f"M{a}_i"] = v
    for a, v in zip("xyz", Fj): d[f"V{a}_j"] = v
    for a, v in zip("xyz", Mj): d[f"M{a}_j"] = v
    return d


def test_transverse_member_maps_global_components_correctly():
    # Member along +Z: global Vz is axial, global Mx is major bending (about -local z), Mz is torsion.
    f = _end_forces(Fi=(0, 10, -7), Mi=(3, 0, 2), Fj=(0, -10, 7), Mj=(5, 0, -2))
    s = member_internal_forces(f, [0, 0, 0], [0, 0, 2])
    assert s["Fx"] == (7.0, 7.0)          # axial: S_i = -F_i·ex = 7, S_j = F_j·ex = 7
    assert s["Fy"] == (-10.0, -10.0)      # vertical shear, same at both ends (no span load)
    assert s["Mx"] == (-2.0, -2.0)        # torsion from global Mz; constant along member (equilibrium)
    assert s["Mz"] == (3.0, -5.0)         # bending from global Mx (ez = -X)


def test_girder_internal_forces_match_global_components():
    f = _end_forces(Fi=(1, 2, 3), Mi=(4, 5, 6), Fj=(-1, -2, -3), Mj=(-4, -5, 7))
    s = member_internal_forces(f, [0, 0, 0], [4, 0, 0])
    assert s["Mz"] == (-6.0, 7.0) and s["Fx"] == (-1.0, -1.0)


def test_transverse_map_excludes_overhang_strips():
    girders = {"G1": {"nodes": [2, 7], "index": 1}, "G2": {"nodes": [3, 8], "index": 2},
               "G3": {"nodes": [4, 9], "index": 3}}
    members = {str(k): v for k, v in MEMBERS.items()}
    nodes = {str(k): v for k, v in NODES.items()}
    ends = build_crossbracings([1, 2, 3, 4], members, nodes, girders)
    rd = {"end_diaphragms": ends, "crossbracings": []}
    tmap = build_transverse_member_map(rd)
    assert [i["member"] for i in tmap["end_diaphragms"]] == ["2", "3"]   # 1 and 4 are overhangs
    assert tmap["end_diaphragms"][0]["left_girder"] == "G1"
    assert tmap["cross_bracings"] == []


def test_zero_length_member_rejected():
    with pytest.raises(ValueError):
        member_local_axes([1, 0, 1], [1, 0, 1])
