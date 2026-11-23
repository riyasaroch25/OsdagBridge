# 07 — Experimental Evaluation

**Environment.** Apple M4, 16 GB RAM, macOS 27.0.1; Python 3.12.16, PySide6 6.9.3,
matplotlib 3.11.2, NumPy 2.5.5, openseespy 3.8.0.0, osdag 2026.04.0.0 (installed without
`osdag_latex_env`). Native macOS Qt platform (the `offscreen` platform crashes in the OCC 3D
viewer). All scripts are in `screening_task/experiments/`; raw outputs in `results/`.

**Bridge fixture.** Default OsdagBridge inputs with span 20 m, carriageway 5 m (3 girders,
spacing 1.97 m, overhang 0.98 m, overall width 5.90 m). Project location supplied in the
dialog's "custom data" form (Vb = 44 m/s, zone III, Z = 0.16, 45/5 °C) — a test fixture
only. Skew 0° and 15°. Full design (analysis + checks) takes ≈ 5 s.

There is no external dataset or published baseline for these UI features. Baselines are
therefore (a) the unmodified behaviour on `dev` and (b) a naive alternative implementation.

## E1 — Task I end-to-end (`e2e_task1_cad_editing.py`)

*Objective:* verify editing through real mouse/keyboard events. *Method:* `QTest`
double-click on the label centre from the paint-time registry, type, press Enter/Esc; error
dialogs intercepted and recorded. *Metric:* resulting `input_dict`, dialogs shown.

| Case | Editor | Dialog | Result (spacing / deck / overhang / width / n) |
|---|---|---|---|
| Girder spacing 1.80 (cross-section) | opened | — | 1.80 / 250 / 1.15 / 5.90 / 3 |
| Deck thickness 220 mm | opened | — | 1.80 / **220** / 1.15 / 5.90 / 3 |
| Carriageway 7.5 m | opened | — | 2.80 / 250 / 1.40 / 8.40 / 3 (re-solved; deck default re-applied — existing behaviour) |
| Span 30 m (plan view) | opened | — | span = 30 |
| Girder spacing 2.2 (plan view) | opened | — | 2.20 / 250 / 2.00 / 8.40 / 3 |
| Deck thickness 50 mm | opened | "Deck thickness must be at least 100 mm." | unchanged |
| Girder spacing 99 | opened | "Girder spacing is outside the practical range…" | unchanged |
| Overhang / Overall width (locked) | **not opened** | tooltip only | unchanged |
| Esc while editing | opened | — | unchanged |
| Input dock locked | **not opened** | tooltip only | unchanged |

In every accepted spacing edit, $(n-1)s + 2o = W$ holds exactly (e.g. 2×2.2 + 2×2.0 = 8.4).
Screenshots: `task1_before.png`, `task1_after_spacing_deck.png`, `task1_final.png`.
*Unit tests:* 30 (label mapping, NaN/inf, locked keys, ranges, width invariant,
non-mutation).

*Defect found during E1:* the first version found the previous, hidden editor by object name
(its deletion is deferred), so second edits typed into a dead widget. Fixed by clearing the
stale editor's name; recorded here because the unit tests could not catch it.

## E2 — Task II end-to-end (`e2e_task2_additional_inputs.py`)

| Step | is_modified | Visible | Dialogs |
|---|---|---|---|
| Open dialog, no edits | False | yes | — |
| Close without edits | False | **closed** | none |
| Gust factor → Custom, value empty | True | yes | — |
| Save | True | yes | Critical: `Error: The custom value for 'Gust Factor, G' cannot be empty.` (field highlighted) |
| Crash barrier → Custom, width empty, Save | True | yes | Critical naming `Width (m)` |
| Fill both, Save | **False** | yes | Saved |
| Edit deck thickness → close → Cancel | True | yes | Warning (exact text) |
| Same → **Esc** → Cancel | True | yes | Warning |
| Same → close → Discard | False | closed | Warning; `input_dict` deck = 250 (edit discarded) |
| Reopen | False | yes | widget shows 250.00 |

*Defect found during E2:* the first version reported `is_modified = True` immediately after
opening. A stack trace showed the segment table re-emitting unchanged data on its deferred
refresh. Fixed by marking only on a real change; re-run shows no false positive.
Also observed (pre-existing, not changed): clearing a mode-line value triggers the existing
field validator popup "Custom gust factor must be a numeric value" on focus-out.
*Unit tests:* 8 (rule coverage over the real schema — every Custom mode-line has a rule —
label cleaning, active/inactive logic, exact format).

## E3 — Transformation verified against OpenSees (`verify_local_force_transform.py`)

*Objective:* confirm that `member_internal_forces`' rotation reproduces OpenSees' own local
end forces. *Method:* for every element, rotate `eleResponse(e, "forces")` with
`member_local_axes` and compare with `eleResponse(e, "localForces")`, allowing a fixed sign
convention for local y/z.

