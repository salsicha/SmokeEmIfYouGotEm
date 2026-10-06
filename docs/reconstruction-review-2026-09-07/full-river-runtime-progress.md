# Global run progress, registered material frame and held paddle input

September 12, 2026, 06:33 UTC. Progress, not full reconstruction acceptance.

## Delivered gameplay correction

The actual-game `RaftSim.P3.RunScoresAndSaves` regression initially stalled:
the raft stayed at X=0 and zero speed while paddle calls continued. Inspection
found that `IssueCrewCommand` restarted the .4 s crew reaction delay on every
refresh of the same pending order. Held W/S/A/D could therefore prevent the
crew from ever beginning a stroke. This is runtime behavior, not a terrain
fixture issue.

`RaftSimRaftActor.cpp` now starts reaction latency only for a new pending
command. Reaffirming the active command cancels a different pending order.
Stroke force, water purchase, cadence, animation phase and propulsion caps are
unchanged. The corrected module is rebuilt and used by normal playable scenes.

The old scoring test's first latent command also returned false indefinitely,
preventing its advertised 25 s bound and final assertion from executing. It
now emits one input refresh per scheduled .1 s step and reaches its unchanged
finish/score/save assertions after the bounded sequence. This still refreshes
input faster than the reaction delay and exercises the original defect.

Evidence:

- Original stalled diagnostic: `south-fork-progress-scoring-regression-20260912.log`,
  PID38768 explicitly stopped; terminal exit1, no passing report claimed.
- `Saved/RaftSimValidation/south-fork-held-paddle-gameplay-20260912/index.json`:
  CrewRespondsToCommands and RunScoresAndSaves both pass, zero test warnings/errors.
- `Saved/RaftSimValidation/south-fork-held-paddle-isolated-20260912/index.json`:
  a fresh-process, isolated RunScoresAndSaves passes. This excludes a preceding
  test's standing forward order as the explanation for success.

These are actual game-world motion tests using NullRHI and ephemeral profiles,
not visual crew-animation or river-water acceptance. The user save SHA remains
`181d1e570485d1ec3139aec4e1d9b56d0a420fd107ce5a94218368324207f5b1`.

## Global progress distinct from local water coordinates

`ARaftSimRunManager` now supports an explicit `ProgressCoordinateMapPath`.
The corrected full-river map migration must place/configure the run manager
with `full_reach/playable_route/coordinate_map.json`. Empty retains legacy
single-map behavior. Invalid nonempty configuration never falls back to
local rapid distance or an X-axis finish test.

The first native test failed its unchanged one-centimetre geographic station
assertion: a curved hydraulic ribbon inverse is not nearest-polyline chainage
away from the centerline. Run progress now retains the exact source polyline
corners and projects to the nearest geographic segment with a spatial index.
It does not mutate the hydraulic inverse or reuse its warm cache. Section
starts use global placement and resolve that world location into the active
local hydraulic window. A missing wet region prevents the raft move instead
of pretending global station 8,344 is local station 8,344.

Final report:
`Saved/RaftSimValidation/south-fork-global-progress-final-20260912/index.json`.
Five tests pass with zero errors: RunProgressDistinctFromRapidHydraulics,
SouthForkFullRouteCoordinates, SouthForkEmbeddedRapidWater, CareerCatalog and
ProgressionMigration. The new run-manager test checks 2,002 downstream and
scrambled full-river positions: maximum station error is zero at nine logged
decimal places. Rapid origin chainage is 8,343.945510131 m, lateral distance
2.062945697 m, while its local hydraulic origin remains zero. Out-of-domain
positions and invalid configurations are rejected. Initial failed evidence is
retained under `south-fork-global-progress-20260912`; gates were not loosened.

## Registered material prepared for map placement

`unreal/Scripts/create_south_fork_composite_material.py` successfully created:

- `/Game/RaftSim/Environment/SouthForkReconstruction/FullReach/M_SouthForkCompositeGround`
  SHA256 `a37e9e330c79be3ea33ced13859e902a61c98158fae508a89360b5fdecef5a95`.
- Matching `MI_SouthForkCompositeGround`
  SHA256 `e957f7bd8f1810ef86135b1780cd1e3340d30d4993056a1a969d61bc8b50f2c7`.

Both registered UV expressions subtract the rapid's rigid world translation.
Classification and aerial color are explicitly bounded to their captured
domain; clamped edge pixels cannot masquerade as imagery of the rest of the
river. Outside coverage, the existing rock response is an appearance prior.
Normal, roughness and displacement graphs are unchanged, as are the original
material packages. Report: `Saved/RaftSimValidation/south-fork-composite-material-20260912.json`.
The new instance must be applied as a map component override so verified mesh
package hashes remain stable. This is not yet a visually reviewed map change.

## Import and next integration

The tile importer was paused at 110 verified assets for the progress build;
all 110 hashes matched and no unreported assets existed. A new explicit pause
file mechanism then shut it down cleanly at 124 for the paddle rebuild.
It retains the existing 4 GiB disk guard. The temporary pause request was
removed and the importer resumed at 06:31 UTC as PID17124. Inspect this live
process and its per-tile report before any relaunch. Current log:
`Saved/Logs/south-fork-composite-tiles-held-paddle-resume-20260912.log`.
At 06:36 UTC PID17124 is confirmed live with 155/390 verified tiles and no
pause reason. Final Python syntax checks and all nine geometry/delivery tests
pass. Scoped diff whitespace checks are clean; map and save hashes were
rechecked unchanged.

Normal FullReach map SHA remains
`e77da92b73bf0a2c566fe69ee8a0ef7115d26182bb2f91648582aa1197ce13a0`.
Terrain/rapid flow are not yet integrated there; Troublemaker stays off the
scenario menu. Finish native tiles, compatible full-river flow/region handoff,
map/material placement and simultaneous start/section/finish migration.
The existing streaming actor also advances by hydraulic X only; a global
Cartesian hydraulic approach must follow both axes, not mistake easting for
downstream distance. Boundary and overlap conservation still require validation.
Breaking/froth appearance, traversal robustness, frame cost and later rivers
remain open. No release acceptance or final commit is claimed.
