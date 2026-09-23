# Shared crew foot fitting — 2026-09-23

Work in progress. This extends the [actual sole measurement](crew-foot-contact.md),
not geographic reconstruction, hydraulic settling or complete crew acceptance.

## Implementation under validation

The normal avatar fits paired boot footprints to the actual uploaded raft floor
and checks adjacent tube/thwart triangles. The same solved feet and two-bone knee
targets drive equipment and the owned CC0 body; airborne/reentry poses retain
their authored trajectories. Runtime fitting uses asset bounds, not stripped
cooked mesh vertex buffers. Initial paired placement preserves separate feet;
leg lengths are preserved and unreachable candidates are rejected before binding.
The normal seating path reconciles the actual glute after fitting knees, retaining
the existing one-centimetre compression target. Appearance changes invalidate
the cached placement. No captured source, terrain, collision or hydraulic field
is changed by this work. The nonlinear solver remains OFF.

## Retained rejected trials

- v1 independently selected footprints and brought some feet too close together;
  paired placement replaces that candidate. Its capture process exited1 despite
  writing its report; it is not a clean process pass.
- v2/v3 native tests did not dispatch the production BlueprintNativeEvents in
  the editor test context. All body targets were zero and seating logged
  `rendered_contact=0`. A registered editor world alone was insufficient.
  The corrected fixture uses `FEditorScriptExecutionGuard` and explicitly
  requires the actual CC0 body to be ready. No contact tolerance was loosened.
- The v3 posed diagnostic accidentally modified a reflected location struct
  while deriving its comparison target. It now constructs an independent Vector.
  Its action-to-action millimetre body/boot discrepancies are invalid evidence.
- v4/v5 correctly initialized all five bodies and preserved glute contact, but
  retained71 planted-boot failures, all belonging to the guide. A floor candidate
  was geometrically supported but unreachable, prematurely ending the search.
- v6 passes all four native suites, including320 actual crew/action/time samples
  and640 body/boot target comparisons. However its independent9,600-tread-sample
  audit rejects the guide's tube fallback: a bounding-box corner can touch a tube
  while the actual tread floats27.7cm above the floor. Passing native anchor and
  no-slide tests did NOT establish sole contact. The tube fallback is removed.
  The v6 capture process exited1 after writing its report, so no clean process
  acceptance is inferred from those artifacts either.

Reports and logs are retained under `tmp/crew-foot-fit-native-v*-20260923` and
`tmp/crew-foot-contact-fit-v*-20260923`. The four projection unit tests pass.
The v7 candidate moves the visual guide seat20cm forward within the stern
quarter to allow unchanged leg lengths to reach the real interior floor. Its
editor tread capture terminates exit0. All rest/forward/brace sole samples have
support; minimum per-boot clearances are0.11–0.73cm. Guide soles no longer float
above the floor or penetrate the stern tube. Maximum sampled clearance is3.59cm
over the curved floor. Actual body/boot anchors agree to floating-point precision.
Both renderer-produced idle views were inspected; clothing, leg silhouettes and
other crew realism remain unfinished.

High-side remains rejected: v7 has up to32.25cm clearance and0.14cm penetration
in the cross-tube stance. The v8 runtime therefore applies the new fit only to
seated idle, forward/back strokes, turns and brace. High-side keeps its authored
trajectory, as do airborne/rescue/reentry actions; no high-side contact acceptance
is claimed. The guide's new seat location also affects its authored high-side
placement, so that combination remains explicitly unqualified. This is a bounded
normal-play correction, not a claim that all crew actions are finished.

The v8 editor and Game targets build successfully and all four native suites
pass. Normal-start motion completes through the standard FullReach/full_descent
path (no review-station or feature opt-in):24 stills and470 decoded movie frames
over15.63s. The3/6/11s source frames were inspected. They show changing crew
strokes, feet on the interior floor and downstream progress0.12→0.14km. Occlusion
prevents complete sole-surface certification from this gameplay camera. Water,
shoreline, garment and remaining crew defects are not accepted by this change.

