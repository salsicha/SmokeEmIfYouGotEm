# Total energy on the original moving-front geometry

2026-09-18 UTC. Implements the missing gravitational contribution to the
moving-front energy derivative. This is a prerequisite for the coupled force
law, not that law or a playable breaking-water fix. Nonlinear runtime stays OFF.

## Implementation

`subcell_affine_front_metric.py` now also integrates the two depth-weighted
spatial moments `X = integral((x-origin)*h)` and their analytic physical-time
rates. These use the same exact clipped source polygons and quadratic fan depth.
They do not substitute footprint-centroid times volume, round away positive
fragments or change the original depth/pressure moments. The bed origin,
original height and represented gravity are retained explicitly.

`subcell_front_total_energy.py` combines the existing original two-pole kinetic
functional with `g*((b0-datum)*M1 + M2/2 + gradient(b).X)`. It supplies primitive
derivatives for depth moments, common face columns, bed slope, bed height and
spatial moments, in both physical and canonical momentum coordinates. Potential
has the same sign in both coordinates; their distinct kinetic derivatives and
conjugate velocities remain intact. Physical time work includes spatial-moment
motion, not only changing volume. A shifted energy datum changes energy/work
by exactly minus gravity times shifted mass/mass-rate, not a fabricated force.

No gravitational work is inferred from a final energy residual. No transport
bracket, dry-owner creation, interacting fronts, slope-junction force, natural
open-boundary work or native integration is supplied. The already implemented
closed fixed-wet-support stage is not replaced or relabelled as a front solver.

## Verification

50 focused checks PASS in42.14s, including24 new controls. Independent branch
quadrature checks potential, physical-time work and spatial moments on three
bed slopes. Complex-step checks cover every primitive partial in BOTH momentum
coordinates; an independent time refinement verifies the complete chain rule.
Source subdivision, reversed winding and translated origin preserve exact
moments. Positive sub-float water/potential remain positive; fully dry state
stays zero and unsupported dry pressure creation rejects. Original bed mismatch,
invalid gravity, bad directions and unknown momentum coordinates reject.
Report: `tmp/front-total-energy-focused-v1-20260918.xml`, SHA256
`25af0845bb9cbc5e035448ce7ca11ffd6e072bdb1b30ae411f6895b2c965a5ad`.

Full prior65-module regression plus the new module completes **832 PASS / 13 FAIL**,
845 tests, zero errors/skips,287.77s, one existing JUnit metadata warning.
Failure identities match the prior suite exactly: four constant-velocity energy
controls, eight paired nonlinear energy controls and the legacy storage/face
consistency gate. No failure is waived and no tolerance is relaxed.
Report: `tmp/front-total-energy-full-suite-v1-20260918.xml`, SHA256
`7f8211613aad04350331ea10f2df564cdc41cae33f6b3e0e41384880b88c9228`.

All11 supported original local source cases reproduce every old whole/wet-side/
dry-side metric field exactly. Their new spatial moments, potential and potential
time work partition exactly across the same original source split. Both unsupported
record indices remain explicit. The old metric code is loaded from commit
`f84bb92eb5397ccf21bd91392c1efd0765b89992` only after its SHA256 matches the
qualified source report; every old output is compared to both the saved record
and new implementation. The new metric SHA256 is
`e45465d3bc6ed4d06265a20aeb1cac6722ceb521f83c094f9bd1452ca41428e8`.
All631 protected entries are checked, with this explicit implementation
transition and one unused historical restart-auditor version verified in Git.
Measured inputs and all other loaded physics must match current bytes.
Report: `tmp/front-total-energy-source-geometry-v1-20260918.json`, SHA256
`49de6c700ec7c49725ffecdf03f66b9754f066052836816d97f5d586f2c4cc1c`.
This is original-source geometry/partition verification, NOT a repeated all-case
total-pressure solve, coupled-force verification or gameplay acceptance.

## Remaining work

Derive and verify the coupled changing-support conservative mass/force law using
these total-energy derivatives, preserving original source geometry and original
pressure poles. Then integrate it into the shared rendered/contact surface and
verify real engine motion against references. No native build, fresh rendered
comparison or FPS qualification is claimed for this Python reference change.
Prior normal p9538.6731ms remains FAIL30; froth and crest appearance remain unaccepted.

The7250 hydraulic checkpoint passes BOTH state and artificial-bank audits but
is not settled; installed4950 remains unchanged. Cook28776/session93831 is the
same verified live continuation. Next7300/local2000 needs a complete marker and
both audits. South Fork, then Colorado, Pacuare, Futaleufu, all-scene Chilko/Zambezi,
crew, normalization, outstanding regressions and release remain required.
