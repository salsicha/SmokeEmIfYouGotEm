# South Fork: contact refinement and continuous correction paths

2026-09-11. **Still CPU-reference work, not a completed river or native game
integration.** The preceding goal turn made implementation/verification progress.
This continuation adds a reusable contact system, solver refinement, and an
actual triangle-wise path constraint. The full reconstruction queue is unchanged.

## What the completed experiments establish

Input remains the 726,900-particle `liquid-native-unified-transport-600-v4`
capture and the same registered terrain. Particle volume, identity and momentum
are not modified. The world frame and physical exterior are not enlarged.

- The former uncached v6 diagnostic was deliberately stopped (session38714,
  exit1) after two recorded geometry iterations, to replace redundant solver
  work. It was not declared finished or successful. It has no final package.
- Cached v1 (session75116, terminal0) reproduced those first two failing
  corrections. The third solve failed its unchanged KKT gate at 30,000 sweeps:
  1.63655e-5 cm versus a required 1e-7 cm. Its final pressure error was only
  2.44e-15, illustrating why an equation pass alone is insufficient.
- Warm-started cached v2 (session65250, terminal0) also failed the third solve,
  at 1.63721e-5 cm. There were **zero exactly duplicate contact rows** among its
  5,399 rows. Exact duplicate elimination is tested, but it did not cure this
  dataset's conditioning. Do not attribute the remaining difficulty to proven
  duplicate rows.
- Projected over-relaxation v1 (session90525, terminal0) reduced the third-solve
  KKT error to 6.05886e-7 cm, but still failed the 1e-7 cm gate after 30,000
  sweeps. It is retained as a failure, not promoted by relaxing the tolerance.

The cache reuses a fixed pressure factorization and unchanged Schur columns.
Changed rows invalidate the column cache; changed boundary/mobility requires a
new system. The 169 new columns in cached v1's third solve required 3.08 seconds
of preparation rather than rebuilding 5,399 columns. These CPU reference timings
are **not playable frame time or a native GPU performance claim**.

## Independent all-particle checks

`liquid-geometric-density-cached-evaluation-v1.json` evaluates the serialized
field from the failed cached v1 solve without hiding its failed solver status:

| Measurement | Before | After |
| --- | ---: | ---: |
| Represented water volume | 15,143.75 m³ | 15,143.75 m³ |
| Maximum particle-density ratio | 14.77381 | 12.69602 |
| Density RMS error | 0.265044 | 0.230289 |
| Endpoints below exact bed | 0 | 0 |
| Endpoints outside physical exterior | 0 | 0 |
| Particles below nominal 2 cm skin | 5,145 | 760 |
| Exact coincident particle pairs | 89 | 89 |

Despite the improved endpoints, 322 particles lose some of their required
preserved skin; the worst loss is 4.75131e-5 m. Density remains far too high.
The coincident markers cannot separate under one shared position-only field;
they are counted, not merged or deleted.

The deposition comparison is now localized: maximum CPU/native density
difference 0.0550715 occurs at parent cell ZYX `[8,38,496]`, a fixed correction
halo cell, not at the worst density clump. Fluid-cell RMS difference is
2.60170e-6. Native-grid represented volume is 15,143.712099 m³ versus the
particle redeposit's 15,143.75 m³. This discrepancy is reported, not silently
treated as an accepted native mass match or attributed wholly to rounding.

### Endpoint checking missed a real rock crossing

`liquid-geometric-density-swept-evaluation-v1.json` checks every straight
correction segment through the actual registered triangles. One particle,
array index219074, crosses **8.3452 mm below the bed** at fraction0.625584,
triangle248546, even though all final endpoints are above the bed.

The new `liquid_swept_bed.py` clips each segment to its triangle intervals.
Both the path and each triangle height are affine on such an interval; their
minimum clearance occurs at an interval endpoint. This avoids a distance-sampled
test that could miss a narrow ridge. Queries must remain in the guaranteed mesh
interior and bounded local search; off-mesh/unsupported paths are rejected.
This verifies **straight position-correction paths only**, not native RK2
advection, raft collision, or an entire animated simulation.

Swept contact rows use the contact-time fraction times the normal as their
Jacobian. They do not divide by a nearly zero time or move individual particles
back onto rocks. The actual full path is rechecked after a new shared-field solve.

## Implemented refinement

- Memory-local projected coordinate iteration with independently recomputed KKT.
- Cached pressure/contact system, exact duplicate-row reduction with the
  strongest bound, and validation against **all** original rows.
- Warm multipliers recompute the residual for the current system; failed
  incompatible solves cannot corrupt the cached state.
