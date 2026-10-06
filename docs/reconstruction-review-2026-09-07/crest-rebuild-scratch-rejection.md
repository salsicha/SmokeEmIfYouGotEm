# Crest rebuild scratch capacity trial — September29

Rejected for negligible measured benefit. No normal-play or packaged change
was enabled. Removal of the three source-file changes is PENDING because the
patch engine cannot overwrite them; do not report the rollback complete.

The trial retained capacity for root XY, integer indices and expanded XY
between rebuilds. It recomputed every current coordinate/profile value and
swapped only the root coordinate buffers after successful selection. No
geometry tolerance, source field, solver step or presentation setting changed.

Editor build passed229.50s. Native tests CrestRebuildScratch,
ShorelineCrestTargetCache and ReferencedWaterVertices all passed without
warnings/failures. The new test compares36 updates, including growth/shrink,
profile/coordinate/winding changes, temporal history, all vertex attributes,
detail bounds and reset. Actual normal FullReach8310m audit completed300frames,
65 paired publications in frame120..183 (one frame has two publications).
Both evolving histories consumed every publication from startup. All paired
vertices, indices, cell offsets, corrections, expanded weights and build counts
were exactly equal. Whole-update timings include identical source gathering.

| First path | Pairs | Reference mean ms | Candidate mean ms |
| --- | ---: | ---: | ---: |
| Reference | 32 | 27.589047 | 27.523091 |
| Candidate | 33 | 24.569839 | 24.532703 |

Savings of0.037–0.066ms do not establish a useful repeatable improvement against
the heavy-section frame failures. No FPS acceptance or visible change follows.
Do not repeat this unchanged candidate. Next work should address substantive
surface/crest computation and genuine breaking/foam dynamics, not buffer churn.

Qualification session45745/wrapper34064, native32172 and game12144 all exited0.
Receipt:`tmp/crest-rebuild-scratch-v1-20260929-process.json`, SHA256
`5f9cbca3ccbc2dd447850d2caf474903693273684b94f8ceca2e5fd1b149123d`.
Native report:`tmp/crest-rebuild-scratch-v1-20260929-native/index.json`.
Runtime log:`tmp/crest-rebuild-scratch-v1-20260929-pairs.log`.

## Exact pending restoration

The following files were clean before this turn; their only diffs are this
rejected experiment. Their exact reverse patch is prepared at
`tmp/restore-crest-rebuild-scratch-compact-v1-20260929.patch`:

- `unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/RaftSimShorelineCrests.h`
- `unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimShorelineCrests.cpp`
- `unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimShorelineMeshComponent.cpp`

Candidate remains OFF unless explicitly requested by its diagnostic flag.
The new test was successfully moved out of active source and retained at
`tmp/crest-rebuild-scratch-rejected-v1-20260929-test.cpp`. No captured data or
other owner's changes were removed. After restoring the three files, rebuild
the editor to remove the compiled candidate and verify their diff is empty.
The independently staged v28 executable was never modified by this trial.

## Write failure evidence, not an established root cause

The normal patch tool and an approved direct invocation of the installed
patch engine both report `Failed to write file` on the header. A relative-path
patch fails too. File is not read-only; the current Windows account salsi has
FullControl. An approved non-mutating FileMode.Open/FileAccess.Write handle
succeeds. No live engine/compiler/UBA process remained. A recent Defender
1123/1124 query returned no block entries; this alone does not rule out all
security software. Ownership of exactly these three sandbox-owned files was
normalized to salsi without changing access rules, but the patch still failed.
No broad permission/security setting was changed. Do not repeatedly retry the
same failed operation or call this a missing blanket repository write grant.

The OpenAI Docs skill prompted a check of official Windows sandbox guidance;
it describes scoped filesystem boundaries but does not establish this exact
failure's cause or a guaranteed repair. A fresh app session is the next proposed
recovery check, not a proven permanent fix. Keep the full river goal active.
