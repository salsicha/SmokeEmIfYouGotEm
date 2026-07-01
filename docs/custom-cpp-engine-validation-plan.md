# Custom C++ Engine Full Validation Plan

## Purpose

This plan defines what is required before the custom C++ shallow-water / height-field engine can be treated as the accepted live-water runtime for Unreal.

The current engine is a runtime candidate, not a fully accepted production solver. GeoClaw remains the offline reference model. PyClaw artifacts are legacy regression data only.

## Geometry Decision

The full game should model rivers as continuous gridded 2.5D geometry with explicit reach, drop, pool, hazard, roughness, and hydraulic-control annotations.

The canonical cascading storage format supports reach-local grids with overlap or ghost zones for authoring, streaming, and runtime cost, but every package must also export stitched whole-window validation outputs. The stitched output is the acceptance view that proves reach/drop seams do not hide momentum, wet/dry, bed-slope, conservation, or raft-transition errors. Disconnected pools stitched only by scripted handoffs are not acceptable for full validation because they hide failures at the exact places rapids matter most.

## Validation Principle

GeoClaw and the C++ engine must consume the same solver-neutral scenario package. GeoClaw-specific files are generated exports, and C++-specific runtime parameters are recorded as manifests. Acceptance compares outputs and raft-relevant behavior, not internal numerical methods.

Fallback or initial-state-only GeoClaw normalization is useful for schema smoke tests, but it does not count as full shallow-water solution validation.

## Current Closure Order

The Milestone 16 gate has enough evidence to guide the next work, but it does not approve live Unreal water. GeoClaw reference runs, C++ run manifests, promoted regression subsets, runtime budgets, and deterministic replay checks pass. The blocking failures are the GeoClaw/C++ threshold comparisons, geometry-specific validation, and raft-coupling agreement over C++ water.

The closure work must happen in this order:

- Keep the Milestone 17 analytic fixtures green before and after every retune batch.
- Build a failure triage matrix from the blocked GeoClaw/C++ comparison, geometry, raft-coupling, and full-gate reports.
- Fix GeoClaw-vs-C++ field, probe, cross-section, conservation, Froude, wet/dry, and feature-localization failures before accepting raft outcome fixes.
- Close the geometry families that still fail. Focused Milestone 18 evidence has cleared wet/dry shoreline parity and the finite-volume bed-step lane, while constrictions, drops/ledges, tailwater controls, and broader cascading reach/drop water-field behavior still need closure before the aggregate gate can pass.
- Retune raft coupling only after the relevant C++ water fields improve, so force and outcome fixes are not masking bad hydraulics.
- Keep the distinct pin/release fixture separate from shallow-shelf or boulder proxy evidence.
- Re-run the full Milestone 16 gate and regenerate the GeoClaw-to-Unreal readiness report.

Chaos/Jolt runtime authority evaluation stays after this closure work. Those engines can be evaluated for raft/contact/swimmer authority, but no authority decision should treat unapproved C++ live water as accepted input.

## Authored Feature Forcing Decision

Authored feature forcing is allowed, but only as a bounded, manifest-recorded, GeoClaw-compared layer that does not hide conservation failures. It is a runtime and gameplay tuning tool, not permission to replace shallow-water geometry with scripted outcomes.

The accepted feature-forcing surface includes holes, boils, laterals, eddy lines, wave trains, shallow shelves, boulder push/damping, pins/releases, and flips. Parameters must be exposed for gameplay and visual tuning, but default gains stay low until the Milestone 16 GeoClaw/C++ geometry and raft-coupling gates pass.

Each feature-forcing parameter set must record:

- Feature kind, location, radius/width/length/angle, strength, damping/aeration proxy, and visual-only intensity where applicable.
- Flow-response curve keyed by discharge, flow band, flow percentile, or boundary inflow.
- Solver-state effects separately from raft-coupling effects and visual/audio-only effects.
- Conservation diagnostics before and after forcing: mass drift, momentum delta, energy delta, wet/dry mask changes, and reach/drop handoff deltas.
- Validation evidence: GeoClaw/C++ comparison when GeoClaw can represent the feature, or accepted real-world reference footage/data/guide review when the feature is primarily raft-outcome or gameplay readability.

Flow response is mandatory. For example, a hole can be sticky in one flow range, wash out at high water, and become a non-retentive rapid or shallow obstacle at low water. The same rule applies to laterals, eddy lines, wave trains, shelves, boulder contacts, pins, releases, and flips: water volume changes the running technique and the acceptable outcome envelope.

