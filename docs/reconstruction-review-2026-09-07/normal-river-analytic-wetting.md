# Analytic conserved-direction wetting force — September 14 UTC

This turn is implementation progress. The explicit research pressure path now
evaluates an analytic first-wetting force on the original zero-depth state,
and a retained original-start CPU replay has been launched. Neither that
launch nor the local limit tests establish history, physical, native, cost or
playable acceptance. No source depths, momentum rates, timestep or gates changed.

## Direct geometry and conserved limits

`PressureGeometryRate(..., one_sided=True)` evaluates the right original-MC
branch on the support h>0 or (h=0 and actual h_t>0). Its separate coefficient
values and derivatives are bound to `DirectionalPressureGeometry`; using them
with the old dry-stencil geometry is rejected. Original depth/bed arrays stay
read-only, including their exact zeros. No epsilon state is created.

On a zero reconstructed column opening as H=t*H_t and R=t*R_t, r=R_t/H_t gives
the finite A limit r^2*(3-2r), A_t=0, C=0 and C_t=-H_t*r^2*(1-r). A stationary
zero column retains zero coefficients. Invalid directions and a positive owner
with an identically zero reconstructed column are rejected. When both owning
depths are zero but their mass rates sum positive, the limiting depth weights
are h_ti/(h_ti+h_tj) and h_tj/(h_ti+h_tj), with zero weight derivative on the
linear ray. No mass rate is discarded or converted to native FP32 zero.

`nonlinear_pressure(..., dry_treatment='directional_limit')` is explicit opt-in;
the default still rejects dry activation. Entering m_t/h_t is a SEPARATE finite
velocity trace, not a value stored in an originally dry cell. Scalar G=-D^T
can act on that trace, while physical pressure/bottom pressure still must be
zero at original h=0. Prescribed divergence lifts use the same directional
trace support. Both D_t and E_t remain in the nonlinear Q/C forcing.

For the exact linear conserved ray (h,m)=t*(h_t,m_t), the partial-time derivative
of m/h is exactly zero before normalization. The finite Q/C and Adv terms have
h^(3/2)*Q, sqrt(h)*C and sqrt(h)*Adv tending to zero. This is evaluated
analytically at zero mass, NOT by overwriting a residual from a rounded positive
depth state. Already-wet cells retain their actual conservative rate terms.

## Zero-mass auxiliary block versus physical wet block

The raw D/E limit can have nonzero zero-depth rows. The normalized zero-mass
auxiliary block does NOT generally tend to identity. The research solve instead
projects exactly zero-mass rows and solves the positive-mass block. For this to
be valid, coupling to that block must vanish in the limit; this is explicitly
tested rather than asserting full-matrix continuity. No positive-depth row is
projected, and nonzero coefficients reaching a zero-mass column from a positive
row remain errors.

The new tests verify coefficient/derivative limits, scalar/physical domain
separation, signed adjoints, positive-mass matrix-block convergence and
zero-mass decoupling, flat/variable-bed nonlinear force limits, exact source
preservation and default/invalid-direction rejection. The matrix test retains
all probes2^-8,2^-16,2^-24 and adds2^-32: error2.20758e-8 at2^-24 did not yet
meet the unchanged1e-8 test threshold. The additional refinement satisfies that
threshold and the required convergence ratio; no threshold was relaxed.

These tests concern admissible linear conserved directions. They are not a
general wet/dry theorem, positive pressure-column proof, or evolved-history
qualification. Higher-order activations and later reconstructed states must be
handled by the unchanged evolution gates, not silently inferred acceptable.

## Original captured source comparison

Session65350 completed exit0 and wrote
`tmp/south-fork-analytic-wetting-force-v1-20260914.json`, SHA256
`0dfea909361ac8145674dace965738826cd07cedcc409d41637c87474989980a`.
Source SHA256 remains
`0114ce4611375f4e169e077d36747754306b867e67fa44bf7858ca5566f6bf10`.
The same trace/binary/wetting bracket is retained; the analytic force is evaluated
on the original zeros, not on an initialized perturbed state.

Maximum analytic pressure force is8.643717269411345 at y69/x80, y component.
All originally dry force rows are exactly zero, and both actual positive dry
mass rates are retained. Maximum field differences versus the represented-ray
probes1e-8,1e-16,1e-24 are3.2037039643384446e-7,1.6986412276764895e-14 and
1.865174681370263e-14. Larger-pole residual is6.105096310016504e-8 (physical
7.024991676532656e-8) at40 iterations; smaller-pole residual2.689425867897165e-16.
This agreement supports this analytic source-direction test only.

