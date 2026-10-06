# Natural drift — first actual-tick traversal

The opt-in `RaftSim.Survey.SouthForkNaturalDrift` diagnostic observes the normal
gameplay clock and raft for up to 120 seconds. It issues Rest once and never
teleports, injects velocity or manually steps water/raft physics. Tube clearances
are independently queried against the captured collision mesh about ten times
per second. This is not a clean frame-time benchmark.

Initial report: `unreal/Saved/Automation/SouthForkNaturalDrift_20260907_045235.json`.
Test result: `engine-natural-drift-initial/index.json` (**Fail**, retained).

- 120.108 seconds; station −55.527 → 90.172 m, about 145.7 m downstream.
- All 1,075 observations sampled wet water; finite state throughout.
- Zero missed ground queries; minimum sampled tube clearance −0.000029 cm.
- Ground contact in 185 observations. After about 100 seconds, the raft
  settles against a downstream obstruction near station 90.17, lateral 9.02 m.
- The outlet criterion (station ≥110 m) was not reached. This is an incomplete
  free-drift traversal, not evidence of pass-through collision. A real unsteered
  raft can lodge against rocks; do not weaken contact or inject downstream motion
  to satisfy this diagnostic. Guided traversal remains untested.

Five captures with prefix
`unreal/Saved/Screenshots/SouthForkNaturalDrift_20260907_045235_` show the actual
guide camera. Images 001 and 002 were inspected: dark, mostly smooth water,
little convincing froth and column-like rock edges remain. The editor's actual
PIE captures are 954×502; requested launch dimensions are not their pixel size.
No visual, whole-rapid or production acceptance follows from the contact checks.

The LiDAR recovery uses a minimum return count per cell. Some enclosed cells
without enough returns fell to the inferred submerged bed, leaving narrow pits
inside an otherwise supported rock top. `repair_captured_rock_gaps.py` now
creates a **separate** candidate, preserving all measured cells and outer rock
outlines. It fills only enclosed inferred cells in gaps no larger than 1 m²,
surrounded by rock with at most 1 m rim relief. Eight-connected exterior water
and open cracks are not filled. New authority code 4 means inferred interpolation.

Candidate: `tmp/south-fork-rock-gap-candidate-20260907`. It fills 40 half-metre
cells (10 m²); all captured bank and rock heights remain byte-equal. Five new
regressions plus thirteen survey reconstruction tests pass. This limited repair
does not resolve all rock shape, submerged-bed or rendering defects. It has not
been substituted into the live review mesh or water fields.
