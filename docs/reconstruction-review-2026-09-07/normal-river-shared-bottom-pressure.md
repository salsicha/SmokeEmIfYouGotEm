# Integrated pressure trace and shared bottom quadrature — September 14 UTC

The preceding goal turn made progress by implementing a static original-MC
pressure/traction operator and exposing its constant-integrated-pressure error.
This continuation addresses that error and the corresponding bottom-kinematic
accuracy, without promoting a new pressure solve or evolved/playable history.

## Explicit research variants; existing defaults retained

`ReconstructedPressureGeometry` now accepts explicit research choices:

- `pressure_trace='integrated_column'`: holds integrated P and bottom B constant
  in a cell's uncut pressure trace, rather than stretching P with H_face/h.
  The local P/h*dh term is consequently zero. The original MC h/eta geometry
  and its exact face-arithmetic fallback are unchanged.
- `bed_quadrature='shared_bottom'`: interpolates one bottom-pressure trace
  `B_face=own*Bi+other*Bj` for both one-sided cut profiles, with the original
  cell-depth weights. It then fixes the diagonal from the physical constant-B
  bed-slope moment, as derived below.

The previous mean-column/polynomial variant remains the default research
control, including its documented defect. None of these options is wired into
`rate`, the native solver, raft contacts or playable presentation. Original
terrain/source arrays, FV hydrostatic source/transport, limiter and timestep
have not changed. The shared-bottom option IS a new nonhydrostatic bed-source
quadrature; it is not claimed to preserve the previous within-cell pressure
source integral unchanged.

## Why the bottom quadrature must preserve both moments

Keeping integrated P constant fixes the flat-bed constant-P defect exactly, but
alone does not remove the manufactured variable-bed peak errors: at256 cells
the maximum force error is still0.0020485863. The reconstructed within-cell bed
slope and interface bed jumps enter the old polynomial quadrature differently
at MC extrema. Fixing only a force diagonal could move the error into the
transpose kinematics. The new quadrature preserves both sides.

For cut-profile B coefficients Ca/Cb and depth weights own/other, using the
same B_face on both sides yields the symmetric off-diagonal coefficient

`k_face = own*other*(Cb-Ca)`.

Set the diagonal using the original physical geometric bed-slope field s,
not a fitted error, cutoff or smoothed depth. For each horizontal component:

`(E_component v)_i = s_i*v_i`
`  + [k_right*(v_right-v_i) + k_left*(v_left-v_i)] / dx`.

The off-diagonal k coefficients are unchanged by this diagonal moment choice.
Thus each component operator is symmetric and BOTH `E(1)=s` and `E^T(1)=s`.
The pressure/bed force is still `L(P,B)=-D^T P+E^T B`, using the same E in
kinematics. Consequently:

- Constant bottom pressure gives the physical geometric bed traction.
- Constant horizontal velocity gives the corresponding bottom velocity.
- The summed B-force is exactly the discrete sum of B times the geometric
  bed slope (to arithmetic accuracy); symmetric neighbor exchanges cancel.
- The same completed-square static acceleration matrix remains SPD.

This is a moment-consistent research source quadrature, not a post-solve force
correction or a proof of nonlinear energy conservation. The physical validity
of its reconstruction through breaking, steep steps and wetting still needs
the original full-history/reference tests. No artificial viscosity or pressure
deactivation has been introduced.

## Refinement and captured-source evidence

`tmp/south-fork-shared-bottom-refinement-v2-20260914.json`, SHA256
`1da6252fbf039d9328e6eedddfbae445d159df53e384435f876059c7b5a2ba35`,
retains the same32→1024-cell manufactured fields from the preceding audit and
adds the independent D/E kinematic errors. It does not replace the older failed
variant's report. Constant integrated P on the variable-depth FLAT bed now has
exactly zero force at every tested resolution.

| Cells | Shared-bottom maximum force error | Original-stencil maximum error |
| --- | --- | --- |
| 32 | 0.0401225657 | 0.0386205511 |
| 64 | 0.0099497903 | 0.0097327172 |
| 128 | 0.0024699250 | 0.0024403245 |
| 1024 | 0.0000381973 | 0.0000381537 |