Crew weight distribution is part of the validation surface. Seat occupancy, high-side, lean, brace, paddle timing, and recovery actions must change mass distribution, roll moment, contact loading, and pin/flip/release thresholds in deterministic raft telemetry. A forced rock or hydraulic feature may create a flip/pin hazard only if the player has a fair, validated counterplay window.

The first feature-forcing contract is frozen as `raftsim.feature_forcing.v0` in `physics/schemas/feature_forcing.schema.json`, with low-default parameters in `physics/config/feature_forcing_defaults.json` and contract checks in `raftsim.feature_forcing`. The validator rejects manifests that enable forcing by default, exceed low default gains, omit flow-response curves, skip GeoClaw comparison requirements, merge physics/raft/visual controls, or allow forcing to hide mass, momentum, energy, wet/dry, or reach-handoff failures.

The first crew weight-distribution telemetry implementation lives in `raftsim.raft_coupling2_5d`. It exposes version-ready seat/action primitives, bounded lean and high-side offsets, per-seat occupancy telemetry, crew and combined center-of-gravity offsets, roll/pitch moment proxies, side and longitudinal contact-load proxies, and pin/flip/release threshold multipliers. These values feed the timed rock, sticky-hole, lateral-hit, shallow-shelf, pin/release, and flip fixtures; they are not yet accepted capsize/contact outcomes by themselves.

The first timed crew-hazard fixture gate lives in `raftsim.feature_validation` as `CrewTimedHazardFixture2_5D`. It covers rock high-side, sticky-hole brace/release, lateral-hit lean, shallow-shelf recovery, pin/release weight shift, and flip high-side cases. Each fixture checks that missing or late crew action remains unsafe, while the correct high-side, brace, lean, or recovery action inside the response window clears the hazard by improving roll, pin, release, or lateral-bias margins.

Crew-overboard validation is also represented in `raftsim.feature_validation` with `CrewOverboardFixture2_5D` and `CrewOverboardTelemetry2_5D`. The first fixture gate covers impact ejections, flips, pins, holes, missed brace timing, and missed high-side recovery. Each case validates swimmer drift, rescue timing, pull-in and re-seat duration, failed-rescue behavior, and fatigue/trust/safety-score telemetry before those states are wired into full Unreal gameplay.

## Analytic Fixture Decision

Add a small manually encoded SWASHES-style analytic fixture set before more broad retuning. These fixtures should isolate solver fundamentals such as lake-at-rest balance, sloping-channel friction, wet/dry shoreline motion, bed steps, dam-break/bores, hydraulic jumps, and transcritical flow over a bump where practical.

Each analytic fixture must include provenance notes that explain the source equation or benchmark family, why the case is representative, which fields are expected to be exact or approximate, and which tolerances are used. Do not vendor external SWASHES data or code until licensing, redistribution, update cadence, and maintenance ownership are clear.

Analytic fixtures are diagnostic gates, not gameplay content. Parameter retuning for big rapids must not be accepted if it regresses these small cases.

The first Milestone 17 fixture package is generated by `raftsim.examples.generate_analytic_fixtures` and written under `physics/data/validation/milestone17/analytic_fixtures/`. It contains manually encoded lake-at-rest, sloping-channel friction, wet/dry shoreline, bed-step, dam-break/bore, hydraulic-jump, and transcritical-bump cases with scenario packages, analytic reference files, and no vendored external SWASHES data.

Milestone 17 analytic validation reports are generated by `raftsim.examples.run_analytic_fixture_validation` and written under `physics/reports/milestone17/`. The report can compare the analytic reference fields against scenario initial states, C++ frame CSV manifests, or GeoClaw normalized NPZ manifests. C++ retuning must be considered blocked whenever one of these small fixture reports fails.

Milestone 17 also freezes validation contracts for reach-local grids, river validation annotations, and geospatial package formats in `physics/schemas/` with examples in `physics/config/` and validators in `raftsim.validation_contracts`. These validators reject reach-local grids that lack stitched whole-window outputs, annotation packages that lack footage/gauge/imagery/guide evidence, and geospatial contracts that omit CRS/source-manifest tracking or allow Shapefile as a canonical format.

Cascading packages now emit a stitched whole-window validation bundle in `stitched_validation/` whenever `CascadingScenarioPackage2_5D.write_package()` is called. C++ and GeoClaw comparison runners should consume the bundle manifest plus `fields.npz`, `probes.json`, `cross_sections.json`, `conservation_summary.json`, and `raft_transition_checkpoints.json` so reach-local grid seams cannot hide field errors, handoff conservation failures, or raft-state discontinuities.

