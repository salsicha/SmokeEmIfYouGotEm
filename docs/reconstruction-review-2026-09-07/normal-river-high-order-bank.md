# Higher-order total-depth bank control — September 12

Research-only continuation of [paired mean/bed capture](normal-river-paired-mean.md).
No Unreal source, shader, map, material, save, or ordinary-play defaults changed
in this work. Desktop target remains 30 FPS; the last measured build remains
21.571211 FPS / p95 52.6052 ms, NOT a pass. No fresh video playback or engine
motion acceptance. The full remaining goal stays active.

## Same difficult input, higher-order accuracy

All actual-bank trials below start from the SAME valid 15-second snapshot
`tmp/south-fork-paired-strain-input-v1-20260912/live_01.json`, including its
simultaneously captured bed. Reports retain the four input hashes. No easier
state or invented flat terrain replaces the original comparison.

`total_depth_bank_replay.py --second-order` reconstructs depth, free surface and
velocity with MC slopes, preserves face-average momentum using opposite-depth
velocity weights, and applies a matching within-cell bed source. The cell-average
bed and conserved h/hu/hv are not repaired. First-order remains the default
control. Both modes use reflecting box boundaries and SSP-RK2.

The underlying hydrostatic construction follows
[Audusse et al.](https://publications.imp.fu-berlin.de/478/1/file_2004_siam.pdf).
Known shallow/slope limitations are discussed by
[Delestre et al.](https://arxiv.org/pdf/1206.4986), and thin-film reconstruction
and velocity bounds by [Skevington](https://arxiv.org/pdf/2106.11273).
These sources motivate checks; they do NOT prove this implementation correct.

## Rejected trials remain evidence

Reports are `tmp/south-fork-total-depth-mc-bank-vN-20260912.json`; successful
integration writes `.total-state.npy`. Completion alone is NOT acceptance.

| Trial | Change | Five-second result |
| --- | --- | --- |
| v1 | Independent depth/surface/velocity reconstruction | Completed; 2,659 steps, 2,510 retries, final max speed 61.8107 m/s. Rejected. |
| v2 | Cell-constant bed | Completed; 1,729 steps, 1,567 retries, 34.9088 m/s. Rejected. |
| v3 | Also preserve face-average momentum and bound face velocities | Completed; 1,759 steps, 1,601 retries, 36.1598 m/s. Rejected. |
| v4 | Reconstructed bed and centered source, retaining old eta slope restriction | 600 steps, no retries, 7.9480 m/s. NOT accepted: the restriction suppresses thin-film gravity. |
| v5 | Remove inappropriate eta slope/depth restriction | Completed; 1,770 steps, 1,552 retries, 51.1358 m/s. Rejected. |
| v6 | Datum-independent face differences | Completed; 1,757 steps, 1,536 retries, 49.2137 m/s. Rejected. |
| v7/v8 | Local partially dry polynomial treatment; v8 adds failure-state export | Both stop at 2.441666667 s, 293 steps. v8 records 23 rejected trials, dt 9.934107463e-10 s. Rejected. |
| v9 | Cancellation-safe Rusanov transport weights | Completes 5 s in 600 steps, no retries; final max speed 7.96322 m/s, peak accepted-state speed 8.01637 m/s, volume error 0 m3. Admissibility control only. |

The v3 failure was NOT confined to effectively empty cells: its final maximum
36.1598 m/s occurs at depth 0.116018 m. About 1.589 m3 travels above 20 m/s.
Global energy still decreases, so a global energy-only check cannot dismiss
these local failures. v4's thin-film defect was exposed independently by a
constant-thickness film on a linear bed; the expected initial acceleration is
exactly -g times the slope, regardless of film thickness.

The partially dry treatment classifies the original reconstructed hydrostatic
faces. It uses the balanced cell average only where an owning wet cell has a dry
face, then rebuilds the shared flux. It is local and has no depth threshold or
speed cap. An attempted repeated neighbor-flattening variant failed the thin-film
gravity regression by propagating artificial bed steps across the domain; that
variant was removed before actual-bank use. This remains an experimental local
treatment, NOT a proven wet/dry high-order scheme or a production substitution.

## Exact roundoff failure and cancellation-safe flux

v8 preserves the last admissible state, reports the implementation SHA, and
identifies the last rejection. Its final maximum speed was only 7.92285 m/s and
the initial CFL bound was 0.0104224 s. The rejected forward stage instead affects
cell (x6,y119), world (-5463,3630) m, which has exactly zero h/hu/hv. Its derivative
is (0, 1.0947644252537633e-47, 0): momentum arrives but mass cancels to zero.
This happens at both dt=1/120 and dt=1e-9. It is a different cell from the
original frozen-mean bank failure, on the same captured input.

The Rusanov flux is now factored as

`F = 0.5*(s+uL)*UL - 0.5*(s-uR)*UR + pressure`.

The transport weights evaluate the two candidate signal-speed differences
BEFORE combining velocity with sqrt(g*h). This avoids subtracting two rounded,
equal speeds in tiny water and ties momentum transport to the same positive
mass transfer. It is an algebraic reformulation, not an added film, height
repair, dry momentum deletion, or relaxed timestep floor. Six regressions cover
1e-20, 1e-40 and 1e-100 m films with both spatial orders, including exact expected
incoming mass, bounded incoming velocity, successful advancement and conservation.

Additional regressions cover lake at rest, the original two-cell bank
counterexample, dry-bed dam break, 200/400-cell finite-amplitude analytic-wave
convergence, face-average momentum/bounds, thin-film gravity, exact invariance
under a 1e6 m vertical-datum shift, and last-admissible failure preservation.

The final v9 implementation SHA is
`8884688e8b2c666b8654e078d1cfe39d27ce3a88246f850cc351eb31b6634c86`.
Its five-second depth range is [0, 3.667002811] m. Energy per density decreases
from 107363.250940 to 102945.432960 m5/s2; its maximum across accepted states is
the initial value. These are closed-box numerical diagnostics, not proof of
physical dissipation, reference-matched river motion, or production acceptance.
The finite-amplitude wave mean-height error falls from 4.544123152e-5 m at 200
cells to 1.116861613e-5 m at 400 cells (ratio 0.245782). All 18 targeted tests
and all 71 focused water/capture/performance/release-parser regressions pass.

A same-implementation 20-second replay also completes:
`tmp/south-fork-total-depth-mc-bank-long-v1-20260912.json`, 2,401 accepted steps
(including the final floating-point time remainder), zero retries. Final depth
range [0, 3.433207097] m; final max speed 6.185904415 m/s; peak accepted-state
speed 9.172819992 m/s; volume error 9.094947018e-13 m3. Final energy per density
94692.274797 m5/s2, with its run maximum still the initial value. This longer
closed-box control supports continued development; it does not test moving
boundaries, actual river forcing, dispersion or breaking-wave realism.

## Still required

The control has no finite-depth dispersion, forcing, evolving mean/window
coupling, or foam. It cannot replace the requested playable surface. Validate
the corrected higher-order bank control before adding consistent finite-depth
pressure and coupling, then test actual engine motion and rendered/contact
agreement. Terrain/boulders/collision, other rivers in order, crew, normalization,
performance, release qualification and the final commit remain unfinished.

The ongoing full-river cook was not restarted. Its 2800 s checkpoint passes BOTH
integrity and artificial-bank audits, but outlet 90.8091 versus inlet 45.3070
m3/s still indicates settling. Runtime remains on the previously audited 600 s
state; 2900/local18000 is the next checkpoint requiring both audits.
