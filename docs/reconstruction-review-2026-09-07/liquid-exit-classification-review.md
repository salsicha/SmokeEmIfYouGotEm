# Physical parent outlet crossing classification

2026-09-10. Goal active; this is not sustained flow or scene acceptance.

## Implementation

`RaftSimLiquidParticleExitGPU` reads the original full native route packet and its
verified `RiverStepStartPosition`/current-position planes. It writes separate
candidate records and accounting, without modifying or deleting native particles.
The first outward segment intersection is computed against all six faces of the
physical parent box, not each regional tile. A local ownership cut stays inside.
Floor/roof escapes, ambiguous simultaneous corner crossings, invalid/stale source
indices, nonfinite endpoints and origins already outside are not approved.

An approved horizontal exit uses the row at the crossing point, not the endpoint
outside the box. The row must be wet, have negative inward normal speed (the same
outgoing condition used by the pressure-stage boundary), and the intersection
must be above its bed. Spray above the prescribed stage may leave a wet outlet;
the stage is not a ceiling. Dry rows, below-bed leaks, closed rows and prescribed
inlets do not become outlets. Inlet flow reversal is not silently authorized by
this outgoing-pressure policy.

`RaftSimLiquidParentExterior::FProfile::ExitPlan` binds the original validated
parent bed/stage/normal-speed rows. It rejects a changed parent cell count, owner
count, world origin, axes or spacing. It uses the physical height, not the
negative-height discriminator in the existing query ABI. No full-domain texture
is allocated. This does not make the inferred submerged bed captured bathymetry.

Candidate uint4 layout: status, face, global face-row index, float32 intersection
fraction bits. Status0 is inactive,1 stays inside,2 is an approved candidate,
4 is a rejected exterior crossing,8 is invalid input. Eight counters retain
inside; approved west/east/south/north; rejected; invalid; actual source live.
Capacity overflow is counted as invalid, never clamped away. The original packet
still holds every word needed for an exact exit ledger and survivor transaction.

## Verification

- First build failed only at the test's address-of a const vector component;
  fixed by copying its float value. Build42094 then succeeded.
- `engine-liquid-exits-v1` stopped before tests at Unreal's shader parameter
  parser: comma-combined global declarations were incompatible with root
  parameter extraction. Split declarations; no engine modifications.
- `engine-liquid-exits-v2`: the classification assertions passed, but RHI
  validation rejected readback of a test input buffer without `BUF_SourceCopy`.
  Corrected the test allocation rather than disabling validation.
- Final build17727 succeeds. `engine-liquid-exits-v3` executes all eleven engine
  tests successfully, zero warnings/failures and no RHI errors; process exits0.
- New actual GPU cases use a translated, rotated frame and cover internal cuts,
  wet/dry/below-bed rows, above-stage spray, floor/roof first intersections,
  simultaneous corners, outside/nonfinite origins, malformed routes, an exact
  outer endpoint, north/east exits, and the crossing-row/endpoint distinction.
  Empty and over-capacity populations retain exact counts; all original float
  and integer payload bits remain unchanged, including non-position NaN data.
- The regional exterior regression binds all1304 real parent face rows and
  rejects a shifted or unvalidated policy. Existing fluid/identity/handoff
  regressions still pass. 261 liquid-specific Python tests pass.

## Still required

The classifier is not yet connected to native retirement. Existing assembly
still rejects exterior particles (bit2). Next integrate classification with an
atomic survivor/exit transaction: retain exact exited payload, immutable birth
identity, face and volume; validate every source/route/candidate count; reject the
whole transaction for any forbidden exit or capacity error. Only after valid
exit accounting may native live counts and free-ID tables exclude retired
particles. Add live native outlet-crossing evidence, including an entirely
emptied owner, continued emission, and subsequent native motion.

Then reset/generation/lifetime, dense sustained flow, single-surface/foam, raft,
reference imagery and FPS acceptance, followed by the rest of the river/crew/
cleanup queue. No map promotion or final commit. Saved map SHA256 unchanged:
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.
