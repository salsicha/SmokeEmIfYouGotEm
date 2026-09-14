# Reconstructed pressure/traction geometry — September 14 UTC

Follow-up: [integrated trace and shared bottom quadrature](normal-river-shared-bottom-pressure.md)
addresses the measured pressure-transfer and bottom-kinematic accuracy defects
in an explicit static research variant. Default/native physics remains unchanged;
time-dependent pressure and full-history qualification are still required.

The previous goal turn made progress: it removed a nonconserving unused edge
weighting and verified exact top/blocked pressure-column integrals. This turn
implements their static assembly on the ORIGINAL unscaled second-order MC
h/eta polynomials. It also finds and records a pressure-transfer accuracy
limitation. No native, nonlinear-history or playable promotion is justified.

## Static assembly and signed adjoints

`physics/scripts/reconstructed_pressure_geometry.py` calls the existing MC and
hydrostatic reconstruction, including its exact-arithmetic fallback. It does
not replace the raster geometry, flatten additional slopes, add a depth floor,
or change transport. External pressure lifts and time derivatives are not yet
implemented; nonperiodic static actions use homogeneous algebraic boundary rows.

The research pressure transfer holds mean column pressure q=P/h and bottom B
constant inside each cell. At its reconstructed face height Hf, the uncut
integrated pressure is P*Hf/h. Because H varies linearly across the MC cell,
this preserves the cell-average integrated pressure P. A reconstructed column
of zero height carries zero integral without dividing by that height.

Using the exact quadratic profile integral, each one-sided cut traction is

`Ta = Aa*Pi + Ca*Bi`, `Tb = Ab*Pj + Cb*Bj`,

where `Aa=(Ha/hi)*r_a^2*(3-2r_a)`,
`Ca=-Ha*r_a^2*(1-r_a)`, and r_a=fa/Ha (similarly for b).
Zero reconstructed faces give zero coefficients. The two cell-depth weights
are kept separately: own=hi/(hi+hj), other=hj/(hi+hj). Only physical endpoint
rows and singleton axes are excluded; there is no boolean wet-face threshold.

Assemble one shared pressure `F=other*Ta+own*Tb`, each owning blocked-column
correction, and the within-cell bed term B*(deta-dh). Their oriented difference
simplifies to the cell operator, for each axis:

`L_i = [own_i*(Tb-Ta)_right + other_left*(Tb-Ta)_left`
`       + (dh_i/hi)*Pi + (deta_i-dh_i)*Bi] / dx`.

The local P term is essential: it is the pressure variation across the original
within-cell column polynomial. The local B term retains the within-cell bed
traction. Omitting either is not this assembly. Adding the old independent
B*geometric-bed-gradient force would count a second bed-traction discretization.

The code derives D and E from these SAME coefficients, so
`L(P,B)=-D^T P+E^T B`. E is generally nonlocal, not merely a pointwise bed slope.
Tests verify the signed adjoint identity, equivalence to explicit shared flux +
blocked-face + within-cell assembly, unchanged input arrays and bed-datum
translation, uniform-column agreement with the original operator, and flat
periodic momentum conservation with nonzero original MC slopes. A small dense
matrix check verifies the completed-square acceleration algebra is SPD; that
is not a nonlinear energy-invariant or evolution test.

