# 05 — Implementation Plan

Minimum viable implementation first (M0–M3), then verification (M4) and documentation (M5).
Status reflects the final state of branch `screening-task/ui-2dcad-plotting`.

| # | Milestone | Objective | Files | Acceptance criteria | Risks | Status |
|---|---|---|---|---|---|---|
| M0 | Reproducible environment | App starts from the documented setup | `environment.yml` (unchanged), `screening_task/experiments/harness.py` | Template page renders; screenshot matches task Figure 1 | `osdag` 2026.x needs `osdag_latex_env` (not built for macOS arm64); PySide6 / navcube etc. not declared | Done (workarounds documented in README) |
| M1 | Task I core + UI | Double-click editing of 4 labels; 3 locked | `core/.../cad_parameter_editing.py`, `desktop/ui/docks/cad_label_editing.py`, `cad_cross_section.py`, `cad_top_view.py`, `template_page.py` | Edits reach `input_dict` + input dock; redraw; width equation holds; invalid → error; locked → no editor | Required-field re-solve overwriting edits; stale CAD change-cache | Done |
| M2 | Task II | Block Save on empty Custom; unsaved-change guard | `common.py`, `ui_fields_additional_input.py`, `core/.../custom_input_rules.py`, `additional_inputs.py` | Exact message format; inactive tabs skipped; no false "unsaved" prompt; Esc covered; Discard restores | Programmatic signals setting the dirty flag | Done |
| M3 | Task III | Transverse members selectable and plotted for 9 components | `results_data.py`, `results_data_post_processing.py`, `plot_generator.py`, `plategirderbridge.py`, `mpl_plot_widget.py`, `output_dock.py`, `template_page.py`, `common.py` | Dropdown entries; plots for every component and load case; classification correct incl. skew | Global vs local axes; ungrouped elements | Done |
| M4 | Verification | Evidence for every claim | `tests/unit/test_*.py`, `screening_task/experiments/*.py` | 48 unit tests pass; E1–E4 recorded in `experiments/results/` | Qt plugin path conflicts | Done |
| M5 | Documentation | Docs 01–08, report, README | `screening_task/` | Consistent with code and results | — | Done |

Deferred (see `08_final_implementation_roadmap.md`): undo for CAD edits, keyboard access to
labels, a "which parameter absorbs the change" chooser for derived labels, and splitting
cross-frame equivalent-beam forces into diagonal/chord forces in the plot.
