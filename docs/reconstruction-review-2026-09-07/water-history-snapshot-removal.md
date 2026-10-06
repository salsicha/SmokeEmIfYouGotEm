# Remove retired water-interpolation snapshots

September 28 UTC. Default runtime change delivered in rebuilt v17. Editor
build, rendered native tests, packaged normal launch and bounded motion review
are complete. Menu timing passes; BOTH rapid timing gates still fail. No
causal whole-frame speedup, visual improvement or river acceptance is claimed.

## Terminal packaged results

Validation owner69999/wrapper34984 completed06:26:40.6323838UTC, exit0. No
build, cook, game or capture remains live in this chain. All frozen input
hashes were checked again after runtime validation and remained unchanged.
Staged closure passes2,405files/917,995,570bytes with no external fallback.

Three isolated cooked-standalone runs use normal configuration, D3D12,
1280x720,1200frames, audited rows30..1169. All exit0 with zero runtime errors.

| Run | Mean ms | p95 ms | Maximum ms | Frames>100ms |20FPS gate|
| --- | ---: | ---: | ---: | ---: | --- |
| Boot/menu |38.1535|45.6996|55.2429|0|PASS|
| Rapid8310 |42.7731|54.9304|112.5504|2|FAIL|
| Rapid11520 |45.4329|51.5825|96.9479|0|FAIL|

Reports are `unreal/Saved/RaftSimValidation/sf-v17-<normal-menu|rapid8310|rapid11520>-20260928-frame-audit.json`;
strict scope/clock reports are `tmp/sf-v17-...-scopes-and-clock.json`.
Corresponding raw CSV hashes are
`9ba9989d6ce265a62a27e14346e93674c2ec14bc31b0a716b872544e3d701259`,
`949617e2c156d200bc96d3ce1ef6ac4abfa4243b2ebcfc42492cd81f1045bb72`,
`44c5fca19f124ffcfbfe2dc5fb66755a0fe22e10269a1f2404e571c315634346`.
The11520 source-clock backlog decreases0.5453s to0.003416s, with3,141fixed
ticks and zero failed frames/adapter-commit disagreement. This is a bounded
observation, not new simulation-capacity acceptance. The preceding v16 run's
7.8s backlog is retained; different trajectories/host load are not a controlled
proof that removing these copies caused the large11520 timing difference.

The actual packaged approach retains80samples, station8313.610 to8487.347m
(173.737m), exit0 with no runtime errors. All18enabled/sampled source centres
retain6/3/3cm clearances. Video `RaftSim_20260927-232514.mp4` in the v17
stage's `SmokeEmIfYouGotEm/Saved/VideoCaptures` has SHA256
`12502020a633dc206b4ef0bd41ec04b47489d0ece2f92d39ec48de681674bedf`.
Every frame decodes:2,481frames, increasing PTS0..82.666667s,35exact adjacent
duplicates. Encoder cadence is not gameplay FPS. Original decoded frames and
report: `tmp/sf-v17-motion-decoded-20260928/`.

Inspected6/11/20/40/80s views show the raft passing the right-bank rocks and
progressing into calmer water. Broad flat white foam, weak breaking, detached-
looking spray near the crew, coarse bank/rock geometry and crew-fit limitations
remain. No appearance improvement, complete animation/shoreline stability or
full-hull collision acceptance is established by this memory-work change.

The distinct carrier-contact report was produced at10.008119s:
`tmp/sf-v17-motion-20260928-contact.json`, SHA256
`306dad0ebefa4d726753f9319a34abd9cfdf38db1a17edba7bf71861117e721f`.
1,982wet support probes have maximum error0.0000475907cm and RMS0.0000247583cm
against independently sampled submitted triangles. Paired detail affects896
points.42probes are dry,0unavailable;41are ground-occluded and none of those
report wet support. The remaining dry probe has raw_wet=false at
(-542931.461481,-361170.336937)cm despite its sampled triangle above ground;
retain this shoreline/support discrepancy for follow-up, not acceptance.
The report does not independently verify GPU latency/upload or full traversal.

Native report SHA256:
`52350cdcd5a4cc07705417ab07f34a8979e510a34b99cc3f4f041f05973d27f7`.
Terminal runtime receipt SHA256:
`8a193b974183e0d4c7125868853a160cf1d611e905845b2d60415505da0a5275`.
Decode report SHA256:
`1d7201ab878289cde1cd67cbc962158ebae702aa2dbeff5eafb7613f5231a547`.

Next work remains the measured recurring crest/publication cost and the
unaccepted rapid appearance/shoreline/physical geometry. Do not rerun these
unchanged captures, promote transient hydraulic fields, coalesce away required
history updates, or move to the next river on the strength of this cleanup.
The build chronology below is retained; this terminal section supersedes its
earlier live/pending wording.

## Scoped runtime change

