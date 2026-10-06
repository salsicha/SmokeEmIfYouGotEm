# Exact crest-range preparation and spatial membership

September 16, 2026 UTC. This work targets measured water-mesh CPU cost, not
wave amplitude, foam calibration, resolution, timestep, or scene acceptance.

The original range evaluator repeatedly validates and clamps immutable site
records. `FRaftSimPreparedBreakingHeightRange` owns those constants for one
captured profile. It preserves the original range arithmetic and accumulation
order; unsupported profiles still disable the shortcut. No height is cached
between evolving profiles.

## Retained unsuccessful experiment

Constant preparation alone did not reproduce its apparent timing gain. Both
captures have 64 alternating current-scene pairs after two warmups, exact
ordered topology/coordinates, and preparation charged to every candidate build.

| Constant-only run | Reference-first: reference / candidate ms | Candidate-first: reference / candidate ms |
| --- | --- | --- |
| `prepared-range-pairs-v1-20260916` | 12.963197 / 12.258747 | 12.326629 / 11.964850 |
| `prepared-range-default-pairs-v1-20260916` | 12.768700 / 12.962440 | 12.416122 / 12.669206 |

The second run loses in both orders. Its temporary default enable was removed;
constant preparation alone is NOT a qualified optimization. Local captures and
summaries remain under ignored `tmp/`. Capture hashes respectively:

- `bb3ffad64b70d9e5754de67a1791a19ff7d1c5d0a648bd5c376e14e629be5b1c`
- `2bb4564800253e77d4241d6fbc0425e3d1c8fcb8fc081da747353c9efe5d9cb2`

## Conservative spatial candidate

For query centers within the site-coordinate bounding box expanded by 256 m,
and nonnegative query half extents at most 8 m, the reference roundoff pad has
a finite upper bound. The index expands BOTH independent along/across interval
tests by that pad and the maximum projected query radius, inverts the original
flow frame (including its squared norm), and bins the resulting center bounds.
Each tile retains original site order. Numerical construction margins only
enlarge membership; returned range values and refinement tolerance are unchanged.
Queries outside this envelope and oversized indexes use the complete scan.
Index limits never truncate sites or geometry.

The first spatial attempt bounded actual support intersection instead of the
reference's independent projected tests. Native query 5265 exposed the mismatch;
the automated launch gate correctly stopped before gameplay. The corrected
membership retains the reference's extra corner cases, including its roundoff
cushions. The original seeded test and exact-equality requirement are unchanged.

The corrected build succeeds. All 51 native tests pass, including 24,000 exact
spatial comparisons, support boundaries, non-unit directions, profile ownership,
query/index fallbacks, existing GPU foam, and full-hull tests. Report:
`tmp/spatial-range-native-v2-20260916/index.json`, SHA-256
`04fa62e57bdc0c34551823a5983969e5b73a3a4f072afa98eec19b491159892d`.
The earlier failed native report remains `spatial-range-native-v1-20260916`.
All 53 targeted Python comparison/snapshot tests pass.

Two corrected spatial captures preserve all 128 ordered geometry comparisons:
8,230,214 expanded vertices and 5,349,244 triangles. Both execution orders are
slightly faster in both runs, with preparation charged to every candidate build.

| Spatial run | Reference-first: reference / candidate ms | Candidate-first: reference / candidate ms |
| --- | --- | --- |
| `spatial-range-pairs-v2-20260916` | 12.221650 / 12.134119 | 11.385772 / 11.268169 |
| `spatial-range-pairs-v3-20260916` | 11.980301 / 11.907706 | 11.386775 / 11.375757 |

All-pair mean reductions are only 0.102568 and 0.041806 ms. This is a small
component improvement, not a meaningful solution to the remaining frame budget.
The corrected spatial implementation is now the default; use
`-RaftSimUnpreparedCrestRange` for the original complete reference scan.
`-RaftSimCrestPreparedRangeAudit=<fresh path>` compares
actual changed-input builds without publishing its private diagnostic meshes.
The summarizer requires all 64 pairs, exact counts/order/results, finite timings,
and a win in BOTH execution orders after charging preparation to each build.
Capture SHA-256 values respectively:

- `42a7c023ea04cfaa4ec4e20fde952b166e32b4f09c07cbd16344bad44be038e1`
- `cc8638be5f81d3a2cc25626c24498616958f6c8804370a26f548b8be1a3a9c3f`

The final default-path build succeeds and all 51 native tests pass again:
`tmp/spatial-range-native-final-v1-20260916/index.json`, SHA-256
`7efaa01d504f49786d573c38bc7eb4cf65b396b60223624a0e14fb29601b5255`.
The final actual South Fork run completes with the prepared path active by
default (no prepared-range or pair-audit flag). It retains the opt-in full-hull
reconstruction preview; this is not packaged/default collision promotion.
Three captures complete, the last at world time 32.266 s / station 8356.000 m.
The final still was inspected and remains visually unaccepted. Shared hull/render
verification reports zero position error at revision 1209. Recorded GPU/native
water time is only 11.933334 s against 36.492 s elapsed: no real-time or 30 FPS
acceptance. The finalized recording has 114 source frames over 25.140 s;
encoder duplicates are not game frames.

Log: `tmp/spatial-range-default-playable-v1-20260916.log`, SHA-256
`3e971206fd8d67373c36c75f055448793a5d3e9ed15383fbd5b8015253eb8d83`.
Captures: `unreal/Saved/Screenshots/spatial-range-default-playable-v1-20260916_*.png`.
Video: `unreal/Saved/VideoCaptures/RaftSim_20260915-224421.mp4`.
All 464 protected asset hashes were rechecked unchanged after the spatial runs.

## Hydraulic continuation and remaining acceptance

The same 600-to-1200-second cook remains active (owned session84989 / PID32068).
Independent 850, 900, and 950-second cell/bank audits pass: all 5,350,400 cells
checked, all 86,720 artificial bank-face cells dry. At 950 s, maximum depth is
4.644417933 m, maximum speed 9.278411429 m/s, and maximum step mass residual
1.435986996e-8 m3. Storage has fallen 4,444.815276989 m3 since restart; net boundary
flux is about -17.723191458 m3/s. This is still evolving, NOT settled or promoted.
Reports: `tmp/south-fork-landward-{850,900,950}s-{snapshot,banks}-v1-20260916.json`.
Next complete checkpoint: local step 8000 / absolute 1000 seconds. Do not restart
the cook on an observation timeout.

The later constant-only gameplay capture was inspected: broad froth and faceted
inferred rock flanks remain visually unaccepted. Experimental installed engine
Toolset Python startup errors also remain in game logs; this is not a clean
release run. No ordinary FPS pass is claimed during concurrent cooking/audits.
The last uncontended 17.819710 FPS / p95 81.6343 ms still fails the unchanged
30 FPS / 33.333333 ms gate. Physical regressions, reconstruction, breaking/froth
motion, traversal, Colorado -> Pacuare -> Futaleufu, other-scene water, crew,
normalization, and release remain open. Troublemaker is a South Fork rapid only.
