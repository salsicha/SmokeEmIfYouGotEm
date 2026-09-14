# Two-pole variational stage — research only

September14,2026. Previous goal turn: PROGRESS (independent exact dry-face
oracle, connected-energy counterexamples, completed8900 cook audits).
This turn develops an energy-based alternative stage rather than another
precision/scalar tweak. No playable solver, source, material or terrain change.

## Reference boundary and scope

[Duchene and Klein, equations SGN/WGN and their conserved quantities](https://arxiv.org/html/2005.13234v2#S1.SS2)
distinguish layer velocity from the velocity variable in the Hamiltonian
formulation and give nonlinear terms tied to a modified energy. Their work is
one-dimensional and flat-bottom; it does not validate this repository's
cut-cell geometry, finite two-pole approximation, dry banks or breaking model.
The [authors' implementation background](https://waterwavesmodels.github.io/WaterWaves1D.jl/dev/background/#The-Whitham-Green-Naghdi-system)
also explicitly distinguishes those velocities and the associated elliptic
relation. These motivate the approach, not a claim that our proposal is WGN
or inherits a published stability result.

All formulas and discrete tests below are our own development for the existing
reconstructed response. The original nonlinear acceleration blend and all
original failed assertions remain unchanged.

## Derived dual-energy primitive

New `physics/scripts/rational_dual_energy_reference.py` uses the ORIGINAL
pole lengths, weights, factored pressure geometry and40-CG residual gates.
Write `A_j=I+lambda_j*(W.T W+3/4 V.T V)` and
`S=(1-sum(w_j))*I+sum(w_j*A_j^-1)`.
For canonical vector v, define `q=sqrt(h)*v`, `z_j=A_j^-1*q`,
`F=sqrt(h)*S*q`, `u=F/h` and proposed energy
`H=1/2*q.T*S*q + sum(g*h*(h/2+b))`, with cell area included.

At fixed canonical v the depth-direction derivative is
`q_t.T*S*q - 1/2*sum(w_j*z_j.T*A_j,t*z_j) + potential_t`.
The factor derivative uses original D/E and their actual mass-direction
derivatives, without dense derivative matrices or a projected energy correction.
This is the Legendre-dual quadratic form of the existing inverse-response
metric. It does not prove the old acceleration blend conserves that metric.

Seven initial tests pass: inverse-metric dual equality, both exact pole
constants, three independent state-direction finite differences, factor
direction, original discrete dispersion, and explicit dry/open rejection
(some checks share tests). Initial test collection had a missing parenthesis;
the failed v1 XML remains. Fixed v2 passes. An initial audit serialization
error was also corrected; it produced no completed v1 report.

The original eight64-cell smooth profiles are converted with
`v=invsqrt(h)*K*sqrt(h)*u`, not relabeled. Maximum recovered layer-velocity
error1.969536e-13; primal/dual energy discrepancy1.421085e-14. All eight
depth-direction checks meet the original1e-7 gate at epsilon1e-5; maximum
error9.241333e-10. Omitting the pole-operator variation gives errors from
0.01328883 to0.24417493 in these cases. These terms are necessary for this
proposed energy derivative; they are NOT a scalar correction to add to the
old momentum equation.
Report: `tmp/south-fork-rational-dual-variation-v2-20260914.json`.

## Rotational closed stage

New `rational_velocity_bracket_reference.py` uses `a=H_h`, `F=H_v=h*u`:

```
h_t = -div(F)
v_t = -grad(a) - curl(v)*J(u),  J(u)=(-u_y,u_x)
```

Periodic central grad/div are paired adjoints. Their energy work cancels;
`F dot J(u)=0` cancels the rotational work pointwise. This does not require
restricting v to an irrotational field. No damping, energy projection, source
reset or pressure-pole substitution is applied.

The depth gradient is currently assembled with expensive basis directions,
limited explicitly to64-cell controls. The full actual h_t directional
derivative is checked against the assembled gradient: a mismatching MC branch
rejects the stage, rather than repairing its energy. This is not a general
proof of differentiability at all limiter/cut transitions.

Five stage tests pass, including three random genuinely2-D rotational states,
independent finite-difference energy directions, paired adjoints, mass balance,
variable-bed resting lake, and control-size rejection. Combined reference
suite **23PASS4.96s**, report
`tmp/rational-variational-combined-controls-v1-20260914.xml`.

All ORIGINAL eight64-cell smooth states are also tested, with unchanged
source hashes and converted original layer velocity. Maximum instantaneous
energy-rate magnitude1.332268e-15; all net mass rates exactly zero in these
eight records. At the original epsilon1e-5, independent state-space derivative
error is at most3.552719e-10, all eight below the unchanged1e-7 gate.
Report: `tmp/south-fork-rational-velocity-bracket-v1-20260914.json`.

## Not a replacement for the requested river solver

This stage CHANGES transport relative to original FV. The maximum mass-rate
difference on the original profiles is0.050473529876. Central flux has no
positivity, shock, breaking or open-boundary qualification. There is no time
integrator, preserved full original trajectory, physical wave validation,
wet-bank support, conservative moving-window transfer or native mode here.
64-cell stages take4.35–6.63 SECONDS under shared load, not milliseconds.
That is far outside the production solver budget, not an optimization claim.

The earlier40PASS/8FAIL and positive rational-metric rates for the OLD
forcing remain visible; these new directions do not supersede them. Do not
splice the proposal into original histories or mark dry-front gates passed.
The changed nonlinear model still requires physical/asymptotic consistency,
not merely a skew-work identity. The published WGN result does not certify it.

NEXT: replace expensive basis derivatives with exact local reverse accumulation,
verify its branch handling against the independent directional primitive, and
develop consistent positive/wet-bank transport plus boundary energy flux before
time-evolution qualification. Preserve rotational flow and both pole responses.
Then original-source moving histories, wave/breaking/froth/contact, native cost
and actual playable/rendered checks remain mandatory. No smaller control replaces
those requirements or the complete South Fork/later-river/crew/release goal.

Both replay guards checked:417/422 files, zero changes. All five original job
handles directly live this turn; no restart or suspension. Latest complete
cook8900 passes both audits but remains unsettled; next COMPLETE9000/local20000
needs BOTH audits. Desktop target30FPS/p9533.333ms, physics120Hz. No new FPS
measurement, visual acceptance, final commit or goal-completion claim.
