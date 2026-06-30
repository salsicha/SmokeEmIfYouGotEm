# GeoClaw Reference Solver Transition Plan

## Decision

Replace PyClaw with GeoClaw as the offline reference solver for river-water validation.

The custom C++ reduced shallow-water / height-field solver remains the Unreal runtime candidate. It should now be tuned and accepted by matching GeoClaw outputs, not PyClaw outputs.

PyClaw outputs remain useful as historical regression data, but they are no longer the physics acceptance target for cascading river water.

The next reference target is a variable cascading 2.5D scenario package: an ordered sequence of pools, reach-local slopes, sudden drops, rapid transitions, and recovery zones that represents California pool-and-drop rivers more faithfully than a single averaged channel.

## Why GeoClaw

GeoClaw is built around depth-averaged geophysical flow over varying topography. That matches the river problems this simulator cares about better than the earlier PyClaw-only plan:

- Cascading flow over steep and spatially varying bed elevation.
- Wet/dry shoreline and shallow shelf behavior.
- Topography/bathymetry source terms.
- Manning-style friction and roughness fields.
- Adaptive mesh refinement for hydraulic features, constrictions, drops, bores, and inundation fronts.
- Fixed-grid output that can be normalized into the existing comparison harness.

Reference docs:

- GeoClaw overview: https://www.clawpack.org/geoclaw.html
- GeoClaw topography inputs: https://www.clawpack.org/topo.html
- GeoClaw fixed-grid output: https://www.clawpack.org/fgout.html

## Architecture

The shared scenario package stays the source of truth.

```text
shared scenario package
  -> GeoClaw exporter
      -> setrun.py
      -> topography/bathymetry files
      -> initial depth/surface/momentum state
      -> boundary and hydrograph inputs
      -> Manning/roughness fields
      -> reach/drop transition metadata
      -> AMR refinement regions
      -> fixed-grid output requests
  -> GeoClaw reference run
  -> normalized reference frames
      -> h, eta, u, v, hu, hv
      -> wet/dry masks
      -> Froude number
      -> surface normals and slopes
      -> probes and cross sections
  -> existing dual-solver comparison harness
  -> custom C++ tuning and acceptance
```

The C++ solver does not need to duplicate GeoClaw numerics. It must match GeoClaw outputs and raft-relevant behavior within accepted tolerances.

For cascading packages, reach-local grids with overlap/ghost zones are the canonical authoring and streaming representation, while stitched whole-window outputs are mandatory validation artifacts. GeoClaw should validate both the stitched domain and reach/drop-local windows. The C++ solver may later stream or update reach windows for runtime cost, but the source package must preserve the same bathymetry, roughness, boundaries, and transition semantics.

The full C++ acceptance sequence is tracked in [Custom C++ Engine Full Validation Plan](custom-cpp-engine-validation-plan.md). Setup checks, fallback exports, or initial-state-only normalized files are useful smoke artifacts, but they do not replace full GeoClaw fixed-grid solution runs for live-water acceptance.

## Local Setup Check

The Python package now includes a GeoClaw setup check:

```bash
cd physics
PYTHONPATH=src python -m raftsim.examples.run_geoclaw_reference --check --allow-unavailable
```

The check writes `outputs/geoclaw_reference/geoclaw_setup_report.json` and verifies the required Clawpack Python modules plus local build tools normally needed by GeoClaw reference runs:

- `clawpack`
- `clawpack.geoclaw`
- `clawpack.clawutil`
- `clawpack.pyclaw`
- `make`
- `gfortran` or a compatible Fortran compiler

Install the Python research dependency with `python -m pip install -e ".[research]"`, then install compiler tools through the host platform package manager when the setup report flags missing build executables.

## Transition Steps

1. Freeze PyClaw outputs as legacy baseline artifacts.
2. Add a GeoClaw availability/setup check and document system dependencies.
3. Build a scenario-to-GeoClaw exporter.
4. Map shared bed grids to GeoClaw topography files.
5. Map water depth, surface elevation, velocity/momentum, wet/dry masks, and roughness into GeoClaw initial and auxiliary inputs.
6. Map inflow/outflow/wall boundaries and hydrographs into GeoClaw run configuration.
7. Define AMR rules for drops, constrictions, ledges, rocks, wet/dry fronts, bores, holes, and steep-gradient rapid segments.
8. Configure fixed-grid output over the same comparison windows used by the C++ solver.
9. Normalize GeoClaw frames into the current field/probe/cross-section schema.
10. Update the comparison harness from PyClaw-vs-C++ to GeoClaw-vs-C++.
11. Retune C++ numerical coefficients, roughness, damping, wet/dry thresholds, authored feature forcing, and raft-force parameters against GeoClaw.
12. Replace the current monolithic real-world package with a variable cascading reach/drop package for South Fork American baseline validation.
13. Add reach-boundary diagnostics for mass flux, momentum flux, energy loss, wet/dry fronts, and raft-state continuity.
14. Re-run real-world low/median/high flow validation and regenerate the Python-to-Unreal readiness report.

## Validation Matrix

### Canonical Fixtures

- Flat pool.
- Uniform channel flow.
- Dam-break / bore.
- Bed step.
- Constriction.
- Wet/dry shoreline.
- Sloping channel with Manning friction.
- Drop/ledge over variable topography.

### River-Specific Fixtures

- Steep boulder garden.
- Cascading wave train.
- Hydraulic hole with downstream boil.
- Lateral wave off an angled bank.
- Eddy line with shear/yaw impulse.
- Shallow shelf grounding region.
- Real-world low, median, and high runnable flow bands.
- Cascading pool-and-drop sequence with alternating low-gradient pools, steep reach entries, sudden bed drops, hydraulic controls, and recovery eddies.

### Metrics

- Mass conservation.
- Depth and surface-elevation L1/L2/Linf error.
- Velocity and momentum error, with shallow-cell-aware masking.
- Wet/dry boundary location.
- Hydraulic jump/standing-wave crest location.
- Wave-train phase and amplitude.
- Froude number class agreement.
- Hole retention geometry and downstream boil strength.
- Eddy-line shear location and strength.
- Raft force envelope and trajectory outcome.
- Runtime cost for the custom C++ solver.
- Reach/drop handoff conservation and continuity: mass flux, momentum flux, expected energy loss, wet/dry boundary behavior, and raft transition stability.

## Acceptance Gates

GeoClaw becomes the new reference when:

- The shared scenario exporter can produce deterministic GeoClaw runs.
- Full GeoClaw fixed-grid solution output is normalized into the frozen telemetry schema.
- Canonical and river-specific fixtures produce stable reference outputs.
- The custom C++ solver can run identical packages and meet revised GeoClaw comparison thresholds.
- Raft coupling sampled against GeoClaw fields and C++ fields produces comparable force envelopes and outcomes.
- The Python-to-Unreal readiness report is regenerated and explicitly re-approved against GeoClaw.

## Unreal Runtime Impact

GeoClaw is not planned for shipping or for the UE5 runtime. The Unreal runtime remains:

- Custom C++ reduced shallow-water / height-field solver for water fields.
- Selected raft/contact runtime for raft kinematics and contact, chosen after the Chaos/Jolt fixture evaluation.
- GeoClaw offline for reference validation, regression fixtures, parameter fitting, and readiness gates.
