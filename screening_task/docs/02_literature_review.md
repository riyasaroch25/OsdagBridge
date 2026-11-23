# 02 — Literature Review

## Scope and method

The assignment is an engineering-software task, so the relevant literature falls into
three strands, one per subtask:

1. **Direct manipulation and bidirectional editing** (Task I): editing a model by acting
   on its rendered output.
2. **Error prevention in form-based input** (Task II).
3. **Grillage analysis and transverse-member forces in steel girder bridges** (Task III),
   plus the two software components OsdagBridge builds on (OpenSeesPy, ospgrillage).

Sources were located with web search (Google Scholar–style queries, publisher pages, arXiv,
National Academies Press) on 2026-11-23. Every bibliographic record below was checked
against a publisher, DOI, or index page. **Access level is stated per source**; where only
an abstract or index record was available, no methodological detail is claimed.

| Access level | Meaning |
|---|---|
| **Full** | Full text read |
| **Partial** | Part of the full text read (sections noted) |
| **Record** | Only bibliographic record / abstract / publisher summary available |

## Strand A — Direct manipulation and bidirectional editing (Task I)

**A1. Shneiderman (1983)**, *Direct Manipulation: A Step Beyond Programming Languages*,
IEEE Computer 16(8):57–69, doi:10.1109/MC.1983.1654471. *Access: Record (+ scan located).*
Coins "direct manipulation": continuous representation of the object of interest, physical
actions instead of command syntax, rapid incremental reversible operations with immediately
visible effect. Relevance: the stated rationale for editing a dimension on the drawing
instead of in a distant form field.

**A2. Hutchins, Hollan & Norman (1985)**, *Direct Manipulation Interfaces*, Human–Computer
Interaction 1(4):311–338, doi:10.1207/s15327051hci0104_2. *Access: Record (table of
contents).* Introduces the *gulfs of execution and evaluation*. Relevance: in OsdagBridge
the gulf of execution for "change girder spacing" spans two windows (drawing → Additional
Inputs → Typical Section tab).

**A3. Hempel, Lubin & Chugh (2019)**, *Sketch-n-Sketch: Output-Directed Programming for
SVG*, UIST 2019, doi:10.1145/3332165.3347925 (arXiv:1907.10699). *Access: Partial
(abstract, introduction, overview, design; later sections only via summary).* Canvas edits
rewrite the numeric constants of the program that produced the drawing. When several
rewrites are valid, candidates are ranked and previewed; users can **freeze** constants
so drags cannot change them. Evaluation: case study of 16 parametric designs built without
text edits. Stated limitations include sluggishness on large programs and the need for
"richer interaction" to resolve ambiguous intent. **Relevance:** our locked labels are the
same idea as freeze annotations, except that in OsdagBridge the frozen items are the
*derived* quantities, fixed by the domain rather than chosen by the user.

**A4. Cascaval, Shalah, Quinn, Bodik, Agrawala & Schulz (2022)**, *Differentiable 3D CAD
Programs for Bidirectional Editing*, Computer Graphics Forum 41(2):309–323,
doi:10.1111/cgf.14476. *Access: Full (arXiv:2110.01182 via ar5iv).* Direct edits of
output geometry are resolved by constrained optimisation (SLSQP) over program parameters,
using automatic differentiation and a choice of heuristic energies (e.g. L1
parameter-change). Integer parameters are always fixed. Timing on 7 models: mean sync
0.08–4.66 s. The user study was informal (no quantitative measures). Stated limitations:
ambiguity is handled only heuristically ("not a fully automatic solution"); units/
sensitivities of parameters are not normalised; users wanted explanations for infeasible
edits. **Relevance:** directly addresses the ambiguity we face for *Overall Width*, and
shows that general solvers spread a change across parameters in ways users find hard to
predict. Fixing the integer count (girders) matches our solver contract.

