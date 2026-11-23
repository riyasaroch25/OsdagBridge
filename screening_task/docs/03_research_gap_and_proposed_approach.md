# 03 — Research Gap and Proposed Approach

This is a software-engineering assignment, not an open research problem, so we do **not**
claim a scientific research gap. What we identify are *engineering gaps*: places where
existing systems (the literature and the OsdagBridge codebase) leave a correctness or
usability problem unresolved, which our design closes.

## Gap 1 — Ambiguous back-propagation of derived dimensions (Task I)

* **What exists:** general bidirectional editors resolve ambiguous edits with ranking
  (Hempel et al. 2019), optimisation heuristics (Cascaval et al. 2022), or ad-hoc variable
  choice (Gonzalez et al. 2023). All three report residual ambiguity as a limitation.
* **What OsdagBridge needs:** a drawing that mixes independent and derived quantities, with
  the derived relation known exactly: `W = (n − 1)·s + 2·o`.
* **Gap:** no general method gives *predictable* edits for derived labels. Code-level gap:
  the drawing retains no geometry for its labels and has no route from a label to an input
  key.
* **Approach:** (i) lock derived labels (as the assignment requires) and explain why in a
  tooltip; (ii) route every editable label through the **same validator and layout solver**
  as the forms, holding the integer girder count fixed, so CAD and forms share one
  definition of "valid"; (iii) a paint-time hit-test registry, because labels are painted,
  not widgets.

## Gap 2 — Silent substitution of empty "Custom" values (Task II)

* **What exists:** `AdditionalInputs._update_input_dict` replaces an empty value with the
  default; `_save_inputs` claims to validate but does not; closing the dialog drops edits
  silently, and `Esc` bypasses `closeEvent` entirely (Qt `reject()`).
* **Approach:** derive the "Custom requires value" rules **from the UI schema**. Mode-line
  fields are detected automatically, and combo dependencies are declared beside the field
  with central keys, so rules cannot drift from the UI. Track modifications with
  **user-only signals** (`textEdited`, `activated`, `clicked`, delegate `commitData`) so
  programmatic refreshes never produce false warnings; intercept both `closeEvent` and
  `reject()`.

## Gap 3 — Global components shown under member-local labels (Task III)

* **What exists:** NCHRP 725/962 (summaries) report that cross-frame results from simplified
  models are sensitive to modelling and post-processing. In the code, ospgrillage returns
  **global** end forces by default; the girder plots label them as local quantities (Fx
  axial, Tx torsion, Mz bending). For girders along X the two coincide, so this is invisible
  today.
* **Gap:** reusing the girder path for transverse members (which run along global Z) would
  silently swap quantities. Experiment E4 shows that the naive "Mz" plot reads 0.001 kN·m
  where the true bending is 62.4 kN·m (the 62.4 appears under "Tx"). In addition,
  `results_data.py` classifies members only geometrically, and post-processing drops the
  end-diaphragm groups.
* **Approach:** (i) classify members by ospgrillage group membership, with geometry only as
  a fallback (needed: one edge beam is in no group); (ii) keep support-line groups and build
  a transverse-member map (end diaphragms, cross bracings) with the *same* girder-pair rule
  the design code uses; (iii) rotate global end forces into a member frame whose axes reduce
  to global for girders (so the existing girder plots are unchanged) and convert to internal
  forces with one sign convention at both ends; (iv) verify against OpenSees' own
  `localForces` (E3).

## Why this approach is worth implementing

* It satisfies every explicit requirement with the smallest footprint on existing code.
* Each correctness claim is testable without a display (48 unit tests) and was checked in
  the real UI (headless end-to-end experiments).
* It turns two latent defects (NaN accepted by the validator; global/local mislabelling) into
  documented, tested behaviour.
