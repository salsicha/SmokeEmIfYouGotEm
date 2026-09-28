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
