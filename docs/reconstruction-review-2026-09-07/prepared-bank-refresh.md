# Current-call bank preparation and rebuild reuse

September28 UTC. CPU shoreline optimization, not a new hydraulic model, depth
tolerance, shoreline shape or visible-water acceptance. The isolated v24 baseline
still fails20FPS and accumulates simulation debt; see
[actual timing and clock](adjacent-bank-envelope-design.md#v24-isolated-normal-settings-performance-and-clock).

## Implementation

`FTopologyCache::Update` refreshes independent curved banks in16-bank batches
only when at least128 banks are present. Smaller sets retain the original serial
loop. Source vertices and already refreshed shared-edge nodes are read-only;
each bank owns its metadata and disjoint interior vertices. Changed-size banks
do not write into their old ranges. Workers join before winding checks or rebuild.

When current depths change a node count or triangle winding, the full topology
is still rebuilt. The already computed local curves can be carried into that
rebuild within the SAME call. Adoption requires identical four source IDs, dry
corner/pair classification, current bed/depth values, and exact actual shared-edge
XY endpoints. Node IDs, all vertex attributes, indices and cell ownership are
regenerated. A mismatch recomputes the curve. Nothing survives to authorize a
stale profile on a later frame; wet masks, availability, XY and eligibility keep
their existing full validation. No physical time is dropped or fixed step changed.

`RaftSimSerialBankCurves` retains the old scheduling/repeated-solve path as an
explicit diagnostic control; ordinary callers use the qualified candidate.
The unrelated conservative three-wet envelope candidate remains unintegrated.

## Verification and rejected intermediate results

Initial parallel-only implementation passed12 native tests and two64-pair live
captures, preserving all submitted attribute bits, ordered triangle indices,
ownership, current curve coordinates/fractions and rebuild/reuse counters.
At8310 the small58-60-bank set improved3.9361->3.8312ms when serial-first but
regressed1.4379->1.5284ms when parallel-first. This did NOT qualify as a general
improvement. At11520,60/64 updates rebuilt topology, identifying repeated curve
solves as a separate target. Original receipts remain `tmp/parallel-bank-v1-20260928-*`
and `tmp/parallel-bank-live-v1-{8310,11520}-20260928.json`.

The v2 native run failed the explicit prepared-reuse COVERAGE assertion: its
small additive depth changes did not exercise the new same-call handoff. All
geometry comparisons passed, but that was insufficient. The assertion was NOT
removed or lowered. The final test scales wet donors together so fan eligibility
stays fixed while adaptive node counts change. It covers96 frame/configuration
combinations with reflected world axes, compact/reserved storage, changing
depths, attributes, positive films, availability, wet masks and moving XY.
It requires more than100 prepared reuses, plus actual cache reuse and rebuilds.

Final v3 editor build22.32s and all12 rendered native tests PASS, zero warnings,
failures, skipped or running tests. Native owner21416 ended0 at12:35:31.9259196Z.
Receipt `tmp/parallel-bank-v3-20260928-process.json`; all17 frozen inputs were
independently rehashed after completion, including the untouched user water test.

Two new live FullReach editor-game captures each contain64 exact pairs after
two warmups, with32 pairs in each execution order. Both histories complete exit0,
zero runtime errors, unchanged17 inputs. These are whole shoreline-cache update
timers with source copies excluded equally; nested work is not summed. They are
NOT isolated packaged FPS runs or additional normal-menu validation.

| Live capture / order | Serial mean ms | Candidate mean ms |
| --- | ---: | ---: |
|8310 serial-first|1.584525|1.126435|
|8310 candidate-first|2.059706|1.363043|
|11520 serial-first|6.723919|6.443331|
|11520 candidate-first|6.466241|6.331266|

The new8310 history contains667 banks and no rebuild handoffs. At11520 there are
approximately269 banks,60/64 rebuilds and13,179 prepared curves reused. All128
pairs are exact. The8310 trajectory differs from the earlier small-bank run:
do not compare absolute timings across those histories as a causal speedup.
Within each current pair the inputs and histories are identical.

- Live terminal receipt: `tmp/parallel-bank-live-v3-20260928-process.json`, completed12:38:07.9170150Z.
-8310 report SHA256:1885c1a50b3c0c7826c39c63e19e4f09c946709e43dd23577c752d20bacdfdf3.
-11520 report SHA256:480948cdb44fd3b48942a8ab921c16fed0e069295fecca8f68cd28b2d49a690d.
- Reports: `tmp/parallel-bank-live-v3-{8310,11520}-20260928.json`.

## Playable delivery and storage gate

Normal v24 is still the last delivered package. Next build normal v25, verify
staged source closure, Boot/menu travel, actual rapid motion/contact and isolated
menu/8310/11520 performance/clock. The component gain is modest and does not
establish20FPS, zero hitches or zero growing simulation debt. Do not weaken those
gates or claim full river/shoreline/physics/animation acceptance.

Lossless compression, no deletion:17 inactive September24 package snapshots,
symbols/Paks retained all content hashes (`tmp/retired-sep24-stage-compression-20260928.json`).
Eleven closed historical diagnostic JSON ledgers likewise retain every hash
(`tmp/closed-ledger-compression-20260928.json`). Current v21/v23/v24 timing packages,
captured sources and runtime payloads are untouched. Further headroom recovery
uses the two original-v4 executable/symbol backups with the same hash checks.
The14GiB next-package gate is unchanged. No push.

Both original-v4 backup hashes now also pass; receipt
`tmp/original-v4-backup-compression-20260928.json`. All30 compressed files are
preserved. Free space reached15,261,855,744bytes; the14GiB gate passed before
starting ONE normal v25 BuildCookRun at12:43:27.4830401Z. Session49968/wrapper18052
is LIVE. Receipt `tmp/parallel-bank-v25-package-20260928.json` freezes22 inputs;
recipe `tmp/package-prepared-bank-v25-20260928.ps1`; stage
`tmp/south-fork-playable-v25-20260928`. Follow this owner, do not duplicate it or
edit frozen source/assets. On terminal0 independently verify receipt,22 hashes
and staged closure. Then run `tmp/validate-prepared-bank-v25-motion-20260928.ps1`,
decode and inspect the actual video/contact evidence, and measure isolated
menu/8310/11520 frames AND bridge-clock debt. No source replay remains live.

## v25 terminal playable validation

The preceding LIVE/pending state is superseded. The same package owner completed
exit0 at12:51:44.9495493Z, BuildCookRun452.62s. Staged closure verifies2405 files,
917995570bytes, with no external-source fallback. All22 frozen source/asset
hashes were independently rechecked unchanged. Normal staged executable SHA256:
`422cd9748a285ea29cbfc94586c1b79db6945ebb24eb4c9043271915fe87ef94`.

`tmp/parallel-bank-v25-motion-20260928.json` completed at12:54:11.3545565Z,
both game processes exit0 and zero runtime Error/Fatal entries. Default Boot ->
real main menu -> FullReach ->600 post-travel frames is verified in order.
The separate normal-settings8310 rapid placement recorded80 motion samples from
8313.254 to8487.307m (174.053m). It is not a claim that a normal menu spawns there.

The contact sample has1859 wet probes, maximum support/carrier error
0.000047669091372881667cm,155 raw-dry probes all counted ground-occluded,
zero unavailable or ground-occluded-wet probes. This stride-based sample does
not prove every historical bank location, collision clearance or full reach.
All18 sampled/enabled emitter centres pass6/3/3cm anchor clearances; this is
not whole-particle landing or breaking-wave acceptance.

Original video `tmp/south-fork-playable-v25-20260928/Windows/SmokeEmIfYouGotEm/Saved/VideoCaptures/RaftSim_20260928-055245.mp4`
has SHA256 `0c6cc61ae2b8b369ff306d6deb57324b22a625f80ddaec646810db1fd311dbe2`.
Full decode:2481 frames,82.666667s,1280x720,41 exact adjacent duplicates;
all seven requested review frames are present in `tmp/sf-v25-motion-decoded-20260928`.
The6/20/80s engine views show a moving raft from the rapid to quieter water,
but broad flat foam, weak breaking, coarse boulders/banks and crew/paddle fit
remain unacceptable. This optimization intentionally preserves existing shapes;
it is delivered CPU work, not a new visible hydraulic reconstruction. Encoded
video rate never establishes game FPS, and sampled stills do not clear animation.

After every build/game/decode/source workload ended, three isolated1200-frame
same-binary runs used normal graphics/solver settings;1140 rows30..1169 were
audited in each. Review stations are diagnostic placements, not menu launches.
All exit0, runtime errors0, binary unchanged. No quality/legacy overrides.

| Launch | Mean ms | p95 ms | Maximum ms | Frames >100ms |20FPS timing gate|
| --- | ---: | ---: | ---: | ---: | --- |
|Boot/menu|38.6400|46.1802|51.7660|0|PASS for this sample|
|8310|45.1303|66.6051|183.5665|6|FAIL|
|11520|80.1968|102.1761|195.4715|74|FAIL|

Receipts: `unreal/Saved/RaftSimValidation/sf-v25-isolated-{menu,8310,11520}-20260928-frame-audit.json`.
Strict independent parser/scope/clock reports:
`tmp/sf-v25-isolated-{menu,8310,11520}-20260928-scopes-and-clock.json`.
Actual logs confirm `csv.UseLegacyFrameTime=false`; offset1 aligns preceding
logical-frame timing with scope work. No measured duplicate columns are waived.
CSV SHA256 respectively:

- menu: `bfac92318f2a4e30a866f60a530b821e4e3d7381e03d6acf405ce834962bf9aa`
-8310: `12531bf7954d75e4caeb51ae1ed97a49d0070bc1acb821aad4b3d17562b6913c`
-11520: `1f2cd362b5ff7b3ce9143bfcaec51696551fb42c686e29e4c3d0b9d4ce11400c`

Menu bridge backlog is0.009097->0.012405s, max0.016659s. At8310 it falls
0.902600->0.012258s, max0.937800s. These bounded observations are not sustained
simulation-capacity acceptance. At11520 backlog grows1.3734->16.7611s
(+15.3877s), max16.8551s, with all1140 rows hitting four fixed ticks.
Requested clock advances91.3210s while committed clock advances75.9333s.
Do not hide this shortfall by dropping elapsed time, increasing dt or weakening
the unchanged50ms p95/zero >100ms gates. All capacity-acceptance flags stay false.

At11520 mean GameThread77.9160ms versus GPU23.4117ms; surface Tick52.5313ms
contains publication31.5919ms, SetMesh30.1994ms, crest Update20.2595ms,
Selection13.0492ms and topology8.2997ms. StepWater15.0310ms is separate.
Nested scopes must NOT be summed. These remain CPU publication/crest targets.
The11520 tail worsens versus v24 (p9592.3504ms/8 hitches); separate trajectories
and captures do not establish causation or a controlled overall speedup.
The exact paired component proof does not override this failed playable gate.

No package, runtime, decoder, profile or source owner remains live. Preserve
both packages and evidence. South Fork stays open; three-wet contour integration,
coherent physical breaking/recirculation, complete collision/animation and
sustained timing/clock validation remain. No known-broken solver enabled; no push.
