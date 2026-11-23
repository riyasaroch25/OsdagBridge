"""
cad_parameter_editing.py
------------------------
Display-independent logic behind *Task I — Interactive 2D CAD parameter
editing*.

The 2D CAD shows two kinds of dimension labels:

* **independent parameters** the user may edit in place
  (span, carriageway width, girder spacing, deck thickness), and
* **derived quantities** that follow from the girder-layout equation

      overall_width = (n - 1) * girder_spacing + 2 * deck_overhang

  (overhang, overall width) or from other inputs (bracing spacing).
  Editing a derived value is an under-determined inverse problem (which of
  n, spacing or overhang should absorb the change?), so these labels are
  locked.

This module maps label text to central keys (``core.utils.common``), parses
and validates typed values with the *same* ``BridgeInputValidator`` used by
the input fields, and re-solves the girder layout with the *same*
``BridgeConfigurationSolver`` used by the Additional Inputs dialog, so the
CAD and the forms can never disagree about what is legal.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_CARRIAGEWAY_WIDTH,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_OVERALL_WIDTH,
    KEY_TS_NO_OF_GIRDERS,
    KEY_MP_CB_SPACING,
    KEY_FOOTPATH,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_RL_WIDTH,
    KEY_CB_WIDTH,
    KEY_MD_WIDTH,
)


@dataclass(frozen=True)
class CadLabelSpec:
    """How one CAD dimension label maps onto an input-dictionary key."""
    key: str            # central key from core.utils.common
    caption: str        # label caption as painted on the CAD (without value)
    unit: str           # unit the label displays and the editor accepts
    cad_param: str      # CrossSection/TopView widget param name (stored in mm)
    editable: bool
    basic: bool = False  # True -> lives in the input dock (basic input)
    lock_reason: str = ""


# Order matters only for documentation; matching is by exact caption.
CAD_LABEL_SPECS: tuple[CadLabelSpec, ...] = (
    CadLabelSpec(KEY_CARRIAGEWAY_WIDTH, "Carriageway Width", "m", "carriageway_width", True, basic=True),
    CadLabelSpec(KEY_SPAN,              "Span Length",       "m", "span_length",       True, basic=True),
    CadLabelSpec(KEY_TS_GIRDER_SPACING, "Girder Spacing",    "m", "girder_spacing",    True),
    CadLabelSpec(KEY_TS_DECK_THICKNESS, "Deck Thickness",    "mm", "deck_thickness",   True),
    CadLabelSpec(KEY_TS_DECK_OVERHANG,  "Overhang",          "m", "deck_overhang",     False,
                 lock_reason="Overhang is derived from overall width, girder count and girder spacing."),
    CadLabelSpec(KEY_TS_OVERALL_WIDTH,  "Overall Bridge Width", "m", "",               False,
                 lock_reason="Overall bridge width is derived from carriageway, barrier, footpath, railing and median widths."),
    CadLabelSpec(KEY_MP_CB_SPACING,     "Bracing Spacing",   "m", "cross_bracing_spacing", False,
                 lock_reason="Bracing spacing is a derived/design value; change it in Additional Inputs."),
)

_SPEC_BY_CAPTION = {s.caption.lower(): s for s in CAD_LABEL_SPECS}
_SPEC_BY_KEY = {s.key: s for s in CAD_LABEL_SPECS}


def spec_for_key(key: str) -> CadLabelSpec | None:
    return _SPEC_BY_KEY.get(key)


def classify_label(text: str) -> CadLabelSpec | None:
    """Return the spec of a painted label, or None for non-parameter text.

    Painted labels look like ``"Girder Spacing = 1.97 m"`` or, in the plan
    view, ``"Girder\\nSpacing\\n= 1.97 m"``; whitespace/newlines are
    normalised and anything after ``=`` is ignored.
    """
    if not text:
        return None
    caption = text.split("=", 1)[0]
    caption = re.sub(r"\s+", " ", caption).strip().lower()
    return _SPEC_BY_CAPTION.get(caption)


def cad_value_to_display(spec: CadLabelSpec, value_mm: float) -> float:
    """CAD widgets store lengths in mm; labels display m (or mm)."""
    return value_mm / 1000.0 if spec.unit == "m" else value_mm


@dataclass
class EditResult:
    ok: bool
    updates: dict = field(default_factory=dict)   # key -> new value for input_dict
    message: str = ""                             # error or info text


def parse_number(text: str) -> float | None:
    """Parse user text to a finite float; rejects '', 'nan', 'inf', junk."""
    try:
        value = float(str(text).strip())
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def _num(d: dict, key: str, default: float = 0.0) -> float:
    try:
        v = d.get(key)
        return float(v) if v not in (None, "") else default
    except (TypeError, ValueError):
        return default


def layout_solver_from_inputs(d: dict):
    """Build the BridgeConfigurationSolver exactly as defaults.solve_extend_basic_input_dict does."""
    from osdagbridge.core.bridge_types.plate_girder.initial_sizing import BridgeConfigurationSolver

    footpath = str(d.get(KEY_FOOTPATH, "None")).strip()
    if footpath in ("None", ""):
        n_fp, fp_w, rl_w = 0, 0.0, 0.0
    else:
        n_fp = 2 if "Both" in footpath else 1
        fp_w = _num(d, KEY_TS_FOOTPATH_WIDTH)
        rl_w = _num(d, KEY_RL_WIDTH)
        rl_w = rl_w / 1000.0 if rl_w > 10 else rl_w  # railing width may be stored in mm
    return BridgeConfigurationSolver(
        carriageway_width=_num(d, KEY_CARRIAGEWAY_WIDTH),
        crash_barrier_width=_num(d, KEY_CB_WIDTH),
        footpath_width=fp_w,
        railing_width=rl_w,
        median_width=_num(d, KEY_MD_WIDTH),
        n_footpaths=n_fp,
    )


def evaluate_cad_edit(input_dict: dict, key: str, raw_text: str, validator=None) -> EditResult:
    """Validate an in-place CAD edit and compute the dictionary updates.

    Pure function: ``input_dict`` is not modified. Basic inputs (span,
    carriageway width) are only parsed and range-checked here; the caller
    routes them through the input dock so that the existing basic-input
    pipeline (validation popup, required-field re-solve, CAD refresh) runs
    unchanged.
    """
    spec = spec_for_key(key)
    if spec is None:
        return EditResult(False, message=f"'{key}' is not a CAD-editable parameter.")
    if not spec.editable:
        return EditResult(False, message=spec.lock_reason or f"{spec.caption} is read-only.")

    value = parse_number(raw_text)
    if value is None:
        return EditResult(False, message=f"{spec.caption} must be a finite numeric value ({spec.unit}).")
    if value <= 0:
        return EditResult(False, message=f"{spec.caption} must be greater than zero.")

    if validator is None:
        from osdagbridge.core.bridge_types.plate_girder.validator import BridgeInputValidator
        validator = BridgeInputValidator()

    trial = dict(input_dict)
    trial[key] = value
    check = (validator.validate_basic_inputs if spec.basic else validator.validate_additional_inputs)
    problem = check(key, trial)
    if problem is not None:
        _corrected, message = problem
        return EditResult(False, message=message)

    if key == KEY_TS_GIRDER_SPACING:
        # n is held fixed; the overhang absorbs the change (solver contract).
        try:
            n = int(_num(input_dict, KEY_TS_NO_OF_GIRDERS, 0))
            result = layout_solver_from_inputs(input_dict)._solve_layout(
                no_of_girders=n,
                girder_spacing=value,
                deck_overhang=_num(input_dict, KEY_TS_DECK_OVERHANG),
                changed_field="spacing",
            )
        except ValueError as exc:
            return EditResult(False, message=str(exc))
        return EditResult(True, updates={
            KEY_TS_GIRDER_SPACING: result.girder_spacing,
            KEY_TS_DECK_OVERHANG: result.deck_overhang,
            KEY_TS_OVERALL_WIDTH: result.overall_width,
            KEY_TS_NO_OF_GIRDERS: result.no_of_girders,
        })

    return EditResult(True, updates={key: value})