Raw geometry-limit differences include ab/own/other up to1, from newly enabled
zero-mass traces. These are NOT claimed roundoff-small geometry changes.
The physical force comparison above is the relevant measured limit. The old
tiny-cell represented-ray acceleration discrepancy remains preserved in its
earlier reports; it was not repaired or relabeled as an acceptable history.

A wrapper test also exposed a missing physical-residual key for a zero-RHS
solve. The report now records the mathematically zero residual for that case.
That reporting fix and a guard against applying unbound one-sided derivatives
follow the saved source comparison; they do not alter its evaluated nonzero-RHS
force. Final combined regression suite passes282 tests in6.31s.

## Requested-endpoint history and diagnostic prefix are running

`reconstructed_pressure_adapter.py` swaps only the process-local research
pressure call and supplies the original exterior bed. FV transport, unscaled
reconstruction, SSP-RK2, pressure residual gate2e-5, minimum timestep, boundary
interpolation and same-instant ownership transfer remain in their original
implementations. Adapter tests verify unchanged uniform transport and cleanup
after failures. Nothing is installed in Unreal.

The first harness, session95666 / `replay_reconstructed_owner.py`, reuses an old
comparison runner whose target is the FAILED retained clock2.325785777831797s.
Its prefix `tmp/south-fork-reconstructed-owner-history-v1-20260914` is therefore
DIAGNOSTIC, not full requested-history evidence. This scope defect was found by
reading actual source metadata, not by timing out. The earlier description as
a full-target run was corrected. It remains live with23 pressure calls at last
observation; no prefix success or accepted interval is inferred from that count.

The original request source is
`tmp/south-fork-qualified-range-owner-v1-20260914.json`, SHA256
`bf20b0b6c467b78d5d1b02a7174f502e1de3cba89996ee7f3b32cf0dfe5736ec`.
Its80 observations match the failed-source record exactly. The actual requested
endpoint is9.066667139530182s with TWO moves:3.4666668474674225s and
9.066667139530182s, the latter exactly at the requested endpoint. Its completed
state is not used as an interior reset or new-model accuracy truth.

Continuing the failure-time prefix would inherit a shortened final step at its
artificial endpoint, so it cannot establish the original full timestep schedule.
The corrected `replay_requested_reconstructed_owner.py` starts a separate
continuous original-start history using the actual requested endpoint and all
source brackets. It verifies the reached clock AND both ownership moves, even
the same-instant endpoint move. Three tests explicitly reject the old truncated
target, mismatched sources and false completion after an original rate failure.
No existing output or interior state was deleted/reset; the prefix is retained
separately and is not substituted for this required run.

MAIN live session59896 writes prefix
`tmp/south-fork-requested-reconstructed-history-v1-20260914`.
Source start0.06666667014360428s/origin[-5450,3566] is unchanged. Its first
accepted step reaches0.07500000347693761s, dt1/120,0 rejects, maximum speed
6.930827045660083m/s and mass residual2.0070056727661267e-13m3. First-stage
pressure reports8 activating dry cells; second stage2. Both solve at40 iterations,
with larger-pole residuals5.059797653177101e-8 /7.176441404866014e-8. First step
takes70.15s wall in this slow exact reference; this is NOT a capacity/FPS pass.
Full target/history/accuracy remains unproved. Final combined tests pass285
in6.71s; separate existing nonlinear/finite-depth suite78 in23.29s.

Both runners write `.progress.jsonl`, then terminal `.json` and `.last-state.npy`.
DO NOT edit their implementation dependencies while either runs: they record
start hashes and checks for changes at completion. Poll the same session/file;
do not restart on observation timeout. If it fails, inspect the saved retained
state and failure under the original gates. If it completes, it still requires
independent physical/reference accuracy and native/history agreement.

The separate full-river cook74818/PID41820 remains live at7516s/local30320.
BOTH7500s/local30000 audits pass,5,382,400 finite cells and86,720 exactly dry
bank cells. Outlet109.11651572113369 vs inlet45.30695454719997m3/s remains
unsettled. Complete7600s/local32000 requires BOTH audits.
Desktop30FPS/p9533.333ms, physics120Hz, solver1.6ms and source fidelity are
unchanged. The slow exact CPU reference is not a cost or30FPS pass. All terrain,
crest/froth integration, actual motion/reference comparisons, later rivers,
crew, release checks and final commit remain open. No new gameplay capture.
