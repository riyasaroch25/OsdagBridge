"""Tests for Task II core rules (no display needed)."""
from osdagbridge.core.utils.common import (
    KEY_CB_TYPE, KEY_CB_WIDTH, KEY_RL_LOAD_MODE, KEY_RL_LOAD_VALUE, KEY_WC_MATERIAL,
    KEY_WC_DENSITY, KEY_WL_GUST_FACTOR, KEY_DESIGN_MODE, KEY_MP_GIRDER_DEPTH, VALUE_CUSTOM,
)
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import ADDITIONAL_INPUTS_SCHEMA
from osdagbridge.core.bridge_types.plate_girder.custom_input_rules import (
    CustomRule, extract_custom_rules, find_empty_custom_fields, format_errors, plain_label,
)

RULES = extract_custom_rules(ADDITIONAL_INPUTS_SCHEMA)
PAIRS = {(r.selector_id, r.required_id) for r in RULES}


def test_rules_cover_every_custom_pattern():
    assert (KEY_WL_GUST_FACTOR + ".mode", KEY_WL_GUST_FACTOR + ".value") in PAIRS   # mode-line
    assert (KEY_CB_TYPE, KEY_CB_WIDTH) in PAIRS                                     # combo + deps
    assert (KEY_RL_LOAD_MODE, KEY_RL_LOAD_VALUE) in PAIRS
    assert (KEY_WC_MATERIAL, KEY_WC_DENSITY) in PAIRS
    assert (KEY_DESIGN_MODE, KEY_MP_GIRDER_DEPTH) in PAIRS                          # adaptive


def test_every_mode_line_with_custom_has_a_rule():
    from osdagbridge.core.bridge_types.plate_girder.custom_input_rules import _walk_fields
    from osdagbridge.core.utils.common import TYPE_MODE_LINE
    mode_lines = [f["id"] for f in _walk_fields(ADDITIONAL_INPUTS_SCHEMA)
                  if f["type"] == TYPE_MODE_LINE and VALUE_CUSTOM in f.get("mode_choices", [])]
    assert mode_lines and all((i + ".mode", i + ".value") in PAIRS for i in mode_lines)


def test_plain_label():
    assert plain_label("Drag Coefficient, C<sub>D</sub>", "x") == "Drag Coefficient, CD"
    assert plain_label("Width (m):", "x") == "Width (m)"
    assert plain_label(None, "fallback") == "fallback"


class FakeState:
    def __init__(self, selectors, texts, inactive=()):
        self.selectors, self.texts, self.inactive = selectors, texts, set(inactive)

    def selector_value(self, rule):
        return self.selectors.get(rule.selector_id)

    def is_active(self, wid):
        return wid not in self.inactive

    def text(self, wid):
        return self.texts.get(wid)


R1 = CustomRule("a.mode", "a.value", "Gust Factor, G")
R2 = CustomRule("cb.type", "cb.width", "Width (m)")


def test_custom_and_empty_is_reported():
    state = FakeState({"a.mode": VALUE_CUSTOM, "cb.type": VALUE_CUSTOM}, {"a.value": "  ", "cb.width": "0.5"})
    assert find_empty_custom_fields([R1, R2], state) == [R1]


def test_non_custom_selection_is_ignored():
    state = FakeState({"a.mode": "As per IRC 6"}, {"a.value": ""})
    assert find_empty_custom_fields([R1], state) == []


def test_inactive_tab_or_hidden_field_is_ignored():
    state = FakeState({"a.mode": VALUE_CUSTOM}, {"a.value": ""}, inactive={"a.value"})
    assert find_empty_custom_fields([R1], state) == []
    state = FakeState({"a.mode": VALUE_CUSTOM}, {"a.value": ""}, inactive={"a.mode"})
    assert find_empty_custom_fields([R1], state) == []


def test_message_format_is_exact():
    assert format_errors([R1]) == "Error: The custom value for 'Gust Factor, G' cannot be empty."
