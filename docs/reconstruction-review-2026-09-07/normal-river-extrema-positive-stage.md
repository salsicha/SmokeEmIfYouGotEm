# Extrema-preserving transport and coupled evolution controls

September 14, 2026. Previous turn: PROGRESS (isolated MC transport accuracy
failure, positive mass/adjoint primitive, complete 9000-second cook audits).
This turn changes research code only. No native/source-history/terrain/material
or gameplay changes, no original job restart, no final commit. Full goal open.

## Reconstruction correction

Read the primary paper with the PDF skill:
[Sekora and Colella, Extremum-Preserving Limiters for MUSCL and PPM](https://arxiv.org/pdf/0903.4200),
section 2.1, equations 35-51. The implementation uses that slope limiter with
the published C_VL=1.25, not the paper's complete MUSCL/PPM algorithm. The
curvature checks distinguish smooth extrema from inconsistent neighboring
curvatures. The paper explicitly does not guarantee positivity; the river
candidate needs its own positive reconstruction and transport constraints.

`extremum_preserving_transport.py` adds the EP slope to the donor mass primitive.
Depth endpoints are constrained by |dh| <= 2h without altering cell averages.
Hydrostatic face cuts still compare the two reconstructed bed sides. The
original MC pressure geometry is NOT changed. New transport geometry therefore
differs from the old MC transport; this is not claimed to preserve the original
FV evolution or automatically qualify a physical dispersive river model.

Differences are computed before adding depth and bed, and sign comparisons
avoid product underflow. Cancellation-prone cut polynomials are reevaluated
using rational arithmetic on the same represented inputs and limiter. No
depth floor, wet/dry threshold, state clamp or energy projection is introduced.

An initial five-cell wet mask unnecessarily flattened an extra near-bank band.
The new regression caught face depth 2.0 instead of the original 2.5. Retained
failure: `tmp/extremum-preserving-bank-stencil-v1-20260914.xml`. Corrected behavior
uses EP on connected five-cell support, original MC on connected three-cell
support, and the original zero slope when immediate dry support interrupts it.
It neither looks through a dry gap nor widens the original flattened band.

The unchanged original 32/64/128 smooth mass-rate test now has errors
0.00075004146, 0.00017211067 and 0.00004100385: ratios **4.35790 and 4.19743**,
both above the unchanged 3.2 gate. Additional tests span 16 phases, both flow
directions and both axes; square discontinuity, rational slope oracle,
2^-500 positive depths, dry barriers/inflow, and adjoint work also pass.
These are tests of the candidate, not removal of the old MC failure.

## Coupled stage

`positive_rational_velocity_stage.py` couples this mass transport T to the
existing dual-energy reverse depth gradient a. At each frozen state:

    h_t = T u
    v_t = -(T^T a)/h - curl(v) J(u)

The normalized transpose uses the same donor faces as T, with owner depth
cancelled algebraically. Since the canonical energy gradient is h*u, their
work cancels; the rotational term remains pointwise work-free. Both original
poles, 40-CG solves and the independent actual-direction chain-rule check
(1e-10 scaled gate) remain. No post-hoc correction forces the result to zero.
This is an energy-work pairing, not proof of a Jacobi identity, physical
asymptotic equivalence, entropy/shock closure or correct dry pressure.

All 16 original synthetic smooth profiles at 64/128 cells pass the original
three-probe energy-direction test and final 1e-7 gate. Largest final errors:
1.065813e-9 (64) and 6.892265e-8 (128). Keep the larger result and finite-solve
layer-velocity recovery error 7.985898e-8 at 128; no bit-exact source-velocity
claim. Original synthetic state hashes and canonical conversion are retained.
These profiles are NOT captured South Fork river histories.

`tmp/south-fork-positive-rational-stage-v1-20260914.json` records the initial
stage audit, before the RK2 addition and near-bank correction. The final-code
audit is recorded separately, not overwritten, at
`tmp/south-fork-positive-rational-stage-v2-20260914.json`: all 16 gates and the
unchanged refinement gate pass with the final code. Initial mean shared-load stage
cost is 0.240947 s at 64 cells and 0.401306 s at 128: FAR outside the native
1.6 ms gate. This is not an Unreal FPS measurement or performance acceptance.

The final combined controls retain the old MC transport test and report
**45 PASS / 1 FAIL in 10.68 s**:
`tmp/positive-rational-stage-all-controls-v2-20260914.xml`. The sole failure is
the original MC 2.597618 ratio; the candidate passes that unchanged test.
Earlier 40 PASS / 8 FAIL and other model failures remain separate and unresolved.

## Actual short evolution exposes another unresolved defect

`rk2_step` executes both SSP-RK2 constituent stages. Each must obey its own
donor draining bound and remain strictly positive for the existing pressure
primitive. Invalid trials raise; there is no reset, clipping, retry shortcut
or energy projection. Tests compare it to explicit constituent stages and
verify mass, unchanged inputs and rejection behavior. Exactly dry pressure is
still explicitly rejected, despite passing mass-only dry tests.

`audit_positive_rational_evolution.py` evolves ALL eight original 64-cell
synthetic smooth states to 0.008 s using 4/8/16 fixed steps. This is a new short
diagnostic, NOT the requested 9-second moving-source history. The first run
completed all 24 trajectories with positive depth and tiny mass residuals,
but temporal accuracy is NOT established:

| Seed | Consecutive depth L1 ratio | Canonical-velocity L1 ratio |
| --- | --- | --- |
| 2200 | 3.99874 | 4.00184 |
| 2201 | 3.52396 | 2.25542 |
| 2202 | 4.00047 | 4.00099 |
| 2203 | 3.82092 | 2.20595 |
| 2204 | 3.99972 | 3.99912 |
| 2205 | 3.93720 | 2.81633 |
| 2206 | 3.49721 | 3.98966 |
| 2207 | 2.08331 | 2.47961 |

Ratios compare consecutive endpoint differences when halving dt, not errors
against a known solution. Several are far from the expected second-order
factor four. Seed 2203's energy error grows from 6.7406e-10 at 8 steps to
7.1133e-9 at 16, despite instantaneous stage work staying near roundoff.
No monotonic energy-convergence or full-evolution pass is claimed.

Retained initial report: `tmp/south-fork-positive-rational-evolution-v1-20260914.json`.
Final bank-corrected implementation completed a separate rerun:
`tmp/south-fork-positive-rational-evolution-v2-20260914.json`. All 24 endpoint
hashes are identical to v1; the bank correction does not alter these fully wet
trajectories. Minimum final depth is 1.0211176848 m, maximum mass change
2.498002e-16 m3, maximum instantaneous stage energy rate 3.108625e-15.
The temporal defects above persist, not just the passing results.

Next investigate the
temporal regularity/branch changes on the SAME profiles and probes, then exact
dry-pressure and boundary qualification. Do not hide these results by shortening
the horizon further, replacing states, weakening gates or splicing another
model into any original history.

All terrain, boulder/collision/hydraulics, visible waves/breaking/froth/contact,
30 FPS/p95 33.333 ms, remaining rivers, crew and release requirements remain.
Physics 120 Hz and solver 1.6 ms unchanged. South Fork remains the scenario;
Troublemaker remains an embedded rapid, not a menu entry.

At finish all five original long-job handles are directly live. Cook 83142 is
at 9055.5 s/local21110. Latest complete9000 still has BOTH audits passing but
is unsettled; next9100/local22000 requires BOTH audits after completion.
Both original dependency guards rechecked:417/422 files, zero changes. All
new short research/test handles are terminal; no unfinished extra run is left.