**v8 cost fails:** a separate ordinary900-frame run, rows60–840, reports
mean41.93694ms/p9550.1671ms versus the unchanged33.333333ms budget. No screenshot
or paddle injection was used in that cost run. Both normal receipts exit0 and
confirm successful guarded suspension/resumption of original cook36692.
The decode completed before the cost CSV began. Movie cadence is not engine FPS.
The new runtime was scanning all support triangles for each crew/foot/frame;
v9 adds reuse keyed to actual geometry uploads and relative seating. All three
geometry writers (initial, flexible and shared-hull review) invalidate it.
The v9b editor build, v9 Game build and all four native suites now pass, including
relative-seat invalidation and advancing the revision on an actual mesh rebuild.
The initial v9 build failed on a nonexistent actor-location accessor in the new
test; the corrected component accessor is retained in v9b, without gate changes.
The independent v9 tread capture terminates exit0. All5,760 samples in the30
rest/forward/brace boot poses have solid support. Per-boot minimum clearance
ranges0.1089365–0.7297056cm; maximum sampled gap3.5921189cm. Body/boot target
error is at most8.30e-14cm. The excluded authored high-side poses still penetrate
the complete tube/floor geometry by up to39.93cm; full crew contact is NOT passed.

The final isolated v9 cost run also exits0 with successful cook suspension and
resumption: mean31.333791ms/p9540.5902ms over the same781-row window. This is lower
than v8's50.1671ms but still FAILS33.333333ms and is worse than the earlier rigid-
paddle run's32.8541ms. These are short observations, not an isolated causal
speedup or sustained/full-route acceptance. No build, capture or decode workload
was active during v9 measurement. Frame-time mode is confirmed, scope offset1.
The regression is not accepted or presented as a performance win. Next profile
remaining support-query costs on changing geometry and reduce them; do not rerun
the unchanged failed candidate or relax the budget.

Evidence: `tmp/crew-foot-fit-native-v8-20260923/index.json`,
`tmp/crew-foot-fit-motion-v8-20260923/report.json`,
`tmp/crew-foot-fit-cost-v8-20260923.json`, and normal/cost process receipts under
`unreal/Saved/RaftSimValidation/south-fork-foot-fit-*-v8-20260923-process.json`.
Movie: `unreal/Saved/VideoCaptures/RaftSim_20260923-151421.mp4`, SHA256
`f86f418af734f8ba6d0c8a05914fba45b0b23d901be90da38631fe81c5ffba6f`.

Final cache/tread/cost receipts:
`tmp/crew-foot-fit-native-v9-20260923/index.json`,
`tmp/crew-foot-contact-fit-v9-20260923/report.json`,
`tmp/crew-foot-fit-cost-v9-20260923.json`, and
`unreal/Saved/RaftSimValidation/south-fork-foot-fit-cost-v9-20260923-process.json`.
Implementation SHA256 (`RaftSimCrewFootContact.cpp`):
`78ae53d35844b334a526dc687a8f21533982f711b88aeb64b06b23292d76859f`.

Final v9 normal-start motion also terminates exit0, with24 stills and467 fully
decoded frames over15.533333s (16 exact adjacent duplicates). Original3/9/11s
frames were inspected: crew strokes and water change while the raft advances
from roughly0.12 to0.15km; the visible seated boots remain inside the floor.
This is actual engine motion, not a posed editor substitute or cadence-derived
FPS claim. It does not certify high-side, capsize, reentry, limb/garment collision,
all deforming hull states, rapid shoreline stability or full-route continuity.
Movie `unreal/Saved/VideoCaptures/RaftSim_20260923-153002.mp4`, SHA256
`9dfd97a3d1dbd7cc3214b8fb06648901a9b5d50c262ab73cad8ec4c354ee0bc1`;
decode `tmp/crew-foot-fit-motion-v9-20260923/report.json`.
The final normal/cost receipts confirm normal scenario start, no review-station
override, the unchanged solver archive and successful cook resumption.
All editor/Game/native/tread/motion/cost/decode jobs are terminal. Original
cook36692 remains the sole live cook. No river/release gate is closed.

