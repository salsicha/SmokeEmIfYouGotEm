# Playable crest assembly — September 12

## Measured cause, not performance acceptance

Target-only cache separation passes all55 targeted native/GPU tests:
`unreal/Saved/RaftSimValidation/south-fork-crest-target-cache-regressions-v1-20260912/index.json`.
Geometry selection no longer depends on coarse crest subtraction or shoreline
weights. Current target values still recompute exactly; temporal corrections
and every rendered vertex attribute match a forced selection rebuild.

Isolated normal-map profile1549 exits0; identified cook29308 suspension and
resume both return0. CSV `south-fork-crest-target-cache-profile-v1-20260912.csv`,
SHA256 `5788f38ed81ba1be1487cea770f286163d9c6c242bb802c506395e1d0063a5ac`.
Inclusive rows100..250:12.635722FPS, p9593.5121ms, GPU23.551826ms,
crest update32.461611ms including selection19.941856ms. This does NOT improve
the previous13.019499FPS run and still fails60FPS. Nested scopes must not be
summed. Report `tmp/south-fork-crest-target-cache-performance-v1-20260912.json`.

Exact invalidation counters over151 calls: XY151, profile151, coarse151,
indices0, shore0, detail window2. Therefore target-only separation cannot
avoid selection in this interval. The source triangle layout is stable even
while shore coordinates and physical profile values change.

The profile's actual raft-camera PNG was inspected. Terrain/rocks are present;
smooth wave faces and broad bright water patches remain visually unaccepted.
This is a different camera from the fixed rapid review, not a controlled visual
before/after comparison. No new reference footage was viewed.

## Exact assembly reuse implemented and tested

Each refinement level retains its exact selection mask, ordered midpoint
parents, output triangles and original cell/triangle ownership. Every build
still samples its current XY/profile and makes all selection decisions. Only
when root topology and all preceding masks are identical can assembly reuse
the combinatorial result. Midpoint coordinates are recomputed from current
parents, not retained from a past frame. A changed prefix rebuilds that level
and all subsequent levels. Cache storage is bounded to the current root and
at most three levels. No tolerance, mesh density, profile, update cadence or
acceptance gate was lowered.

New regression compares20 changing frames against a forced-empty cache and a
serial build: exact parents, triangles, owners, current coordinates and current
interpolated values; varying height, XY, window, root winding and level count.
Build97812 exits0 in203.94s (existing D6 damping conversion warnings retained).
Native/D3D12 regression45905 exits0:56successes, zero warnings/failures/unrun.
Report `unreal/Saved/RaftSimValidation/south-fork-topology-cache-regressions-v1-20260912/index.json`.
The new fixture compares38,416 vertices;25 assembled levels and33 reused levels
versus58 forced assembled levels. Actual-play performance is still being measured.

Built RaftDLL SHA256
`3925f625b245a86af6d3a04ca8fa7833eae41e1eadff9572f409f293ecc31644`;
mainDLL `d5643b642117a3aa7c7ac78361ff44c0328de0d46304661cfd44ce8cd78dab5b`.
Mapdb3080cc…, materiale4e9b2f3… and save181d1e57… rehashed unchanged.

First assembly-cache profile54673 exits0 with cook suspend/resume0.151 sampled
calls reuse268 levels and assemble17;95 selection calls, source XY/profile
changes94, indices/shore0, detail window2. Mean58.998050ms=16.949713FPS,
p9593.0764ms STILL FAIL60; GPU16.901469ms. Crest update20.572271ms, selection
8.814528ms across all151 rows (14.010461ms among95 positive rows). Refresh93
positive rows versus151 previously; scheduling thresholds/trajectory differ
with frame time, so this short run is not a controlled fixed-trajectory or
sustained speedup guarantee. Persistent detail backlog8.238ms at34.042s.
CSV SHA256 `aaf2daedfd49f70c8a9d02734a2ce650808c4082c455a56864d92da887864f12`;
report `tmp/south-fork-topology-cache-performance-v1-20260912.json`.

Follow-up build16730 exits0 in19.53s: when every level reuses its exact topology,
retain the identical combinatorial boundary-midpoint flags. Current fine
profile evaluations now run independently in parallel, as selection already
does. No cached heights cross a profile change. RaftDLL now
`fe53d43d1d9e0d10bee6050dc711f1b108ac626a94c6a3fd32ce107451fca60e`.
Final regression99951 exits0:56successes, zero warnings/failures/unrun;
`unreal/Saved/RaftSimValidation/south-fork-topology-cache-regressions-v2-20260912/index.json`.
Final isolated profile18441 exits0, cook suspend/resume0. Same151 rows:
mean56.578473ms=**17.674567FPS**, p9581.0531ms STILL FAIL60.
GPU16.851860ms; crest update18.032328ms including selection9.072309ms
(13.563550ms among101 positive rows).100 XY/profile changes,0 index/shore
changes,2 detail-window changes;15 levels built,288 reused. Mean improves
over13.019499FPS pre-cache and16.949713FPS first-cache short runs, but none is
sustained or release acceptance. CSV SHA256
`101756442b6a8a8befaed278374147fa783bc0fa145e761b64972c0780f04b76`;
report `tmp/south-fork-topology-cache-performance-v2-20260912.json`.
Detail simulation34.033335s over34.038s, backlog5.026ms,3 exact remaps,
0 teleports.

Final actual game46667 exits0. Crest report
`tmp/south-fork-topology-cache-crest-v2-20260912.json.cartesian-mesh.json`:
1,550,016 samples, max target error0.6006679535cm<=2cm, fine temporal correction
tracking0.0003077984cm, sourcechange0;50,625source/68,117active/77,824render
vertices and50,511submittedtriangles. This excludes GPU detail, other relief
and macro temporal lag, so is not total contact/shaded surface acceptance.
Foam report `tmp/south-fork-topology-cache-transport-v2-20260912.json`:
all50,625 source UV3 backtrace errors0, unchanged bulk UV1 errors0.

Actual fixed-camera series `south-fork-topology-cache-v2-20260912` contains40
unique PNGs across12.761 sampled game seconds. Frames000/039 inspected: broad
smooth central wave and thin linear foam persist, NOT convincing breaking or
froth acceptance. Movie `unreal/Saved/VideoCaptures/RaftSim_20260912-160818.mp4`,
SHA256 `8929068051ce363461125a1122b03a4ce59848b3a0f8ee88597b6e04eeb852ea`;
86sourceframes/17.325s is diagnostic capture, not FPS or continuously viewed
motion. Recording lags detail5.721453s at27.246elapsed (21.525001 simulated),
3 exact remaps,0teleports. Do not replace the isolated profile's5.026ms lag
with the heavy capture's lag or claim correct recording-time physics pace.
Motion report `tmp/south-fork-topology-cache-motion-v2-20260912.json`.

NEXT: remaining current-profile selection/vertex-normal/refresh/GPU costs;
physical crest/overfall and persistent entrainment/optics, GPU/raft contact,
ordinary-play motion and full-river lifecycle. Do not treat cache or sampling
passes as visual completion. No real reference playback became available.

South Fork remains the scenario; Troublemaker is an internal rapid. Catalog and
save migration tests remain in the targeted suite. Hydraulic1900s v3 state and
all86,720 artificial face cells pass their independent audits, but discharge
is still settling. Runtime remains the audited600s baseline. All realism,
contact, full-river, later-river, crew and release requirements remain open.
