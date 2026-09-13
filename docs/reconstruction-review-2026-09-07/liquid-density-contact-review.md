# South Fork: density correction with geometric contact

2026-09-11. **CPU reference work, not native integration or scene acceptance.**
Continued by [contact refinement and continuous paths](liquid-density-contact-refinement-review.md).
The live-process statements below describe the prior checkpoint, not current
process state; the follow-up records their terminal outcomes and the current job.
The preceding user-status turn was informational/no progress. This continuation
resumed the unfinished numerical experiment, verified its actual process state,
and changed/tested the implementation. South Fork and the entire later queue
remain incomplete. No saved-map change, promotion, final commit, or push.

## Fixed input and purpose

The input is `liquid-native-unified-transport-600-v4`: all 726,900 captured
particles, all twelve owners assembled into one 498 × 170 × 24 parent field.
The registered terrain and captured particle volume are unchanged. This work
does not improve the provenance of the inferred submerged bed or relocate rocks.

The native input already has a worst particle-density ratio of 14.77 and a
declining outflow. A divergence-free velocity field alone did not remove this
particle clumping. The prototype tests a separate **position** correction;
particle identity, volume and momentum remain unchanged. It is not a replacement
for fixing native pressure/contact, interface consistency or source/outflow.

The position-density split follows the motivation in Kugelstadt et al.,
[Implicit Density Projection for Volume Conserving Liquids](https://animation.rwth-aachen.de/media/papers/66/2019-TVCG-ImplicitDensityProjection.pdf).
Our centered derivative pair and contact solve are project-specific adaptations,
not a claim that the paper's MAC method has been implemented unchanged.

## Implemented and checked

- Density-target support in the existing matched divergence/gradient reference.
  The correction RHS is limited, but measured density and particle mass are not.
- Solid contribution to the particle kernel integrates the actual registered
  bed rather than filling missing liquid with extra particles.
- Off-grid contact inequalities constrain a shared interpolated displacement
  field. No individual particle pushout or deletion is used by this prototype.
- A sparse pressure elimination followed by a unilateral contact solve avoids
  treating every detected contact as a compulsory equality.
- The independent evaluator reads the serialized field, checks every particle
  against the exact bed and exterior, and redeposits all represented volume.
  It does not silently rescale a coupled contact solution after solving it.
- The temporary SciPy installation is workspace-local. Its initial import
  failure was sandbox access to installed files; elevated tests imported the
  real package successfully. SciPy is not an Unreal runtime dependency.

## Evidence and rejected attempts

| Experiment | Result | Consequence |
| --- | --- | --- |
| Solid integration, orders 2 → 4 | Maximum difference 0.218761 | Coarse sampling not accepted around steep rocks. |
| Adaptive 8/16/32/64/128 integration | No columns unresolved at successive-order threshold 0.001; maximum retained estimate 0.000999045 | Numerical agreement estimate only, not a certified integral error bound. |
| Density-only correction | Density 14.77381 → 12.85759; 225 below-bed endpoints; 7 exterior crossings | Reject as physical correction. |
| Alternating density/contact projection, 12 iterations | Maximum equation error 0.0054145 | Does not meet 0.00001 equation gate. |
| Matrix-free joint equality attempt | 800 iterations failed; tensile contact multipliers | Reject; use unilateral contact solve. |
| Direct contact solve, v2 | Two geometry iterations; equation error 2.61e-15 | Requires independent serialized-position check. |
| Serialized v2 | 61 tiny below-bed endpoints, 2 newly outside; maximum equation error 3.01e-8 | No physical pass despite converged equations. |
| Nominal 2 cm contact, v4/v5 | Incompatible fixed-geometry constraints | Preserve and report pre-existing captured skin discrepancies; do not shift the bed. |

The v2 independent evaluation retained 15,143.75 m³ before and after, with zero
unsupported interpolation stencils. Density RMS error fell from 0.265044 to
0.232511, but maximum particle density remained 12.85759: still unacceptable
as corrected liquid. The minimum serialized clearance was -3.02e-9 m. Tiny
violations are recorded rather than converted into proof of containment.

The captured minimum bed clearance is 1.985756 cm, not exactly the native
contact's nominal 2 cm. The revised reference requires the nominal skin where
the input has it; otherwise it requires preservation of the input clearance.
Both nominal-skin failures and any loss of preserved clearance are reported.
This explicitly does **not** prove that every native particle has a 2 cm skin.
An inward field-storage guard is reported separately; it does not move the bed
or enlarge the exterior, and does not yet verify native world-position storage.

## Current comparison and remaining work

The current comparison keeps the same input and clearance policy:

- v6: solid displacement nodes fixed, nearby fluid components constrained by
  exact contact rows instead of additional axis-aligned neighbor locks.
- v7: original axis-aligned mobility, with the same coupled contact inequalities.

v7 is terminal and rejected: contact row 272 has effectively zero remaining
freedom after pressure elimination (Schur diagonal -5.42e-20), yet requires
0.133351 cm of correction. This is not a nominal-skin rounding discrepancy.

v6 is still running as Python session **38714**, process **32132**. The first
equation solve converged but created 722 below-bed endpoints and 86 exterior
crossings. Its second solve has 5,230 contact rows, 2,203 active multipliers and
20,235 dual sweeps; it reduces these to 13 below-bed endpoints and 4 exterior
crossings. Minimum clearance is still -4.876684 cm. The equations pass, but
geometry does not. Re-poll this same live session; do not restart on a timeout.
No variant is approved for native use on that evidence.

The slow CPU contact loop also motivated a separate memory-local implementation
in `liquid_contact_dual.py`. A 2,200-row, 30-sweep synthetic comparison gives
identical multipliers, 0.176677 s original versus 0.101348 s contiguous. Both
properly report nonconvergence at that bounded iteration count. Five focused
tests pass, including redundant unilateral contacts and fixed incompatibility.
The new loop additionally recomputes the dual residual rather than trusting its
incremental update. It is **not yet wired into the live v6 solver**: keep that
run's source immutable until terminal, then integrate and verify it. These
timings are not native performance or playable FPS.

Next: finish the comparison, reject any geometry/storage failure, then test
repeated correction and native feasibility. A single reduced-density snapshot
does not establish volume stability over time. The game still needs native
pressure/contact and particle/interface consistency, one visible evolving
surface, froth/spray, raft coupling, realistic motion and playable frame time.
Later rivers, crew work, cleanup and release checks remain in the original queue.

## Retained artifacts

- `tmp/south-fork-liquid-density-projection-20260911`
- `tmp/south-fork-liquid-density-projection-refined-v2-20260911`
- `tmp/south-fork-liquid-geometric-density-schur-v2-20260911`
- `liquid-geometric-density-schur-evaluation.json`
- v3 is an incomplete output: JSON serialization failed; never use as a package.
- v4/v5 record failed solves; v6/v7 are separate comparison outputs.

Latest completed full numerical regression: **438 liquid tests passed**; separate
mesh-sampling suite: **7 passed**. No Unreal build/test was run in this
continuation. Saved playable map SHA256 remains
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.
This includes the oblique-contact test (5 sparse-solver tests total) and the
new dual-loop tests. The captured-rock registration suite has 5 passing tests.