`RefreshSurface` copied all five rendered arrays into interpolation-start
snapshots on each retarget. Repository reference inspection finds no reads of
their contents: only five size guards in `UpdateLiveVolumeCoreInterpolation`.
The current exponential chase already advances the rendered position, normal,
color, flow and wake arrays directly, as documented in
[the original interpolation review](water-interpolation-parallel.md).

Remove those five dead arrays and copies. Check the actual rendered-history
sizes instead before advancing. Leave all target sampling, exponential
arithmetic, fixed timesteps, publication order, fine-crest history and recenter
carry intact. In particular, interpolation publication still precedes refresh;
recenter publication is NOT skipped or coalesced. Invalid live-history shapes
return without mutation. No solver, terrain, bed, collision, material or
captured source change is included. Normal play requires no new opt-in.

The recorded v16 grid has 50,625 source vertices. The removed element storage
is `N*(2*sizeof(FVector)+sizeof(FLinearColor)+2*sizeof(FVector2D))`, plus array
capacity overhead. With this double-vector build, that is 4,860,000 bytes of
payload copied on every eligible refresh and retained as unused snapshots.
This is a source-level memory-work reduction, NOT a measured frame-time gain.

## Verification owner

24 presentation source guards pass in 1.24 s, including a new guard against
retired snapshots and publication-order changes. These are supporting checks,
not engine execution or appearance evidence. The first sandboxed invocation
could not resolve `pytest.__main__`; the same tests ran successfully with
access to the existing dependencies. No package was installed.

Original owner: session52242 / wrapper39448, started
`2026-09-28T06:04:28.9814554Z`. Recipe:
`tmp/verify-water-history-v17-20260928.ps1`; receipt:
`tmp/water-history-v17-verification-20260928.json`. It builds the editor, runs
exact native WaterInterpolation, CrestHistory and ShorelineFineCrest tests,
then stages v17. Failure is terminal and prevents dependent stages. Existing
v14/v15r2/v16 packages and evidence remain untouched. All build inputs are
hashed and frozen until completion; no duplicate build or cook should start.

Editor build succeeded in333.54s. The initial native invocation incorrectly
used NullRHI for a test requiring a real rendering proxy: WaterInterpolation
and CrestHistory passed, while ShorelineFineCrest failed exactly its two
proxy-preservation assertions (both geographic orientations). Original
receipt/report/log are preserved; package never started from that owner.

Recovery owner session79479 / wrapper14624 started
`2026-09-28T06:12:45.0492496Z`, recipe
`tmp/recover-water-history-v17-20260928.ps1`, receipt
`tmp/water-history-v17-rendered-verification-20260928.json`. It reused the
successful build and reran the same three tests with D3D12/RenderOffscreen,
without weakening assertions or filtering errors. All3 pass, zero warnings,
errors, not-run or in-progress tests; native exit0 at06:13:20UTC. Native report:
`tmp/water-history-v17-rendered-native-20260928/index.json`. This owner now
packages the frozen inputs. No other engine/cook/build should run meanwhile.

Package completed06:20:33.1807950UTC, exit0, BuildCookRun429.76s, checked inputs
unchanged. New stage `tmp/south-fork-playable-v17-20260928/Windows`, inner
executable SHA256
`3ad1b9683365060687979a9970d8d50be665202cea1386da65d4354b211ae264`.
Known missing MetaHuman texture-dependency cook warnings remain release work.
Runtime validation now has exactly one owner: session69999 / wrapper34984,
started06:21:03.2378405UTC. Receipt:
`tmp/water-history-v17-validation-20260928.json`. Do not duplicate it or change
its frozen inputs. Build/native/package success is not runtime acceptance.

Prepared runtime recipe `tmp/validate-water-history-v17-20260928.ps1` requires
successful native tests and package completion before running. It checks
staged closure, isolated 1200-frame normal Boot/menu and rapid8310/11520
timing, then an80-sample recorded approach with normal rendering defaults.
The unchanged gates are20FPS, p95<=50ms and no frame>100ms; failed timing is
retained, not hidden by workflow success. Full video decoding and inspection
are still required before judging motion. No causal FPS gain can be inferred
from a single trajectory comparison with v16.

The earlier `RaftSimGroundContactAudit` request is an event-only projection
observer in PhysicsBridgeSubsystem, not a carrier sample export. It writes
only when the observer receives a correction>=5mm, capped at64 observations.
No v16 output exists; that absence alone proves neither collision success nor
the exact reason for no observation. The new recording separately requests
`RaftSimCarrierContactAudit`, which compares actual submitted triangles with
raft water support after10s. These audits answer different questions and are
not interchangeable. Neither constitutes full-hull/traversal acceptance.

South Fork remains first and unfinished; Colorado, Pacuare and Futaleufu are
not advanced by this change. The nonlinear solver remains disabled, and the
450s v8 fields/material/source data are preserved.
