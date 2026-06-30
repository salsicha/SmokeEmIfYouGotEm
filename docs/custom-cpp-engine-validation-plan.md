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
- Close the geometry families that still fail: wet/dry shorelines, bed steps, constrictions, drops/ledges, tailwater controls, and cascading reach/drop behavior.
- Retune raft coupling only after the relevant C++ water fields improve, so force and outcome fixes are not masking bad hydraulics.
- Add a distinct pin/release fixture that is not only shallow-shelf or boulder proxy evidence.
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
- Milestone 16 geometry evidence is tracked in `physics/reports/milestone16/geometry_validation.json` and `physics/reports/milestone16/geometry_validation.md`; hydrostatic/sloping balance and stitched reach/drop handoffs pass, while wet/dry shorelines, bed steps, constrictions, and drops/ledges/tailwater remain blocked by GeoClaw-vs-C++ threshold failures.
- Validate hydrostatic balance and bed-slope source terms on sloping and frictional channels.
- Validate wet/dry fronts over shelves, banks, and shallow eddies.
- Validate bed steps, constrictions, ledges, drops, tailwater controls, and expected energy loss.
- Validate mass, momentum, energy, and wet/dry behavior at reach/drop boundaries.
- Validate that stitched global windows and reach-local windows produce consistent probes, cross sections, and raft entry/exit states.
- Reject any seam artifact that changes raft outcome, feature location, or conservation diagnostics at a reach/drop boundary.

## Phase 4: Whitewater And Raft-Relevant Validation

- Milestone 16 raft-coupling evidence is tracked in `physics/reports/milestone16/raft_coupling_validation.json` and `physics/reports/milestone16/raft_coupling_validation.md`; the gate remains blocked with 7 of 50 GeoClaw-vs-C++ raft comparisons passing, while force deltas, candidate feature checks, and several outcome classes still fail.
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

- Milestone 16 promoted-regression evidence is tracked in `physics/reports/milestone16/regression_promotion_manifest.json`, `physics/reports/milestone16/regression_promotion_manifest.md`, and `physics/regression_fixtures/milestone16/registry.json`; 4 passing GeoClaw/C++ threshold runs were copied as fixtures and 7 passing raft-coupling cases were captured as artifact manifests.
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

### 2. Geometry-Specific Failures

Treat each blocked geometry family as its own acceptance lane. Wet/dry fixes must show bounded shoreline movement, dry-cell velocity masking, and mass drift. Bed-step fixes must show the right free-surface response and source-term balance. Constriction fixes must preserve flux, velocity acceleration, and Froude-class transitions. Drop/ledge/tailwater fixes must show expected energy loss, hydraulic control, and downstream recovery. Cascading reach/drop fixes must compare reach-local outputs against stitched whole-window outputs so seams cannot hide errors.

Each family should be promoted into regression artifacts when it passes. Do not tune a whitewater feature by sacrificing lake-at-rest, sloping-channel, wet/dry, bed-step, bore, hydraulic-jump, or transcritical-bump guardrails.

### 3. Raft Coupling Agreement Over C++ Water

Re-run raft coupling after the relevant water-field and geometry failures improve. Compare GeoClaw-derived and C++ water fields with the same raft initial states, water samples, feature probes, crew actions, and contact setup.

The raft gate must compare force envelopes, impulse timing, trajectory deltas, yaw/roll/pitch proxies, surf/flush/clear/ground/pin/flip outcome classes, recovery timing, swimmer/ejection state when present, and reach/drop transition stability. Retuning may adjust sampling, force integration, damping, contact thresholds, crew center-of-gravity effects, and feature-forcing modifiers only when the water-field diagnostics remain inside threshold.

### 4. Distinct Pin/Release Fixture

Add a dedicated pin/release fixture separate from shallow-shelf grounding and boulder-impact proxy coverage. The fixture should encode a flow-dependent pin against a rock, strainer, or ledge-like obstruction with explicit approach angle, water depth, discharge band, contact normal, wrap depth proxy, side load, and release threshold.

The fixture must include at least three outcomes: unsafe no-action or late-action pin, successful high-side or weight-shift release inside the counterplay window, and failed release that transitions into swim/rescue or safety-score consequences. Reports should expose pin force, side load, raft orientation, crew weight distribution, release margin, flow band, and whether feature forcing contributed to the outcome.

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
- Exact report schema for the Milestone 18 failure triage matrix and the distinct pin/release closure artifact.

## Related Docs

- [2.5D Dual-Solver Simulation Plan](2.5d-simulation-plan.md)
- [GeoClaw Reference Solver Transition Plan](geoclaw-transition-plan.md)
- [Custom Water Runtime Baseline](custom-water-runtime-baseline.md)
- [Python-To-Unreal Readiness Gate](python-to-unreal-readiness-gate.md)
- [Chaos And Jolt Runtime Evaluation](chaos-jolt-runtime-evaluation.md)
- [Chrono Water And Raft Coupling Plan](chrono-water-raft-coupling-plan.md)