## Real-World Validation Evidence Decision

GeoClaw parity is necessary but not enough for raft outcomes such as surf, flush, pin, release, and flip. Real-world footage, gauge history, aerial/satellite imagery, and guide feedback must be attached to precise river locations through a validation annotation editor.

Each river-validation annotation should record its anchor location, source/provenance, flow context, rights status, expected feature behavior, expected raft outcome, reviewer confidence, and whether it is used for physics validation, visual/audio fidelity, gameplay tuning, or all three. These annotations should be visible during game-engine fidelity review so rendered rapids, solver fields, raft trajectories, foam/spray/audio cues, and guide notes can be compared in the same place.

## Non-Goals

- Do not require full 3D CFD or Navier-Stokes simulation for the first accepted runtime.
- Do not require Chrono::FSI for the water solver validation gate.
- Do not accept scripted teleports, boosts, or hidden pool handoffs as substitutes for gridded drop and reach dynamics.
- Do not treat PyClaw parity as acceptance for live Unreal water.

## Phase 0: Freeze Acceptance Definitions

- The frozen scenario matrix and threshold tiers live in `physics/src/raftsim/validation_gate.py` and `physics/config/custom_cpp_validation_gate.json`.
- Freeze the canonical scenario matrix: flat pool, uniform channel, dam-break/bore, bed step, constriction, wet/dry shoreline, sloping channel with Manning friction, drop/ledge, standing-wave transition, boulder garden, hydraulic hole, eddy line, shallow shelf, real-world low/median/high flows, and South Fork cascading reach/drop suites.
- Define threshold tiers for smoke, research-accepted, Unreal-prototype, and production-candidate validation.
- Define field metrics: L1/L2/Linf error for `h`, `eta`, `u`, `v`, `hu`, `hv`, surface slope, and wet/dry masks.
- Define diagnostic metrics: mass drift, energy trend, Froude-class agreement, hydraulic-jump location, wave-train phase/amplitude, feature location/strength, and reach/drop boundary fluxes.
- Define raft metrics: force-envelope error, trajectory deltas, surf/flush/clear/ground/pin/flip outcome agreement, and crossing stability at reach/drop boundaries.
- Define feature-forcing bounds, low default gains, flow-response curves, conservation-failure guards, and manifest fields for physics, gameplay, and visual-only tuning.
- Define the manually encoded analytic fixture manifest, provenance fields, expected metrics, and tolerance tiers.

## Phase 1: GeoClaw Reference Runs

- Milestone 16 reference evidence is tracked in `physics/reports/milestone16/geoclaw_reference_runs.json` and `physics/reports/milestone16/geoclaw_reference_runs.md`; generated GeoClaw app/output trees use the compact ignored `physics/outputs/m16g/` path to avoid GeoClaw/Fortran path truncation.
- Run real GeoClaw fixed-grid simulations for the canonical, rafting, real-world, and cascading suites.
- Store manifests with GeoClaw availability, dependency versions, AMR/fixed-grid settings, scenario package hash, and export time.
- Normalize full solution frames into the shared field/probe/cross-section telemetry schema.
- Export per-reach windows for authoring/debugging and stitched whole-river windows for validation acceptance on cascading packages.
- Flag any scenario that only has schema, setup, or initial-state fallback output as not fully validated.

## Phase 2: C++ Parity Runs

- Milestone 16 C++ run evidence is tracked in `physics/reports/milestone16/cpp_solver_runs.json` and `physics/reports/milestone16/cpp_solver_runs.md`; the run/manifests gate passes for reduced and finite-volume modes, while cascading finite-volume validation failures remain visible for comparison/tuning gates.
- Run the C++ reduced and finite-volume modes on the same scenario packages.
- Emit manifests for solver mode, timestep, CFL policy, dry tolerance, roughness mapping, bed-slope source scale, feature forcing, damping, reach/drop metadata, and executable version.
- Emit feature-forcing manifests for active feature kinds, flow-response curve IDs, gain scales, conservation deltas, raft-coupling modifiers, and visual-only parameters.
- Compare C++ fields, probes, cross sections, diagnostics, and raft samples against the GeoClaw reference runs.
- Record failures by scenario family so tuning does not improve one rapid feature while regressing canonical shallow-water behavior.

## Phase 3: Geometry-Specific Shallow-Water Validation

