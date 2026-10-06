# Shared South Fork particle/interface transport — September 11

South Fork and the full queue remain incomplete. This is a verified transport
consistency change in the unsaved native river experiment, not photoreal water,
playable performance, or production-map acceptance.

## Implementation and preserved constraints

`-RaftSimRegionalUnifiedTransport`, with the compatible-transport, interface,
interface-pressure and advection-packet flags, makes particles and the retained
surface sample the same post-extrapolation velocity with the same 32-load
averaged-quadratic-normal/tent-transverse basis. Particle forward midpoint and
surface backward midpoint use actual equal native fluid/engine clocks. Scalar
interpolation remains trilinear. Surface owner halos exchange after transport.

Native FLIP/PIC momentum, solid/air fallback motion, exact registered contact,
inlet sources, strict exterior exits, all identities and ownership gates remain.
This does **not** yet make momentum interpolation, cut-cell geometry, particle
volume correction, or provisional fixed exterior/Z boundaries physically final.
The visible renderer is still not coupled to this evolving interface.

The native scaled inverse disagreed slightly with the actual cell-placement
frame. Particle queries now use captured UnitToWorld and preserve subtraction,
dot-product and division residuals with DoubleFloat until one final demotion.
Nearest-cell multiplication/subtraction is explicitly float and precise. No
boundary epsilon, threshold relaxation, particle removal or density clipping.

The runner now snapshots the three transport includes before native compilation,
hashes them, and rejects changes during capture. Motion replay verifies those
snapshots rather than assuming today's worktree matches an older experiment.
Earlier unified captures without source snapshots cannot use the final replay
silently; their retained earlier reports remain explicitly historical evidence.

## Authoritative native evidence

`liquid-native-unified-transport-600-v4/`, native session 55491, terminated 0:
complete, unchanged transport sources, clean RHI validation, 726900 particles.

- `native-transfer-audit.json`: full P2G verification passes, zero reduction
  mismatches. Two survey-double/internal native-float owner differences remain
  within the existing declared coordinate contract; physical exterior unchanged.
- `advection-diagnosis.json`: all 726900 particle positions replay within
  0.002730 cm; 722158 grid-driven positions within 0.000489 cm. Unchanged
  acceptance tolerance 0.02 cm. All particles, including fallbacks, are checked.
- `interface-audit.json`: 599 native updates, both clocks 0.0166666675359 s;
  paired 2178720 scalar samples, max CPU error 0.000503793 cm. Every owned update
  and internal halo verifies. Actual selected stage: Extrapolate Velocities Again.
- Interior interpolated divergence RMS 0.000273416/s agrees with sampled
  centered-grid divergence. This is not an integrated volume-conservation claim.
- `flow-budget.json`: 598 valid commits, 22496 births, 25357 approved exits;
  726863 survivors plus 37 current-step births. Storage change -59.604167 m³.
  Final outflow 37.521552 versus inflow 47.047414 m³/s; outflow still declines.
- Worst density: owner 4, 14.773808 times nominal cell volume; owner 6, 12.359556.
  This remains unacceptable clumping, not a physically correct liquid.

`interface-coverage-v2.json` uses the actual residual-preserving captured frame;
the earlier coverage report used ideal survey coordinates. Positive phi is not
a geometric distance. It finds 123/726900 particles outside the interface,
zero incomplete stencils, and zero centres below the exact bed. No outside
particle is silently reclassified as spray. Remaining coverage/volume drift
still requires correction, even though this is lower than earlier trajectories.

The registered-mesh sampler can now return the upward normal of the **same
exact triangle** used for height. Owner 4 has 2470 of 3120 particles within
2.5 cm of bed moving inward before contact. The peak's 267 nearby particles
include 261 nearest-fluid and six nearest-solid; mean precontact normal speed
is -2.500618 cm/s. Owner 6 has 2318 of 3053 near-bed particles moving inward.
Thus ballistic solids alone do not explain accumulation: interpolated wall
flow and subsequent contact need consistent treatment with pressure and volume.

## Earlier attempts and regression results

First unified run (78008) and precise-float run v2 (49487) completed with clean
RHI/P2G but failed particle replay at half-cell phase boundaries. Maximum
all-particle error in v2 was 0.284547 cm. Disabling FMA alone was insufficient.
Residual-preserving v3 (5303) passed all-position replay (max 0.002607 cm);
v4 repeated with immutable include provenance. No tolerance was increased.

Builds 52635 and 71672 passed (48.36 and 37.97 seconds). Both engine suites,
99875 and 1915, have 20 clean successes, zero warnings/failures; final report
`liquid-unified-transport-engine-v2/index.json`. GPU operator compares 2181600
samples over 12 actual river-field cases and 3 analytic cases. All 413 liquid
Python tests and 5 captured-rock registration tests pass. These are separate
operator, trajectory, source-provenance and regression checks, not game FPS.

Saved playable map SHA256 is unchanged:
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.
No promotion, final commit or push. Final process checks must precede new UE work.
All owned UE/build and audit sessions were terminal at this checkpoint; final
process inventory found no UnrealEditor, UnrealEditor-Cmd or UnrealBuildTool.

## Next physical correction

Investigate and correct pressure/transport boundary geometry against the exact
bed, not just another visual layer or an outward particle bias. The current
axis-aligned solid mask constrains grid components on a stair-step approximation;
continuous interpolation can still point into the actual sloping triangle.
Contact then removes penetration without restoring displaced liquid volume.
This is a supported failure mechanism to test, not a proven complete cause of
the declining outlet flux.

Relevant primary reference: Batty, Bertails and Bridson's
[variational solid-fluid coupling](https://www.cs.ubc.ca/labs/imager/tr/2007/Batty_VariationalFluids/)
accounts for sub-grid solid geometry in pressure projection. Its MAC-grid
discretization is **not** a drop-in coefficient tweak for this centered ±2
pressure graph; derive matched divergence/gradient/boundary weights before
using it. Particle-assisted interface correction is another distinct remaining
piece; [Enright et al.'s water-surface work](https://www-graphics.stanford.edu/papers/water-sg02/)
provides the relevant interface-tracking context. Neither reference proves our
current river physically correct.

After bed/volume/outflow checks pass: integrate one visible surface, whitewater
froth/spray and raft support; compare real South Fork geometry and moving water;
measure playable performance. Then Colorado → Pacuare → Futaleufu, remaining
all-scene water and crew work, cleanup, release checks, and final commit.
