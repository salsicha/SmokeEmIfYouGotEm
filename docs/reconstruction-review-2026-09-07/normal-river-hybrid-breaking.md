# Hybrid breaking candidate and pressure-column diagnosis

September 12 continuation. This is an opt-in CPU model plus its matching GPU
elliptic operator, NOT playable breaking/froth acceptance. The last turn made
concrete progress on the distributed operator; this turn adds physical-model
coupling and tests without declaring the unresolved river motion accepted.

## What the pressure evidence rules out

`tmp/south-fork-peak-pressure-column-v1-20260912.json` evaluates the exact saved
pre-surge state, not a repaired copy. At cell(y28,x48), depth0.103059010m,
the rational model has positive bottom gauge pressure per density28.17453603
m2/s2, with the minimum0 at the free surface. Standard SGN also has positive
pressure and a still larger downslope forcing. Therefore neither negative
pressure at that cell nor the rational poles alone explain the surge.
Elsewhere, six rational-model columns have negative gauge pressure, minimum
-0.221972214m2/s2 (head-0.022627137m). This is not by itself evidence of
cavitation or confirmed separation. No pressure has been clamped.

`pressure_column` reconstructs the model's quadratic vertical profile from its
integrated and bottom pressure, checks interior extrema as well as endpoints,
and reports hydrostatic plus nonhydrostatic terms. The optional `on_pressure`
observer receives copies of pole RHS, solution correction and pressure fields;
mutating diagnostic copies cannot change the force or caller inputs.

## Physical basis and explicit adaptation

