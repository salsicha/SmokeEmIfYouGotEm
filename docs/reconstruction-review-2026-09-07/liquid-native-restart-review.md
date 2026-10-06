# Native generation and restart — September 10

South Fork remains incomplete. This verifies bounded native water restart and
identity/transport safety, not the playable river, dense sustained flow, reference
appearance or frame rate.

## Enforced generation lifetime

`RaftSimLiquidLifetime.h` replaces the previously comment-only generation
contract with a coordinator and generation-scoped tick tokens. It checks complete
owner/reset participation, consecutive ticks, non-reused transfer epochs, and
one transfer claim per open tick. A stale generation, closed tick, duplicate
transfer, unexpected native reset, skipped tick or exhausted identity namespace
fails closed. Failed coordinators cannot be reinitialized; restart requires a
fresh coordinator and fresh native systems.

Cumulative native birth counts are uint64. All 2^32 unsigned identity patterns
are permitted, including the signed-negative half; the next birth is rejected
instead of authorizing a transfer with a reused identity. These checks run on
the observed first native stage's spawn plan, before cross-owner coupling. They
are not a claim that this hook can cancel Niagara's already-dispatched spawn or
that a production pre-spawn allocation/reset policy has been finished.

The native handoff entry point now requires a claimed tick token. Generation
GUIDs accompany every particle sample, handoff record and stage group. Independent
audits check that all of them agree and that lifetime counts match the complete
native spawn schedule. New captures are checked by both the retiring and closed
handoff audit paths. Old captures without generation metadata remain historical
transport evidence, not restart evidence.

## Bugs exposed by same-process restart

The replay driver can stop and recreate all twelve native regions in the same
world/process, then repeat the full inlet/outlet test. It does not quit Unreal
between generations or clear unrelated objects.

1. `liquid-native-restart-v1`: generation one completed, generation two setup
   failed. Fixed duplicate transient system names being reused while destroyed
   components still referenced the prior object. Creation now uses
   `MakeUniqueObjectName`; the existing refusal to change a referenced system
   remains intact.
2. `liquid-native-restart-v2`: both captures completed, but the independent audit
   **rejected** generation two for lost particles. Four ticks had been batched
   with the initial reset; native CPU dispatch bounds were prepared before the
   next-view incoming-particle reservation, so imported particles disappeared
   on the next native step. Engine exit success was not treated as acceptance.
3. Fixed a first-native-tick barrier in the driver, based on observed native
   stage progress rather than a fixed frame delay. The coordinator also refuses
   transfer until incoming dispatch reservation has actually been installed.
   This prevents an early multi-tick reset batch from silently losing imports.

## Verified live evidence

Builds 18821, 31174 and final 13066 succeeded. Final
`liquid-native-restart-v3` (session 41397, terminal exit 0) and its independent
`restart-audit.json` pass for both generations in process 28708:

| Evidence | First generation | Restarted generation |
| --- | ---: | ---: |
| Initial particles | 12 | 12 |
| New native births by retained P2G | 10 | 10 |
| Approved downstream exits | 3 | 3 |
| Native survivors | 19 | 19 |
| Consecutive native commits | 9 | 9 |
| Verified moving segments | 117 | 117 |
| Deposited physical volume (m3) | 0.39583458469132893 | 0.39583434810811013 |
| Expected survivor volume (m3) | 0.39583334513008595 | 0.39583334513008595 |

Both raw P2G/reduction audits pass with zero reduction mismatches and the original
computed numeric envelope (approximately 0.005132859061343158 m3). Shared nonzero
column-cell counts are 76 and 84. Different scheduling/roundoff need not produce
identical snapshots; each replay independently satisfies the same physical and
identity checks. The full recorded lifetime includes 11/12 native steps and
22/23 births respectively; the second includes a later step beyond the retained
P2G snapshot, which is separately accounted for rather than mistaken for loss.

Native generation GUIDs:

- `8d95d147-4f72-ab47-6410-44be37b3fcd5`
- `05f9553a-4adf-9b1f-16b3-8c82be923886`

285 liquid-specific Python tests pass, including six generation-auditor tests.
The new engine lifetime test exercises stale/duplicate/closed tokens, unexpected
resets, skipped steps, full uint32 birth namespace exhaustion and missing owners.
`engine-liquid-lifetime-v1` (session 29021, terminal exit 0) runs all thirteen
engine regressions successfully, with no failures or RHI errors. One unrelated
HTTP connectivity timeout is recorded as a warning. All owned engine/build
processes are terminal. Saved geographic map SHA256 remains
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.

## Remaining work

Bounded restart is now exercised; this does not complete sustained allocation,
empty-region repopulation under dense transport, calibrated physical inlet flow,
long-duration discharge stability or the playable river. Next establish the
dense native allocation/dispatch budget without retaining the probe's entire
full-state history each tick, then run the actual prepared water and exterior
forcing. Keep the real single-surface/crest/foam/shoreline, raft collision/drift,
reference/FPS and complete multi-river/crew/cleanup/release requirements open.
No saved geographic map or production assets were promoted in this pass.
