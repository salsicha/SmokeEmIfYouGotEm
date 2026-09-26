# Combined South Fork canopy readback

September 26, 2026 UTC. Supporting validation of the existing normal playable
scene, **not a new scenery delivery or river acceptance**.

The additive lower-gorge pass followed the channel repair. To ensure these
independent changes compose correctly, a fresh Unreal editor process loaded
all 862 original/additive NAIP canopy actors from
`/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach` and checked every instance.
No engine, Blender or cook process was active before this audit started.

## Results

- 140,417 surviving original trees plus 24,211 lower-gorge additions = **164,628**.
- Every actor has the correct placement source hash; every populated component
  has the expected mesh, instance count, root position and uniform height scale.
- Maximum placement/bottom-position error: 3.64e-12 cm; scale error: 1.78e-15.
  Expected mesh bottoms retain the installer’s 20 cm ground embedding.
- All 862 actors are spatially loaded. Canopy components remain non-colliding
  with overlap events disabled.
- No missing, extra, duplicated or reintroduced removed root was found.
- Four data-backed regression tests pass: source/mask lineage, exact original
  water-cell removal set, every added root dry and covered, combined count and
  absence of duplicates. The context mask hash is preserved.

Script: `unreal/Scripts/verify_south_fork_combined_naip_canopy.py`.
Tests: `physics/tests/test_south_fork_combined_naip_canopy.py`.
Receipt: [fresh engine readback](south-fork-naip-drape-v2/combined-canopy-readback.json).
Engine exit 0 and the explicit `RAFTSIM_COMBINED_CANOPY_VERIFIED` receipt both
confirm completion. The source placement files, imagery, masks, geometry,
collision assets and hydraulic fields were not changed.

## Limits and current performance status

This exhaustive inventory check is not an exhaustive ground-contact trace:
it matches installed transforms to the preserved placements. It does not
validate yaw, foliage material appearance, exact two-metre shoreline clearance,
HLODs, ground clearance between sample points, water animation or boat motion.
The original and lower-gorge root trace samples remain separate evidence.
The dry-mask tests refer to the captured context mask, not a newly surveyed
waterline; tree forms, species and individual stems remain inferred.

No duplicate profile was run. The earlier 74.35 ms p95 channel-repair run was
contaminated by the other session's Blender/capture work. The later idle-host
normal Boot/menu run is 35.1554 ms p95 with no frame over 100 ms, passing the
user's 20 FPS / 50 ms goal; lower-gorge station 30.5 km is 37.2 ms p95.
See [drape v2 and its original receipts](south-fork-naip-drape-v2.md).
Neither performance pass closes South Fork's remaining shoreline, rock/bed/
field consistency, breaking-water, collision and visual acceptance work.
