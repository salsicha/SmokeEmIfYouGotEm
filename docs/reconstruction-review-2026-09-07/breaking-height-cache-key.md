# Crest-height identity without foam-only invalidation

September28 UTC. Native implementation and correctness checks complete;
v22 packaging is running. Local commit dbb6961b1; no push. Not a delivered FPS gain, breaking-water visual
improvement, complete physics law or South Fork acceptance.

## Normal-scene change

The ordinary Cartesian crest-height key included every site's spilling
fraction and intensity. The height evaluator does not read spilling fraction;
for physical sites it uses the already resolved physical height instead of
intensity. These optical changes could invalidate adaptive geometry even when
its continuous height function was identical.

`RaftSimBreakingHeightKey.h` builds the height-only identity used directly by
`RaftSimWaterSurfaceActor.cpp`. It omits spilling fraction, and replaces only
physical-site intensity with a fixed zero. It retains site count/order, exact
coordinates, directions, physical height/length, local-cap flag, legacy-site
intensity and all four global height inputs. No rounding, threshold change,
quality reduction, source-history bypass or simulation-time change is made.
The full fresh support-site records still feed foam, indexed sampling and
material data. Foam is not frozen to obtain a cache hit. The known-broken
nonlinear solver remains off; hydraulic fields/materials are unchanged.

This only avoids selection work when geometry, height profile and detail
window actually remain identical. Real rapid motion often changes other
inputs: synthetic cache hits do not establish a whole-game speedup.

## Verification

Editor build succeeds in145.21s. Eight rendered D3D12 native tests pass with
zero failed, warning, not-run or in-process tests and no runtime error/fatal
log entries. Verification session27361/wrapper17344/native31060 is terminal,
completed2026-09-28T09:28:19.1390519Z. The later package wrapper reuses PID17344;
identify jobs using their separate receipt/start time, not PID alone.

Two new tests cover:

- Full and indexed height invariance across1,445 independent
  sample positions while the actual foam source changes. Every retained
  physical/global height input invalidates; legacy intensity still changes
  actual height and invalidates. Site removal/order and branch changes remain.
- Twelve evolving frames using the actual height function: two cached builds
  rather than twelve forced builds, zero height queries on optical-only
  updates, exact topology, ownership, target corrections, vertex positions,
  normals, colours, UVs, tangents and temporal history. The reference forces
  rebuilding without resetting its temporal history.

Existing crest target-cache, selective-edge/mode, fine-crest, curved-bank and
crest-history tests also pass. Protected user's native water-surface test
remains SHA256
`d9abdd3643882d192e41af879eef023ed1e58f12a39d26698e42cb0f0773e8f3`.

- Recipe: `tmp/verify-breaking-height-key-v1-20260928.ps1`.
- Receipt: `tmp/breaking-height-key-v1-20260928-process.json`.
- Native report: `tmp/breaking-height-key-v1-20260928-native/index.json`.
- Build log: `tmp/breaking-height-key-v1-20260928-build-console.log`.

All five frozen native inputs still match. No Python source-replay input was
edited. Original source replay84030/Python33152 remains live, index0 checked,
index1 started, no error output; do not duplicate or alter its frozen inputs.

## One pending package; no timing acceptance

Session49561/wrapper17344 runs
`tmp/package-breaking-height-key-v22-20260928.ps1`; receipt
`tmp/breaking-height-key-v22-package-20260928.json`, start09:30:09.0845466Z.
Compression96592/wrapper37212 is COMPLETE; this same owner is now packaging.
It requires verified preservation,14GiB free,
no competing native build, successful eight-test evidence, and12 frozen input
hashes before packaging the normal game into a fresh
`tmp/south-fork-playable-v22-20260928/Windows`. It verifies staged payload
closure and frozen inputs afterward. No runtime benchmark is queued.

Compression is limited to old v8-v13 staged runtime-data copies and PDBs,
stopping at15GiB free or the end of that list. Every file is hashed before
and after. No source/capture/package deletion or hardlink alias is permitted.
Receipt: `tmp/v8-to-v13-staged-data-compression-20260928.json`.
Completed09:34:14.5182922Z with18,378 before/after file hashes unchanged,
zero files deleted. Independent compact-log totals give5,612,225,724 data
bytes saved. Free space after was16,502,554,624 bytes, above the unchanged
14GiB packaging gate. Compression is reversible; all six stages remain.

