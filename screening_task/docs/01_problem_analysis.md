# 01 — Problem Analysis

**Assignment:** FOSSEE Osdag Winter Internship 2026, Software Development track:
*"OsdagBridge UI, 2D CAD, and Plotting Enhancements"*.
**Source:** task document linked from the Osdag screening page
(`docs.google.com/document/d/1YT7vpak9EFFyPxX46O_e9FAw01iiVFtx`), retrieved 2026-11-23.
**Codebase baseline:** `Nidhikhare12/OsdagBridge`, branch `dev`, commit `d74f56d` (2026-07-26).

---

## 1. Problem statement (in our own words)

OsdagBridge is the bridge plug-in of Osdag. It analyses short-span steel plate-girder
bridges with a grillage model (ospgrillage on top of OpenSeesPy) and designs the girders,
cross-bracing, end diaphragms and deck according to IRC/IS codes. Its PySide6 desktop UI
has three parts: an input dock, a central canvas (2D CAD, 3D CAD or result plots), and an
output dock.

The assignment asks for three independent improvements to this UI:

| # | Subtask | Short description |
|---|---------|-------------------|
| I | Interactive 2D CAD parameter editing | Double-click a dimension label on the template-page 2D CAD, type a new value in an in-place editor, validate it, write it to the input dictionaries, and redraw. Four parameters are editable; three derived parameters must stay locked. |
| II | Additional Inputs dialog: validation and state management | (a) Block *Save* when a field set to "Custom" has an empty value, naming the field in the error. (b) Warn before closing the dialog with unsaved changes (Discard / Cancel). Use the central keys in `core/utils/common.py`; no hard-coded parameter strings. |
| III | Result plotting for transverse members | Extend the post-analysis plots, which only cover longitudinal girders, so that transverse members (end diaphragms, intermediate cross-bracing) can be selected and plotted for all nine response components, with data extraction routed through `results_data.py`. |

## 2. Background and motivation

* **Why Subtask I matters.** In the current UI a dimension shown on the drawing (e.g.
  *Girder Spacing = 1.97 m*) can only be changed by locating the matching field, which may
  sit in a different dialog (Additional Inputs → Typical Section). Editing the value
  where it is displayed removes that indirection. This is the *direct manipulation*
  principle in HCI (see `02_literature_review.md`). The difficulty is that the drawing
  shows both **independent** parameters and **derived** quantities. Editing a derived
  quantity is an under-determined inverse problem. Overall width equals
  `(n − 1)·s + 2·overhang`, so a new width could be reached by changing *n*, *s* or the
  overhang. The assignment resolves this by locking derived labels.