The SGN momentum equation contains both integrated-pressure gradients and
bottom-pressure traction; see Gavrilyuk and Shyue's
[2D elliptic-operator formulation](https://www.math.ntu.edu.tw/~shyue/mypapers/sgn_jhe2023.pdf),
Eqs.1 and7. That source does not prove the pressure transfer proposed here valid
at wet/dry faces. This assembly and its qualification are project-specific.

## Original captured wetting edge: static limit

`tmp/south-fork-recorded-pressure-geometry-v1-20260914.json` completes against
the exact original trace/binary/history and the prior48-iteration wetting bracket.
V2 reruns the same calculation after adding the accuracy warning to the module.
V2 report SHA256:
`a9bf8a76b1727fdf719bb9a6bf35e19ad100e5c89ffd527d97c041eeba7e1061`.
The original native failed-history input hash is
`0114ce4611375f4e169e077d36747754306b867e67fa44bf7858ca5566f6bf10`.
The consumed bracket-report hash is
`dc8c0afd281a699810d38ec433d57889bfc19bb5f8156dcdd12506f6cb9b3ef4`.

The audit computes one OLD left-side pressure field and then holds it and the
left-side velocity fixed. Only the geometry changes across the bracket. No
new pressure equation is solved. The homogeneous static boundary rows are not
claimed to implement the original prescribed pressure trace.

At y22/x102, ha0.03481288m and hb6.0494857e-7m remain positive while fa changes
0->7.8054086e-19m. The owning pressure coefficient Aa changes0->1.5081086e-33;
Ca changes0->-1.7500535e-35. The neighbor remains fully open with Ab1/Cb0.
The within-cell bed coefficient is-0.25324267169854187, not discarded.

Across the source state difference1.7763568e-15, the frozen-pressure action
changes[1.7347235e-18,0] at the owner and at most4.6629367e-15 over the domain.
Frozen-velocity D/E changes are at most1.3502088e-11 and6.3560268e-15.
The largest signed-adjoint relative discrepancy is2.0470254e-16.
Source arrays are made read-only and checked unchanged afterward.

This removes the finite jump from this STATIC geometry response; it does not
establish stability of the pressure equation, its forcing or time integration.
The original full nonlinear history still fails and has not been replaced.

## Accuracy limitation — do not promote on static passes

`tmp/south-fork-pressure-geometry-refinement-v2-20260914.json`, SHA256
`f83d6bdb3ab7039a0b30459f63fa207e0a422266788fb90ea603cd8a1b0ef2ed`,
compares manufactured smooth fields on32,64,128,256,512,1024 periodic cells:

`h=1+0.2sin(x)`, `bed=0.1cos(x)`,
`P=0.7sin(2x+0.3)`, `B=cos(3x)`, x in[0,2pi).

The exact operator is P_x+B*bed_x. The report retains all L1/L2/maximum errors
and observed orders for the candidate and original pressure stencil. It also
tests P=1/B=0, with both the varying bed and a flat-bed control.

The candidate does NOT exactly annihilate constant integrated pressure on a
variable-depth flat bed. Its maximum error is0.0177497 at32 cells,0.00229966 at
256 and0.000575222 at1024. Refinement shows roughly first-order maximum error,
order1.5 L2, and order2 L1, concentrated near the MC depth extrema. The flat-bed
control isolates the pressure transfer, not bottom-force clipping, as sufficient
to produce the defect. Original constant-P gradient is zero.

For the nonconstant manufactured pressure, candidate maximum error at256 cells
is0.00207087 versus0.000610243 for the original stencil. This is not permission
to weaken a pointwise accuracy gate or advertise a bulk norm as full second-order
qualification. The module explicitly carries the limitation, and a regression
test ensures the audit reports it rather than issuing a false pass.

Next resolve the pressure-profile transfer's constant-integrated-pressure/local
accuracy defect while preserving the column moment, zero-height/closing-face
limit, original MC geometry and momentum/adjoint identities. Simply reverting
to P_face=P keeps pressure on a vanishing reconstructed column, while arbitrarily
normalizing cut coefficients can reinstate a nonphysical closed-face connection.
Neither is qualified. Then derive D_t/E_t from the actual FV mass rate and
differentiate the original geometry; implement the compatible nonlinear force
and prescribed boundary lifts, with range-factored acceleration solve. The exact
dry-owner/MC wet-stencil transition remains a separate continuity gate.

## Verification and remaining scope

Session98821 passes210 pressure/provenance/boundary/30FPS checks in18.44s,
including18 new geometry tests and the previous192 tests. This includes explicit
tests recording the known accuracy limitation, not210 physical acceptance gates.
The static captured probe and refinement audit complete separately. No native
build, gameplay change, screenshot, new reference-video inspection, performance
measurement or final commit. Desktop30FPS/p9533.333ms, physics120Hz and solver
1.6ms gates remain unchanged. Last gameplay18.899245FPS/p9570.33ms still fails.
Troublemaker remains inside South Fork; all later-river/crew/release work remains.

The unchanged full-river cook74818/PID41820 completed7200s/local24000. BOTH
`tmp/south-fork-expanded-7200s-state-v1-20260914.json` and
`tmp/south-fork-expanded-7200s-banks-v1-20260914.json` pass:5,382,400 finite cells,
86,720 exactly dry artificial-bank cells, max depth3.808975954m, max speed
6.216878015m/s. Outlet111.205419127 versus inlet45.306954547m3/s still indicates
settling; no source promotion. Next COMPLETE7300s/local26000 needs BOTH audits.
No cook restart or pause. All local numerical probes/tests are terminal.