[Filippini, Kazolea and Ricchiuto (2016), section6](https://www.math.u-bordeaux.fr/~mricchiu/GN1D.pdf)
describes a hybrid breaking closure: detect fronts using surface rise or slope,
check a peak/trough depth-ratio bore Froude number, then use shallow-water
dynamics in a front-centered band. The candidate uses gamma0.6, slope30degrees,
critical Froude1.3, and width7.5 times the peak/trough depth difference, within
the paper's described choices. These parameters have NOT been calibrated to
South Fork. The paper requires physical breaking dissipation and does not
justify capping velocities or treating every steep bed as a breaking wave.

Our raster implementation is an explicit adaptation, not a reproduction of the
paper's validated 1D method. It searches contained monotone free-surface fronts
along both cardinal axes, reports boundary-truncated runs, and leaves uniform
downhill sheets and lakes unflagged. The band uses exact interval/cell overlap,
including subcell widths, without changing conserved state. It cannot cross
disconnected wet components. Positive tiny trough depths are retained; bore
Froude is evaluated in log space to avoid overflow, not bounded numerically.
Cardinal-front anisotropy and truncated-front treatment remain limitations to
evaluate for curved river flow; 90-degree transpose tests do not establish full
rotational invariance. This detector is not a demonstrated froth-production law.

## Consistent pressure coupling

The cell-average nonbreaking fraction f is in[0,1]. The CPU and GPU operators
now support A=I+l*(W^T*f*W+0.75*f*b*b^T), retaining symmetry/coercivity and the
unchanged40-iteration budget. The same fraction enters nonlinear forcing and
pressure reconstruction on CPU. Pressure gradients remain conservative instead
of multiplying the final force by a cell-local mask. Uniform f=1 is identical
to the unchanged model; uniform f=0 gives zero nonhydrostatic force. Mixed
regions communicate through the coupled pressure solve. The GPU requires the
caller to apply the fraction consistently to forcing/reconstruction too; that
full GPU pipeline is still not implemented.

CPU `--breaking-model hybrid_front` requires nonlinear kinematic pressure and
fixed physical bed slopes; default remains `none`. Neither candidate is enabled
in playable evolution. No water state, timestep, resolution, solver budget,
velocity or depth limit was changed to obtain a pass.

## Verification and retained experiments

154 focused Python tests pass in30.64s (session78898 CLOSED). New checks cover
pressure reconstruction/copy isolation, stationary/interior pressure minima,
front thresholds/locality/periodic translation/subcell overlap/disconnected
water, genuine1e-310m troughs, mixed-fraction matrix symmetry/positive spectrum/
diagonal, nonbreaking-wave identical evolution, lake balance, flat-bed momentum,
and hydrostatic-energy loss in a periodic breaking bore. That last diagnostic
does not establish full nonlocal-energy stability or laboratory agreement.

Build50889 succeeded in16.09s. Actual GPU regression85728 CLOSED with67 successes,
zero warnings/failures/unrun,15.654921532s:
`unreal/Saved/RaftSimValidation/south-fork-hybrid-fraction-regressions-v1-20260912/index.json`.
Independent double-precision face-accumulation checks verify mixed and zero
fractions in both GPU solver paths. Mixed-fraction acceleration error9.43772161e-8,
true relative residual1.44944947e-7,28/11iterations. Zero-fraction operator solves
in1/1iterations. NaN fraction and wrong buffer stride are rejected. Existing
512x512, boundary, dry and thin-cell cases still pass. No accuracy gate was relaxed.
This native run was concurrent with owned CPU jobs, so it is NOT a new isolated
timing result or scene FPS qualification.

Short replay60752 CLOSED:
`tmp/south-fork-hybrid-peak-continuation-v1-20260912.json`.
From the14.500554884s saved state it completes0.51s,107steps/83retries,
peak15.878523966m/s, volume error0, compared with the retained20.756189560m/s
peak in that original interval. This v1 precedes the disconnected-band and
log-Froude hardening. Current-code repeat48914 is now CLOSED:
`tmp/south-fork-hybrid-peak-continuation-v2-20260912.json`, completed0.51s,
107steps/83retries, peak15.878523966m/s, volume error0, residual7.318143334e-7.
It confirms the short-interval result, not a full-trajectory or scene pass.
The instantaneous hybrid audit
`tmp/south-fork-hybrid-peak-pressure-column-v1-20260912.json` left the fast cell
nonbreaking(f=1); influence from other fronts is coupled, not a local speed cap.

Fresh full hybrid replay23543/PID40864 started
UTC2026-09-13T06:36:15.2874881Z. It runs from the original capture for20s, saves
every0.5s, and has reached4.5s/540steps/0retries, peak7.975453436m/s,
worst correction residual2.275818715e-6. Destination:
`tmp/south-fork-hybrid-front-bank-twenty-second-v1-20260912.json`.
Preserve the same handle/process and its eventual outcome. It has NOT completed.

CPU driver SHA256:
`7b439ba2813e59cbce0705f808e3e5e82ffcb42f19a9c0d6e7ef7f535c662bff`.
Pressure SHA256:
`17cd22feb67c29e7530fe322ff14040c55a582dbf6819c4b0c797713831ad434`.
Breaking SHA256:
`70d863394e573fbdc9a21bb4b158b6903cccbb2ccd7320b1148fce42a3e36937`.
GPU shader SHA256:
`b769ff049d2695b7d36db39a1b5abbed7211103e1bfe9fffabfa850287b38f2d`.
WaterDetail DLL SHA256:
`45896f432ad08d2a95aa44a48e255b1aa88c158aaa7f6fb795fea1f7ad9aa14e`.

## September 13: full 20-second replay completed, not physically accepted

Owned session23543/PID40864 exited0; no restart. Final report:
`tmp/south-fork-hybrid-front-bank-twenty-second-v1-20260912.json`.
Completed20s in2903 accepted steps/957 rejected trials, volume error0m3,
final maximum depth3.392114808m and speed6.338289154m/s. Peak accepted-state
speed17.017388151m/s remains a physical-validation concern, despite being below
the previous nonbreaking20s peak20.756189560m/s. The detector did not eliminate
the high-speed transient. Worst pressure residual2.275818715e-6, maximum40
iterations,13526 solves. Hydrostatic-only energy107363.250940 to95006.354674
excludes the nonlocal pressure contribution and is not a total-energy proof.
Final state SHA256:
`a91e9d60794a31aab853f214780b94f2e3f0506da12be2c66d08e5b40c6173d4`.
No GPU state evolution or playable promotion follows from this diagnostic.
The source/implementation hashes above remained unchanged during this replay.

## Integration and reference access remain open (prior-turn record)

Both reference videos were retried this turn. The browser runtime and the
computer-use skill's Windows runtime each fail on startup with
`failed to write kernel assets` / OSerror3. Web fallback returns cache misses
for John Elkins `ZEG1kvjNI30` and Qweniden `2XTbOCNDcZQ`. Neither video was viewed,
and no remote media was downloaded to bypass playback restrictions.

Normal map, V4 water material and saved game hashes remain unchanged. The
hydraulic cook96057/PID29104 is still live;3200/local24000 is the latest BOTH
audited checkpoint,3300/local26000 next, last observed3252.5s/local25050.
No new ordinary-play FPS capture.
Remaining work includes physical/laboratory/reference validation, actual GPU
nonlinear forcing/transport/pressure reconstruction, breaking-energy-to-froth
coupling, mean/window/boundary exchange and one completed render/contact surface.
Terrain/rapid evidence, all remaining scenarios/rivers, crew,30FPS, release and
the final commit remain active parts of the full goal.
