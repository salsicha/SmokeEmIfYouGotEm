# Native particle transfer — 2026-09-10

South Fork and the full queue remain incomplete. These are actual native GPU
particle/grid checks, not a photorealistic scene, sustained-flow, or performance
acceptance. No saved map or Niagara asset was promoted.

## Implementation and observed failure

The regional source template inserted particles into the neighbor query only
during Particle Update. Newly born particles did not enter that update, so their
first P2G step deposited nothing. `liquid-native-packet-v2` preserved four actual
live particles but zero raw volume in every region. The independent audit failed.

Regional clones now insert particles into the same neighbor query at the end of
Particle Spawn too. The inserted module copies the native matrix and parameter
bindings into the spawn stack; it does not link back into the update parameter
map. Native single-bin insertion (method 0), persistent-ID lookup and the complete
centered 27-bin gather remain consistent. The method's inherited dynamic enum is
resolved explicitly for this regional configuration.

The inherited `KillParticlesInVolume` module also used a fixed 21 m fixture box.
That box is not the larger region's physical domain and could delete valid water.
Regional clones disable it, alongside the previously disabled stand-in solid
kill. Captured-terrain projection remains active. This does **not** implement
outflow accounting or particle handoff; those must replace fixture deletion, not
silently discard escaping particles.

## Independent native evidence

`-RaftSimRegionalTransferPacket` retains one existing wet-prior seed from each of
four owners meeting at parent cell corner (128,64). Positions and parent seed
selection remain from the prepared inputs. Deliberately distinct diagnostic
velocities exercise signed momentum; they are not measured river velocities.
The other eight regions have zero particles. Exterior forcing and synthetic
pressure markers are forbidden in this mode.

After the requested aligned native raster step, the probe copies actual live GPU
positions, velocities and counts, immutable raw deposits, and reduced totals.
Default step is 1; `-RaftSimRegionalTransferPacketStep=1..4` selects a later step
inside the bounded replay. Stop drains queued render work before inspecting the
RT-owned snapshot flag. This blocking diagnostic fence is not gameplay code.

`audit_liquid_native_transfer.py` independently reconstructs centered tent weights
from actual particle positions and the rotated anisotropic region frames. It
checks raw volume and local momentum, then independently rebuilds the ownership
map and checks every reduced component exactly. Halo copies are excluded from
physical volume totals. The raw comparison uses a predeclared float32 forward
error envelope; empty regions must remain exactly zero.

`liquid-native-packet-v5/native_transfer_audit.json` verifies the first step:

- Four live particles in four owners; all raw components within their numerical
  envelopes, including momentum, and zero phantom deposits in empty owners.
- Zero mismatched reduced components, with 24 nonzero shared-column cells.
- Physical volume 0.08333362103439867 m³ versus the four-particle nominal volume
  0.0833333358168602 m³. The discrepancy is about 0.000342 percent.
- Capture wall time 26.17 seconds includes loading/compilation/blocking readbacks;
  it is not FPS.

The source/terrain regressions in `liquid-regional-transfer-v5` remain exact:
898 inlet velocities, 6,720 prescribed outlet pressures, 143,040 shared boundary
cells, and 1,587,600 physical interior terrain classifications. That replay has
zero water and is not wet boundary-flux evidence.

`liquid-native-packet-step3-v2/native_transfer_audit.json` independently passes
the third native P2G step too. All four particles survive two intervening updates;
their world X positions move 6.60–7.18 cm. All raw components pass, all reduced
components match exactly, and 24 shared-column cells remain nonzero. Physical
volume is 0.0833336419891566 m³. Its 26.99-second blocking capture time is not FPS.
The preceding step3-v1 capture failed because the game thread inspected the
snapshot flag before pending render work finished; the explicit stop fence fixed
the diagnostic race. No numerical gate was relaxed.

The 228-test Python liquid suite passed. Final
`engine-liquid-native-packet-v2/index.json`: **five succeeded, zero warnings,
zero failures**, 17.1888 seconds. This covers native contact/exterior compilation,
spawn insertion/fixture-kill assertions, boundary halo GPU, raw transfer GPU, and
native resolve GPU. The first engine run
failed the new spawn assertion because Niagara named the module from its source
script (`AddParticleToNeighborQuery001`), not its display label. The corrected
assertion finds the native symbol and checks both its spawn-frame binding and
actual neighbor insertion call.

## Remaining work

Follow-up [birth identity implementation](liquid-particle-identity-review.md)
installs and verifies persistent integer birth tags on12native particles. Actual
ownership transfer and runtime generation/sequence-lifetime management are still
required; identity persistence is not migration evidence.

1. Implement actual same-step particle ownership handoff. Native persistent IDs
   are emitter-local: copying only position/velocity into another emitter is not
   sufficient. Preserve stable global identity, all transported state and volume;
   maintain native counts, ID-to-index and free-ID tables without collisions.
   Engine dispatch sizes are prepared before stage execution, so importing into
   an empty or underallocated owner also requires a bounded allocation/dispatch
   contract, not just changing the GPU live-count value. No such mutation has
   been enabled by this packet diagnostic.
2. The current regional compiled source does not yet contain the separate
   `RiverAffine` transport fields used by the legacy affine fixture. Do not claim
   that legacy affine tests prove regional affine transport. Integrate and verify
   that state with connected wet projection/G2P and handoff.
3. Dense native NQ capacity/conservation, real inlet/outlet flux, sustained
   connected wet simulation, continuous surface/foam and secondary ownership.
4. Full-rapid geometry, boat/collision/shoreline, real-reference motion and
   appearance, uninstrumented performance; then the rest of the river, crew,
   normalization and release queue, including final commit.

Saved `SouthForkRegisteredRockPlayable.umap` still hashes to
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.
Failed attempts are retained. No commit or push has been made.

All owned processes are terminal: final build39164, later packet81600,
engine58682. The preceding status-only turn did not change implementation; this
continuation made and verified the fixes above. No external blocker, no goal
completion claim. Next implement handoff/global identity/native count contracts,
then connected wet transport and the original full-scene acceptance work.