- Milestone 16 comparison evidence is tracked in `physics/reports/milestone16/geoclaw_cpp_comparisons.json` and `physics/reports/milestone16/geoclaw_cpp_comparisons.md`; the comparison gate currently blocks live-water approval because most frozen field/probe/diagnostic/feature thresholds fail, while cascading reach/drop metadata checks pass.
- Milestone 16 geometry evidence is tracked in `physics/reports/milestone16/geometry_validation.json` and `physics/reports/milestone16/geometry_validation.md`; hydrostatic/sloping balance and stitched reach/drop handoffs pass in that aggregate report. Focused Milestone 18 artifacts now clear wet/dry shoreline parity and the finite-volume bed-step lane, but the aggregate Milestone 16 geometry report still needs a full rerun before it stops showing those stale blockers. Constrictions and drops/ledges/tailwater remain active geometry failures.
- Validate hydrostatic balance and bed-slope source terms on sloping and frictional channels.
- Validate wet/dry fronts over shelves, banks, and shallow eddies.
- Validate bed steps, constrictions, ledges, drops, tailwater controls, and expected energy loss.
- Validate mass, momentum, energy, and wet/dry behavior at reach/drop boundaries.
- Validate that stitched global windows and reach-local windows produce consistent probes, cross sections, and raft entry/exit states.
- Reject any seam artifact that changes raft outcome, feature location, or conservation diagnostics at a reach/drop boundary.

## Phase 4: Whitewater And Raft-Relevant Validation

- Milestone 16 raft-coupling evidence is tracked in `physics/reports/milestone16/raft_coupling_validation.json` and `physics/reports/milestone16/raft_coupling_validation.md`; after the first Milestone 18 wet/dry pressure-gradient retune, the gate remains blocked with 11 of 50 GeoClaw-vs-C++ raft comparisons passing, while force deltas, candidate feature checks, and several outcome classes still fail.
- Re-run raft coupling over GeoClaw-derived fields and C++ runtime fields with the same probe/sample sets.
- Validate pool entry, drop entry, hydraulic-hole surf/flush, downstream boil recovery, eddy recovery, boulder impacts, shallow shelves, pins/releases, and transition-boundary crossings.
- Compare force envelopes, trajectory deltas, outcome classes, and contact/grounding events.
- Keep authored feature forcing only when it is documented, bounded, manifest-recorded, flow-dependent, and validated against GeoClaw outputs or accepted real-world reference behavior.
- Validate high-side, brace, lean, seat occupancy, and crew weight distribution as counterplay for boulder pins, sticky holes, lateral hits, shallow-shelf pivots, and flips.

## Phase 5: Runtime, Determinism, And Portability

- Milestone 16 runtime-profile evidence is tracked in `physics/reports/milestone16/runtime_profile.json` and `physics/reports/milestone16/runtime_profile.md`; all 8 promoted C++ profiling repetitions pass desktop, VR, and handheld water-solver budgets, and deterministic replay hashes match for each promoted configuration.
- Verify deterministic replay for repeated runs on the same platform and, where practical, across supported compilers/platforms.
- Profile validated configurations against desktop, VR, and handheld runtime budgets.
- Record memory, output, streaming, and telemetry costs for Unreal preproduction.
- Decide whether GPU acceleration starts only after the CPU path passes the correctness gate.

## Phase 6: Regression Fixtures And Reports

- Milestone 16 promoted-regression evidence is tracked in `physics/reports/milestone16/regression_promotion_manifest.json`, `physics/reports/milestone16/regression_promotion_manifest.md`, and `physics/regression_fixtures/milestone16/registry.json`; 6 passing GeoClaw/C++ threshold runs were copied as fixtures, 3 passing stitched reach/drop geometry checks were captured as artifact manifests, and 11 passing raft-coupling cases were captured as artifact manifests. The focused Milestone 18 wet/dry finite-volume promotion is recorded in its retune report and should be copied into regression fixtures when the aggregate comparison report is regenerated.
- Promote passing GeoClaw/C++/raft comparison runs into committed regression fixtures or artifact manifests.
- Generate one JSON report and one human-readable Markdown report for each scenario suite.
- Keep a CI smoke subset that does not require external GeoClaw execution.
- Keep a manual or scheduled full GeoClaw suite for reference regeneration, parameter retuning, and readiness gates.

## Phase 7: Acceptance Gate

Milestone 16 full-readiness evidence is tracked in `physics/data/readiness/milestone_16/geoclaw_to_unreal_readiness_report.json` and `physics/data/readiness/milestone_16/geoclaw_to_unreal_readiness_report.md`. The final gate explicitly blocks live custom water because GeoClaw/C++ threshold comparisons, geometry validation, and raft coupling still fail, even though GeoClaw reference runs, C++ manifests, promoted regression artifacts, and runtime profiles pass.

