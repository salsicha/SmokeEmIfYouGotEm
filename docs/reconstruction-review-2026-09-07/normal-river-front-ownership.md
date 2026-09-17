# Single ownership of a conditional side front

September 17, 2026. This is a physical reference-model prerequisite, not a
playable breaking-wave, foam, performance or finite-time conservation pass.
The preceding commit-status turn made no goal progress. This turn implements
source ownership, exercises actual registered geometry, and audits new cook
checkpoints. The full requested project remains unfinished.

## Exact ownership and common transfer

`subcell_inlet_front_ownership.py` partitions the complete straight side ray
`X(tau)=A+u*(T-tau)`, with `tau=r^3` in `[0,T]`. Source half-plane intersections
are rational in tau; no rounded cube root or geometric epsilon chooses owners.
The signs of infinitesimal positive/negative inlet-edge displacements identify
the conditional wet/dry traces. Winding and input order do not choose ownership.
Positive-width overlapping source owners and inconsistent affine bed traces
reject explicitly. Missing owners remain explicit, including complete gaps.
Only zero-line-measure endpoint contacts are omitted, never positive slivers.

Each owned segment evaluates the existing mass/momentum and energy integrators
on original source geometry clipped to that segment. Their mass measures must
agree exactly. One transfer id and common rate bounds have separate signed
debit/credit references. An internal front can have the SAME source on both
sides, but its conditional wet/dry domains are distinct. Collapsing those two
domains into a zero source-total update would not evolve the front.

These labels are not actual evolving pool ownership. Initial wet contact,
multiple-stream interactions, donor depletion, finite-time spreading, bed and
dispersive pressure work remain required. No new force is added to the old
distributional pressure residual. Source rationals do not add surveyed accuracy.

## Tests and unchanged actual South Fork sources

Final focused run: 69 PASS in 5.44s, including 18 ownership cases. Controls cover
shared-source-boundary double counting, interior fronts, exact source crossings,
rotated/wound/translated geometry, positive sub-float segments, missing owners,
gaps, point contacts, duplicate vertices, source overlap, bed inconsistency,
concavity, binary-input conversion, unchanged inputs and integration-budget
failure. Adjacent mass/momentum/energy/force/face gates remain unchanged.
JUnit `tmp/inlet-front-ownership-focused-v3-20260917.xml`, SHA256
`e373ecc31202362b0c77efea7a5f83ef37f96b847e0626d370b6b34c23b032f4`.

Actual original block (12,8), registered terrain and 600s atlas: all 11 conditional
streams get an exact whole-ray partition. Ten have paired original-source traces,
each an internal front. They touch seven distinct original source keys. One has
neither trace in the inspected block: donor `[8,600014]`, receiver `[8,198093]`.
Its time is positive, approximately 3.555647144e-15s, NOT floating-point underflow.
Its inlet starts on the west block edge; exact midpoint lies 2.876926573e-22m
outside that edge. The original velocity is approximately
`(-1.618229513e-7,0.2239881923)` m/s. No snapping, invented bed, discarded ray or
claimed complete ownership. The separate positive sub-float stream is retained
and has paired ownership. Two receding/fan records remain unsupported.

Final report `tmp/south-fork-inlet-front-ownership-v2-20260917.json`, SHA256
`06a5b8b9d80ab7dc375f3d23faf0dbfad4bc55bc5ed97e27e4abb73f52f8509d`.
Independent inspection checks exact gap-free interval partitions, shared transfer
ids/signs, both source references and provenance, and all 613 input/implementation
hashes. Every pre-existing record field equals the preceding energy report;
original water is unchanged. Legacy closed per-source flux queries remain
diagnostic and MUST NOT be summed as distinct transfers.

Final broad regression: 672 PASS / 13 FAIL, 685 tests, zero errors/skips, one
existing warning, 143.83s. Failure identities exactly match the preceding run:
four constant-velocity energy, eight nonlinear rational energy, one original
storage/face representation gate. No skip or tolerance changes. JUnit
`tmp/inlet-front-ownership-full-suite-v2-20260917.xml`, SHA256
`7e6f49c0a85c1fc82460931f1bb5274b68dae6c690e2f40fcccdc6c282f72791`.
The earlier v1 broad run also has 672 PASS / 13 FAIL. Final focused, actual-source
and broad runs include the common-measure check and dry-source provenance union.

## Playable investigation and hydraulic continuation

Re-inspected existing ordinary startup PNG
`unreal/Saved/Screenshots/south-fork-crest-boundaries-installed-startup-v1-20260917_022.png`,
SHA256 `4ae43d58e6836ebb197a085dde1e6c459bad0a6b12274f19dfafdcb3bd7e7ed8`.
It still has broad sheet-like whitewater and a sharp foreground mean-stage face.
This is NOT a new capture or new motion/reference acceptance. Traced inherited
drift-foam shading as a possible extra white source: normal single-surface runtime
already zeros its aeration/speed gains, opacity, glow and roughness in
`RaftSimWaterSurfaceActor.cpp`. No unsupported shading tweak was installed.

Same cook PID 17516, start UTC 2026-09-17T12:52:03.0749210Z, directly verified LIVE.
4050, 4100 and 4150s all pass state/conservation AND 86,720 exactly dry artificial
bank cells. Latest 4150/local11000: maximum depth 3.924081317m, speed 5.497121920m/s,
volume 2,887,870.122823m3, maximum step residual 1.521822357e-8m3. Outflow
95.805445235 versus inflow 45.306954547m3/s: NOT settled or promoted.
Depth-array SHA256 `eca9aa0756a6e8a556509405ed083f72459501d438e7053a81f52b6eb7ced4ff`.
Reports `tmp/control-ablation-{4050,4100,4150}s-{state,banks}-v1-20260917.json`.
Next 4200/local12000 requires its completion marker and BOTH audits; do not restart
the live cook. Installed gameplay DLL and material match the preceding hashes.
No new FPS claim: last ordinary 25.907729 FPS / p95 44.7123ms still FAILS 30.

Next resolve out-of-block source coverage without relocating the ray, then couple
the owned rates to evolving donor/receiver domains with depth, physical momentum
and energy, including actual bed/dispersive work and branch transitions. The
current nonlinear instability and thirteen physical failures remain open.
South Fork playable terrain/boulder/collision/flow and convincing breaking/froth
remain unaccepted, followed by Colorado -> Pacuare -> Futaleufu, Chilko/Zambezi,
all-scene water, crew, normalization, regressions and release. Troublemaker remains
a rapid inside South Fork, never a scenario or menu item. Generated evidence is
already ignored; no additional `.gitignore` rule is needed.
