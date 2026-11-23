# 06 — Implementation Details

Branch `screening-task/ui-2dcad-plotting` (3 commits on top of `dev@d74f56d`).
Production code: 15 files changed, ~980 lines added, 22 removed. New tests: 3 files, 46 tests.

## Task I — Interactive 2D CAD parameter editing

| File | Change |
|---|---|
| `core/bridge_types/plate_girder/cad_parameter_editing.py` (new) | `CAD_LABEL_SPECS` maps each painted caption to a central key, unit, CAD param, editable/locked flag and lock reason. `classify_label` normalises captions (the plan view paints `"Girder\nSpacing\n= 1.97 m"`). `parse_number` rejects `''`, junk, `nan`, `±inf`. `evaluate_cad_edit` is pure: runs `BridgeInputValidator` (basic or additional), and for girder spacing calls `BridgeConfigurationSolver._solve_layout(changed_field="spacing")` with *n* fixed, returning spacing, overhang, overall width and *n* together. |
| `desktop/ui/docks/cad_label_editing.py` (new) | `EditableLabelsMixin`: `_record_label` (called from the shared `draw_text_with_background`) stores `(rect, spec)` every paint; `label_spec_at` hit-tests topmost-first with a 3 px tolerance; hover sets I-beam / forbidden cursor + tooltip; `mouseDoubleClickEvent` opens a `QLineEdit` (QDoubleValidator, value pre-filled in the label's unit) or shows the lock reason; commit on Enter or focus-out, Esc cancels; a re-entrancy guard prevents the double commit Qt produces (`returnPressed` followed by `editingFinished`); the emit is deferred so the editor is gone before any modal dialog. |
| `cad_cross_section.py`, `cad_top_view.py` | Inherit the mixin; `label_value_edited = Signal(str, str)`; reset registry in `paintEvent`; forward editor key events and hover. Editing is **opt-in** (`labels_editable`), so the cross-section preview inside Additional Inputs stays read-only. |
| `template_page.py` | `_enable_cad_label_editing` (both views), `_cad_label_edit_allowed` (refuse while the input dock is locked), `_on_cad_label_edited`: basic inputs are written into the input-dock field and passed to the dock's own `_on_field_edited`, so its validation popup, required-field re-solve and CAD refresh run unchanged; additional inputs first ensure `solve_extend_basic_input_dict` has already run (otherwise a later re-solve would overwrite the edit), then apply `evaluate_cad_edit` updates to `input_dict` (shared by reference with the Additional Inputs dialog) and invalidate the dual-CAD change cache before redrawing. |

Design notes:
* *Single source of truth:* the CAD has no validation rules of its own.
* *Pre-existing behaviour preserved:* changing a basic input (span/carriageway) re-applies
  typical-section defaults (e.g. deck thickness back to 250 mm). This also happens when the
  field is edited in the dock; it is documented, not changed.
* *Bug found:* `BridgeInputValidator._to_float("nan")` yields NaN, which passes every range
  check; the CAD path guards against it (test `test_validator_alone_accepts_nan`).

## Task II — Additional Inputs validation and state management

| File | Change |
|---|---|
| `core/utils/common.py` | `VALUE_CUSTOM = "Custom"`, `SCHEMA_CUSTOM_REQUIRES = "custom_requires"` (only two new keys). |
| `ui_fields_additional_input.py` | Five selectors declare dependants with keys only: crash barrier type, median type, railing type, railing load mode, wearing-coat material. |
| `core/.../custom_input_rules.py` (new) | `extract_custom_rules` walks `ADDITIONAL_INPUTS_SCHEMA`: every `TYPE_MODE_LINE` with a Custom choice → (`<id>.mode`, `<id>.value`); every combo with `SCHEMA_CUSTOM_REQUIRES`; every `TYPE_ADAPTIVE` whose Custom mode is a textbox (controller `KEY_DESIGN_MODE`). Labels come from the schema with HTML stripped. `find_empty_custom_fields` takes a *state* protocol (testable without Qt). `ERROR_TEMPLATE` is the exact required format. |
| `additional_inputs.py` | `_validate_custom_inputs` at the top of `_save_inputs`: lists every missing field, sets the existing `error` style property, switches nested tabs to reveal and focus the first one. `_is_widget_active` treats a page of a `QTabWidget` as active iff its tab is **enabled** (non-current pages are hidden by `QStackedWidget`, so visibility cannot be used) and other ancestors iff not explicitly hidden — e.g. crash-barrier density is hidden for "Custom" and is correctly not required. Dirty tracking via user-only signals; `_on_segment_data_changed` marks only on a real change (its table re-emits unchanged data on refresh — found in E2). `closeEvent` and `reject` share `_confirm_discard_changes`; **Discard** calls `set_input_dictionary(default_input_dict)` so widget state cannot leak into compute functions that read widgets at design time (`compute_railing_values` reads the load-mode combo). |

## Task III — Transverse member plotting

| File | Change |
|---|---|
| `results_data.py` | `classify_members`: group membership first, geometry fallback (the second edge beam is in no group). `_build_full_data` stores `support_transverse_members` (start/end edges). New: `build_transverse_member_map`, `member_local_axes`, `member_internal_forces`, `transverse_member_results` (forces → member-local internal kN/kN·m; displacements → global mm, consistent with girder plots). |
| `results_data_post_processing.py` | `end_diaphragms` built with the existing `build_crossbracings` girder-pair rule; added to `OUTPUT_KEYS`. |
| `plot_generator.py` | `build_figure_transverse`: per member baseline, filled diagram, end values, group extremes tagged `max_line`/`min_line` (so the existing Max/Min/All toggles work), summary per girder pair (`ED G1–G2`, `CB G2–G3`). |
| `common.py` | Dropdown values and `ANALYSIS_TRANSVERSE_SELECTIONS` (value → map groups). |
| `output_dock.py`, `mpl_plot_widget.py`, `template_page.py`, `plategirderbridge.py` | Dropdown entries; `setup(..., transverse_map=…)`; dispatch to the transverse builder; `get_transverse_member_map()`; camera restored only within the same plot family. |

Equations (per member, per end *e* ∈ {i, j}):

$$R = \begin{bmatrix} e_x^T \\ e_y^T \\ e_z^T\end{bmatrix},\quad
\mathbf f^{loc}_e = R\,\mathbf f^{glob}_e,\quad \mathbf m^{loc}_e = R\,\mathbf m^{glob}_e,\quad
S(i) = -\,\mathbf s^{loc}_i,\; S(j) = +\,\mathbf s^{loc}_j$$

UI mapping: Fx → $S_{f,x}$ (axial), Vy/Vz → $S_{f,y}$/$S_{f,z}$, Tx → $S_{m,x}$,
My/Mz → $S_{m,y}$/$S_{m,z}$.

```text
for member in selected transverse members:
    n1, n2 = members[member]
    F = ds.forces.sel(Element=member)             # global end forces (12)
    R = [ex; ey; ez](n1 → n2)
    S_i, S_j = −(R·F_i), +(R·F_j)                 # force and moment triplets
    draw baseline n1–n2; fill polygon (n1,0)(n2,0)(n2,S_j)(n1,S_i)
```
