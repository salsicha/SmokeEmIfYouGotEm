# Exact roof jump and swept-contact candidate

September 16, 2026 UTC. Work in progress, not traversal or release acceptance.

## Observed failure, not just a proposed mechanism

The opt-in read-only observer committed in `02e52b206` records the actual
South Fork landward preview at world time 19.827281366 s. The local tube support
(1.850000095, -0.85, 0) m crosses onto roof face 1090 of the captured rock.
The existing height constraint raises the entire 605 kg body by
1.841773265899 m during a 0.008333333768 s substep. The corresponding change
in gravitational potential is 10927.283608 J, not a complete energy balance.
The collision re-query identifies the original component/mesh and exactly
reproduces the float ground height consumed by the solver.

Evidence: `tmp/ground-projection-observation-v1-20260915.json` and its log.
The intended mesh and 50-second water state installed before BeginPlay;
single-surface mode is verified. The completed recording
`unreal/Saved/VideoCaptures/RaftSim_20260915-174235.mp4` contains 274 source
frames over 24.185 seconds. Full decoding yields 726 presentation frames;
that encoded cadence is NOT measured gameplay FPS. Unmodified decoded frames
at video seconds 6 and 8 visibly show the jump and suspension above the water.
At world times 22.042 and 32.080 seconds station remains about 8363.83 m.

Decoder outputs: `tmp/ground-contact-baseline-decoded-v1-20260915/`.
The decoder's historical ROI names are not registered semantic regions for
this new camera; their image statistics are not used for acceptance.
Fixed comparison camera: (-545900, -362700, 2000) cm, pitch -35.27 degrees,
yaw 46.85 degrees, FOV 90. Capture starts at 12 seconds, stills at 12/22/32.

## Candidate and limits

`-RaftSimContinuousGroundReview` is opt-in, non-shipping, OFF by default.
It sweeps the same six tube-support spheres against the same registered
`RaftSimPhysicalGround` component triangles. It does not sweep arbitrary
scenery, move rocks, reduce their collision, change water, or save a map.
The normal impulse couples linear and angular motion using the selected
integrator's world-axis diagonal inertia convention. It consumes the remaining
part of the same substep rather than dropping time at first impact.

Rotation uses piecewise chord sweeps of at most 0.005 radians; this is NOT
exact rotational CCD or a complete continuous raft hull. A ten-micrometre
numerical contact skin prevents float hit-time rounding from re-entering the
just-contacted surface. The corner regression independently bounds its gap
and retains exact unblocked displacement. Initial overlap or iteration
exhaustion is an explicit failure, not successful motion or a hidden fallback
to roof-height lifting. Existing height support and landscape fallback remain.
The default path is unchanged. Broader replay, ongoing contacts, full hull
coverage, robust rotational clearance and performance remain to be proved.

Initial build passed, but its native run discovered only the eight old tests;
it is not counted as exercising the two new cases. Forced source discovery
then compiled the new fixture. Actual complex-mesh side sweep passed; the
corner math case failed because rounded hit time masked the second wall.
The explicit contact skin addresses that failure. Final native report
`tmp/swept-contact-native-v3-20260915/index.json` proves all TEN selected tests
pass, zero warnings/failures/not-run (including both newly discovered cases).
SHA256 `f39db8c35e04293cad013df41a4da22966dea0978f88c7e00907e69f1f8d9186`.
Existing dry-ground, loaded buoyancy, water-mask gap, passive-current capture,
flexible contact, paddle coast-down, source streaming and observer tests pass.
The rebuilt editor succeeded; pre-existing D6 float-conversion warnings remain.

## Actual first replay moves beyond the failing rock

`tmp/swept-ground-playable-v1-20260915.log` verifies the same cap/source-water
installation, single-surface mode and enabled swept contact. It records 154
contact substeps, zero rejected steps, and a finalized 24.288-second recording
with 253 source frames. At world time 22.072 s the raft reaches station
8372.560 m, and at 32.046 s it reaches 8394.057 m rather than remaining at
8363.83 m. Nearby drift samples have about 11.6 and 12.5 cm floor freeboard,
not the old ~220 cm. No >=5 mm projection report was emitted; that absence
alone is not a complete contact/clearance ledger.

