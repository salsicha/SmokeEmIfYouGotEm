# Full-rapid water ownership and pressure tail — September 10

South Fork remains incomplete. This pass preserves the full prepared domain
while removing a pressure-dispatch obstacle to regional integration. It does
not install twelve independent tanks or claim their interfaces are coupled.
The preceding status-only turn was no implementation progress; this pass is
progress through code changes, actual full-state audit and wet GPU regression.

## Pressure change

`RaftSimLiquidPressureColoring.h` wraps the actual compatible pressure body.
The native dispatch has NX/2 threads and the +/-2 stencil uses floor(index/2)
colors. An NX=4k+2 extent formerly left its last parity lane unsupported.
The final thread now computes both remaining cells during their shared color,
and skips the out-of-range base during the other color. All body reads and
writes are inside the extent guard. NX=4k retains the prior one-cell mapping.
The physical extent, spacing, number of cells and pressure equation do not
change. Odd X remains rejected because native dispatch is half-X; the existing
2,000,000 reconstruction-voxel cap remains unchanged.

The full prepared domain has 494 computational X cells; the last partition
has 110. Neither can be handled by truncating to a multiple of four.
The exhaustive editor test checks every even X from 4 through 4096, both phases,
and Y/Z phase origins: exactly one visit per pressure cell, no duplicate writes,
and opposite colors for +/-2 dependencies. The actual compiled coupled shader
contains the guarded two-lane loop and indexed write. Its dumped source has no
second pressure-stage write outside that loop.

Actual-RHI editor reports `engine-liquid-pressure-tail/index.json` and final
`engine-liquid-pressure-tail-final/index.json`: four tests
pass, zero warnings/failures, including the fourteen coupling variants. This
final run includes the new compiled-tail-marker assertion and takes 22.177 s. It
compiles the tail branch but does not exercise a wet NX=4k+2 region on GPU yet.
Do not misrepresent the legacy 68-cell replay as tail-branch execution.

## Full prepared regional state

New preparation: `physics/scripts/liquid_region_state.py`.
Input remains `tmp/south-fork-whole-rapid-liquid-float-seeds-20260910`.
Output: `tmp/south-fork-liquid-regional-state-20260910`.

Twelve regions partition every physical cell of the existing 490x162x24
domain. Typical physical XY is 128x64; the final region is 106x34, computational
110x38x24. Seventeen internal interfaces are stored once with their two owners
and matching face ranges. They require shared pressure/velocity/particle state;
they are explicitly **not** native inflow reservoirs.

Each seed and inlet has its original parent identity, exactly one owner and
unchanged canonical ENU position/velocity. Region origins are explicit, with
the original vertical datum. No global geographic translation is applied to
these files. Half-open ownership handles shared faces/corners; points outside
the parent domain raise an error instead of being clamped or deleted. The old
seed burst and volume caps are enforced without truncation.

Independent reassembly audit:
`physics/scripts/audit_liquid_region_state.py`, result
`liquid-regional-state-audit.json`:

- 719,335 seeds and 6,144 inlet sites verified exactly once.
- 79,380 physical XY cells covered exactly once; all 17 interfaces matched.
- Positions, velocities and inlet weights match their parent rows exactly.
- Nominal particle volume 1/48 m3; represented volume 14,986.145833333332 m3.
- External numerical inflow 47.0068051381853 m3/s retained; no internal emitters.
- Largest region: 158,248 seeds below 163,840 inherited burst capacity.
- Largest regional reconstruction: 1,723,392 voxels below 2,000,000.
- Aggregate reconstruction including halos: 16,904,448 voxels. This is arithmetic,
  **not** a claim of affordable concurrent GPU execution or measured memory/FPS.

Manifest SHA256:
`11ec3a4e36c4cf1a7a395ac269bab8ffad6653ae50009ad5faa3b436d6f5a0b3`.
The manifest hashes each parent and emitted region file. No source geometry,
hydraulics or saved scene was rewritten. Seven new Python tests cover ownership,
extent/metric integrity, capacities, inconsistent data and boundary behavior;
all 197 liquid Python tests pass.

## Actual wet regression and remaining work

`liquid-pressure-tail-regression` is the existing 12-second geographic coupled
fixture, not full-rapid regional water. Capture complete, no capture error or
engine errors. Clock, stage order, live density, affine and current-surface foam
audits pass: 757 callbacks, 714 positive-clock steps, 30 distinct motion images,
57,297 final primary particles; maximum position error 1.852258e-6 m and affine
error 3.715529e-6 /s. Blocking capture time 84.368 s is not a frame-rate measure.
Secondary trajectory audit was not rerun; no broad secondary acceptance claim.

Viewed actual `terrain_0720.png`: glossy/lumpy isolated water with exposed
vertical edges. It is not convincing returning-roller whitewater. No visual,
physical-full-rapid, performance or production acceptance.

Next: strict engine regional-state consumer using explicit canonical frames,
matching bounded contact and boundary tables; actual wet partial-X GPU check;
shared pressure/velocity/particle exchange and persistent particle ownership;
one continuous visible surface coupled to the raft; actual whole-rapid motion,
reference and performance validation. Keep the v3 installer guard until matched
state and coupling are actually implemented. Do not start independent emitters
on the 17 internal interfaces or reset particles when ownership changes.

No commit, no production promotion, no goal completion. Later rivers and the
remaining queue retain their original scope.