The suite-level C++ validation gate is tracked separately in `physics/reports/milestone16/full_cpp_validation_gate.json` and `physics/reports/milestone16/full_cpp_validation_gate.md`. This report aggregates the seven component reports in `physics/reports/milestone16/` so the C++ validation gate itself has one JSON/Markdown decision artifact before the Unreal-readiness report consumes summaries.

The C++ engine is accepted for live Unreal water only when:

- Every required scenario has a full GeoClaw solution run with fixed-grid frames, not only fallback or initial-state output.
- C++ field, probe, cross-section, diagnostic, and reach/drop-window comparisons pass the frozen thresholds.
- Raft force envelopes, trajectories, and outcome classes pass the frozen thresholds.
- Runtime and memory profiles fit the target prototype budgets.
- Deterministic replay is documented for the accepted solver mode and parameter set.
- The GeoClaw-to-Unreal readiness report explicitly approves live custom water.

## Phase 8: Validation Closure Workplan

Milestone 18 is the closure pass for the blocked Milestone 16 evidence. It does not relax acceptance thresholds. It turns the current failures into ordered implementation work and requires the same JSON/Markdown report trail before the readiness decision can change.

### 1. GeoClaw/C++ Parity Failures

Create a triage matrix where each failed comparison records the scenario package, solver mode, metric, threshold tier, observed error, likely cause, and retune lever. The matrix should split field errors from probe, cross-section, conservation, wet/dry-mask, Froude-class, feature-localization, and reach/drop-window errors.

Retune in dependency order. Preserve flat-pool and sloping-channel behavior first, then work through wet/dry, bed-step, constriction, drop/ledge, and cascading cases. Feature forcing must remain disabled or at low validated defaults while core field parity is being fixed. A parity fix is accepted only when the corresponding GeoClaw/C++ report passes without causing an analytic fixture regression.

The first closure artifact is `physics/reports/milestone18/geoclaw_cpp_failure_triage_matrix.json` with a human-readable companion report at `physics/reports/milestone18/geoclaw_cpp_failure_triage_matrix.md`. It is generated by `raftsim.examples.generate_milestone18_failure_triage_matrix` from the Milestone 16 threshold, geometry, raft-coupling, and full-gate reports. Root-cause fields are hypotheses for retuning order, not proof; the acceptance decision still comes from rerunning the underlying comparison reports.

Before retuning, the GeoClaw reference export must run the same authored boundary contract as the C++ solver. Constant authored stage, depth, or velocity boundaries now export as GeoClaw `user` boundaries with a generated `bc2amr.f90` adapter, while native walls and unconstrained outflows remain GeoClaw `wall` or `extrap`. Every export records `boundary_semantics` in `manifest.json`, including the exact `bc_lower`/`bc_upper` codes and per-edge enforced state. Dynamic boundary hydrographs are deliberately rejected until a time-varying GeoClaw boundary adapter is implemented, so reference runs cannot silently ignore gauge-driven inflow.

The first retune artifact is `physics/reports/milestone18/uniform_channel_parity_retune.json` with a companion report at `physics/reports/milestone18/uniform_channel_parity_retune.md`. It records a partial promotion for the corrected-boundary `uniform_channel` family: finite-volume mode passes all gate-threshold checks with HLL flux, `roughness_scale=0.5`, `bed_slope_source_scale=0.75`, `preserve_initial_mass=false`, and `feature_strength_scale=0`. Reduced mode remains blocked on field, slope, probe, cross-section, and mass-drift checks, so it should not be treated as the strict parity lane for this family until the reduced dynamics are redesigned or explicitly scoped down.

The second retune artifact is `physics/reports/milestone18/wet_dry_shoreline_parity_retune.json` with a companion report at `physics/reports/milestone18/wet_dry_shoreline_parity_retune.md`. It records the first partial promotion for the `wet_dry_shoreline` family: reduced mode masks dry neighbors out of pressure-gradient sampling, preserves the shoreline wet mask without feature forcing, passes the Milestone 17 analytic retune guardrail with zero regressions, and passes all wet/dry GeoClaw/C++ threshold checks. Its finite-volume blocker is superseded by the focused wet/dry finite-volume reconstruction artifact below.

