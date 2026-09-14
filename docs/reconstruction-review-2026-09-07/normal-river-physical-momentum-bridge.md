# Physical momentum coordinates and unchanged-operator derivative solves

September14,2026. Previous goal turn: PROGRESS (independent reversal oracle,
retained regressions and updated authoritative plan). This turn implements a
missing coordinate/energy bridge for the conservative coupling; it does not
claim that a conservative coupled solver is finished. Full scope remains open.

## Why the conservative variables must be handled explicitly

The existing two-pole metric maps canonical velocity v to physical momentum
p=R*S*q, q=R*v, R=sqrt(h), S=c*I+sum(wj*Aj^-1), c=1-sum(wj).
Canonical momentum h*v and physical momentum p have equal **integrals** on
the periodic flat controls, but they are not the same local field. Their
rates differ locally by as much as2.383918285544306 in the current sixteen
smooth controls. Variable-bed total rates can differ as well. Treating the
canonical rate as the local physical momentum flux would introduce an error.

`physics/scripts/rational_physical_momentum_rate.py` differentiates the entire
map, including both normalizations and each actual depth-dependent pole:

    ell=h_t/(2h)
    q_t=R*v_t+ell*q
    z_j,t=A_j^-1(q_t-A_j,t*z_j)
    p_t=ell*p+R*(c*q_t+sum(w_j*z_j,t))

The transpose factor derivative is independently assembled from the geometry
tangent, not finite differences. Operator-rate terms are not discarded or
frozen. Both original pole constants, original smooth reconstructed geometry,
and40-CG remain. The code rejects malformed/unsupported inputs; it is a
positive-periodic research implementation, not dry/open/native qualification.

The Legendre-transformed energy in physical (h,p) coordinates has derivatives
E_p=v and E_h=2g(h+b)-H_h, where H_h is the existing derivative at fixed
canonical v. Consequently the same energy work must agree in both coordinates.
The conjugate variable is canonical v, not physical layer velocity u. This
identity is a check needed by a future physical conservative flux; it is not
itself a momentum/pressure flux or an energy projection.

## Tests and measured accuracy limitation

Initial `tmp/rational-physical-momentum-rate-v1-20260914.xml`:6PASS.
Controls include three2-D/singleton/short-axis shapes with rough beds,
independent factor-transpose identities, full physical-rate finite differences,
independent physical-momentum perturbations with dense two-pole metric
inversion, flat constant-mode/zero-direction controls and invalid-input rejection.

`tmp/south-fork-rational-physical-rate-v1-20260914.json` evaluates the original
sixteen64/128 profiles without changing their canonical stage directions.
The original cell-block derivative preconditioner passes12/16 energy-coordinate
gates; all four odd128 seeds fail the unchanged1e-10 scaled criterion:
2201 3.7598713031883335e-10;2203 2.9071545171177604e-10;
2205 1.9769028636318353e-9;2207 3.819661670290131e-10.
The eight flat-bed physical momentum rates still fail zero-net-force gates.

## Stronger local preconditioning, not a changed wave model

`physics/scripts/patch_pressure_preconditioner.py` builds disjoint principal
blocks of at most8x8 cells, both components, directly from the original W/V
factor coefficients. Each block has an unshifted Cholesky factor. Cross-patch
couplings are omitted ONLY in the preconditioner; full operator actions and
40-CG remain identical. No physical stencil edge is removed, no depth floor
or diagonal shift is introduced, and no result is projected. Row assembly
uses contiguous sparse-row slices rather than repeated whole-graph searches.
Memory/setup/solve cost on large/native scenes has not been qualified.

`tmp/rational-physical-patch-controls-v1-20260914.xml`:9PASS before the
equivalent row-traversal optimization. Tests compare principal blocks against
independent basis actions, require exact original full-operator actions,
positive symmetric preconditioning, and small full residuals.

`tmp/south-fork-rational-physical-rate-patch-v1-20260914.json`: all16 original
energy-coordinate gates pass with patched **derivative** preconditioning.
Worst coordinate discrepancy4.296563105299356e-14; worst derivative solve
residual2.144837722380508e-14. This fixes the measured derivative-solve accuracy
defect; all eight physical momentum failures remain. Primal/source evaluations
still use the original solver and the original canonical stage is untouched.

Important remaining measurement limit: some128-cell finite-difference probes
of the original primal solves become noisy as epsilon shrinks; worst finest
probe error6.1519329319637e-7. The improved derivative residual alone is not
proof that all original finite-difference probes pass. A same-operator improved
primal reference is needed to separate this remaining numerical error before
relying on tight pointwise derivative comparisons at128.

The audit captures implementation hashes before and after execution. The
v1 block and v1 patch reports intentionally retain their earlier file hashes;
the final patch v2 audit repeats all sixteen profiles after the equivalent
linear-cost row traversal change. Default original block behavior remains an
explicit control; nothing is switched in a recorded history or gameplay.

Current full physical failures from the previous turn (momentum, rest force,
reversal and reflection) remain mandatory. The initial combined bridge suite
`tmp/physical-momentum-bridge-all-controls-v1-20260914.xml` is37PASS/16FAIL
before adding the fourth128 accuracy regression (seed2201); see the v2 report
for the final combined result. No xfail or looser tolerance is used.

Final `tmp/physical-momentum-bridge-all-controls-v2-20260914.xml`:
**38PASS/17FAIL,47.90s**, process74762 terminal exit1. The17 failures are
four retained original block-accuracy cases plus the13 existing physical
momentum/rest/reversal/reflection failures. All four patch-accuracy cases pass.
Process49902 completed the patch v2 audit successfully; all16 result records
are exactly identical to patch v1 after the row-traversal optimization. The
v2 report records the final implementation hashes. All new short jobs ended.

## Next real implementation work

Use physical conservative (h,p) transport and the above full two-pole energy
variables to derive local compatible momentum/pressure stress. Do not reuse the
frozen donor-pressure transpose, identify h*v with local physical momentum,
replace the model by single-pole shallow water, center all mass fluxes without
positivity, or globally project energy/momentum. Keep bed force, wave response,
positive donor transport, both poles, all physical/energy/time/dry/open gates.
The bridge is supporting implementation, NOT a finished alternative model.

The conservative split-form lead in
[Ranocha/Ricchiuto sections3 and6](https://arxiv.org/html/2408.02665v3)
was rechecked; its classical SGN guarantees cannot be transferred automatically
to this two-pole reconstructed wet/dry model. No such replacement was made.

## Full-river/source status

Both independent9200/local24000 cook audits pass:
`tmp/south-fork-expanded-9200s-state-v1-20260914.json` and
`tmp/south-fork-expanded-9200s-banks-v1-20260914.json`.
5,382,400 finite cells;86,720 artificial-bank cells exactly dry. Maximum
depth3.778196305m, speed6.233357583m/s. Outflow101.677527207 versus
inflow45.306954547m3/s remains unsettled. Original cook continues to10000;
next complete9300/local26000 requires BOTH audits, no source/boundary change.

All five original handles were directly verified live this continuation.
417/422 guarded files each checked unchanged. Original histories were not
reset, restarted, suspended or spliced. Physical high-speed/history failures
are not excused by mass closure. Terrain/native motion/froth/contact/30FPS,
later rivers in the requested order, remaining reviews/crew/normalization/
regressions/release/commit all remain open; no completion or promotion claim.