- Optional projected over-relaxation, preserving the original constraints.
- Active-set refinement after a bounded coordinate seed. Rank-deficient active
  systems do not silently discard their RHS residual or add pressure leakage.
  The initial implementation rejected a residual that was not a verified null
  direction. The revised branch uses its actual directional curvature and an
  energy-decreasing feasible step; verified unbounded null directions still
  reject incompatible constraints. Full KKT/pressure/contact checks remain.
- Start-of-run source snapshots, incremental `progress.jsonl`, retained per-step
  constraint rows and multipliers, and end-of-run source-change rejection.

## Current run and next work

### Verified single-correction geometry milestone

**Authoritative final reference:**
`tmp/south-fork-liquid-geometric-density-swept-active-v4-20260911`.
Session41482 terminal0; independent evaluator88285 terminal0. No owned jobs
remain running. All12 start-snapshotted algorithm-source hashes match, and the
run verified no source changes before finalization.

The curvature-aware active refinement resolves the difficult contact systems.
V3 passed every contact solve but, after12 geometry iterations, still missed
the swept skin by0.0642976 cm. Its frozen contact-time plane was a poor bound
at a ridge whose crossing time changed. `liquid_edge_visibility.py` now uses
the exact plane through the original particle and the raised edge. This gives
a time-independent zero-RHS inequality, verified analytically and in tests.
Every final path is still checked against the actual triangles.

V4 converges in **4 geometry iterations,217.65 seconds** (CPU reference only).
Final full contact KKT error7.80474e-8 cm and density equation error2.33147e-15
meet their original gates. The independent float32-field evaluation is
`liquid-geometric-density-swept-evaluation-v4.json`:

- All726,900 particles evaluated, zero unsupported interpolation stencils.
- Zero endpoints or full straight correction paths below the bed; zero exterior
  crossings. Minimum swept bed clearance is0.019857560055 m.
- Minimum preserved-skin margin is-5.77638e-9 m, within the existing1e-8 m
  (1e-6 cm) geometric tolerance. All309 raw negative margins are still reported;
  they are not relabeled as exact equality. There remain743 particles below the
  nominal2 cm skin versus5,145 in the input, under the documented input-preserving
  policy. This does not prove that every native particle has a2 cm skin.
- Serialized density-equation maximum error2.69711e-8.
- Represented volume remains15,143.75 m³ (floating sum difference~4e-12 m³).
- Maximum particle density14.77381→12.69585 and RMS error0.265044→0.230289.
  **Still far too concentrated; not density/volume stability acceptance.**
- The89 coincident pairs persist. No particle merging/deletion or momentum
  modification. Native world-position storage and native advection not tested.

Next: repeated density relaxation with honest evolving-phase/global-density
checks, coincident-particle handling, and a feasible native implementation.
Do not present smoothing a frozen pressure mask as a time-evolving fluid pass.
Interface correction, pressure/contact consistency, real flow budgets, rendering,
raft interaction, reference footage and playable FPS remain unverified.
No production promotion or scene completion. Latest suite: **468 liquid tests
passed**. All work below is retained as the preceding experiment history.

### Preceding experiments (terminal)

Swept-active v1 (session69272) is now terminal0 and **rejected**. Its second
solve had2,212 active rows but numerical rank2,203; the6.49621e-5 cm active
linear residual was not a verified null direction. The old refinement
correctly refused to declare convergence. Swept-active v2 (session27175) was
deliberately interrupted after a unit regression exposed a missing incompatible
system rejection; its partial output is not a completed package. That regression
was fixed and all465 liquid tests pass again.

Session28698 is terminal0, geometrically **not converged** after12 iterations:
`tmp/south-fork-liquid-geometric-density-swept-active-v3-20260911`.
Flags: `--cached --geometric-mobility --relaxation 1.8 --active-set
--swept-contact --iterations 12`.

That run's first1,521-row solve converged after a1,024-sweep seed and two active-set
pivots, with full-contact KKT error4.94e-15 cm. Actual geometry still failed:
718 swept penetrations and86 exterior endpoints, requiring more contact rows.
Later contact systems also converged, but the swept skin converged slowly.
It was superseded by the edge-clearance formulation described above.

After it becomes terminal, independently evaluate its serialized field,
including the full correction path, before attempting repeated density
correction. No repeated-step volume stability, native world-position storage,
native pressure/particle/interface coupling, visible surface, froth, raft
interaction or playable FPS has been accepted by these experiments.

Regression at that checkpoint: **465 liquid tests passed**, including six swept-bed tests.
The earlier separate mesh/registered-rock suites remain7/5 passes. No Unreal
build or engine run was performed in this continuation. The saved playable map
remains unchanged, with SHA256
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.
No scene completion, promotion, final commit or push. Colorado, Pacuare,
Futaleufu, the remaining all-scene work, crew fixes, cleanup and release checks
remain queued after unfinished South Fork work.