Next inspect these SAME owners. After successful package/closure and source
replay completion, verify the normal Boot/menu path, actual rapid motion,
shoreline/contact continuity and isolated1200-frame menu/8310/11520 costs.
Do not claim synthetic avoided work as measured FPS, or reuse old v21 footage
as proof of the new executable. Retain all failed20FPS/hitch results and the
unresolved flat foam, weak breaking, shoreline, terrain and crew shortcomings.
South Fork stays first; Colorado/Pacuare/Futaleufu remain queued.

## v22 playable delivery and retained failures

The pending-package paragraph above is historical. The SAME package49561
completed successfully: BuildCookRun450.57s, exit0, closure2405files/
917995570bytes, no external fallback, all12 frozen inputs unchanged.
Receipt completed2026-09-28T09:42:32.3186942Z. No second cook was launched.

One follow-through16700/wrapper37892 completed09:49:56.6231640Z, exit0:
tmp/validate-height-key-v22-motion-20260928.ps1, receipt
tmp/height-key-v22-motion-20260928.json. Actual staged default Boot -> main
menu -> FullReach -> post-travel600-frame capture ordering passed; exactly
one of each required event, zero runtime error/fatal entries, actual normal
selective-edge mode confirmed. The600-frame CSV is an automatic smoke-test
stop, NOT isolated timing evidence. Original Python33152 remained live
throughout; no profiler isolation guard was changed or bypassed, and no FPS
statistics/acceptance are reported from this concurrent run.

Separate actual rapid review starts at8310 in that SAME normal-scene binary.
80 telemetry samples advance8313.076 ->8487.313m,174.237m total, no runtime
errors. All18 spray source centres pass unchanged6/3/3cm checks; this does
not validate particle trajectories or realistic breaking. Contact evidence
samples1897 wet points with max support/carrier error0.00004764635cm;
128 raw-dry points,126 ground-occluded, zero occluded wet and zero unavailable.
These are independent submitted-triangle support probes, not a full collision
or temporal shoreline test.

Two raw-dry probes have rendered water above registered ground and remain
failures, not silently removed or treated as wet:

- XY(-542609.867033,-360212.234553)cm: water870.852992cm,
  ground868.137817cm, raw depth0, hydraulic bed8.666412m.
  Source cell has three wet corners and one dry corner.
- XY(-539440.000000,-360243.409684)cm: water960.875862cm,
  ground958.122681cm, raw depth0, hydraulic bed9.612991m.
  Source cell has two wet corners and two dry corners.

Full triangle vertices and same-call cached/current source cells are retained
in tmp/sf-v22-motion-20260928-contact.json. Changed time/triangulation changes
the sampling set; this is NOT proof the cache repair introduced the failures,
nor does it resolve the older positive-film point. Next reproduce these exact
points/triangles against the shoreline construction before changing geometry.
Do not lower the wet threshold, weaken support gates or hide dry probes.

The original engine video fully decodes2482frames, monotone PTS0..82.7s,
44 exact adjacent duplicates,1280x720. Seven retained samples include6/20/80s
views inspected here: raft moves through rapid into calmer water; broad flat
white foam, weak breaking, coarse banks and crew fit remain. No full temporal
continuity, collision, animation or visual acceptance is claimed. Recording
frame rate is not engine frame rate. Decoder61554 completed exit0; output
tmp/sf-v22-motion-decoded-20260928/report.json.

Binary SHA256:
65a222ed55bf0825eee7bdcb53600d7f8bd6410e4254c31b86eafe1319533521.
Video SHA256:
689985dfec4d3f8a39cb75a04d3ff546c966a710df19dba77d4b10da5e584eee.
Contact SHA256:
bff4c53b8ad86c0003b40036862ae8c0e8e6aeb3a2e238e5e70ab0ff4dd2b74f.
All12 source inputs and executable still match after runtime. Protected user
test unchanged. No captured data deletion, solver/field/material edit or push.

No package/game/decode owner remains live. Source replay33152 alone remains
at index1 after index0 passed; keep its existing owner and frozen inputs.
Its uncompleted report is not acceptance. After terminal provenance checks,
run isolated normal menu/8310/11520 timing at the unchanged20FPS target
(p95<=50ms, zero frames>100ms); retain failures. No new cook is queued.
This is playable integration verification of the narrow cache optimization,
not a demonstrated visible or performance improvement or South Fork completion.
