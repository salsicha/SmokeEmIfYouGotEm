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

## Analytic Fixture Decision

Add a small manually encoded SWASHES-style analytic fixture set before more broad retuning. These fixtures should isolate solver fundamentals such as lake-at-rest balance, sloping-channel friction, wet/dry shoreline motion, bed steps, dam-break/bores, hydraulic jumps, and transcritical flow over a bump where practical.

Each analytic fixture must include provenance notes that explain the source equation or benchmark family, why the case is representative, which fields are expected to be exact or approximate, and which tolerances are used. Do not vendor external SWASHES data or code until licensing, redistribution, update cadence, and maintenance ownership are clear.

Analytic fixtures are diagnostic gates, not gameplay content. Parameter retuning for big rapids must not be accepted if it regresses these small cases.

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

The C++ engine is accepted for live Unreal water only when:

- Every required scenario has a full GeoClaw solution run with fixed-grid frames, not only fallback or initial-state output.
- C++ field, probe, cross-section, diagnostic, and reach/drop-window comparisons pass the frozen thresholds.
- Raft force envelopes, trajectories, and outcome classes pass the frozen thresholds.
- Runtime and memory profiles fit the target prototype budgets.
- Deterministic replay is documented for the accepted solver mode and parameter set.
- The GeoClaw-to-Unreal readiness report explicitly approves live custom water.

## Open Decisions

- Exact schema fields for reach-local grids, ghost-zone ownership, stitched whole-window validation exports, and seam diagnostics.
- Exact numerical bounds and default gains for each allowed feature-forcing family.
- Whether the first accepted runtime remains CPU-only or starts a GPU path after correctness is established.
- Exact numerical thresholds for research-accepted, Unreal-prototype, and production-candidate tiers.
- Which real-world footage, gauge histories, guide notes, and aerial references are required to validate rapid-specific behavior beyond GeoClaw parity.

## Related Docs

- [2.5D Dual-Solver Simulation Plan](2.5d-simulation-plan.md)
- [GeoClaw Reference Solver Transition Plan](geoclaw-transition-plan.md)
- [Custom Water Runtime Baseline](custom-water-runtime-baseline.md)
- [Chrono Water And Raft Coupling Plan](chrono-water-raft-coupling-plan.md)
