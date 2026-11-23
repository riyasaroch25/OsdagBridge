# 08 — Critical Review and Roadmap

## Status

| Requirement | Status |
|---|---|
| I-1…I-5 double-click edit, 4 editable, 3 locked, Enter/click-outside commit, dictionaries + redraw | **Completed** (E1) |
| II-1…II-3 Save interception, all active tabs, exact error format | **Completed** (E2) |
| II-4 `is_modified`, `closeEvent`, Discard/Cancel with exact text | **Completed**; also covers Esc (`reject`) |
| II-5 central keys only; minimal new keys | **Completed** (2 keys + 4 dropdown values) |
| III-1…III-4 transverse members in dropdown, 9 components per load case, extraction via `results_data.py`, accurate tag mapping | **Completed** (E3–E5) |
| Video, PDF report submission, GitHub collaborator | **Not done by the implementer** — require the candidate's accounts |

## Self-critique (as an evaluator would)

1. **Single test bridge.** E1–E5 use one 3-girder geometry. *Partially mitigated* by unit
   tests on synthetic geometries.
2. **Pre-existing reset of additional inputs on basic edits.** Editing span/carriageway
   (on the CAD or the dock) re-applies typical-section defaults, discarding e.g. a custom
   deck thickness. Correct by the existing contract, surprising to users.
3. **Equivalent-beam cross-frame forces.** The plot shows the grillage's equivalent beam
   force, not diagonal/chord forces (explicitly allowed by the task). NCHRP 962 warns that
   converting these is error-prone; the existing `CrossBracingForces` does this for design.
4. **Plot widget complexity.** `build_figure_transverse` follows the existing builders'
   style (3-D axes, gid tags); mplcursors hover is not wired for transverse points.
5. **Environment fragility.** `environment.yml` does not yield a runnable desktop app on
   macOS arm64 (see README); this affects every contributor, not only this work.
6. **Validator NaN gap** is guarded only on the CAD path; the form path still accepts NaN.

## Roadmap

| Priority | Improvement | Reason | Expected impact | Complexity |
|---|---|---|---|---|
| Critical | Fix `BridgeInputValidator._to_float` to reject non-finite values | Silent NaN acceptance in forms | Removes a latent invalid-design path | Low |
| Critical | Complete `environment.yml` (PySide6 ≤ 6.9.3, navcube, mplcursors, ifcopenshell, openpyxl, plotly) and document the Qt plugin path | Reproducibility | New contributors can run the app | Low |
| High | Run E1/E5 on 2-, 4-, 6-girder and no-overhang bridges in CI (pytest-qt) | Coverage | Regression safety | Medium |
| High | Preserve user-set additional inputs when a basic input changes (re-solve only dependent keys) | Item 2 | Fewer surprises | Medium |
| Medium | Undo/redo for CAD edits; keyboard navigation (Tab between labels, F2 to edit) | Direct-manipulation reversibility, accessibility | UX | Medium |
| Medium | Optional diagonal/chord force view using `CrossBracingForces` | Item 3 | Design-relevant member forces | Medium |
| Future | Chooser for derived labels ("absorb change in spacing or overhang?") | Cascaval et al. / Hempel et al. ambiguity | Editing W directly | Medium |
| Future | Compare grillage transverse forces with a 3D shell model for selected bridges | NCHRP 725 | Quantify model error | High |