The third retune artifact is `physics/reports/milestone18/bed_step_parity_retune.json` with a companion report at `physics/reports/milestone18/bed_step_parity_retune.md`. It now records a partial promotion for the `bed_step` family: finite-volume mode uses a scoped augmented topography source distribution for `fixture_kind=bed_step`, carries donor momentum during the bounded shoulder/shelf redistribution, passes the Milestone 17 analytic retune guardrail with zero regressions, and passes `field_linf` at 0.295881, `slope_linf` at 0.079763, probe, cross-section, wet-mask, mass, energy, Froude, and feature checks without feature forcing. Milestone 18 scopes reduced-mode bed-step parity out of the strict discontinuous-bed acceptance lane: reduced mode remains diagnostic/smoke-only for bed-step cases until a separate reduced-dynamics redesign is justified, and its field, slope, probe, mass-drift, and energy failures remain tracked in reports without undoing the finite-volume promotion.

The fourth retune artifact is `physics/reports/milestone18/constriction_parity_retune.json` with a companion report at `physics/reports/milestone18/constriction_parity_retune.md`. It records a corrected-reference blocker for the `constriction` family: the stale Milestone 16 snapshot used west `extrap` while the authored scenario requires west inflow, so Milestone 18 regenerates the constriction GeoClaw reference with `bc_lower=['user', 'wall']`, `bc_upper=['extrap', 'wall']`, and generated `bc2amr.f90` evidence before retuning. Reduced mode, finite-volume HLL, and finite-volume Roe all remain blocked with `feature_strength_scale=0`; Roe improves mass and energy error versus HLL but still fails field, slope, probe, cross-section, mass-drift, Froude, and feature-strength checks. The next constriction lever is geometry-aware throat reconstruction/source treatment, not feature forcing.

The fifth retune artifact is `physics/reports/milestone18/constriction_source_treatment_retune.json` with a companion report at `physics/reports/milestone18/constriction_source_treatment_retune.md`. It records a bounded constriction source-treatment sweep against the corrected `user`-boundary reference. Finite-volume Roe with `bed_slope_source_scale=1.5` and `feature_strength_scale=0` brings mass-drift and energy-change deltas inside the constriction thresholds, while field, slope, probe, cross-section, Froude, and feature-strength checks still fail. The accompanying guardrail at `physics/reports/milestone18/analytic_retune_guardrails/constriction_source_treatment/analytic_retune_guardrail.json` passes with zero regressions. This rules out scalar source scaling as a sufficient fix; the next implementation step must change throat reconstruction/water-shape treatment.

The constriction hydrostatic-bank attempt is recorded in `physics/reports/milestone18/constriction_hydrostatic_bank_attempt_retune.json` with a companion report at `physics/reports/milestone18/constriction_hydrostatic_bank_attempt_retune.md`. It tests two rejected finite-volume Roe candidates against the corrected `user`-boundary reference with `feature_strength_scale=0`: full hydrostatic interface reconstruction at the dry-bank throat and abrupt-bank source reconstruction. Both variants keep mass, energy, and feature-strength checks inside the default comparison bounds, and the guardrail at `physics/reports/milestone18/analytic_retune_guardrails/constriction_hydrostatic_bank_attempt/analytic_retune_guardrail.json` passes with zero regressions. Neither variant is promoted because field, slope, wet-mask, probe, cross-section, and Froude errors remain blocked, and the attempted solver change is not retained as runtime behavior. This further narrows the next constriction lever to true throat/water-shape reconstruction or scenario width/depth mapping, not more scalar source scaling or bank-face hydrostatic source terms.

The constriction parameter-only scan is recorded in `physics/reports/milestone18/constriction_parameter_scan_summary.json` with a companion report at `physics/reports/milestone18/constriction_parameter_scan_summary.md`. It tested 336 finite-volume Roe/HLL candidates across roughness, bed-slope source scale, and CFL while keeping `feature_strength_scale=0`. No lane passed; the best-ranked family remains Roe with `roughness_scale=0.5` and `bed_slope_source_scale=0.75`, still failing field, slope, wet-mask, probe, cross-section, mass-drift, and Froude checks. The guardrail at `physics/reports/milestone18/analytic_retune_guardrails/constriction_parameter_scan/analytic_retune_guardrail.json` passes with zero regressions. This rules out parameter-only retuning for the corrected-reference constriction lane.

The constriction throat shape diagnostic is recorded in `physics/reports/milestone18/constriction_throat_shape_diagnostic.json` with a companion report at `physics/reports/milestone18/constriction_throat_shape_diagnostic.md`. It samples the authored initial state, GeoClaw final frame, and C++ final frame at the constriction throat with a 0.15 m wet-depth threshold. GeoClaw keeps the throat at 4 m wet width, while the current finite-volume Roe candidate wets the full 12 m column, adds 1.97845 m3 of throat-column water, lowers mean wet depth by 0.554978 m, and raises the cross-stream velocity envelope by 0.75398 m/s. The guardrail at `physics/reports/milestone18/analytic_retune_guardrails/constriction_throat_shape_diagnostic/analytic_retune_guardrail.json` passes with zero regressions. This blocks promotion and points the next constriction implementation step at geometry-aware width/depth reconstruction before any more parameter scanning or feature forcing.

