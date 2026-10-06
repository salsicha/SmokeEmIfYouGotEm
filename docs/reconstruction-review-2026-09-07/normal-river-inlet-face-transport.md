# Original source-face transport of conditional inlet profiles

Recorded 2026-09-17 UTC. This adds conservative, time-integrated advective
transport for the non-horizontal inlet profile. It is a prerequisite for
evolving water, not a delivered playable solver or a pressure-law acceptance.

## Transport, not hydrostatic redistribution

For each original source edge a+lambda*E, solve the parcel crossing directly:

    A+s*D+u*alpha = a+lambda*E,
    alpha(s) = cross(a-A-s*D,E)/cross(u,E),
    lambda(s) = cross(a-A-s*D,u)/cross(u,E).

Retain only alpha>=0, 0<=lambda<=1 and r^3+alpha<=R^3, together with the original
entry support 0<=s<=k*r/B. Integrate 3*J*r^2*(k*r-B*s)^p for p=0..3 using exact
rational polynomial bounds. This is the cumulative advective face flux from
birth to R^3, not an instantaneous flux or an extrapolation past the original
constant-velocity regime. Velocity tangent to an edge gives exactly zero flux.
An original inlet birth crossing is retained, not excluded by an epsilon age.

`subcell_inlet_face_transport.py` uses the same certified integration engine
as independently clipped storage, but derives its constraints from actual
crossings. Positive signed flux is outward. Reversing a shared face reverses
the bounds exactly; splitting an edge preserves its flux within the explicit
integration bounds. No residual is spread into neighboring sources.

The first actual-source attempt correctly failed: a bounded storage candidate
was the original upstream donor, not an empty downstream receiver. Its outgoing
birth flux requires an equal donor debit. The implementation now validates an
explicit original birth-donor role, computes that withdrawal once per stream,
and checks change in moments plus outward face flux encloses zero. The original
donor state itself is not mutated, and physical donor availability/pressure
coupling is not certified by this accounting identity.

The same investigation resolved an exact boundary case in storage integration.
A nonzero polynomial bounded above by zero permits only finitely many roots,
which have zero entry-time measure. Those intervals can be classified exactly.
An identically zero constraint is instead unrestricted and retains all water.
This removes artificial uncertainty at exact contacts without removing any
positive sliver, adding a depth floor, or widening a tolerance.

## Actual South Fork evidence

The unchanged registered source block (12,8), original 600-second water and
13 original immediate faces produce:

- 10 float-representable conditional streams, 17 routed source pieces and
  60 original piece edges: 8 positive outward fluxes, 17 negative inward fluxes,
  and 35 exactly zero fluxes.
- All four advected moment balances enclose zero on every routed source.
  Maximum relative balance width: 2.094718213952378e-34. Independently clipped
  aggregate moments have the same maximum relative uncertainty.
- All 11 represented original donors have exactly closing withdrawal balances,
  including the positive stream below float time/volume range. The latter
  remains unsuitable for a float physical state; two receding/fan records
  remain unsupported.
- All 55 stream pairs remain separated within common original windows.
  All 599 source/implementation hashes were checked and original pool volume
  and momentum remain unchanged.

Captured DEM/exposed rock remain distinct from submerged priors, interpolation
and inferred flanks. Rational calculations do not add measured precision.

## Verification and retained reports

Focused suite: **65 PASS**, 5.05s. Includes original inlet debit/credit,
cross-source storage/flux balance, exact shared-face antisymmetry, independent
Eulerian time integration on an oblique face, edge subdivision, transformed
coordinates/orientation, tangent and not-yet-reached faces, sub-float positive
flux, donor-role rejection, insufficient integration resolution, exact isolated
polynomial contact, and previous inlet geometry/contact/overlap controls.

Broad regression: **599 PASS, 13 unchanged FAIL**, 612 tests, 145.03s console
duration (145.012s JUnit suite), no errors/skips and one existing JUnit warning.
Failure identities exactly match the prior suite: four constant-velocity
energy gates, eight nonlinear paired-base energy gates and the original
storage/face representation gate. None was weakened or relabeled as passing.

- Actual report: `tmp/south-fork-inlet-face-transport-v3-20260917.json`, SHA256
  `9af21b0e4ff62a7620c92ad552161e7f47408f0d74ef57f005d78cf78cabd372`.
- Focused JUnit: `tmp/inlet-face-transport-focused-v3-20260917.xml`, SHA256
  `154efc9b7f533f18cd16d55ac76a1baa905af9cf1da336828e3c105bb6e5d73a`.
- Broad JUnit: `tmp/inlet-face-transport-full-suite-v3-20260917.xml`, SHA256
  `f3330693292996fd899d2d1c4944cbb37e0feda8411c7af9bffac7ef635175d6`.

## Other live work and remaining integration

Original native SM5 replay 55459/editor36412 and worker37836 remain live,
compiling the remaining transport permutations. This is not a native pass.
Shader inputs remain frozen; no installed module was replaced.

Same hydraulic continuation 51728/PID36872: 2250s/local9000 state and all 86,720
exactly dry artificial-bank checks PASS across 5,382,400 cells. Maximum depth
4.2130460132m, speed7.0875951365m/s, volume2,974,446.1646291753m3 and maximum step
mass residual1.5158152511e-8m3. Outflow97.1305358603m3/s versus45.3069545472m3/s
in: **not settled, calibrated or promoted**. Next2300/local10000 needs both audits.

- State: `tmp/control-ablation-2250s-state-v1-20260917.json`, SHA256
  `4ab4b0bee963ddb0cb5a6657fe7d266a12b8a1e4948555536dddb36fd9179df6`.
- Banks: `tmp/control-ablation-2250s-banks-v1-20260917.json`, SHA256
  `17dbd09818b74e5c81523b632617b67ef2da6000fe6aabc0406c87c476a02b2a`.

Next physical work: couple source-resolved transport to pressure/curvature,
bed forces and physical donor evolution, and handle outward-to-fan/receding
branch transitions. Advected depth powers alone are not a conservation proof
for total mechanical energy over varying terrain. Do not substitute a
minimum-centered hydrostatic pool, superpose interacting streams, or enable
the known broken solver to claim a visible improvement.

Normal playable South Fork is still the delivery target; Troublemaker remains
only its rapid, never a scenario menu entry. No terrain/material/crew/runtime
behavior changed here. Last28.057157FPS/p9541.2354ms still fails30FPS. All remaining
terrain/boulder/collision/physical/visual work, Colorado->Pacuare->Futaleufu,
Chilko/Zambezi/all-scene water, crew, normalization/regressions and release remain
open, not superseded by this prerequisite.