## Measured attribution after v9 — September23

Added enabled CSV timing scopes for `FitFeet` and `SupportQuery`, plus explicit
cache-hit, geometry-miss, seat-miss and support-query counters in the existing
normal runtime. No contact geometry, cache policy, simulation, source data or
solver enablement changed. The editor instrumentation build succeeds in62.55s
(`tmp/crew-foot-cost-scopes-editor-v1-20260923.log`). This is not a new Game build
or visible delivery; the previous rebuilt Game and motion evidence remain v9.
The instrumented build also passes all four native crew suites (4 succeeded,
0 failed/not-run/in-process), terminal engine exit0, retained at
`tmp/crew-foot-scopes-native-v1-20260923/index.json`. Original cook36692 remains
live afterward. The existing unrelated uninitialized-variable build warning is
not resolved by this change.

Fresh ordinary normal-start capture `south-fork-foot-scopes-v1-20260923` is
terminal exit0,900 rows,1280×720 D3D12,4 solver lanes, no replay/paddle injection.
The guarded helper suspended and resumed exact original cook36692 successfully;
no competing engine/build/decode was active during measurement. The receipt
confirms default FrameTime mode, so elapsed rows60–840 correspond to scope
rows59–839. The existing strict CSV parser verifies the completed capture.

Across those781 scope rows, `RaftSimCrewContact/GameThread/FitFeet` has mean
0.0338886044ms, p950.0425ms and max0.0843ms. Every row records10 cache hits:
7,810 total. Explicit support-query, geometry-miss and seat-miss counters are
all zero, as is support-query timing. These counters—not zero timing alone—
establish that no support scan ran in this warmed interval. They do not certify
deforming hulls or startup search cost. `SupportQuery` is nested within `FitFeet`
when called there; do not add their inclusive times.

Elapsed-frame mean31.3756918ms/p9540.9277ms still FAILS33.333333ms. The prior
proposal to optimize changing-geometry support scans is therefore not supported
for this run; preserve the qualified foot fit and its invalidation rules.
Phase-aligned water-workload grouping identifies315 of332 over-budget intervals
in323 refresh-positive rows (mean38.00193ms, p9542.201ms). The other17 occur in
326 crest-selection-positive/non-refresh rows;132 rows with neither positive
timing contain no over-budget intervals. These are associations, not isolated
causal attribution. Next isolate refresh work, not a speculative foot-cache
rewrite or lower-quality simulation. No unchanged baseline rerun is needed.

Receipts: `unreal/Saved/RaftSimValidation/south-fork-foot-scopes-v1-20260923-process.json`,
`tmp/crew-foot-scopes-frame-v1-20260923.json`; source CSV
`unreal/Saved/Profiling/CSV/south-fork-foot-scopes-v1-20260923.csv`, SHA256
`f599069f8fede59a1383a151af69538fc7b93f7a67cb7669d288ae74e27f846b`.
Crew columns are present in its initial header; counter values are counts, not
milliseconds. Statistics above use those exact inclusive scope rows, separately
from the existing water/frame report. High-side contact, full-route water and
all acceptance gates below remain open; Colorado/Pacuare/Futaleufu stay queued.

## Remaining gates

Independent full-tread support, guide and high-side contact, within-action motion,
normal launch and rebuilt game, deformation/transformed-raft behavior, collision,
and measured cost must remain separate checks. Initial poses, source-text tests,
or matching foot-bone anchors alone cannot close them. South Fork remains the
first unfinished river; Colorado, Pacuare and Futaleufu are not yet eligible.