The sixth retune artifact is `physics/reports/milestone18/drop_ledge_parity_retune.json` with a companion report at `physics/reports/milestone18/drop_ledge_parity_retune.md`. It records a corrected-reference blocker for the `drop_ledge_tailwater` family: the stale Milestone 16 snapshot used west `extrap` while the authored drop-ledge scenario requires west inflow, so Milestone 18 regenerates the GeoClaw reference with `bc_lower=['user', 'wall']`, `bc_upper=['extrap', 'wall']`, and generated `bc2amr.f90` evidence before retuning. Finite-volume HLL and Roe both pass slope, wet-mask, cross-section, mass, energy, Froude, feature-location, and feature-strength checks with `feature_strength_scale=0`, but both still fail `field_linf` and `probe_linf`; reduced mode also fails cross-section and mass-drift checks. The accompanying guardrail at `physics/reports/milestone18/analytic_retune_guardrails/drop_ledge_corrected_reference/analytic_retune_guardrail.json` passes with zero regressions. No drop-ledge lane is promoted yet; the next implementation step must improve water-shape reconstruction at the hydraulic control and downstream recovery.

The seventh retune artifact is `physics/reports/milestone18/wet_dry_finite_volume_reconstruction_retune.json` with a companion report at `physics/reports/milestone18/wet_dry_finite_volume_reconstruction_retune.md`. It records full focused promotion for the `wet_dry_shoreline` family: finite-volume mode uses fixture-scoped hydrostatic interface reconstruction so a constant free surface over a sloped bed does not become a depth discontinuity, then applies a shoreline reconstruction that keeps initially dry analytic shoreline cells dry, returns leaked mass to the nearest initially wet in-column cell, and zeros spurious cross-shore momentum. Both reduced and finite-volume wet/dry lanes pass all GeoClaw/C++ thresholds with `feature_strength_scale=0`; finite-volume errors are now `field_linf=0.0112652`, `cross_section_linf=0.00901216`, zero wet-mask mismatch, zero mass-drift delta, and matching raft outcome. The accompanying guardrail at `physics/reports/milestone18/analytic_retune_guardrails/wet_dry_finite_volume_reconstruction/analytic_retune_guardrail.json` passes with zero regressions. The aggregate Milestone 16 comparison, geometry, regression-promotion, and full-gate reports still need a full rerun before their stale wet/dry finite-volume blocker disappears.

### 2. Geometry-Specific Failures

Treat each blocked geometry family as its own acceptance lane. Wet/dry fixes now have focused reduced and finite-volume promotion evidence, including bounded shoreline movement, dry-cell velocity masking, and zero mass-drift delta; the full aggregate report still needs regeneration. Bed-step strict parity is the finite-volume lane unless a future milestone explicitly redesigns reduced discontinuous-bed dynamics; reduced bed-step reports are still useful diagnostics, but they are not readiness blockers after the finite-volume promotion. Constriction fixes must preserve flux, velocity acceleration, and Froude-class transitions against the corrected `user`-boundary GeoClaw reference before any feature forcing can be considered; source scaling, bank-face hydrostatic treatment, roughness sweeps, CFL changes, and flux-scheme swaps have all been ruled out as sufficient unless the water-shape metrics also pass. Drop/ledge/tailwater fixes must show expected energy loss, hydraulic control, and downstream recovery. Cascading reach/drop fixes must compare reach-local outputs against stitched whole-window outputs so seams cannot hide errors.

Each family should be promoted into regression artifacts when it passes. Do not tune a whitewater feature by sacrificing lake-at-rest, sloping-channel, wet/dry, bed-step, bore, hydraulic-jump, or transcritical-bump guardrails.

### 3. Raft Coupling Agreement Over C++ Water

Re-run raft coupling after the relevant water-field and geometry failures improve. Compare GeoClaw-derived and C++ water fields with the same raft initial states, water samples, feature probes, crew actions, and contact setup.

The raft gate must compare force envelopes, impulse timing, trajectory deltas, yaw/roll/pitch proxies, surf/flush/clear/ground/pin/flip outcome classes, recovery timing, swimmer/ejection state when present, and reach/drop transition stability. Retuning may adjust sampling, force integration, damping, contact thresholds, crew center-of-gravity effects, and feature-forcing modifiers only when the water-field diagnostics remain inside threshold.