Full clip decoding yields 729 presentation frames. Unmodified video frames
at seconds 6, 8 and 18 were inspected: the raft passes beside and downstream
of the rock and exits the fixed view, instead of jumping onto its roof. This
is direct evidence of local traversal improvement, not complete river/hull
acceptance. Broad froth, abrupt inferred rock sides and smooth water faces
remain visually unaccepted. Recorded runs are contended and not FPS tests.

Recording: `unreal/Saved/VideoCaptures/RaftSim_20260915-180621.mp4`, SHA256
`695aa8b6470b79bc46909c202d9f32ebeada5a05b7a77e3dc80239a0475bfad5`.
Log SHA256 `d6e2b30ba836c3eab437ae8724e43c3fde8e8689af3726f1c45780e313daabaf`.
Decoded frames: `tmp/swept-ground-decoded-v1-20260915/`.
Baseline contact JSON SHA256
`fe1dfb72e4dcd9b186cc00895488d3aa7e76ef6ea94b8bc126a0aa93c23afcb3`.
The extended repeated run also completed: `tmp/swept-ground-long-v1-20260915.log`
records 153 contact substeps, zero rejected steps, stations 8399.763 / 8422.730 /
8440.910 m at 32.116 / 52.086 / 72.080 seconds. Later sampled floor freeboard
remains 16.1-16.8 cm with no grounded points. This is progression telemetry;
the raft is beyond the fixed camera, not a claimed visible whole-river review.
The finalized recording has 792 source frames over 64.163 seconds:
`unreal/Saved/VideoCaptures/RaftSim_20260915-180830.mp4`, SHA256
`606c395f2de5539fdbf23c1c2ef738aeeaabfe557512c402297b0c1f57f082a7`.
Log SHA256 `520fef4e7fe80a8103790119a27822adeafec500dcca6d0318d40a0d968b145b`.
Starting inputs are the same, but actual trajectories are not bit-identical:
this is not a determinism or paired-performance claim.

All 464 protected source/map/save/actor hashes remain unchanged after both
replays. Generated video, stills, logs, binaries and audits remain ignored.
NEXT qualify sustained/multiple-support and rotational clearance, full-hull
coverage and contact cost before default promotion. The successful local
improvement does not prove a globally safe initial-overlap/failed-step recovery
policy, and explicit rejected-step behavior must not be called playable success.

## Own-state hydraulic continuation

The landward continuation PID 2344 was confirmed live, not restarted.
Independent completed local-step 1000 / absolute-time 100-second audits pass
all 5,350,400 cells and all 86,720 artificial bank-face cells remain dry.
Maximum depth 4.077397654 m, speed 12.168448361 m/s, maximum step conservation
residual 1.283153361e-8 m3. This is NOT hydraulic settling acceptance.
Input SHA256 remains
`c7b1f796a76b9944abe3725f0d2648bfe6b757a1a33109a2869c9c6bdf71fe73`.

Reports: `tmp/south-fork-landward-100s-snapshot-v1-20260915.json` and
`tmp/south-fork-landward-100s-banks-v1-20260915.json`.
The subsequent 150-second checkpoint also completed and independently passed
both audits: `tmp/south-fork-landward-150s-snapshot-v1-20260915.json` and
`tmp/south-fork-landward-150s-banks-v1-20260915.json`. All 5,350,400 cells checked,
all 86,720 bank-face cells exactly dry; depth 3.952322866 m, speed
12.168753620 m/s, maximum step residual 1.283153361e-8 m3. Net boundary flow
is still about +20.102379 m3/s: NOT settled. The same live process continues
toward 600 seconds; next complete checkpoint is local step 3000 / absolute
200 seconds. Never mix the older-geometry 600-second state into this bed.

All visual, 30 FPS, full traversal, remaining physical regressions and
Colorado -> Pacuare -> Futaleufu / other scenes / crew / release gates remain
open. Troublemaker remains a rapid within South Fork, never a menu scenario.
