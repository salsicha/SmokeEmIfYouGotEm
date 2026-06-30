# Custom C++ Engine Full Validation Plan

## Purpose

This plan defines what is required before the custom C++ shallow-water / height-field engine can be treated as the accepted live-water runtime for Unreal.

The current engine is a runtime candidate, not a fully accepted production solver. GeoClaw remains the offline reference model. PyClaw artifacts are legacy regression data only.

## Geometry Decision

The full game should model rivers as continuous gridded 2.5D geometry with explicit reach, drop, pool, hazard, roughness, and hydraulic-control annotations.

Reach-local grids with overlap or ghost zones are acceptable for authoring, streaming, and solver cost. A single stitched global grid is also acceptable. Disconnected pools stitched only by scripted handoffs are not acceptable for full validation because they hide momentum, wet/dry, bed-slope, and raft-transition errors at the exact places rapids matter most.

## Validation Principle

GeoClaw and the C++ engine must consume the same solver-neutral scenario package. GeoClaw-specific files are generated exports, and C++-specific runtime parameters are recorded as manifests. Acceptance compares outputs and raft-relevant behavior, not internal numerical methods.

Fallback or initial-state-only GeoClaw normalization is useful for schema smoke tests, but it does not count as full shallow-water solution validation.

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

## Phase 1: GeoClaw Reference Runs

- Milestone 16 reference evidence is tracked in `physics/reports/milestone16/geoclaw_reference_runs.json` and `physics/reports/milestone16/geoclaw_reference_runs.md`; generated GeoClaw app/output trees use the compact ignored `physics/outputs/m16g/` path to avoid GeoClaw/Fortran path truncation.
- Run real GeoClaw fixed-grid simulations for the canonical, rafting, real-world, and cascading suites.
- Store manifests with GeoClaw availability, dependency versions, AMR/fixed-grid settings, scenario package hash, and export time.
- Normalize full solution frames into the shared field/probe/cross-section telemetry schema.
- Export per-reach windows and stitched whole-river windows for cascading packages.
- Flag any scenario that only has schema, setup, or initial-state fallback output as not fully validated.

## Phase 2: C++ Parity Runs

- Milestone 16 C++ run evidence is tracked in `physics/reports/milestone16/cpp_solver_runs.json` and `physics/reports/milestone16/cpp_solver_runs.md`; the run/manifests gate passes for reduced and finite-volume modes, while cascading finite-volume validation failures remain visible for comparison/tuning gates.
- Run the C++ reduced and finite-volume modes on the same scenario packages.
- Emit manifests for solver mode, timestep, CFL policy, dry tolerance, roughness mapping, bed-slope source scale, feature forcing, damping, reach/drop metadata, and executable version.
- Compare C++ fields, probes, cross sections, diagnostics, and raft samples against the GeoClaw reference runs.
- Record failures by scenario family so tuning does not improve one rapid feature while regressing canonical shallow-water behavior.

## Phase 3: Geometry-Specific Shallow-Water Validation

- Validate hydrostatic balance and bed-slope source terms on sloping and frictional channels.
- Validate wet/dry fronts over shelves, banks, and shallow eddies.
- Validate bed steps, constrictions, ledges, drops, tailwater controls, and expected energy loss.
- Validate mass, momentum, energy, and wet/dry behavior at reach/drop boundaries.
- Validate that stitched global windows and reach-local windows produce consistent probes, cross sections, and raft entry/exit states.
- Reject any seam artifact that changes raft outcome, feature location, or conservation diagnostics at a reach/drop boundary.

## Phase 4: Whitewater And Raft-Relevant Validation

- Re-run raft coupling over GeoClaw-derived fields and C++ runtime fields with the same probe/sample sets.
- Validate pool entry, drop entry, hydraulic-hole surf/flush, downstream boil recovery, eddy recovery, boulder impacts, shallow shelves, pins/releases, and transition-boundary crossings.
- Compare force envelopes, trajectory deltas, outcome classes, and contact/grounding events.
- Keep authored feature forcing only when it is documented, bounded, and validated against GeoClaw outputs or accepted real-world reference behavior.

## Phase 5: Runtime, Determinism, And Portability

- Verify deterministic replay for repeated runs on the same platform and, where practical, across supported compilers/platforms.
- Profile validated configurations against desktop, VR, and handheld runtime budgets.
- Record memory, output, streaming, and telemetry costs for Unreal preproduction.
- Decide whether GPU acceleration starts only after the CPU path passes the correctness gate.

## Phase 6: Regression Fixtures And Reports

- Promote passing GeoClaw/C++/raft comparison runs into committed regression fixtures or artifact manifests.
- Generate one JSON report and one human-readable Markdown report for each scenario suite.
- Keep a CI smoke subset that does not require external GeoClaw execution.
- Keep a manual or scheduled full GeoClaw suite for reference regeneration, parameter retuning, and readiness gates.

## Phase 7: Acceptance Gate

The C++ engine is accepted for live Unreal water only when:

- Every required scenario has a full GeoClaw solution run with fixed-grid frames, not only fallback or initial-state output.
- C++ field, probe, cross-section, diagnostic, and reach/drop-window comparisons pass the frozen thresholds.
- Raft force envelopes, trajectories, and outcome classes pass the frozen thresholds.
- Runtime and memory profiles fit the target prototype budgets.
- Deterministic replay is documented for the accepted solver mode and parameter set.
- The GeoClaw-to-Unreal readiness report explicitly approves live custom water.

## Open Decisions

- Whether the canonical cascading storage format is one stitched grid, reach-local grids with ghost zones, or both.
- How much authored feature forcing is acceptable versus pure shallow-water dynamics.
- Whether the first accepted runtime remains CPU-only or starts a GPU path after correctness is established.
- Exact numerical thresholds for research-accepted, Unreal-prototype, and production-candidate tiers.
- Which real-world footage, gauge histories, guide notes, and aerial references are required to validate rapid-specific behavior beyond GeoClaw parity.

## Related Docs

- [2.5D Dual-Solver Simulation Plan](2.5d-simulation-plan.md)
- [GeoClaw Reference Solver Transition Plan](geoclaw-transition-plan.md)
- [Custom Water Runtime Baseline](custom-water-runtime-baseline.md)
- [Chrono Water And Raft Coupling Plan](chrono-water-raft-coupling-plan.md)
