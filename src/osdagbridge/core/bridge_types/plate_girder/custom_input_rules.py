"""
custom_input_rules.py
---------------------
Display-independent rules for *Task II — pre-save validation of empty
"Custom" values* in the Additional Inputs dialog.

Rules are **derived from the UI schema**, never hard-coded:

* ``TYPE_MODE_LINE`` fields create a ``<id>.mode`` combo and a ``<id>.value``
  line edit; when the mode is ``VALUE_CUSTOM`` the value is required.
* Combo boxes offering ``VALUE_CUSTOM`` declare the fields they unlock with
  the ``SCHEMA_CUSTOM_REQUIRES`` attribute (central keys only).
* ``TYPE_ADAPTIVE`` fields whose ``VALUE_CUSTOM`` mode is a textbox are
  required when their controller (e.g. ``KEY_DESIGN_MODE``) is ``VALUE_CUSTOM``.

The checker receives a small *state* object so it can be unit-tested
without Qt; the dialog supplies one that reads its live widgets.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Protocol

from osdagbridge.core.utils.common import (
    TYPE_MODE_LINE, TYPE_ADAPTIVE, TYPE_TEXTBOX, TYPE_COMBOBOX,
    VALUE_CUSTOM, SCHEMA_CUSTOM_REQUIRES,
)

MODE_SUFFIX = ".mode"
VALUE_SUFFIX = ".value"
ERROR_TEMPLATE = "Error: The custom value for '{name}' cannot be empty."


@dataclass(frozen=True)
class CustomRule:
    selector_id: str     # objectName of the widget holding the choice (or controller key)
    required_id: str     # objectName of the field that must be non-empty
    label: str           # human-readable parameter name for the message
    controller: bool = False   # selector is a dict key (adaptive controller), not a widget


class WidgetState(Protocol):
    def selector_value(self, rule: CustomRule) -> str | None: ...
    def is_active(self, widget_id: str) -> bool: ...
    def text(self, widget_id: str) -> str | None: ...


def plain_label(label: str | None, fallback: str) -> str:
    """'Drag Coefficient, C<sub>D</sub>' -> 'Drag Coefficient, CD'; strips trailing ':'."""
    if not label:
        return fallback
    text = re.sub(r"<[^>]+>", "", label)
    text = re.sub(r"\s+", " ", text).strip()
    return text.rstrip(":").strip() or fallback


def _walk_fields(node) -> Iterable[dict]:
    if isinstance(node, dict):
        if "id" in node and "type" in node:
            yield node
        for v in node.values():
            yield from _walk_fields(v)
    elif isinstance(node, (list, tuple)):
        for v in node:
            yield from _walk_fields(v)


def extract_custom_rules(schema) -> list[CustomRule]:
    """Walk an Additional Inputs schema (or ADDITIONAL_INPUTS_SCHEMA) and build rules."""
    fields = list(_walk_fields(schema))
    labels = {f["id"]: f.get("label") for f in fields}
    rules: list[CustomRule] = []
    for f in fields:
        fid, ftype = f["id"], f["type"]
        if ftype == TYPE_MODE_LINE and VALUE_CUSTOM in (f.get("mode_choices") or []):
            rules.append(CustomRule(fid + MODE_SUFFIX, fid + VALUE_SUFFIX, plain_label(f.get("label"), fid)))
        elif ftype == TYPE_COMBOBOX and f.get(SCHEMA_CUSTOM_REQUIRES):
            for dep in f[SCHEMA_CUSTOM_REQUIRES]:
                rules.append(CustomRule(fid, dep, plain_label(labels.get(dep), dep)))
        elif ftype == TYPE_ADAPTIVE:
            custom_mode = (f.get("modes") or {}).get(VALUE_CUSTOM) or {}
            if custom_mode.get("type") == TYPE_TEXTBOX and f.get("controller"):
                rules.append(CustomRule(f["controller"], fid, plain_label(f.get("label"), fid), controller=True))
    # de-duplicate while preserving order
    seen, unique = set(), []
    for r in rules:
        if (r.selector_id, r.required_id) not in seen:
            seen.add((r.selector_id, r.required_id))
            unique.append(r)
    return unique


def find_empty_custom_fields(rules: Iterable[CustomRule], state: WidgetState) -> list[CustomRule]:
    """Rules whose selector is 'Custom', whose field is active, and whose text is empty."""
    missing = []
    for rule in rules:
        if str(state.selector_value(rule) or "").strip() != VALUE_CUSTOM:
            continue
        if not rule.controller and not state.is_active(rule.selector_id):
            continue
        if not state.is_active(rule.required_id):
            continue
        text = state.text(rule.required_id)
        if text is not None and not str(text).strip():
            missing.append(rule)
    return missing


def format_errors(missing: Iterable[CustomRule]) -> str:
    return "\n".join(ERROR_TEMPLATE.format(name=r.label) for r in missing)
