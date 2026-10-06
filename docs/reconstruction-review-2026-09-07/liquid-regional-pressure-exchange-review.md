# Regional pressure exchange — 2026-09-10

South Fork and the overall queue remain incomplete. This is an implemented GPU
exchange primitive and an **empty-grid** twelve-region integration check, not
wet-flow, conservation, visual, or performance acceptance. No map promotion or
commit. The previous status turn inspected the failed build; this turn corrected
it and implemented/verified the exchange.

## Implemented

- `RaftSimLiquidStageInterface` now collects participating Niagara stage records
  in `PostStage` and broadcasts once in `FinalizePostStage`, after every dispatch
  and interface post-stage callback in that group. The primary initial reader
  binds this interface only for regional installation. Existing defaults remain.
- `RaftSimLiquidHaloGPU` validates physical source cells, unique halo targets,
  distinct untiled R32F textures, bounded compatible dimensions and at most 16
  owners. All bidirectional/corner copies run in **one dispatch per iteration**.
  A read cannot overlap a write: sources are physical interiors and destinations
  are strictly the two-cell XY halos. The mapping upload is reused within the
  same render graph. No whole-volume snapshot or per-interface dispatch chain.
- The unsaved `RaftSim.LiquidRegionalStageProbe start all` creates twelve actual
  regional allocations with their canonical positive-scale actor frames, but
  deliberately clears all initial particles and inlet emission. It locates each
  native pressure grid and dispatches exchange after each aligned `Solve Pressure`
  group. Uses Niagara's own `GetOrCreateTexture`/RDG tracking, without external
  UAV mode or engine modifications. `stop` unregisters and destroys owned actors.
- The probe records every participating stage, iteration, loop, first/last/reset
  flag, region ID, and every source/destination halo address. The Python driver
  independently compares those addresses to the previously audited canonical
  boundary pages, reflecting Y at both endpoints. It also requires a complete
  exchange for every recorded solve iteration and rejects truncated records.

## Actual evidence

Final build succeeded (session 17044). `engine-liquid-pressure-halo-v3/index.json`
has four passing actual-RHI tests in 14.163 s: pressure exchange, reconstruction
owner isolation, all regional geometry, and regional installation. The last has
one unrelated `generate_204` connectivity timeout warning; no test failures.
The pressure test covers all 16 texture slots and compares every float32 voxel
after two exchanges with an intervening write. Physical/non-target values remain
unchanged; duplicate destinations, halo sources, physical targets and aliases
are rejected. All 207 Python liquid tests also passed this turn.

`liquid-regional-stage-groups-all-v2/capture.json` and `stages.json` report:

- All 12 actual regional grids, IDs 0–11, active with zero water.
- 1,414 complete/aligned groups, zero incomplete or misaligned groups.
- 1,080 native pressure-iteration exchanges over 5,960 shared XY columns.
- Every source/destination address matches independently prepared geometry,
  including diagonal owners. No missing iteration or truncated evidence.
- No exchange error or engine/RHI assertion. 15.922 s is diagnostic wall time,
  **not frame rate or performance acceptance**.

Earlier retained failures: `stage-groups-v1` used an editor actor enumeration
that excludes transient actors; `engine-liquid-pressure-halo-v1` hit Unreal's
shader parameter parser on a combined scalar declaration; `stage-groups-v3`
incorrectly interpreted Niagara's `UseRGBATexture` boolean (its scalar R32F
storage also sets it); `stage-groups-v4` incorrectly requested external UAV mode.
All were fixed in project code, without weakening validation. Pair-only `v5`
and all-region `all-v1` passed before the exact-address report was added.

Geographic map SHA remains
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.
No new visual evidence this turn; the previous glossy/lumpy wet fixture remains
visually rejected. Saved source assets are not overwritten by these probes.

## Next work — do not confuse exchange with a coupled fluid solve

1. Install explicit regional terrain/contact and true exterior/shared boundary
   rules before activating water. The empty probe intentionally still uses the
   source template's other physics; its inherited contact/pressure is not a valid
   regional river model. Keep the v3 production installer guard intact.
2. Give the compatible pressure solver a shared **global** color phase and avoid
   solving halo cells as physical owners. In positive-scale Niagara coordinates,
   global XY offset is `(FirstX, ParentNY - RegionNY - FirstY)`, not canonical
   `FirstY`. For the existing row partitions, Y offsets 98/34/0 have different
   wide-stencil color phases. Exchange alone does not correct that.
3. Synchronize boundary/divergence fields and conservatively reduce P2G halo
   contributions before projection. Transfer particles and persistent identity
   between physical owners; share reconstructed surface/foam at cuts. Pressure
   halo copying is not any of these operations and is not a conservation proof.
4. Validate same physical age/delta and reset behavior in the wet orchestrator,
   then measure wet birth, partial-X pressure, contact, mass/flux, crossing waves,
   continuous surface, raft support, reference footage and gameplay performance.
   The native scheduling probe uses identical manual fixed steps; it does not
   prove arbitrary independent component ticks are physically synchronized.

The full sequence remains South Fork → Colorado → Pacuare → Futaleufu, then the
remaining scene/crew/cleanup/release work and final commit.
