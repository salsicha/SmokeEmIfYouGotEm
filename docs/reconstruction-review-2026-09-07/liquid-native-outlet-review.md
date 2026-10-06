# Native outlet and simultaneous emission — September 10

South Fork remains incomplete. These are real native GPU transport observations,
not dense-fluid, photo-reference, raft-response or performance acceptance. The
saved geographic map has not changed or been promoted.

## Implementation

The retirement replay now selects three actual prepared wet seeds from owner 7,
30–70 cm inside the downstream parent edge. Selection requires a wet, outgoing
original boundary row and clearance above the bed. The fixture also retains the
three inner owners and initially empty receiving owner 0. Its prescribed 8 m/s
outlet velocity is an explicit diagnostic stimulus, not a measured river speed.
First-step native positions and original seed IDs are now captured alongside
birth identities, including explicitly empty owners.

`audit_liquid_native_retirement.py` independently checks:

- The initial particles' original wet-seed positions and birth identities.
- Every native precommit route against the prepared physical regions.
- Exact full-word source partition into native survivors or retired records;
  only receiving local handles may change in survivors.
- Original parent-box segment intersections, outgoing wet rows, bed clearance,
  face/row agreement and crossing fractions; floor, roof, corner, dry, inward
  and below-bed leaks remain rejected.
- Complete receiving handles/free lists, source capacities and native volumes.
- Birth sequence/owner/unique-ID consistency against actual native spawn plans,
  no missing survivors, duplicate exits or resurrected identities.
- Actual pre-advection origins between consecutive commits, continued motion,
  final packed/native payload agreement and refreshed P2G origins.

Crossing fractions use a documented forward-error bound derived from original
frame-to-float32 conversion, subtract/dot operations and segment division. An
initial arbitrary 0.0001 fraction threshold was not mathematically justified:
one combined replay differed by 0.000189 at the same exact face/row. The derived
bound replaces that threshold; wrong topology is never tolerated. Unit tests
reject incorrect finite fractions and verify that coordinate magnitude changes
the derived numerical error. The existing P2G numerical envelope is unchanged.

The first combined replay also exposed a real limitation of the old diagnostic:
eight commits ended at step 9, but the final P2G capture at step 11 followed an
uncommitted advection. New source particles could cross a region boundary during
that gap. Retirement replays now require continuous commits through the step
preceding P2G (at least three, up to ten). Non-retiring legacy probes retain their
existing completed-motion mode. Repeated precommit history proves motion in the
continuous mode; the immediate final postcommit-to-P2G interval must preserve
positions exactly rather than pretending it contains another advection.

The raw-P2G auditor dispatches retirement captures to this full ledger auditor
first. The closed-population handoff auditor still rejects retirement captures.

## Live evidence

- Build 23090 succeeded. `liquid-native-retirement-v1` (process 50315, terminal
  exit 0): 12 initial, three downstream exits on step 5, nine survivors, eight
  commits, 72 moving segments, all nine moving after the final commit. Exact
  particle volumes: initial 0.2500000074505806 m3 = exits 0.06250000186264515 m3
  + survivors 0.18750000558793545 m3. Final native P2G/reduction passes, 50 shared
  cells and zero reduction mismatches. This older non-emitting capture has the
  diagnostic gap described above; its survivors did not cross during that gap.
- `liquid-native-open-flow-v1` (79220, terminal exit 0) was **rejected** by the
  physical-owner audit because of the gap. Successful engine shutdown/capture
  alone did not grant acceptance.
- Build 44972 succeeded with continuous diagnostic handoff. Corrected
  `liquid-native-open-flow-v2` (13653, terminal exit 0) passes: 12 initial + nine
  native source births − three approved downstream exits = 18 survivors.
  Nine commits, owner changes `[4,9,1,1,1,1,1,1,1]`, 109 verified moving segments.
  Owner 7 empties; owner 0 ends with 17 particles and source owner 1 with one.
  New births continue after the outlet owner empties. This does not yet test
  repopulating that emptied outlet owner or restarting a whole native generation.
- Corrected final P2G: 18 particles, 84 nonzero shared column cells, zero reduction
  mismatches. Physical deposited volume 0.37500097911015473 m3 versus
  0.3750000111758709 m3 expected, within the unchanged computed envelope
  0.004858227315396016 m3. No RHI errors in either successful outlet replay.
- 279 liquid-specific Python tests pass, including 18 new retirement-auditor
  tests covering dishonest counts, payloads, crossing data, missing/duplicated
  references, source loss hidden by births, and retired identity resurrection.
- `engine-liquid-open-flow-v1` (29334, terminal exit 0): all twelve engine tests
  succeed, no failures or RHI errors. One unrelated HTTP connectivity timeout
  to Google's generate_204 endpoint is recorded as a test warning. All owned
  engine/build processes are terminal.

Final independent report: `liquid-native-open-flow-v2/retirement-audit-final.json`.
The original boundary SHA256 is
`2bcaf0db00766c38638b95edcf82ab8e2e605aab75ce270e51ff9ff3fa9369ff`.
Saved geographic map SHA256 remains
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.

The source emitter in this bounded test is owner 1's prescribed test source,
not a claim of calibrated full-parent inlet discharge. The original boundary
profile's submerged bed remains inferred. There are no new beauty screenshots
and no gameplay FPS measurements in this evidence.

## Still required

Finish generation/reset/identity lifetime and bounded allocation/repopulation
policy, then run the actual dense prepared water with calibrated exterior
inflow/outflow and continuous physical ownership. Return that connected fluid to
the playable geographic scene, verify a single continuous surface, crests/foam/
shoreline, raft collision/support/drift, reference agreement and measured frame
time. Complete the rest of the original river/crew/cleanup/release queue and
commit only when the requested project completion is genuinely verified.
