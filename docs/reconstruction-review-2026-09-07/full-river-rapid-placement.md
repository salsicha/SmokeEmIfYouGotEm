# Full-river geographic placement — September 12, 2026

This is an integration prerequisite and a runtime sampling fix, not a completed
playable reconstruction. South Fork remains the scenario; Troublemaker is never
a separate menu entry. No map, captured terrain, collision asset, flow array or
user save was changed in this pass. No new visual improvement is claimed.

## Authoritative coordinate contract

`physics/scripts/build_south_fork_playable_route.py` builds
`reconstruction_2026_09/full_reach/playable_route/` beneath the South Fork dataset.
It uses the existing survey-water-constrained geographic axis, not the old
49 km upstream extension or the older 33.693 km NHD-clipped profile axis.
The source axis remains a candidate geographic alignment, not a surveyed
thalweg or a navigation line; registration uncertainty is unchanged.

- Route length: 33,334.146393644 m; all 1,238 source vertices retained.
- Runtime coordinate points: 17,563, with exact source segment lengths.
- 135,163 quarter-metre source-mask probes and diagonal corners remain in
  captured water. No dry gaps bridged or banks excavated.
- Maximum runtime 256 m corridor edge step: 7.096191 m, below the unchanged
  16 m loader guard. This density check does NOT prove that a wide curved
  ribbon is injective. Captured terrain must remain Cartesian, not warped.
- EPSG:32610; datum 220 m NAVD88; engine X east, Y south, Z up.
- Troublemaker origin projects to river station 8,343.945510 m, 2.062946 m
  off the geographic axis. This is not a re-certification of rapid identity.
- Existing rapid world to full river world: translation in centimetres
  `[-543186.6369777592, -360044.75875617936, 0]`, unit scale, zero rotation.
  Do not apply the Y reflection twice; the existing rapid world already has it.
- The embedded rapid hydraulic coordinate map retains local rigid stations
  and normals. Those stations are NOT interchangeable with river chainage.
- The new 17,563-sample profile is sampled from the unchanged captured raster
  on this same axis. It contains captured **water-surface elevations, not bed**.
  Do not feed that profile directly into the solver as bathymetry.

Key hashes:

| Artifact | SHA-256 |
|---|---|
| Source geographic axis | `51b8fd98595986a4e038caa9df9c40f0acc49668449223ddd0d91e3b2afb636a` |
| Runtime full-river coordinate map | `e83efad368a978ca035cd89881aab90e10ef86c906f67732480a1dc7b9487e82` |
| Rapid placement contract | `9865f730846967ec44a49c5d38e7ef4031298c7748914cb8a6bf4164efea1109` |
| Embedded hydraulic coordinate map | `cfca83b4e7875d2a5a7b596ce5105ffcd5148ece7b91228e0f84e910d43a8e24` |
| Restationed source profile | `4a88153ad6568daf177a69b215a602679cdfa6d92091a90c213a551da78965b1` |

## Real runtime failure and fix

The first embedded-water test FAILED the unchanged 0.1 mm / 0.1 mm/s
translation-preservation gates: maximum depth difference 0.000380814 m,
height 0.000305176 m, velocity 0.000122215 m/s. Retain the report:
`unreal/Saved/RaftSimValidation/south-fork-full-route-embedding-20260912/index.json`.

The runtime's 24-iteration ternary inverse never reaches segment endpoints.
For constant-normal rigid grids, it could choose opposite approximate sides
of the same station after translation. `WorldToRiverCoordinates` now uses the
exact linear inverse for constant-normal segments, including endpoints. The
curved-segment inverse, corridor bounds, sampling equations, hydraulic arrays
and tolerances are unchanged. This is installed in the rebuilt normal runtime.

Final build succeeded in 15.48 s. Three native tests passed with no warnings:

- `RaftSim.Survey.SouthForkFullRouteCoordinates`: 2,002 downstream/cold-jump
  queries; maximum station error 0.000057994 m, lateral 0.000007881 m.
  This test does not yet establish warm-cache hull-footprint traversal.
- `RaftSim.Survey.SouthForkEmbeddedRapidWater`: 527 translated field queries,
  152 wet. Maximum depth and velocity difference zero at nine-decimal logging
  precision; height 0.000015259 m. Wet/dry availability unchanged.
  These are seeded-field comparisons, not a stepped hydraulic handoff test.
- `RaftSim.M4.CurvedRiverCoordinateMapDrivesLiveWater`: existing full-reach
  live-water and full-corridor regressions pass with original gates.

Final report:
`unreal/Saved/RaftSimValidation/south-fork-full-route-embedding-fixed-20260912/index.json`.
All owned build/engine jobs terminal. Five Python tests cover source corner
preservation, invalid-axis rejection, metric/datum transformation, chainage
distinction, and generated-artifact/profile consistency. Scoped diff check passes.
User-save SHA remains
`181d1e570485d1ec3139aec4e1d9b56d0a420fd107ce5a94218368324207f5b1`.
Legacy FullReach map SHA is
`e77da92b73bf0a2c566fe69ee8a0ef7115d26182bb2f91648582aa1197ce13a0`.

## Next required implementation

Use this coordinate contract for Cartesian full-river terrain and the captured
rapid mesh. Preserve original source XYZ and handle the replacement seam against
the 2 m full-reach terrain explicitly. Infer unknown submerged geometry separately
and cook the same geometry; the hydro-flattened source surface is not bathymetry.
Runtime hydraulic-region handoff must distinguish the local rigid grid from the
global progress axis. A translated coordinate map alone is not that handoff.
Then replace the legacy full-river asset/configuration and update start/section/
finish stations together, verify continuous travel, and inspect actual motion.
Do not rename the 273 m fixture to South Fork or re-add it to the menu.

Breaking/froth fidelity, guided tracking, performance budgets, all later rivers,
crew work, release checks and final project commit remain open.
