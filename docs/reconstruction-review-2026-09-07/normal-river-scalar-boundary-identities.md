# Independent scalar/work identities and a boundary failure — September 14

The previous turn made progress by finding three failures in94 unchanged
controls under the candidate scalar derivative. This turn separates changed
algebraic assumptions from an independent physical consistency defect.
No existing test, operator, native library, material or running replay changed.

## Explicit face-matrix assembly

`physics/scripts/audit_difference_scalar_identities.py` assembles D and E from
individual face/cell contributions using explicit indices. It does not call
the production vectorized actions to construct those matrices. With pressure
gradient G=-D.T, define sigma=G1 and the candidate A by

`A(f) = G(f) - f*sigma`.

This explains why A annihilates constants yet no longer equals the negative
transpose of D. The pressure traction stays `L(P,B)=G(P)+E.T(B)` and satisfies

`<u,L(P,B)> + <P,D(u)> - <B,E(u)> = 0`.

The ordinary scalar action instead satisfies the distinct identity

`<u,A(f)> + <f,D(u)> = -<f,u dot sigma>`.

The audit independently reproduces the nonzero right-hand side; it does not
relabel it as zero pressure work. Periodic and prescribed-boundary fixtures
give scalar-work identity errors8.33e-17 and5.55e-17; original pressure-work
residuals stay below1.67e-16. Explicit matrix/vectorized action differences
remain below8.89e-16.

## Material time derivative

For d=D(u)+the prescribed affine divergence lift, e=E(u), and the actual
acceleration a=u_t+(u dot A)u, the candidate's construction gives

`Q-D(a) = d*d - partial_t(d) - u dot A(d)`

`C+E(a) = partial_t(e) + u dot A(e)`.

Independent matrices at h+epsilon*h_t and u+epsilon*u_t, with the prescribed
trace advanced by its supplied time derivative, check the partial-time terms.
At epsilon1e-4 the maximum errors are3.97e-12 periodic and8.15e-12 prescribed.
The larger1e-3 errors decrease under refinement. These controls explain the
changed material identities without modifying the three original failed tests.
They are NOT a proof of mechanical-energy balance or continuum boundary accuracy.

## Independent analytic boundary check: FAIL

For constant positive depth on a flat bed, use f(x)=x on cell centers in[0,1].
Its exact derivative is1 at EVERY point, including both domain-edge cells.
The candidate returns0.5 at both endpoints and1 in the interior for8,16,32
and64cells. The endpoint error stays0.5 under refinement. Constants remain
exactly zero, showing why a constant-null test alone was insufficient.

This is an actual missing boundary treatment, not an old-test assumption or
floating-point discrepancy. The candidate is not qualified for the finite
moving river window, even if its short retained history has lower velocities.
The current pressure adapter supplies exterior bed and prescribed normal
velocity/time-rate to D's affine lift; those inputs do not supply a scalar
boundary contribution to A. Correcting scalar boundary closure must retain the
original source traces and establish physical consistency through wet/dry
support, rather than silently using periodic wrap, a slope cap or a zero slope.

Report `tmp/south-fork-difference-scalar-identities-v1-20260914.json`.
Initial three independent diagnostic tests PASS0.93s, including a test requiring that
the known affine boundary defect remains marked UNQUALIFIED. A passing test
that detects this failure is not a physics acceptance pass.
An added directional-dry-support check reproduces the original failing fixture:
the scalar work defect matches the independently assembled `-u dot sigma`,
while physical pressure remains zero in dry cells and retains its original
traction. Combined four identity checks plus six existing scalar-gradient
checks:10 PASS1.54s. The three broader original control failures remain failures.
Audit script SHA256
`5db525057458b909870ca30d7143857bf87e3ae3fd2ac222231c0e8640e007df`.

## External consistency reference and next action

Ranocha and Ricchiuto derive mass/energy-preserving SGN discretizations using
complete split forms and summation-by-parts operators, not a pressure-adjoint
check alone. [Primary paper](https://arxiv.org/abs/2408.02665).
This supports requiring a complete work/boundary analysis; it does not prove
this project's mixed operator correct or authorize replacing the requested
two-pole model with a different approximation.

Next derive the finite-window scalar boundary action from retained input
traces and independently verify affine/smooth fields, physical pressure work,
wet/dry validity and full moving history before native/gameplay promotion.
All full-project visual, terrain, hydraulics,30FPS, crew, later-river, release
and final-commit requirements remain open.

Final direct polls confirm59896/95666/97152/83142/41566 LIVE. Main59896 last
0.663617900s/speed33.063211m/s; observer97152 saved0.466666691s/speed30.279665m/s;
candidate41566 saved0.491666691s/speed7.263400m/s. These are partial histories,
not equivalent states or full9.066667s/two-move acceptance. All417 original and
422 candidate guarded scripts rehashed unchanged. Complete8400/local8000 cook
passes BOTH state/bank audits but remains unsettled; next8500/local10000 needs
BOTH audits. No running process was paused, reset, stopped or replaced.
