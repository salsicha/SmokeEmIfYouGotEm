# Exact coordinate memo layout — September 14

This is a measured performance experiment, not terrain, hydraulic, breaking-wave,
froth, traversal or 30 FPS acceptance. The preceding Git-only turn verified a
clean worktree but made no implementation progress. This turn tests a different
lookup layout on actual ordinary South Fork inputs. Previously rejected batch,
shared-corner and region-index variants remain disabled.

The candidate stores full double coordinate keys and profile samples in dense
entries, with open-addressed integer buckets. Equality and the existing signed-
zero-aware hash are unchanged. Each parallel batch still owns its map; the
current profile epoch, 4096-entry bound, original sampling positions, 0.5 cm
selection tolerance, three refinement levels and ordered assembly are retained.
No sampled height may survive a profile-epoch change. No physics cadence,
render quality, captured source, inferred geometry or water material is changed.

The first version used a separate lookup followed by insertion. Build 32941
passed in 119.12 seconds. Native 65370 passed all nine requested tests, zero
warnings/failures/not-run, 0.641398 seconds. The new test covers growth past 8192
entries, replacement, signed zero, misses, reset, and 24 changing profiles,
shoreline coordinates, crop translation, winding, batch size and memo retention.
Existing fine crest, cache epoch/target, normals, compact upload, ground contact,
career catalog and progression migration tests remain included.

Paired ordinary-game process 39965 completed exit 0. The complete 120–250 window
contains 123 build calls and eight explicit unchanged calls. All 8,262,038
expanded vertices and 5,987,129 triangles match exactly, including ordered
parents and source-cell ownership. The parser preserves duplicate calls, demands
every requested frame and both call orders, and rejects any mismatch. Its nine
tests and the nine existing region-profile parser tests pass.

First-version result: original mean 10.887940 ms, candidate 10.953659 ms. The
candidate saves 0.268563 ms when second but loses 0.452784 ms when first. Mean
retained memo storage is 50,785,226 versus 46,902,262 bytes. This is a memory
reduction, **not a qualified latency win**. Do not enable this version based on
one favorable call order. Report:
`tmp/south-fork-flat-memo-paired-v1-20260914.json`; source log SHA256
`c66e82bad6ecb3d31664d3e8934ad64ca4ca279434119416ed4c977a6369b58d`.

The second version fuses lookup and insertion into one probe. On a hit at the
4096-entry bound it preserves every entry; only an absent key at the bound
resets coordinate history. Added native controls explicitly check both cases
and default initialization after eviction. Qualification results follow below.

The comparison runs perform two extra reconstructions per changed input; their
frame rate is not ordinary gameplay performance. Full scene acceptance remains
open, including the prior visual failures and latest ordinary p95 64.9716 ms.

## Final result: retain the ordinary map

Second build 42225 passed in 110.08 seconds. Sequential native/game process
50421 completed exit 0. Final native report
`unreal/Saved/RaftSimValidation/flat-memo-v2-20260914/index.json` has nine successes,
zero warnings/failures/not-run, 0.622356 seconds. Both builds retained the two
pre-existing D6 damping double-to-float warnings; they were not hidden or changed.
Final Python coverage totals 40 passes: 18 paired-parser checks and 22 existing
frame-CSV, ground-contact, captured-rock and carrier-source-epoch checks.

The second complete interval contains 128 builds plus four explicit unchanged
calls (including a repeated call within the 131-frame interval). Every one of
8,597,657 expanded vertices and 6,230,065 triangles matches exactly.

| Complete build cost | Original map | Single-probe flat map |
| --- | ---: | ---: |
| Mean ms | 10.856902 | 10.747665 |
| Median ms | 10.217000 | 10.189300 |
| p95 ms | 15.482798 | 15.284497 |
| Mean retained memo bytes | 51,718,126 | 47,717,539 |

The 0.109237 ms mean benefit is order-sensitive: +0.442314 ms when flat runs
second, **-0.256600 ms when flat runs first**. This does not qualify a reliable
latency improvement. The experimental `-RaftSimFlatCrestMemo` path remains
**disabled by default**. `-RaftSimFlatMemoAudit` retains the exact paired control
for reproducibility; neither flag is used in ordinary gameplay. Do not repeat
this weak result as a delivered FPS gain or promote it solely for the approximately
4 MB memo saving. Report: `tmp/south-fork-flat-memo-paired-v2-20260914.json`.
Log SHA256: `9d48597c19228b88b5d203b4ff48ab636cba9f9fa4dca4fa29b1a0db3cc36526`.

The diagnostic CSV contains all 300 samples and a valid completed footer.
`tmp/south-fork-flat-memo-paired-csv-v2-20260914.json` records 10.893549 FPS with
the extra reconstructions, **not ordinary FPS and not a gameplay regression**.
CSV SHA256: `bb68473c5ccc0a1d8f29f9698807241e11aadadd9d078cd484e3d1a551ed9265`.

Final candidate helper SHA256:
`b4c087fa9ab7f4f3d010a76e40c05b791a8b3ac832f124d1d6f3d4865006b098`.
Refinement header SHA256:
`4aae72ba84eb07486793ae1f0e442a2be78b59fd7dfe01d854a84c6da8086a8c`.
Built raft DLL SHA256:
`8736635372f804e1db0dab70f62cf5e700fd54cace9c051c418463cb81b52a05`.
All 464 protected source, terrain, map and actor hashes were rechecked unchanged.

This rejects lookup layout as a useful near-term FPS fix; it does not justify
more batch/hash variants. Next work must address the dominant source-stage /
fine-terrain hydraulic coupling and breaking/froth failures, plus larger actual
solver/render work. No new visual acceptance is claimed from this timing run.
Colorado, Pacuare, Futaleufu, Chilko/Zambezi, crew, normalization/regressions and
release qualification remain open. The full goal stays active.
