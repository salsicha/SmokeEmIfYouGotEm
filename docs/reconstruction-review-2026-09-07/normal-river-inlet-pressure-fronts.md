# Inlet hydrostatic residual and finite-depth lateral fronts

Recorded 2026-09-17 UTC. The new source-resolved hydrostatic/bed calculation
reveals an additional front-law requirement. It is not a coupled solver,
nonhydrostatic pressure acceptance, or visible playable improvement.

## Pressure on the actual non-horizontal profile

The original conditional profile is X=A+sD+u*age, r^3=T-age, h=k*r-B*s.
Its smooth depth gradient is

    grad(h) = -B*grad(s) - k*grad(age)/(3*r^2).

`subcell_inlet_hydrostatic_force.py` integrates hydrostatic pressure and the
original affine bed force. The apparent 1/r^2 singularity cancels the original
area Jacobian3*J*r^2 analytically. The existing certified integrator now supports
radial powers2 (ordinary area) and0 (pressure-weighted area). Neither a minimum
time/depth nor an epsilon sliver is introduced. Weighted uncertainty is bounded
against the matching weighted incoming moment, not the old ordinary volume.

The volume coefficient of pressure and bed force is combined before interval
bounding. Exact cross-slope balance is retained instead of lost through two
independent interval estimates. Original bed gradients must agree exactly with
their original XYZ polygon; a receiving-source minimum does not place water.

## Missing lateral pressure jump found by independent verification

The first diagonal-flow test failed an independent Eulerian boundary-pressure
integral. At s=0, the profile has depth k*r, not zero. When that edge lies inside
a source, the pressure gradient includes a jump that the smooth formula omits:

    -3*g*J*k^2*grad(s)/2 * integral(r^4 dr along the interior side front).

The implementation now clips and integrates that term exactly with certified
bounds. No tolerance was loosened to make the initial test pass. The upstream
inlet lies on original source boundaries; the leading r=0 tip and h=0 upper
edge have zero pressure. The finite-depth side edge cannot simply be treated
as another zero-depth shoreline.

A separate test aligns that side front exactly with a source partition edge.
The wet and dry one-sided boundary tractions do NOT form a common conservative
numerical flux. This limitation is explicitly exposed, not normalized away:
`wet_dry_riemann_flux_or_lateral_fan_accepted` remains false. The reported quantity
is an **interior-trace spatial residual**, including interior pressure jumps;
it is not an accepted shared-face flux or momentum time update. A physical
wet/dry spreading solution is required even while streams remain separated.

## Actual South Fork evidence

Unchanged registered block(12,8), original600-second input and13 immediate faces:

- All17 routed pieces of10 float-representable streams have bounded hydrostatic
  residuals and unchanged advective mass balances.
- Nine pieces have proven positive-depth lateral fronts strictly inside their
  original source. Each belongs to a different stream. The tenth stream has no
  proven such front within its routed in-block piece; this does not establish
  absence of an out-of-block front.
- Maximum relative pressure-weighted moment width is1.382765944878196e-21.
  Original ordinary moment uncertainty remains2.094718213952378e-34.
- All600 source/implementation hashes and original pool volume/momentum are
  unchanged. Stream-pair separation remains distinct from lateral-front physics.

The positive exact stream below float time/volume range remains retained in the
source records, but its actual source-clipped force is not included in this
17-piece audit. The force implementation's sub-float positive case passes its
independent fixture. Those two evidence scopes must not be conflated. Two
receding/fan records remain unsupported. Captured DEM/exposed rock remain
distinct from submerged priors, interpolation and inferred flanks; exact
arithmetic is not additional measured precision.

## Tests and retained artifacts

Focused suite: **75 PASS**,6.19s. Closed-form force, independent boundary
traction, oblique/transverse flow, source partitioning, shared-front rejection,
exact cross-slope balance, original bed changes, coordinate/vertical-datum
invariance, birth scaling, sub-float positive force and integration rejection
are covered alongside the existing transport/contact/overlap controls.

Broad suite: **609 PASS,13 unchanged FAIL**,622 tests in157.18s console time
(157.154s JUnit), no errors/skips and one existing JUnit warning. All13 failure
identities match the earlier suite: energy conservation and original storage/
face representation remain unmet. No gate was weakened.

- Actual audit: `tmp/south-fork-inlet-hydrostatic-force-v4-20260917.json`, SHA256
  `5c575c95d69c3b40ade67d0e58e49ebd760c9040629b74802eb0361dbb0bcaf4`.
- Focused JUnit: `tmp/inlet-hydrostatic-force-focused-v4-20260917.xml`, SHA256
  `3aa56824de5db7750b21711980830ac5c6992ff46ffbe984ddecccca11049c0b`.
- Broad JUnit: `tmp/inlet-hydrostatic-force-full-suite-v4-20260917.xml`, SHA256
  `95631083fd9ddfc336264740e4df0f477844c47e1c0c7e66a4d3de2069f5bb49`.

## Live validation and next physical work

Native SM5 replay55459/editor36412 logged a7200-second hung-shadermap error
with3 pending jobs and53 finished. Editor and worker37836 remain directly
verified live with increasing CPU; later diagnostics still list transport
permutations4/21. Do not mark this a pass or terminal, or restart on the watchdog
message alone. Preserve the same handles and frozen63 shader inputs.

Same hydraulic continuation51728/PID36872:2350s/local11000 state and all86,720
exactly dry artificial-bank checks PASS over5,382,400 cells. Maximum depth
4.1548995441m, speed6.9802733740m/s, volume2,969,349.6519049513m3 and maximum step
mass residual1.6470207420e-8m3. Outflow94.8473303463m3/s versus45.3069545472m3/s
in remains **unsettled and unpromoted**. Next2400/local12000 requires both audits.

- State: `tmp/control-ablation-2350s-state-v1-20260917.json`, SHA256
  `d240ec29c07bd6d08c42aa2eedf6e1d1d834d8041d15f6eab52dee49bf2deafa`.
- Banks: `tmp/control-ablation-2350s-banks-v1-20260917.json`, SHA256
  `a5c55c41009b9074acb64a0dca366ea36545c841d7604f62d4b9882d3a7e953f`.

Next resolve the finite-depth lateral front and use a common physical wet/dry
flux, together with donor evolution, pressure/curvature/bed forces and time
coupling. Waiting for stream overlap or the inlet's later outward-to-fan knot
does not remove this existing lateral-front requirement. Normal playable South
Fork remains the delivery target; do not enable the known broken solver as a
substitute. No installed module, shader, terrain, material or crew changed.
Last28.057157FPS/p9541.2354ms still fails30FPS. Full reconstruction, breaking/
froth, Colorado->Pacuare->Futaleufu, Chilko/Zambezi/all-scene water, crew,
normalization/regressions and release remain open. Troublemaker is only a
South Fork rapid, never a scenario menu entry.
