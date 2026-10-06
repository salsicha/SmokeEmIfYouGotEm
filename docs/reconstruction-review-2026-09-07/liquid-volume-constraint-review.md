# Shared-map volume constraint and GPU transpose — September 11

Later continuation: see [terrain-aware quadrature](liquid-terrain-quadrature-review.md)
for the current implementation and live full-state run. The results below are
retained historical evidence, not the latest job status.

South Fork and the full reconstruction queue remain incomplete. This turn made
implementation progress after the preceding shared-map investigation; it does
not promote the playable map or claim the physical volume problem is solved.

## Implemented CPU volume coupling

`liquid_surface_volume_gradient.py` differentiates the actual trilinear negative
volume above the unchanged bed. It includes all vertical liquid intervals,
bank clipping and the existing explicit Z-cap extrapolation. Adaptive XY Gauss
quadrature checks both volume and local nodal-gradient differences. Nondifferentiable
zero endpoints and exact bed-crossing ties are counted rather than hidden.
These quadrature differences remain estimates, not certified bounds.

`liquid_map_volume_gradient.py` differentiates the existing finite inverse map
and scalar resampling. It pulls dV/dphi through the inverse Jacobian and the
exact compact interpolation transpose. The derivative belongs to the SAME map
used by particles. Scalar-knot departures are reported; nonlinear volume still
has to be measured after each trial. No uniform height offset or replacement
density isovalue is used.

`liquid_field_equality.py` projects the shared field into one linearized volume
equality and solves exact contact inequalities in its null space. The contact
Schur complement is B B^T - (B a)(B a)^T/(a.a), without diagonal regularization.
`constrained_field` accepts this optional equality while keeping the previous
no-equality path intact. Existing skin/survey/contact tolerances are unchanged.

`refine_liquid_shared_volume.py` now performs sequential volume/contact solves
on the verified early729672-particle state. Its target15201.500453m3 is derived
from the unchanged particle volumes. Each trial must retain exact float32
endpoints, IDs, distinct positions, swept bed and original survey, a global
continuous no-fold bound, improved density relative to original input, and
decreasing measured nonlinear volume error. The numerical volume-root target
is .01m3, separate from the estimated quadrature accuracy and physical acceptance.
No native momentum update or physical-time advancement is installed yet.

Eleven new Python regressions cover multiple zero crossings, sloping bed,
explicit caps, nodal finite differences, the full inverse-map volume chain
rule, no-sensitivity rejection, and joint equality/contact projection. Total
liquid suite:561 pass in8.766s with installed SciPy access, session11809 exit0.

## Actual GPU transpose built and verified

New `RaftSimLiquidCompactAdjointGPU.h/.cpp` and `RaftSimLiquidCompactAdjoint.usf`
compute the same shared-field transpose on the GPU. Two passes bin particles
and gather the union of three component supports (32bins rather than64).
No float/fixed-point atomic accumulation of gradient values is used; integer
atomics only build neighbor lists and diagnostics. Component mobility fixes
field unknowns; it does not remove density residuals. No particle, surface,
terrain or momentum is written. Native solver integration remains open.

Consumers must reject nonzero invalid-input/support/mobility/chain diagnostics.
Live-count overflow rejects the batch; unsupported/invalid particles cannot be
silently omitted from an accepted field. Full-grid results are initialized.
The actual GPU test compares all504 anisotropic nodes against an independent
double-precision reference in seven cases: normal/partial-component mobility,
empty batch, count overflow, incomplete support, invalid gradient validity,
invalid mobility and NaN gradient. Includes typed-buffer/grid/metric API checks.

Build65205 succeeded20.58s. Initial engine82631 failed during shader compilation:
UE's root-parameter parser rejected the combined `uint Capacity,NodeCount`
declaration. Splitting the declarations fixed it; no engine/source gate was
disabled. Initial failure log remains `engine-liquid-compact-adjoint-v1.log`.
Engine23762 then exited0 with one clean success, no warnings/errors:
`engine-liquid-compact-adjoint-v2/index.json`, D3D12_SM6 on AMD Radeon graphics.
The .0614s duration is a small seven-case test with readbacks, NOT gameplay FPS.

Tested source SHA256:

- Shader:93168461c370d93267de86ac3bc2d45ed41940b58940d897f142bdd3e1369048
- C++:29718ba56a0c6c93177f12d5ec6abe2badf4e61f7af64ed091fb440ff6bdf910
- Test:086a6cc7bbc5b8f91cacee0690f3e944477c0d9baefe5901a8a1f524c0838fa8

## Full-state trial is terminal and rejected

Session79716/PID37216 completed with exit1 after1333.15s. It was genuinely live
during the preceding observations, then terminated normally with a reported
numerical failure; do not treat the earlier quiet output as a stall/restart.
Output:`tmp/south-fork-liquid-shared-volume-v1-20260911`, reportSHA
`01d20dcbe56c041f5e79c0d69105ac59155742438f297db72144508645046342`.
All snapshotted sources remained unchanged. No job is still running.

The first volume/gradient integration had82665 physical XY columns. Remaining
columns after orders4/8/16/32/64/128 were22786/20188/18344/16359/10699/1842.
Both volume and local gradient tolerances stayed at1e−4. Zero endpoint and
exact bed-tie ray counts were zero. Final successive-order sums were.517821m3
for volume and1.308413 for scalar-gradient entries (estimated, not certified).
The surface volume was15266.927402m3,65.426949m3 above nominal. This is about
.0101m3 different from the previous volume-only adaptive estimate because
gradient-driven refinement evaluates more columns at higher orders.

The1842 unresolved columns correctly stopped the runner BEFORE a map/contact
update. `converged=false`, failure=`Unresolved geometric volume/gradient
quadrature`. There are no accepted refinement steps. The retained `state.npz`
is the unchanged seed state, not a volume-corrected result. The previously
observed115 outside particles remain. No volume error was fixed by this run.

Next: improve derivative integration where the active zero-crossing interval
or terrain clipping changes inside an XY column. Raising tensor-product order
everywhere is slow; split/refine those integration regions while preserving
the original error gates. Preserve per-column evidence in the next run so
unresolved derivatives can be localized. Then rerun the full nonlinear
volume/contact refinement and independently verify all accepted maps, including
saved particles, exact bed/survey, inverse scalar, coverage and geometric volume.
Implement/verify early native density/contact/momentum coupling so the
known late original-particle coincidence never arises; retain the same surface
map and resolve physical exterior/Z conditions, sustained discharge, visible
breaking/frothy water, boat collision/response and gameplay performance.

The complete Colorado→Pacuare→Futaleufu→remaining scenes/crew/cleanup/release
queue remains active. All current sessions79716/11809/65205/82631/23762 are
terminal. About2.46GB free on C: at the latest check. Saved playable-map SHA
remains36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96.
No files deleted, saved scene promoted, final commit made, or push performed.