**A5. Gonzalez, Kieken, Pietrzak, Girouard & Casiez (2023)**, *Introducing Bidirectional
Programming in Constructive Solid Geometry-Based CAD*, ACM SUI 2023,
doi:10.1145/3607822.3614521. *Access: Partial (first ~40 % verbatim; method/evaluation via
summary).* A modified OpenSCAD links code and viewport both ways. Viewport translation edits
an existing parameter when one affects only that element, otherwise a new one is
introduced. Validation was informal (Thingiverse models, one detailed walkthrough). Noted
limitation: the system must choose when several variables could express an edit.

**A6. Bettig & Hoffmann (2011)**, *Geometric Constraint Solving in Parametric
Computer-Aided Design*, J. Comput. Inf. Sci. Eng. 11(2), doi:10.1115/1.3593408.
*Access: Record.* Survey of parametric representations and geometric constraint solving;
well-constrained systems are typically decomposed into smaller subsystems. Relevance: the
girder-layout relation `W = (n−1)s + 2o` is a tiny constraint system; editing *s* with *n*
fixed makes it well-constrained in *o*.

## Strand B — Error prevention in forms (Task II)

**B1. Nielsen (1994)**, *Enhancing the Explanatory Power of Usability Heuristics*, CHI '94,
pp. 152–158, doi:10.1145/191666.191729. *Access: Record (the available PDF is an
unreadable scan).* Derives a revised heuristic set from a database of 249 usability
problems; **error prevention** is one of the resulting heuristics. Exact list not
re-verified here.

**B2. Seckler, Heinz, Bargas-Avila, Opwis & Tuch (2014)**, *Designing Usable Web Forms —
Empirical Evaluation of Web Form Improvement Guidelines*, CHI 2014, pp. 1275–1284.
*Access: Record (Google Research publication page + abstract).* Controlled eye-tracking
study (N = 65): forms revised with 20 guidelines were completed faster, with fewer
submission attempts and higher satisfaction. Relevance: supports naming the offending
field and placing focus on it, rather than a generic "invalid input" message.

## Strand C — Grillage analysis and transverse members (Task III)

**C1. Hambly (1991)**, *Bridge Deck Behaviour*, 2nd ed., E & FN Spon, ISBN 0-419-17260-2.
*Access: Record.* Standard reference on load distribution in bridge decks and its
representation by simplified models; cited as the classical background for grillages.

**C2. Ngan & Caprani (2022)**, *ospgrillage: A bridge deck grillage analysis preprocessor
for OpenSeesPy*, JOSS 7(77):4404, doi:10.21105/joss.04404. *Access: Full (3-page paper).*
Wraps OpenSeesPy to generate grillage models (beam-only, beam + rigid links, shell + beam;
orthogonal and skew meshes), runs multiple load cases, envelopes moving loads, returns
results as xarray. *The paper does not specify force axes*; we established from the
**source code** vendored in OsdagBridge (`ospgrillage/osp_grillage.py`) that
`get_results()` returns **global** element end forces unless `local_forces=True`, and that
member groups are named `edge_beam`, `exterior_main_beam_1/2`, `interior_main_beam`,
`start_edge`, `end_edge`, `transverse_slab`.

**C3. Zhu, McKenna & Scott (2018)**, *OpenSeesPy: Python library for the OpenSees finite
element framework*, SoftwareX 7:6–11, doi:10.1016/j.softx.2017.10.009. *Access: Record.*
Python interpreter for OpenSees; provides `eleResponse(tag, "forces" | "localForces")`,
which we use to verify our transformation (experiment E3).

**C4. White et al. (2012)**, NCHRP Report 725, *Guidelines for Analysis Methods and
Construction Engineering of Curved and Skewed Steel Girder Bridges*, Transportation Research
Board, doi:10.17226/22729. *Access: Record (summary as indexed; body pages are images and
could not be read).* Compares 1D, 2D-grid and 3D analyses of 60 I-girder bridges with 3D
as benchmark. The indexed summary reports that 2D methods can produce noticeably erroneous
results in several response categories, tied in part to how truss-type cross-frames are
represented, and proposes an improved 2D-grid cross-frame model. No numbers are quoted here
because the full text was not accessible.

