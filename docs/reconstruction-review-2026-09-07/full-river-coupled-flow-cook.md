# Full-river coupled flow cook — September 12

Status at 09:10 UTC: the actual 826-tile / 5,286,400-cell river solve is RUNNING.
It is not settled or promoted to the normal game. South Fork remains the
scenario; Troublemaker is a rapid within it and stays off the menu.

## Physical inlet and conservative driver

Added explicit native `discharge_profile` boundaries on any Cartesian edge.
Profiles use the existing two-layer profile container; nearest-layer depth
times inward normal velocity defines the prescribed face discharge density.
The external bed plus depth supplies stage only when the normal flow is
supercritical or initially dry. Subcritical faces retain the outgoing normal
characteristic and solve for boundary depth. Tangential inflow velocity is
explicit. Zero-discharge cells reflect; invalid outward prescribed inflow is
rejected. This is a physical boundary, not an internal tile ghost exchange.
The distinction between flow and stage conditions is documented in the
[HEC-RAS external-boundary guidance](https://www.hec.usace.army.mil/confluence/rasdocs/r2dum/6.3/boundary-and-initial-conditions-for-2d-flow-areas/external-boundary-conditions).
That reference supports the boundary-condition distinction, not acceptance of
this river's inferred stages or this implementation.

The two upstream faces share ONE 45.3069545472 m3/s target, partitioned by
depth-based conveyance and inward direction projection. Authored/numerical
inlet fluxes are 40.919674617746303 m3/s east and 4.387279929453668 m3/s north.
The downstream west faces use one explicitly inferred stage, 131.0414276123 m
NAVD88 (median captured wet-edge surface). This is not a measured stage matched
to the requested flow and must be judged through settling/reference evidence.

`CartesianWaterDomain::step_with_flux_audit` integrates actual exterior numerical
fluxes at BOTH RK2 stages and every CFL substep. Internal tile faces are excluded
from the exterior balance. A multi-substep test verifies reset/time weighting;
there is no global mass correction. The ordinary non-audit path is retained.
The constructor also validates all scenario field shapes before coupling.

`raftsim_cartesian_cook` loads every package, advances the shared domain and writes
NPY depth/XY-velocity snapshots in tile order (tiles stacked along the row axis).
It retains the copied manifest and original manifest path, per-step conservation
accounting, periodic progress and completed-frame markers. Every step checks all
cells for finite values, nonnegative depth, depth <=10 m and speed <=20 m/s.
The 0.001 m3/s step-conservation gate remains unchanged. State-gate failure writes
the location/values and the full failure state; completed solve is not marked
as settled automatically. Snapshots retain a 512 MiB free-space safety reserve.

## Verified candidate, not installed runtime

Candidate directory: `tmp/troublemaker-row-solver-discharge-v1-20260912`.
Library SHA256 `88cadefdc5233d2106f6f5ebd39ce695eebf70f01346c23e5e6b609184750d0f`.
Running cook executable SHA256
`f22ced82f86e0051f444cf3462780fe5291497e33d7d3cd5a80e7daf086a3741`.
The later test-only rebuild changed neither executable nor library.

All FOUR CTests pass (latest 3.34 seconds): domain, shoreline, lake-at-rest and
transcritical. Domain tests include four-edge prescribed injection with exact
volume accounting over multiple CFL substeps, sixteen-tile/unsplit equivalence,
all four uniform supercritical inlets and initially dry inlets, signed ghost
profiles, invalid input and the retained wet/dry/nonflat-bed partition checks.
The four-edge prescribed example supplies 40.24 m3/s; state and face-flux
partition differences are zero. Existing analytic closed volume drift remains
<=3.41061e-13 m3. No numerical gates were relaxed.

Cook-driver smoke test:
`tmp/cartesian-cook-driver-check-20260912/result` completes 0.5 s of the retained
lake with exactly unchanged depth/volume. Python independently loads the native
NPY frames, verifies their shape and exact depth equality, and bounds numerical
velocity below 1e-12 m/s.

The installed playable archive remains
`e69772d2c856054f6bb37035486e6828c47d3ee3eebdbf9b0261dec6fb9a678c`.
No UE build or editor run was performed in this pass. Do not point that older
runtime at the new discharge-profile packages. Install a verified archive and
rebuild its consumers when the corresponding runtime delivery is ready.

## Input preparation and provenance

Initial velocity is an explicit warm start: 10 m station-bin conveyance from
the unchanged bed/depth, smoothed over 10 m, oriented by the retained river-axis
tangent. A tangent projection extends ONLY this initialization coordinate beyond
the route endpoints; it does not alter terrain or gameplay chainage. These are
not measured velocities or a solved steady state. Captured surface and the
uncalibrated submerged-bed inference remain distinguished from observations.

The v1 inputs accidentally retained analytic-template generator/provenance
labels despite correct real geometry and numerical flags. Those inputs and
their pilot are retained, not edited. The v2 revision replaces the metadata
with per-core captured-source hashes, source paths, coordinate frame and
explicit inference labels. Numerical preparation is otherwise unchanged.

Current input manifest:
`tmp/south-fork-coupled-flow-input-v2-20260912/manifest.json`, SHA256
`13f57b3d2e2a4fbe043fca0f666c6ae83e27d71b5dac9cbf8f7ef4323d810dae`.
Independent `input_audit.json`, SHA256
`9c258a8e72f7294b03cefcf778e201f1e25cae78ccbc7f1e67fc2e96d8a601bd`,
passes all 826 packages / 5,286,400 cells: every file hash, exact bed in the
declared datum, finite depth/velocity, momentum/eta consistency, bool wet-mask
encoding, corrected provenance and combined inlet discharge. Maximum initial
depth 2.8150558472 m, speed 3.9930163809 m/s. Scripts:
`prepare_south_fork_coupled_flow.py` and `verify_south_fork_coupled_flow.py`.

## Whole-river pilot and live long run

`tmp/south-fork-coupled-flow-pilot-v1-20260912` completed 20 steps / 1 s, exit 0,
15.50 seconds solver wall time. Maximum final depth 2.71215 m, speed 9.87563 m/s;
maximum step conservation residual 5.27143e-9 m3. The inlet is exact. Final
outlet magnitude is about 82.98 m3/s, so this is plainly NOT settled.

The current 600 s target run starts from the verified v2 inputs:

```powershell
& tmp/troublemaker-row-solver-discharge-v1-20260912/raftsim_cartesian_cook.exe tmp/south-fork-coupled-flow-input-v2-20260912/manifest.json tmp/south-fork-coupled-flow-600s-v2-20260912 12000 2000
```

LIVE handle: session **63136**, native PID **36216**, started **09:05:06 UTC**.
At **09:10:52 UTC**, the process is confirmed alive. Latest progress: step 290,
14.5 s simulated / 338.25 s wall time, depth 3.74924 m, speed 12.54218 m/s,
maximum step conservation residual 1.03490e-8 m3, cumulative residual
-1.55421e-9 m3. Inlet remains exact; outlet is about 10.69 m3/s and still
transient. Do not claim settling from these early values.

Authoritative live ledger:
`tmp/south-fork-coupled-flow-600s-v2-20260912/progress.jsonl`.
Check the session/process before launching another cook. Do not rebuild or
overwrite the running executable. Saved frames are scheduled every 2,000 steps
(100 simulated seconds), plus initial/final frames. Only a frame containing
`complete.json` is complete. `completed.json` denotes a terminal solve, never
physics/visual acceptance; absence alone is not proof the process stopped.

At 09:10 UTC free space is 3,811,680,256 bytes. No deletion or commit occurred.
Normal FullReach map and user save hashes are unchanged (e77da92b... / 181d1e57...).

## Next delivery work

Continue this live run; investigate any state/conservation failure without
loosening gates. Evaluate settling and actual section discharges, not only total
boundary flow. Build a conservative restart if more spin-up is needed.

The normal runtime loader still defaults to first-order evolution and scalar/
transmissive crop boundaries. It needs an explicit Cartesian MUSCL crop mode
with TWO exact source ghost layers, source-context selection allowing those
layers plus crop rounding, and matching roughness. Preserve the separate
SurveyReplay full-grid/discharge guard. The surface's two-axis movement is
already built, but source export, wider baseline coverage, flow-direction-aware
crest generation, coherent FullReach terrain/material/progress/starts/sections/
finish integration and actual game motion/visual/performance checks remain open.
All later river, crew, normalization, regression and release/commit work remains
in the active goal; no diagnostic result closes those requirements.
