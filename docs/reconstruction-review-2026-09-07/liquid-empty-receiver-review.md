# South Fork initially empty native receiver

2026-09-10. Progress on the active queue, not scene/visual/performance acceptance.

## Change

Niagara's `PrepareTicksForProxy` skips `SpawnInfo.MaxParticleCount` for zero CPU
instances when `fx.NiagaraBatcher.FreeBufferEarly` is on. That explains why empty
owners had only one allocated slot despite the requested 32-particle manual
preallocation. The handoff probe now retains manual capacity for *all* regions,
including initially empty ones, and reserves the bounded CPU dispatch upper count
for them before tick preparation. Actual live counts remain on the GPU; assigning
the CPU upper count does not invent live water particles.

The early-free override is scoped to this transient probe and restored by
`StopProbe`, including failure/world cleanup. No engine source or saved asset was
modified. This is not a production memory-management policy: the probe has no
post-initial births and at most sixteen total particles. Dense water, continuously
growing source budgets, reset ticks, and source/exterior lifecycle still need
their own correct reservation/accounting implementation.

`-RaftSimRegionalEmptyReceiver` only changes the test's initial conditions: owner
0 has no seeds; owners 1, 4 and 5 receive three each. The capacity fix applies to
every handoff probe, not just this test flag. Exact birth counts and actual native
empty-to-nonempty snapshots are required by the auditor. A seeded receiver cannot
pass this check, nor can a missing particle be explained away as empty-start input.

## Evidence

`liquid-native-empty-receiver-v1` finished with a clean RHI-validated log:

- Three consecutive actual native commits with owner changes `[9, 0, 0]`.
- Owner 0 is empty at birth and before the first commit, receives nine particles,
  and retains all nine on native step 6; all nine continue moving.
- Full native payload, local persistent-ID remapping, free-ID tables, per-commit
  epochs, birth identity and subsequent ownership checks pass.
- Native P2G passes, with zero reduced-component mismatches and 56 nonzero shared
  cells. Physical volume 0.1875001064618118 m3 versus 0.18750000558793545 m3;
  predeclared numerical envelope 0.0024716857135242735 m3. This is not a long-run
  discharge/conservation or performance test.
- 249 liquid-specific Python unittest tests pass, including rejection of seeded
  receivers and lost/invented particle counts. Scoped whitespace check passes.

After generalizing the reservation to every handoff run, build73985 succeeded.
`liquid-native-reservation-regression-v1` also passes: three native commits with
owner changes `[6, 3, 0]`, all twelve particles survive/move on step6, all full-word,
identity/free-table/history checks pass. Native P2G/reduction pass with 84 nonzero
shared cells, physical volume 0.2500001434564183 m3 versus 0.2500000074505806 m3.
RHI log clean, process35618 exited 0. No owned engine/build process remains live.

Saved geographic map SHA256 remains
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.
No map promotion, final commit or push. The goal remains active.

## Next implementation

Continuous births/exits and generation/reset lifetime, followed by dense regional
fluid and single connected surface/foam. The existing initial-state reader keeps
the external-source spawn branch, but its actual native birth timing and source
position must be verified: a nonzero configured spawn rate is not proof of water
entering the domain. Do not reuse the no-new-birth reservation as a production
source budget. Preserve actual source-volume accounting and global birth identity
across new births, migration and retirement, then complete the original scene,
raft, reference imagery and CPU/GPU/FPS acceptance work.