**C5. Reichenbach et al. (2021)**, NCHRP Research Report 962, *Proposed Modification to
AASHTO Cross-Frame Analysis and Design*, doi:10.17226/26074. *Access: Record (summary as
indexed).* Field-tested three steel I-girder bridges (straight, skewed, curved). The
indexed summary states that load-induced cross-frame forces are highly variable, and that
errors can arise in **post-processing**, e.g. converting equivalent-beam forces into
cross-frame member forces.

## Comparative table

| Paper | Year | Problem | Methodology | Technology | Data / evaluation | Limitations | Relevance |
|---|---|---|---|---|---|---|---|
| Shneiderman | 1983 | Usability of command interfaces | Conceptual; characterises direct manipulation | — | Examples | Not empirical | Rationale for editing on the drawing |
| Hutchins et al. | 1985 | Why DM feels direct | Cognitive analysis (gulfs) | — | Conceptual | Not empirical | Frames the two-window gulf |
| Hempel et al. | 2019 | Programming via canvas edits | Trace-based rewrites, ranked candidates, freeze annotations | Sketch-n-Sketch (Elm) | 16-design case study | Sluggish on large programs; ambiguity | Locking = freezing derived values |
| Cascaval et al. | 2022 | Bidirectional 3D CAD editing | Constrained optimisation over AD program | DSL, SLSQP | 7 models, timings; informal study | Heuristic ambiguity, unit normalisation, infeasible edits unexplained | Why not to "solve" for derived labels; explain infeasibility |
| Gonzalez et al. | 2023 | Code↔view in CSG CAD | Gizmo edits update/insert parameters | Modified OpenSCAD | 11 models, informal | Choice among variables; informal | Same parameter-choice problem |
| Bettig & Hoffmann | 2011 | Constraint solving in CAD | Survey | — | — | Survey | Layout equation as constraint system |
| Nielsen | 1994 | Explanatory usability heuristics | Factor analysis of 249 problems | — | 11 projects | — | "Error prevention" |
| Seckler et al. | 2014 | Usable web forms | 20 guidelines, eye-tracking | — | N = 65 | Web forms | Field-specific errors, focus on field |
| Ngan & Caprani | 2022 | Grillage modelling cost | Wrapper over OpenSeesPy | ospgrillage, xarray | Software paper | Axes of results not documented in paper | Data source for Task III |
| Zhu et al. | 2018 | Python access to OpenSees | Interpreter refactoring | OpenSeesPy | Software paper | — | Verification oracle (`localForces`) |
| White et al. (NCHRP 725) | 2012 | Analysis level for curved/skewed I-girder bridges | 1D/2D/3D comparison | FE | 60 bridges | Full text not accessed | Cross-frame results from grids need scrutiny |
| Reichenbach et al. (NCHRP 962) | 2021 | Cross-frame analysis/design | Field tests + analysis | — | 3 bridges | Full text not accessed | Post-processing of equivalent-beam forces is error-prone |

## Synthesis

* Bidirectional editing systems (A3–A5) agree that **editing a value that depends on several
  inputs is ambiguous**. Their answers are ranking, optimisation heuristics or user freezing,
  and each reports this as a residual limitation. In a domain tool the dependency structure
  is *known* (the layout equation), so the ambiguity can be removed by design. We lock the
  derived labels and route editable ones through the domain solver with a fixed integer
  count, which is the same choice A4 makes for integer parameters.
* Cascaval et al. note that users want **explanations for infeasible edits**. We surface the
  solver's own message (e.g. "Spacing … is too large for 3 girders").
* Strand C indicates that transverse-member results from 2D grids are **the least reliable
  and most post-processing-sensitive** outputs. Visualising them therefore requires
  correctness in the transformation from model output to engineering quantities. The
  literature we could access does not discuss the specific issue of global vs local
  component labels; it is a software-level issue we identified in the code (see
  `03_research_gap_and_proposed_approach.md`).
