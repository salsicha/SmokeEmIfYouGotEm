# Local reverse depth gradient — research speedup, no gameplay promotion

September14,2026. Previous goal turn: PROGRESS (derived dual-energy primitive
and rotational closed stage; original eight smooth states and23 reference tests).
This turn removes the per-cell basis solve from the research stage while
retaining the independent directional check. No native/source/terrain/material
or original history edits. Desktop30FPS/p9533.333ms, physics120Hz unchanged.

## What changed

`physics/scripts/reverse_rational_depth_gradient.py` accumulates the dual-energy
adjoints to `aa`, `ab`, `own`, `other` and `shared_b` on each original pressure
face, then reverses the local MC/cut reconstruction into depth inputs. Explicit
mass-normalization and fixed-normalized-velocity terms are included. The original
physical bed-slope term remains in the D/E adjoint; no bed derivative is invented.

Forward branch decisions use rational values of the original represented inputs
and their actual mass direction. Reverse adjoints use floating arithmetic: this
is an analytic derivative, NOT a bit-exact output claim. Tied MC/cut branches
follow that actual direction, not a branch average. Periodic singleton and
two-cell aliases are tested. No dry-state epsilon, floor or pressure tolerance
change. The function explicitly rejects dry and open domains.

`reverse_rational_velocity_stage.py` keeps the same research model, flux,
rotational bracket, original two-pole solves and40-CG gates. It replaces the
basis gradient with the local reverse gradient. The assembled depth gradient
is STILL checked against an independent `PressureGeometryRate` evaluation on
the actual stage h_t, using the original1e-10 relative/absolute scaled check.
Failure rejects the stage; it does not project or correct the energy.

The old expensive basis implementation is retained unchanged as an independent
control. The reverse stage no longer has its64-cell basis-size restriction,
but no larger-domain or runtime qualification is inferred from that fact.

## Independent verification

Eight reverse tests pass: full gradient/stage comparisons for3x4,1x7 and2x4
domains; weighted face-adjoint identity against the original directional
coefficient rates; tied branches; unchanged variable-bed resting lake; and two
positive-owner rough-bed fixtures with blocked/partial cut columns.
Combined suite **31PASS8.15s**, retained at
`tmp/reverse-rational-combined-controls-v1-20260914.xml`.

`audit_reverse_rational_stage.py` runs all eight ORIGINAL smooth states with
their original hashes and explicit original-layer-velocity to canonical
conversion. At64 cells it evaluates both basis and reverse, alternating call
order by seed. Maximum differences:

- Depth energy gradient:1.7763568394002505e-14.
- Canonical velocity rate:4.973799150320701e-14.
- Depth rate, flux and recovered layer velocity:exactly identical in all pairs.
- Reverse vs independent actual-direction chain rule:1.7763568394002505e-15.

The original three state-space probes are retained. All eight64-cell and all
eight128-cell reverse cases pass the original1e-7 final energy-direction gate.
Maximum final errors are3.552718e-10 and6.892265e-8, respectively. The larger
128-cell error is retained; do not report only the smaller cases. The128-cell
run has no basis comparison (that reference explicitly rejects >64 cells).

Reports:
`tmp/south-fork-reverse-rational-stage-64-v1-20260914.json` and
`tmp/south-fork-reverse-rational-stage-128-v1-20260914.json`.
Reports hash the measured implementation. An explicit early dry/periodic input
rejection was added afterward; the final31-test run includes it. The valid-domain
derivative and timed algorithm were not changed by that validation addition.

## Measured cost, correctly scoped

All eight paired64-cell reverse calls are faster, in both call orders:
mean basis6.2658276s, reverse0.2206627s, ratio28.3955; smallest per-pair ratio
16.5416. Mean reverse128-cell stage0.4379773s. The reference evaluator,
original five long jobs and other short controls share the machine; this is
not isolated benchmarking and certainly not an Unreal FPS measurement.

The local graph has5,380–5,444 nodes at64 cells and roughly twice as many
at128 cells in these profiles. There are no per-cell pole solves in the
reverse gradient, but the expensive rational graph and independent directional
check remain. Hundreds of milliseconds for128 cells is FAR outside the1.6ms
production solver gate. No cost acceptance or main-game performance gain.

## Next required work

The new closed model still changes original FV transport and has no positivity,
wet-bank, shock/breaking, open-boundary or time-evolution qualification. Earlier
40PASS/8FAIL and the old forcing's energy failures are NOT superseded by the
new stage. Do not splice it into any original moving history or native gameplay.

Next develop positive, second-order face transport with its matching energy
adjoint, then qualify exact dry-state and boundary flux handling. Energy
cancellation alone does not establish correct physical/asymptotic behavior or
an entropy/breaking closure. Retain both pole dispersion and rotational flow.
Full actual-source time integration and moving-window qualification, native
cost, visible waves/froth/contact, terrain and remaining rivers/crew/release
remain mandatory. No reinterpretation of small closed tests as the goal.

All five original handles directly confirmed live at turn start. Cook83142
subsequently advances to8969s/local19380 unchanged;9000/local20000 is not yet
complete and requires BOTH audits when ready. Latest complete8900 still passes
both state/bank audits but remains unsettled. Both guards rechecked:417/422
files, zero changes. No restart, suspension, final commit or goal completion.