Maximum force convergence is second order across the tested refinements,
including the former MC-extremum failure. For manufactured velocity
u_x=0.6+0.1cos(2x), u_y=0, D and E errors also converge overall at second order.
The E maximum order varies with limiter alignment (including1.800833 over
128→256 and2.078078 over256→512); every measured order is retained. This is
not a claim of exact order2 between every pair of grids or full wave/history
accuracy acceptance.

`tmp/south-fork-shared-bottom-recorded-v1-20260914.json`, SHA256
`57dede9c7f65b6e94caac21dd96158b612e6f3ff1acd5c294118c7bd407a72b1`,
uses the original trace/binary/failed-history source and wetting bracket. As
before, one OLD left-side pressure field and velocity are held fixed: no new
pressure equation is solved. The native failed-history source SHA remains
`0114ce4611375f4e169e077d36747754306b867e67fa44bf7858ca5566f6bf10`.

At y22/x102, the opening coefficient Aa goes0→1.5081086e-33 and shared k goes
0→3.0409882e-40. The physical y-bed slope is-0.5064849853515625m/m. Across the
original1.7763568e-15 state difference, the frozen-pressure action changes
exactly[0,0] at the owner and at most1.7763568e-15 over the domain. D/E changes
are at most6.9556583e-12/2.2204460e-16. The signed-adjoint relative discrepancy
is at most2.1204742e-16. Static homogeneous pressure-boundary rows are still
not a qualification of new prescribed pressure lifts. This report precedes a
docstring-only clarification of the shared-bottom rule; numerical kernels are
unchanged by that clarification.

## Closing-face limits: what is and is not proved

At a closing hydrostatic cut with positive uncut height, the integrated trace
still uses the exact quadratic profile integral and tends to zero quadratically.
It never assigns finite pressure to a zero reconstructed column with a positive
owning cell: that invalid trace input is rejected. No depth floor is added.

A distinct joint limit occurs when the ORIGINAL MC raw face approaches zero
as its neighboring cell dries. In that case a one-sided constant integrated P
divided by H_face can diverge. It is not legitimate to call that one-sided
profile bounded. The new tests instead inspect the actual weighted shared
flux for bounded cell means, using an original-MC family whose owning depth
stays1 and neighboring depth epsilon tends to zero. Its shared flux is
5*epsilon/(1+epsilon) and tends to zero, including the exactly dry endpoint.
Dyadic cases extend through2^-1070 without silently losing the nonzero shared
flux or introducing a floor. This is a specific bounded-mean flux limit, NOT
a uniform pressure-profile theorem or a full dry-owner evolution proof.

An initial decimal-epsilon test exposed existing MC face subtraction roundoff:
at epsilon1e-12 the stored face is9.999778782798785e-13. The exact analytical
5 bound cannot be imposed on that rounded face as if it were epsilon. That
arithmetic is preserved and explicitly tested, not repaired by this pressure
model. Exact-bound tests use dyadic input families; the shared flux itself
continues to satisfy its bound on the original decimal inputs.

The earlier warning against blindly assigning constant P to a zero-height
face remains in force. The current choice has an explicit rejection there,
and separately tested shared-flux limits on admissible reconstructed states.
Actual evolved pressure columns and raw-face pinches still require qualification.

## Verification and next implementation

Session14512 passes220 pressure/provenance/boundary/30FPS checks in14.33s,
including10 new shared-bottom tests and the previous210 checks. These are
overlapping regression/diagnostic tests, not220 complete physical gates.
New checks cover both constant moments, signed adjoints, net bed force, SPD
algebra, flat pressure response, cut/raw-face limits and measured force and
kinematic refinement. All local probes and tests are terminal.