* **Why Subtask II matters.** A "Custom" selection with an empty value is a latent error:
  today `_update_input_dict` silently substitutes the default for an empty field, so the
  user's explicit intent ("I want a custom value") is replaced by the code default without
  notice. Closing the dialog without saving silently drops edits. Both are classic
  error-prevention problems (Nielsen's heuristic #5).
* **Why Subtask III matters.** Transverse members (end diaphragms, cross-frames) are
  designed in OsdagBridge, but their analysis results cannot be inspected graphically.
  The steel-bridge literature (NCHRP Report 725 and related work, reviewed in
  `02_literature_review.md`) identifies cross-frame forces as one of the quantities that
  simplified models predict least reliably. Making them visible to the engineer is
  therefore more than cosmetic.

## 3. Requirements

### 3.1 Explicit functional requirements (quoted or paraphrased from the task)

| ID | Requirement |
|----|-------------|
| I-1 | A `mouseDoubleClickEvent` (or equivalent) bound **specifically to the text labels** in the template-page 2D CAD (Figure 1 of the task). |
| I-2 | On double-click, the label is replaced by a temporary line edit for a new numeric value. |
| I-3 | On Enter **or clicking outside**, the value is validated and pushed to the basic/additional input dictionaries, then the CAD is redrawn. |
| I-4 | Editable: Carriageway Width, Girder Spacing, Deck Thickness, Span Length. |
| I-5 | Locked (read-only): Overhang, Overall Bridge Width, Bracing Spacing. |
| II-1 | Intercept the Save click; iterate over **all active tabs** of Additional Inputs. |
| II-2 | If any parameter's radio/dropdown is "Custom" and its input field is empty → halt Save and show the standard OsdagBridge error dialog. |
| II-3 | Message format: `Error: The custom value for '[Parameter Name]' cannot be empty.` |
| II-4 | Track `self.is_modified` on input changes; override `closeEvent`; if modified and not saved, show the standard warning dialog with the exact text *"You have unsaved changes. Closing this window will discard them. Do you want to proceed?"* and options **Discard / Cancel**. |
| II-5 | No hard-coded parameter strings; validation loops use the central keys from `core/utils/common.py`; add new keys only if necessary. |
| III-1 | Member selection UI of the plotting module includes transverse members (end diaphragms, intermediate cross-bracing); one component per transverse member is sufficient (no diagonal/chord split). |
| III-2 | Plots show Fx, Vy, Vz, Tx, My, Mz, Dx, Dy, Dz for the selected **load case**. |
| III-3 | Data extraction routed through `core/bridge_types/plate_girder/results_data.py`. |
| III-4 | The node/element mapping in `results_data.py` must accurately distinguish transverse element tags from longitudinal ones in the OpenSeesPy/ospgrillage output. |

### 3.2 Deliverables (from the submission section)

1. GitHub repository (fork) with the code; add GitHub user `Nidhikhare12` as collaborator.
2. Short unlisted YouTube screen recording (silent is acceptable).
3. Report documenting the approach (PDF via the Osdag submission form).
4. ZIP of all relevant files.

### 3.3 Implicit expectations (inferred, not stated)

* Preserve existing behaviour (no regressions in the CAD, dialog, or plots).
* Follow the existing architecture (schema-driven UI builder, `CustomMessageBox`,
  `BridgeInputValidator`, `BridgeConfigurationSolver`).
* Edits made on the CAD must respect the same validation rules as edits made in the
  input fields; two entry points must not allow two different sets of legal values.
* The work must run with the documented setup (`conda env create -f environment.yml`).

### 3.4 Non-functional requirements

| Category | Target |
|----------|--------|
| Consistency | One source of truth for validation and for the girder-layout equation. |
| Discoverability | Users must be able to tell which labels are editable. |
| Robustness | No crash on non-numeric, empty, NaN/inf, out-of-range or infeasible input. |
| Performance | Hit-testing and validation must not degrade paint/interaction latency perceptibly (interactive budget ≈ 100 ms, Card/Moran/Newell; Nielsen 1993). |
| Testability | Core logic (classification, validation rules, transformations) must be testable without a display. |
| Maintainability | No duplicated parameter strings; changes localised to the modules named in the task. |

## 4. Expected inputs and outputs

| Subtask | Input | Output |
|---------|-------|--------|
| I | Double-click at a canvas position; typed text; Enter / focus-out / Esc | Updated `input_dict` (template page, shared with the Additional Inputs dialog), synchronised input-dock field, redrawn 2D CAD; or an error dialog and the unchanged value |
| II | Save click / close request; current widget state | Save proceeds, or error dialog naming every empty custom field; on close: warning with Discard/Cancel |
| III | Selected member group, load case, response component | 3-D diagram of the chosen component along every selected transverse member, with max/min/summary values |

## 5. Constraints and assumptions

1. **Units.** Input dictionaries store span, carriageway width and girder spacing in
   **metres** and deck thickness in **millimetres**; the CAD stores millimetres
   internally. Labels display m, m, m and mm respectively. The editor accepts values in
   the unit shown on the label.
2. **Girder count is fixed** when girder spacing is edited. This follows the existing
   solver contract (`BridgeConfigurationSolver._solve_layout(changed_field="spacing")`
   keeps *n* and derives the overhang).
3. **Carriageway width and span are basic inputs.** Editing them on the CAD must behave
   exactly like editing the input-dock field. That includes the existing behaviour that a
   required-field change re-solves the layout and resets additional-input defaults via
   `solve_extend_basic_input_dict`.
4. **Edits are disallowed while the input dock is locked** (after a design run), matching
   the existing lock semantics.
5. **"Transverse members"** follow the definitions already used by the design code in
   `plategirderbridge.py` and `results_data_post_processing.py`:
   *end diaphragm* = a `start_edge`/`end_edge` grillage element that joins two girders;
   *intermediate cross-bracing* = a `transverse_slab` element that joins two girders.
   Transverse elements joining an edge beam to a girder are deck overhang strips, not
   transverse members.
6. **Force axes.** ospgrillage's `get_results()` returns **global** element end forces by
   default (`local_forces=False`). The UI labels (Fx axial, Tx torsion, Mz major bending,
   …) are member-local quantities, so components must be transformed into each member's
   local axes before plotting. For girders along global X the two coincide. For
   transverse members along global Z they do not.

## 6. Ambiguities and how they are resolved

| Ambiguity | Resolution | Rationale |
|-----------|------------|-----------|
| Which drawing hosts the editable labels? The cross-section widget is reused inside the Additional Inputs dialog as a preview. | Enable editing only on the template-page instance (opt-in flag). | Task Figure 1 is the template page; the dialog preview already has its own input fields. |
| Girder Spacing appears in both the cross-section and the plan (top) view. | Editable in both. | Same parameter; consistent behaviour. |
| What counts as a "Custom" selector? | Mode-line pairs (`<id>.mode`/`<id>.value`), combo boxes with a "Custom" choice that unlock dependent fields, and design-mode adaptive fields. Dependencies are declared in the schema. | Covers every "Custom" pattern present in the schema; keeps the rule next to the field definition. |
| Fields in inactive tabs (e.g. Median tab when no median) | Skipped. | Task says "all **active** tabs"; inactive tabs cannot be edited. |
| "Single component representing transverse member" | Each transverse grillage element is one plotted member; groups: *All Transverse*, *End Diaphragms*, *Cross Bracings*. | The grillage represents a cross-frame panel by one equivalent beam element; splitting into diagonals is explicitly not required. |
| Sign of plotted forces | Plot internal forces in member-local axes (`N(i) = −F_i`, `N(j) = +F_j`). | Makes i- and j-end values consistent along a member. |

## 7. Potential failure cases (to be tested)

* Non-numeric text, empty text, `nan`, `inf`, negative values, values outside the
  validator range.
* Girder spacing so large that the derived overhang is negative (infeasible layout).
* Double-click on a locked label, on empty canvas, or while the input dock is locked.
* Overlapping label rectangles; zoomed/scrolled canvas (hit-test must use paint-time
  geometry).
* Editor loses focus to another window; Esc pressed; double-click again while editing.
* Additional Inputs: Custom selected in a tab that is later disabled; dependent field
  hidden for the selected type (e.g. crash-barrier density is hidden for "Custom");
  dialog closed with Esc (`QDialog.reject` bypasses `closeEvent`); programmatic refreshes
  that must not set `is_modified`.
* Transverse plots: bridge without overhang (no edge beams); skewed bridge (oblique
  mesh, transverse members not parallel to Z); load case with zero forces; two-girder
  bridge (single bay).

## 8. Existing state (what is implemented vs missing)

| Area | Existing | Missing |
|------|----------|---------|
| 2D CAD | Labels painted with `QPainter.drawText` (`cad_cross_section.py`, `cad_top_view.py`); hover zones for elements; no label geometry is retained | Label hit-test registry, editor overlay, edit routing to dictionaries, lock semantics |
| Validation | `BridgeInputValidator` for span, carriageway width, girder spacing, deck thickness; `_to_float` accepts `"nan"`/`"inf"` (which then pass every range check) | Finite-number guard for CAD edits |
| Layout solver | `BridgeConfigurationSolver._solve_layout` (spacing ↔ overhang ↔ n) | Reuse from the CAD edit path |
| Additional Inputs | `_save_inputs` (no validation despite the comment "validates all tabs"); no close handling | Custom-empty validation, dirty tracking, close/Esc interception |
| Results | `_build_full_data` classifies members geometrically (same Y and Z ⇒ longitudinal) and `post_process` discards the `start_edge`/`end_edge` groups; plots operate on longitudinal girders only, using raw global components | Authoritative longitudinal/transverse classification, transverse-member map, local-axis force extraction, transverse plot builder, dropdown entries |
| Tests | Placeholder tests only | Unit tests for all new logic |

## 9. Initial technical direction

1. **I:** keep painting as it is. During `paintEvent`, record each dimension label's
   bounding rectangle with a semantic parameter id. On double-click, hit-test this
   registry and place a `QLineEdit` overlay on the label. Route the commit through one
   controller in the template page that reuses the existing validator and layout solver.
2. **II:** declare custom-value dependencies in the UI schema (keys only). A pure-Python
   rule extractor turns them into rules; the dialog evaluates the rules against active
   widgets. Dirty tracking uses *user-only* Qt signals (`textEdited`, `activated`,
   `clicked`), so programmatic refreshes don't flag changes. `closeEvent` and `reject` are
   both intercepted.
3. **III:** classify members using ospgrillage group membership (authoritative), with
   geometric classification as a cross-check. Keep the end-edge groups through
   post-processing. Build a transverse-member map in `results_data.py`. Transform global
   end forces into member-local internal forces there. Add a transverse diagram builder
   to `plot_generator.py` and dropdown entries to the output dock.