Milestone 18 source reports now include raft-coupling refreshes after the uniform-channel, wet/dry, and bed-step finite-volume work. The first finite-volume uniform-channel refresh increased passing raft outcomes from 7 to 9 of 50. The wet/dry reduced pressure-gradient refresh increased passing raft outcomes to 11 of 50, adding reduced `eddy_recovery` for `eddy_line_shear` and reduced `shallow_shelf_pivot_release` for `shallow_shelf`. The scoped bed-step augmented-topography promotion preserves those 11 passing raft outcomes, and the stitched reach/drop handoff promotion preserves low, median, and high South Fork cascading seam diagnostics as geometry artifacts. Promoted source-report artifacts now total 20. The raft gate and refreshed full Milestone 16 C++ validation gate remain blocked.

### 4. Distinct Pin/Release Fixture

Add a dedicated pin/release fixture separate from shallow-shelf grounding and boulder-impact proxy coverage. The fixture should encode a flow-dependent pin against a rock, strainer, or ledge-like obstruction with explicit approach angle, water depth, discharge band, contact normal, wrap depth proxy, side load, and release threshold.

The fixture must include at least three outcomes: unsafe no-action or late-action pin, successful high-side or weight-shift release inside the counterplay window, and failed release that transitions into swim/rescue or safety-score consequences. Reports should expose pin force, side load, raft orientation, crew weight distribution, release margin, flow band, and whether feature forcing contributed to the outcome.

The first dedicated fixture artifact is `physics/reports/milestone18/pin_release_fixture.json` with a human-readable companion at `physics/reports/milestone18/pin_release_fixture.md`. It uses schema `raftsim.milestone18.pin_release_fixture.v0` and records a midstream wrap/pin obstruction with low-flow scrape, runnable sticky, and high-flow washout cases. The sticky band includes no-action pin, timed high-side/brace/recovery release, and late failed-rescue paths, with feature forcing recorded at zero so the fixture is not hiding water-field failures.

### 5. Milestone 17 Analytic Guardrails

Run the manually encoded Milestone 17 analytic fixtures before and after every solver retune batch. The guardrail set covers lake-at-rest balance, sloping-channel friction, wet/dry shoreline behavior, bed steps, dam-break/bore behavior, hydraulic jumps, and transcritical flow over a bump where practical.

A retune batch is blocked if these reports regress, even when a larger rapid or raft outcome improves. This keeps broad whitewater tuning from hiding source-term, wet/dry, conservation, or jump-location failures in small trusted cases.

The preflight/postflight wrapper is `raftsim.examples.run_milestone18_analytic_retune_guardrail`. Its baseline scenario guardrail report lives under `physics/reports/milestone18/analytic_retune_guardrails/baseline_scenario_guardrail/` and records both analytic validation stages plus any pass-to-fail regressions.

### 6. Full Milestone 16 Gate Re-Run

After parity, geometry, raft-coupling, pin/release, and analytic-guardrail checks pass, regenerate the suite-level C++ validation report and the GeoClaw-to-Unreal readiness report. The readiness report must still be allowed to block live custom water if any comparison, geometry family, raft outcome, runtime budget, deterministic replay, or regression-promotion requirement fails.

## Open Decisions

- Exact schema fields for reach-local grids, ghost-zone ownership, stitched whole-window validation exports, and seam diagnostics.
- Exact numerical bounds and default gains for each allowed feature-forcing family.
- Whether the first accepted runtime remains CPU-only or starts a GPU path after correctness is established.
- Exact numerical thresholds for research-accepted, Unreal-prototype, and production-candidate tiers.
- Exact schema fields and acceptance thresholds for river validation annotations and guide-review signoff.
- Exact report schema for any future Milestone 18 closure artifacts beyond the failure triage, parity retune, analytic guardrail, pin/release fixture, and constriction throat shape reports.

## Related Docs

- [2.5D Dual-Solver Simulation Plan](2.5d-simulation-plan.md)
- [GeoClaw Reference Solver Transition Plan](geoclaw-transition-plan.md)
- [Custom Water Runtime Baseline](custom-water-runtime-baseline.md)
- [Python-To-Unreal Readiness Gate](python-to-unreal-readiness-gate.md)
- [Chaos And Jolt Runtime Evaluation](chaos-jolt-runtime-evaluation.md)
- [Chrono Water And Raft Coupling Plan](chrono-water-raft-coupling-plan.md)