NEXT derive the actual-FV-mass-rate derivatives of the pressure geometry:
the depth weights, cut coefficients A/C and shared k, with the matching
diagonal moment derivative. Feed the SAME D_t/E_t into the nonlinear Q/C
forcing; implement compatible normalized/range-factored acceleration solve
and the original prescribed pressure lifts. Diagnose the retained MC wet-stencil
switch at exactly dry owners explicitly. Do not drop E_t, normalize coefficients
ad hoc, skip pressure, reset history or replace the original source trajectory.
Only then run original-start full-history stability, physical/reference accuracy,
cost/capacity and native/contact/playable qualification.

The original unscaled native history still fails; no new one has been evolved.
Last gameplay18.899245FPS/p9570.33ms still fails desktop30FPS/p9533.333ms.
Physics120Hz, solver1.6ms, source fidelity, scenario/menu requirements and the
full later-river/crew/release goal remain unchanged. No new screenshot, footage
inspection, gameplay/FPS acceptance or final commit. Cook74818/PID41820 is
directly verified live past7238.5s; latest complete audited state remains7200s.
Next COMPLETE7300s/local26000 needs BOTH state and bank audits; no restart.

## Geometry rates and exact-dry source probe

Research `reconstructed_pressure_rates.py` now differentiates the original MC
polynomials, cut A/C, depth weights and shared bottom coefficient, pairing the
resulting force derivative with D_t/E_t. Nonlinear Q/C includes BOTH geometry
rates. Exact directional limiter ties and positive-part boundaries have focused
tests, along with finite differences, signed adjoints, constant bottom moments,
subnormal positive films and source immutability. The stationary-dry-set tangent
rejects a positive mass rate at an exactly dry cell; it does not zero that rate.
The broad suite passed238 tests in10.51s before the structured dry-limit reporting
helper was added; a later focused rate/frame-budget suite passed28 in1.06s.
The helper has actual-source execution coverage but no dedicated unit suite yet.

Actual-source report `tmp/south-fork-shared-bottom-mass-tangent-v2-20260914.json`
was written by session33419, which correctly EXITED1: neither bracket side has
a qualified tangent. Independently recomputed CPU FV rates at dry cells
y123/x94 and y124/x94 are3.3850534930413954e-52 and1.314378540211901e-66.
Both recorded native stages store zero there. These CPU rates round to zero in
FP32, but the audit retains them and does not substitute native rates to pass.

Read-only h+parameter*h_t probes at1e-12,1e-20 and1e-28 seconds retain all
positive rates and freeze the original pressure/velocity. These are sensitivity
directions, NOT trajectory timesteps. Original MC dh and deta changes approach
1.2893460741393746e-10 and0.002433776823235098. The maximum frozen-velocity
D change remains0.08469855809468334 across all three probes. Frozen-pressure
action changes are3.3459901516152968e-12,1.262852332563716e-112 and
1.2628523325637162e-120; E changes are2.781108676686017e-13,0,0.
Thus this test exposes a nonvanishing raw kinematic change, NOT a finite
frozen-pressure-force jump. It does not establish which weighted wet/dry
extension is valid, a pressure solution or nonlinear stability. No rate, state,
limiter or source was repaired. NEXT resolve that extension/reconstruction
switch before a normalized solve and prescribed boundary lifts; all original
history, physical accuracy, cost, native and playable gates remain open.

Both7300s/local26000 full-river audits now pass, with5,382,400 finite cells,
86,720 exactly dry bank cells, depth maximum3.811920946750463m and speed
maximum6.216627760198487m/s. Depth SHA256 is
`273d89824796faf2130e76e23827e92b388ba7b4ef1d04c88e123873b8282389`.
Outlet108.84967242914268 versus inlet45.30695454719997m3/s is still unsettled.
Reports are `tmp/south-fork-expanded-7300s-state-v1-20260914.json` and
`tmp/south-fork-expanded-7300s-banks-v1-20260914.json`. Same cook remains live,
observed at7322s/local26440; next COMPLETE7400s/local28000 needs BOTH audits.
Desktop30FPS is confirmed in both the runtime budget and native gate, with
120Hz physics unchanged. No new gameplay measurement or playable acceptance.
