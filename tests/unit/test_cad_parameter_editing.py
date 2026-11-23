"""Tests for Task I core logic (no display needed)."""
import math

import pytest

from osdagbridge.core.utils.common import (
    KEY_SPAN, KEY_CARRIAGEWAY_WIDTH, KEY_TS_GIRDER_SPACING, KEY_TS_DECK_THICKNESS,
    KEY_TS_DECK_OVERHANG, KEY_TS_OVERALL_WIDTH, KEY_TS_NO_OF_GIRDERS, KEY_MP_CB_SPACING,
)
from osdagbridge.core.bridge_types.plate_girder.cad_parameter_editing import (
    classify_label, evaluate_cad_edit, parse_number,
)
from osdagbridge.core.bridge_types.plate_girder.defaults import (
    BASIC_INPUT_DICT, solve_extend_basic_input_dict,
)


@pytest.fixture
def solved_inputs():
    d = dict(BASIC_INPUT_DICT)
    d[KEY_SPAN] = 20
    d[KEY_CARRIAGEWAY_WIDTH] = 5
    solve_extend_basic_input_dict(d)
    return d


@pytest.mark.parametrize("text,key", [
    ("Carriageway Width = 5.00 m", KEY_CARRIAGEWAY_WIDTH),
    ("Girder Spacing", KEY_TS_GIRDER_SPACING),
    ("Girder\nSpacing\n= 1.97 m", KEY_TS_GIRDER_SPACING),   # plan-view label
    ("Deck Thickness = 250 mm", KEY_TS_DECK_THICKNESS),
    ("Span Length = 20.0 m", KEY_SPAN),
    ("Overhang = 0.98 m", KEY_TS_DECK_OVERHANG),
    ("Overall Bridge Width = 5.90 m", KEY_TS_OVERALL_WIDTH),
    ("Bracing Spacing = 3.50 m", KEY_MP_CB_SPACING),
])
def test_classify_known_labels(text, key):
    assert classify_label(text).key == key


@pytest.mark.parametrize("text", ["CL of Bearing", "Girder", "Median = 1.2 m", "", "Footpath Width"])
def test_classify_ignores_other_text(text):
    assert classify_label(text) is None


def test_editable_and_locked_sets_match_assignment():
    editable = {classify_label(t).key for t in
                ["Carriageway Width", "Girder Spacing", "Deck Thickness", "Span Length"]}
    locked = [classify_label(t) for t in ["Overhang", "Overall Bridge Width", "Bracing Spacing"]]
    assert all(classify_label(t).editable for t in
               ["Carriageway Width", "Girder Spacing", "Deck Thickness", "Span Length"])
    assert len(editable) == 4
    assert not any(s.editable for s in locked)


@pytest.mark.parametrize("text", ["", "abc", "nan", "inf", "-inf", "1e999", None])
def test_parse_rejects_non_finite(text):
    assert parse_number(text) is None


def test_validator_alone_accepts_nan():
    """Documents the pre-existing gap our parse step closes."""
    from osdagbridge.core.bridge_types.plate_girder.validator import BridgeInputValidator
    v = BridgeInputValidator()
    assert v.validate_additional_inputs(KEY_TS_DECK_THICKNESS, {KEY_TS_DECK_THICKNESS: "nan"}) is None
    assert evaluate_cad_edit({}, KEY_TS_DECK_THICKNESS, "nan").ok is False


@pytest.mark.parametrize("key", [KEY_TS_DECK_OVERHANG, KEY_TS_OVERALL_WIDTH, KEY_MP_CB_SPACING])
def test_locked_parameters_rejected(solved_inputs, key):
    assert evaluate_cad_edit(solved_inputs, key, "1.0").ok is False


def test_deck_thickness_valid_and_out_of_range(solved_inputs):
    ok = evaluate_cad_edit(solved_inputs, KEY_TS_DECK_THICKNESS, "220")
    assert ok.ok and ok.updates == {KEY_TS_DECK_THICKNESS: 220.0}
    assert not evaluate_cad_edit(solved_inputs, KEY_TS_DECK_THICKNESS, "50").ok
    assert not evaluate_cad_edit(solved_inputs, KEY_TS_DECK_THICKNESS, "900").ok


def test_girder_spacing_keeps_width_equation(solved_inputs):
    d = solved_inputs
    n = int(d[KEY_TS_NO_OF_GIRDERS])
    res = evaluate_cad_edit(d, KEY_TS_GIRDER_SPACING, "1.80")
    assert res.ok, res.message
    u = res.updates
    assert u[KEY_TS_NO_OF_GIRDERS] == n                       # n held fixed
    assert math.isclose(u[KEY_TS_GIRDER_SPACING], 1.80)
    width = (n - 1) * u[KEY_TS_GIRDER_SPACING] + 2 * u[KEY_TS_DECK_OVERHANG]
    assert math.isclose(width, u[KEY_TS_OVERALL_WIDTH], abs_tol=1e-3)
    assert math.isclose(u[KEY_TS_OVERALL_WIDTH], d[KEY_TS_OVERALL_WIDTH], abs_tol=1e-9)


def test_girder_spacing_infeasible_rejected(solved_inputs):
    # Spacing larger than overall/2 is rejected by the validator; spacing that
    # makes the overhang negative is rejected by the solver.
    assert not evaluate_cad_edit(solved_inputs, KEY_TS_GIRDER_SPACING, "50").ok
    n = int(solved_inputs[KEY_TS_NO_OF_GIRDERS])
    too_wide = solved_inputs[KEY_TS_OVERALL_WIDTH] / (n - 1) + 0.01
    if too_wide <= solved_inputs[KEY_TS_OVERALL_WIDTH] / 2:
        assert not evaluate_cad_edit(solved_inputs, KEY_TS_GIRDER_SPACING, f"{too_wide}").ok


def test_basic_inputs_use_basic_validator(solved_inputs):
    assert evaluate_cad_edit(solved_inputs, KEY_SPAN, "30").ok
    assert not evaluate_cad_edit(solved_inputs, KEY_SPAN, "5").ok          # below SPAN_MIN
    assert not evaluate_cad_edit(solved_inputs, KEY_CARRIAGEWAY_WIDTH, "1").ok


def test_input_dict_not_mutated(solved_inputs):
    before = dict(solved_inputs)
    evaluate_cad_edit(solved_inputs, KEY_TS_GIRDER_SPACING, "1.8")
    assert solved_inputs == before
