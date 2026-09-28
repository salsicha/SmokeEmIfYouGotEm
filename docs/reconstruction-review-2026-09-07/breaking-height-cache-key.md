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
