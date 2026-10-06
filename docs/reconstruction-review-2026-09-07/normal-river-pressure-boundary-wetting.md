# Prescribed pressure boundaries and the wetting direction — September 14 UTC

This turn is progress: prescribed velocity/time-rate boundaries are integrated
into the research pressure correction, and actual-source nonlinear directional
probes locate the remaining zero-depth arithmetic problem. There is still NO
base-state dry-transition closure, original-start candidate history, native
integration or playable acceptance. No source repair or acceptance change.

## Prescribed boundary implementation

`ReconstructedPressureGeometry.prescribed_divergence_lift` reuses the original
packed west/east/south/north velocity and partial-time-rate convention. It adds
an affine divergence source and its derivative; homogeneous D/E and pressure
adjoints are unchanged. E's physical bed moment already uses the constructor's
original exterior bed. This is the original prescribed-velocity condition,
not a transparent-wave boundary claim.

`kinematic_forcing` now includes the lift in D*u and its time derivative, and
`nonlinear_pressure` passes through the supplied trace. Fifteen new tests cover
uniform through-flow, singleton axes/cells, accelerating flow, the need for
trace time derivatives, variable-bed finite-difference material identities,
affine boundary work, source immutability and invalid/missing traces.

On both sides of the original captured wetting bracket, maximum divergence
lift is8.49120146355775 and maximum time-rate lift is0.011115744130237333.
The calculated affine work and expected boundary work both equal
583.8553579303695, with stored error0. This is a discrete boundary-work check,
not a reference-motion or wave-reflection qualification.

## Full conserved-state direction, not a depth-only perturbation

`audit_directional_pressure_limit.py` tests h/hu/hv + epsilon*(original FV rate)
at epsilon1e-8,1e-16,1e-24 seconds, with the original tangent, dispersion
fraction and boundary traces held fixed. These are sensitivity directions,
NOT accepted timesteps or independently recomputed-FV evolution. No old dry
mass rate is dropped. The fourth captured channel remains preserved in the
original capture and is not fabricated as a fourth hydraulic derivative.

The first wrapper invocation (session51662) rejected its mismatched4-channel
capture/3-channel FV shapes before any pressure probe or report write. The
caller was corrected to pass the three hydraulic columns, as the existing
CPU transport requires. Session66176 then completed exit0 and wrote
`tmp/south-fork-shared-bottom-directional-pressure-v2-20260914.json`, SHA256
`955facaffcea28bd32d6943df1d89bc42e3f707cdc4b7520a5bbb5025617fa3a`.
It retains the original trace/source/binary hashes. Six tests cover entering
momentum, exact source preservation and invalid/unrepresentable directions.

The pressure-force maximum tends from8.643717407045996 to8.643717269411345
at y69/x80, y component. Successive maximum field changes are3.203703977661121e-7
and1.3322676295501878e-14. The larger pole has relative residual about6.1051e-8
and physical residual7.0250e-8 at40 iterations; the smaller pole about2.7e-16.
Maximum Q and C approach1414.5733679885402 and123.16347707604936.

At activating cell123/94, entering velocity is approximately
[3.035210202796457e-7,0.007241208637458807]m/s. At124/94 it is approximately
[-1.1724648367872896e-22,0]. These finite entering velocities matter even though
their source mass rates are3.3850534930413954e-52 and1.314378540211901e-66.
The base-state pressure function STILL rejects these dry activations.

IMPORTANT: domain-force convergence does NOT prove the dry-cell force tends to
zero. Cell123/94's x-force is-3.80537e-72,-2.49401e-74,-9.95018e-74 across the
three probes: non-monotone at the smallest sizes. Dividing the final force by
its actual depth3.38505e-76 gives acceleration[-293.944654,-27.333725]m/s2.
The intermediate user-facing suggestion of vanishing dry force was explicitly
qualified after inspecting these numbers. No uniform dry-limit pass is claimed.

The report's inherited top-level narrative still says boundary lifts were not
implemented and describes only the frozen baseline. Its nested prescribed-
boundary and directional subreports are the actual new evidence. Those stale
descriptions were corrected afterward in the scripts; the immutable report
was not rewritten. No numerical kernels changed in that description update.

## Exact cancellation audit explains the probe limitation

For an exactly dry cell, the EXACT linear ray
(h,m)=epsilon*(h_t,m_t) has u=m_t/h_t and u_t=0. Independently rounded depth and
momentum need not lie exactly on that ray, and subsequently rounding m/h adds
another error. Neither is permission to reset a conserved state or residual.

`audit_conserved_ray_cancellation.py` reproduces the saved depths/velocities
from the original source and decomposes the ACTUAL represented residual using
exact rational arithmetic. It does not rerun pressure or change any input.
Report `tmp/south-fork-conserved-ray-cancellation-v1-20260914.json`, SHA256
`5644f7081c5672757b1bf49d3f98793df94ba6e7cb9fa3b3c3b4d9025495bfc6`, completed
exit0. Five tests distinguish conserved-state and primitive-velocity rounding.

At123/94 and epsilon1e-24, the y-momentum residual due to stored state alone is
2.592131823869384e-70; velocity-division rounding adds1.3259605372606734e-70.
The actual residual is3.9180923611300575e-70. Dividing by the represented depth
gives u_t about765758 from stored-state error alone, or1157468 with the rounded
velocity, although the exact unrounded linear ray has u_t=0. Using an exact
quotient alone therefore would not cure this limiting probe. These numbers
explain why ever-smaller floating-point perturbations cannot establish the
desired uniform dry closure. They are not a license to repair real FV states.

## Next implementation and verification

Derive the analytic one-sided original-MC geometry/cut/weight limit directly
from conserved state and actual FV direction, including finite entering m_t/h_t
as a separate limiting trace. Do NOT store an epsilon-depth state or replace
an actual nonzero mass/momentum rate. Preserve exact leading-order conservative
cancellations before normalization. Check the mass-weighted wet-block and
force limit, rather than assuming raw D or the zero-mass normalized block is
continuous. Retain rejection for unsupported/invalid directions until that
extension is implemented and checked against the saved probes and independent
fixtures. Prescribed boundaries now exist but still require full-history tests.

The combined suite passed265 tests in5.54s before the five cancellation tests,
which separately pass in0.29s. Counts are overlapping implementation/provenance
checks, not completed physical acceptance gates. No new engine build, motion
capture, reference footage or gameplay performance measurement occurred.
Final combined run after all changes passes270 tests in6.14s. All local test
and diagnostic sessions are terminal; only the full-river cook remains live.

Both7400s/local28000 full-river audits pass:5,382,400 finite cells and86,720
exactly dry artificial-bank cells. Outlet108.82185815453806 versus inlet
45.30695454719997m3/s remains unsettled. The same cook74818/PID41820 is verified
live at7418.5s/local28370; next COMPLETE7500s/local30000 needs BOTH audits.
Desktop30FPS, physics120Hz, solver1.6ms, all scene/terrain/wave/froth/crew/later-
river/release requirements and final commit remain open. Last gameplay still
18.899245FPS/p9570.33ms, not a30FPS pass. No promotion or source-state repair.