| Skew | Element set | n | Max abs. error (N, N·m) | Max force magnitude | Axis sign pattern |
|---|---|---|---|---|---|
| 0° | longitudinal | 65 | 0.0 | 4.89 × 10⁵ | [1, −1, −1] |
| 0° | end diaphragms | 4 | 0.0 | 7.39 × 10⁴ | [1, −1, −1] |
| 0° | cross bracings | 24 | 0.0 | 2.68 × 10⁴ | [1, −1, −1] |
| 15° | longitudinal | 65 | 0.0 | 4.87 × 10⁵ | [1, −1, −1] |
| 15° | end diaphragms | 4 | 1.5 × 10⁻¹¹ | 7.60 × 10⁴ | [1, −1, −1] |
| 15° | cross bracings | 24 | 1.1 × 10⁻¹¹ | 2.98 × 10⁴ | [1, −1, −1] |

*Interpretation:* the rotation is exact to floating-point precision, including skewed members.
OpenSees' local y and z axes are opposite to the UI convention (the girder plots use global
components, i.e. our frame). Using `localForces` directly would therefore flip shear and
bending signs relative to the girder plots — one reason for the chosen design.

*Classification (from `member_groups_skew*.json`):* 121 elements; groups and geometry agree on
all 108 grouped elements at 0° and 15°; 13 elements (the second edge beam) belong to no group
and are recovered by the geometric fallback; 4 + 24 transverse members join girder pairs.

## E4 — Baseline (naive global components) vs proposed (`E4_naive_vs_local.py`)

Peak absolute value over all 28 transverse members, skew 0°:

| UI component | 1.0 DL: proposed | 1.0 DL: naive | Class A: proposed | Class A: naive |
|---|---|---|---|---|
| Fx (axial) | 0.000 | 0.000 | 0.000 | 0.000 |
| Vy | 46.420 kN | 46.420 | 32.961 kN | 32.961 |
| Vz | 0.000 | 0.000 | 0.000 | 0.000 |
| Tx (torsion) | 0.001 kN·m | **62.410** | 0.001 kN·m | **45.735** |
| My | 0.000 | 0.000 | 0.000 | 0.000 |
| Mz (bending) | **62.410** kN·m | 0.001 | **45.735** kN·m | 0.001 |

*Interpretation:* reusing the girder path would show transverse members as carrying
essentially no bending and large torsion — the two quantities swapped. Axial force is zero
because the grillage carries no in-plane load under these vertical load cases; it becomes
non-zero for lateral cases (wind/seismic), which are also selectable.

## E5 — Task III end-to-end (`e2e_task3_transverse_plots.py`)

Dropdown after design: `All, G1, G2, G3, All Transverse Members, End Diaphragms, Cross
Bracings`. 2 load cases × 3 selections × 9 components = **54 renders, 0 failures** per skew.
Time from radio toggle to rendered canvas (includes a fixed 50 ms event-pump wait):
median 143 ms, max 251 ms (0°); median 142 ms, max 292 ms (15°). Girder plots still render
after a transverse selection.

Sample results (1.0 DL, skew 0°): end diaphragms Mz 62.41 / −31.21 kN·m in both bays
(symmetric); Vy ±46.42 kN (antisymmetric); cross-bracing Dy up to 24.3 mm; support-line Dy
= 0 — consistent with the symmetric load and supports.

## Limitations of the evaluation

* No user study; usability benefits are argued from the literature, not measured.
* Timings are single-machine, single-run and include harness waits; they show feasibility,
  not a benchmark.
* Only one bridge configuration (3 girders) at two skews. A two-girder bridge and a bridge
  without overhang were not run end-to-end (the code paths are covered by unit tests only).
* Physical correctness of grillage cross-frame forces themselves (vs 3D models) is outside
  scope; NCHRP 725/962 indicate they should be interpreted with care.

## E6 — Scripted demo run (`demo_recording.py` → `media/demo_video.mp4`)

The demo video is rendered from the application's own windows (main window, dialogs,
message boxes, tooltips) with a drawn cursor; inputs are driven by a script. Driving the
real click path end-to-end found two defects that the earlier tests had not exercised,
both fixed:

1. **Focus-order double popup (Task II).** The first version focused the empty Custom field
   *before* showing the Save error. When the error box took focus, the field lost it and the
   field's existing focus-out validator opened a second, nested popup. The field is now
   revealed and focused after the error box closes.
2. **Discard before the dialog was loaded (Task II).** If the dialog was shown without being
   initialised (Additional Inputs opened with a required basic input, such as Project
   Location, still missing), Discard tried to restore an uninitialised state and raised an
   exception inside `closeEvent`. Discard now restores only once the dialog has been loaded.

The transverse deflection plot title was also corrected to state "global" axes
(displacements are global nodal values; forces are member-local).
