# South Fork shared density/surface correction — September 11

The last user-status turn was informational, not implementation progress.
This resumed goal turn implemented and exercised a shared density/contact map
and transported the native scalar by its inverse. South Fork is still incomplete;
the playable map and later reconstruction queue have not been promoted or closed.

## What changed

`liquid_shared_density.py` applies the exact transpose of the component-wise
compact sampler to the all-node particle-density gradient: S^T grad(E).
Fluid/air/solid labels do not mask density residuals. Binary mobility fixes
solid/exterior/Z displacement unknowns; exact swept-mesh and original exterior
constraints act on the shared field, not independent particle pushouts.
Cell-metric projection uses Dykstra with optional existing active-set refinement
of the same contact dual. No diagonal regularizer, altered bed, deleted particle,
volume clamp, jitter, or weakened geometric threshold was introduced.

`solve_liquid_shared_density.py` loads current positions, identities, scalar and
phase. It reuses only the separately verified static bed-kernel integral from the
older geometry package. Accepted native-coordinate endpoints are the actual
float32 rounding of the shared map. The surface uses the inverse of that exact
finite map, not an unrelated velocity backtrace or replacement density isovalue.
This remains a CPU position reference: no native momentum/time integration.

`liquid_map_injectivity.py` adds a conservative continuous-map no-fold bound.
In cell coordinates, compact normal derivatives are convex-weighted centered
differences and transverse derivatives are convex-weighted adjacent differences.
An infinity-norm Lipschitz bound below one gives a positive global separation
factor for x+delta(x). The zero-displacement mathematical extension is not a
physical exterior boundary condition. This cannot certify float32 rounding,
terrain adherence, or geometric-volume preservation; those are separate checks.

## New late-state failure: coincidence already exists natively

Read-only audit: `liquid-highorder-600-coincidence-v1.json`. At step600 the
726920-particle high-order capture already contains one coincident pair:
original birth owner7, sequences9203 and9204. They were born at the same XY but
different Z (473.3487854 and506.8251953cm), about33.4764cm apart. Both now occupy
[-9112.4775390625,-4193.013671875,425.0541687011719]cm. The paired current-step
raw and contacted positions also coincide. This does not identify the first
collapse step or prove which earlier operation caused it.

An identical input pair cannot separate under any single-valued shared map.
The earlier commentary attributing the small-step coincidence to this correction
was superseded by this birth/current audit. The runner now rejects such input
before futile smaller trials; it does not merge, jitter or push particles apart.
Step12 was independently checked:729672 particles, no coincident pair.

Late-state v1 (`tmp/south-fork-liquid-shared-density-v1-20260911`) completed
207.98s, rejected.128 coordinate sweeps did not converge for substantial steps;
tiny geometrically feasible steps retained the existing coincidence.
v2 native and double-precision comparison preserve partial `progress.jsonl` and
algorithm snapshots. Their owned processes24096/34540 were verified by command
line and deliberately terminated after input coincidence made acceptance
impossible. They have NO accepted state or completed report.

The double comparison nevertheless established that the shared contact field
can reduce late-state density in continuous coordinates: full alpha1 reduced
energy3676.0925→3550.3899 and particle peak12.36116→9.51934, with exact bed/survey
paths; it retained the original duplicate and was rejected. Native rounded
contact refinement still had rank-deficient/slow cases. Neither trial is native
or physically accepted.

## Early-state coupled result and persisted-state verification

Candidate: `tmp/south-fork-liquid-shared-density-early-v1-20260911`.
Input: native high-order step12, stagesSHA
`5bcdf0f3d705f5a814ad2babab40c2bd2aa38ac3c856e72321402b79b014a112`.
One alpha1 correction,87.22s CPU reference wall time, not gameplay FPS.

Independent saved-state audit: `liquid-shared-density-early-independent-v2.json`,
SHA `f25da020aa78822507906280ec8f2e899df55efc6f856b3724f5899cb2a58a40`.
It reopens the field/state, checks source hashes, all IDs and exact float32
endpoints, exact swept triangles and original survey, inverse scalar replay,
the global continuous map bound, and above-bed geometric volume. v2 additionally
snapshots all algorithm sources before running and verifies they remain unchanged.
v1 is superseded: a finite-input guard was edited while it was executing and its
end-only source hashes did not establish the executed source version. v2 reran
the complete audit unchanged and reproduced the numerical results.

- All729672 IDs, represented volume15201.500453m3 and distinct native positions
  preserved; no particle deletion, merge, new coincidence or exterior violation.
- Exact swept minimum clearance1.983847728cm; required skin is the unchanged
  min(original clearance,2cm). Minimum required margin−2.374e−13cm, inside the
  existing1e−6cm gate; physical bed never crossed.
- All-node excess-density energy208.61431→150.87105; particle peak1.423548→1.309523;
  total including solid fraction1.782479→1.526076. Not incompressibility.
- All749403 selected scalar cells replay the same finite inverse exactly;
  largest inverse residual9.997654e−7cm, against unchanged1e−6cm tolerance.
- Continuous map Lipschitz bound.72955967, separation factor≥.27044033 in cell
  infinity norm; sampled inverse determinant minimum.89335243. Rounded particle
  uniqueness is separately checked, not inferred from this continuous bound.
- Particle surface coverage117 outside→115 outside, zero unsupported stencils.
  Material scalar RMS change.0372494cm, max1.4985183cm; scalar is not distance.
- Fixed solid/exterior/Z scalar values remain exact. Original exterior extensions
  are still provisional, not physically accepted global boundary conditions.

## Physical volume remains wrong — do not promote

Adaptive exact-Z/XY-Gauss integration against the unchanged captured bed gives
surface volume15245.337166→15266.917295m3: **+21.580129m3**, although nominal
particle volume did not change. Both exceed nominal volume. Orders2..128 leave
zero unresolved columns; successive-order absolute difference sums are about
1.111m3, estimates rather than certified error bounds. Explicit upper Z cap is
.412120m3 in both, lower cap zero. No uniform surface offset was applied to make
these numbers match. Passing density and inverse tests is not physical acceptance.

Next: apply density/contact consistency before native collapse can occur and
constrain the shared correction's geometric volume, rather than fixing a late
coincident state or independently offsetting the surface. Validate repeated
native motion/momentum, current exterior/Z behavior and sustained discharge.
Then connect one visible frothy/breaking surface and validate real-reference
appearance, boat/boulder response and gameplay FPS. Colorado, Pacuare,
Futaleufu, other-scene reviews, crew, cleanup and release/commit remain queued.

## Verification / process state

550 liquid Python regressions pass,8.550s. New tests cover exact compact-adjoint
duality, density chain rule, shared contact effects, same-map inverse, exact
coincidence preservation/detection, and conservative anisotropic derivative
bounds. First restricted full test attempt failed to import SciPy; rerun with
installed numerical dependency access passes. No Unreal code changed this turn.

All owned sessions are terminal:84130 rejected1;10307/95383 deliberately stopped1;
16230 early trial0;35210 superseded audit0;45823 authoritative audit0;
99328/41948 regressions0. No live UE/build/worker remains.
Saved playable map SHA remains
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.
About2.3GB free on C:. No files deleted. No scene promotion, final commit or push.
