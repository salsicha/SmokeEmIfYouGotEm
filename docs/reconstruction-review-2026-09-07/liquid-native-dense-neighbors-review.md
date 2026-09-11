# South Fork dense native water: neighbor storage refresh

September 10, 2026. South Fork remains incomplete. No saved scene promotion,
visual acceptance, packaged-game FPS claim, commit, or push.

## What changed

The earlier compact-handoff pass retained only the commit control/count/exit
summary instead of full particle histories. It preserves the native transfer
transaction and limits accepted destinations to their dispatch reservations.
The small compact replay (`liquid-native-compact-v1`) passes with 19 surviving
particles and 2,736 bytes of history for nine commits. Compact telemetry does
not establish exact per-exit trajectory/payload history.

The dense mode uses all 719,335 original prepared particles, original velocities,
all twelve regional owners, and the prepared parent exterior/inlet forcing
(nominal 47.006805 m³/s). It does not substitute the small authored packet.
Per-owner dispatch reservations and allocation headroom remain bounded review
settings, not a production lifetime/repopulation solution.

The original `liquid-native-dense-v1` retained the particle population but failed
the independent raw particle-to-grid (P2G) check. Owner 4 deposited only
5.4463579 m³ against 1,788.3958866 m³ expected. The other eleven owners passed
their local checks. This capture is rejected, not a dense-flow success.

## Cause and scoped fix

The engine's `FNiagaraPooledRWBuffer::InitializeInternal` replaces its storage
without invalidating cached SRV/UAV views in the same render graph. NeighborQuery
grows its slot storage during birth frames. A subsequent stage can therefore
use views of the prior allocation, despite the wrapper pointing to new storage.

The regional native coordinator now drops cached neighbor views after the first
aligned Spawn/Update group, before the complete post-spawn neighbor insertion.
It uses the exported `EndGraphUsage` operation; it does not clear particles,
alter native counts, change the flow field, or modify engine source. Existing
queued passes keep their own RDG resource references. The refresh occurs once
per observed native step and is reported in the capture.

An optional owner-4 snapshot retains the insertion cell/ID/tag arrays, histogram,
prefix offsets, and sorted ID/tag arrays. The independent auditor checks exact
histogram and prefix sums, per-cell scatter membership, and the complete current
persistent-identity multiset, without assuming parallel storage order.

The first direct-buffer-copy diagnostic (`dense-nq-v1`) exposed empty newly
allocated slot buffers alongside populated histograms; v2's view refresh restored
neighbor membership. Both are rejected validation captures: direct copies from
some native buffers violate their missing `BUF_SourceCopy` flag. The final
diagnostic reads through a small integer shader into its own readback-capable
buffer, with no writes to native storage. GPU regression covers signed bits,
out-of-range requests, wrong formats, and a source without that copy flag.

## Accepted bounded evidence

`liquid-native-dense-nq-v3` completed successfully in the actual engine (process
29816). The clean v3
capture and original P2G audit show:

- 719,335 original births + 149 inlet births − 0 exits = 719,484 survivors.
- Three continuous native commits; five observed native steps, five view
  refreshes, 223 aligned groups. Retained compact history is 912 bytes.
- All original seed IDs and birth positions match the prepared state; native
  identities and current physical owner membership agree, including inter-region
  transfers. 719,325 original particles moved; maximum displacement 41.4778 cm.
- Owner 4's 85,762 current particles occupy 22,887 nonempty neighbor cells.
  Insertion/histogram/prefix/scatter/current identity agreement is exact.
- Owner 4 deposits 1,786.7081241 m³ against 1,786.7083866 m³ expected, with zero
  component mismatches under the unchanged float32 error envelope.
- All twelve raw P2G owners pass; regional reduction has zero mismatches and
  20,072 nonzero shared-column cells.
- Physical-grid volume is 14,973.3441127 m³ versus nominal 14,989.2504467 m³;
  the pre-existing accumulated numeric bound is 173.7878288 m³. This is a bounded
  numerical check, not proof of sustained discharge or long-run mass balance.

295 liquid Python tests pass, including five neighbor-consistency tests. Builds
56829, 93782, 52069 and 86747 completed successfully. Rejected diagnostics are
retained. `engine-liquid-dense-neighbors` (session79506, terminal exit0) passes
all13 regressions with zero test warnings/failures and no RHI errors (ordinary
editor-startup warnings are still present). `liquid-native-neighbor-restart`
(session35034, terminal exit0) independently passes both full-history generations
in process19596: 12 initial + 10 births - 3 exits = 19 survivors in each, exact
identity/payload/exit history and original raw P2G checks. All owned processes
are terminal. Scoped whitespace checks are clean.

The saved review map remains SHA256
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.

## Still required

Longer dense source/exit flow, allocation/repopulation and lifetime checks;
single continuous surface, visible crests/froth/spray, terrain and shoreline
consistency; raft/current/collision coupling; reference comparisons and actual
playable performance. Later rivers, crew, cleanup and final release/commit remain
in the original queue. The last actual beauty review is still rejected.
