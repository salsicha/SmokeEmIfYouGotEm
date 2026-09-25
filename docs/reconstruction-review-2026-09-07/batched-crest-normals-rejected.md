# Explicit crest-normal batching rejected — September25

Candidate grouped face-normal and per-vertex accumulation tasks into contiguous
256-element batches. Math and each vertex's incidence order stayed unchanged;
it was enabled only by `-RaftSimBatchedCrestNormals`. Editor build succeeded in
194.89s with two pre-existing C4305 warnings in the D6 runner. The extended native
test passed1/1 (`tmp/batched-crest-normals-native-20260925/index.json`), including
24 changing mesh frames. A normal Boot/menu South Fork run with the existing
scalar-reference audit yielded151 exact all-attribute comparisons, no mismatches,
and exit0 (`tmp/batched-crest-normals-live-20260925.log`). Audit timing is excluded.

Separate editor-hosted normal-menu runs used1280x720, ephemeral profile,
300 post-travel CSV frames, confirmed nonlegacy frame timing, and the established
analyzer over rows30–270 inclusive with scope offset1. No direct-map override,
solver toggle, geometry change or tolerance change was used.

| Run order | Scheduling | Mean frame ms | p95 ms | Mean normals ms |
| --- | --- | ---: | ---: | ---: |
| First pair, first | Candidate | 25.813802 | 34.9118 | 0.892139 |
| First pair, second | Default | 23.495741 | 32.8372 | 0.787166 |
| Reverse pair, first | Default | 23.157332 | 31.0330 | 0.825788 |
| Reverse pair, second | Candidate | 23.556580 | 31.5110 | 0.871358 |

Reports with exact CSV identities and SHA256:
`tmp/batched-crest-normals-cost-pair-a-20260925.json` and
`tmp/batched-crest-normals-cost-pair-b-20260925.json`.
CSV timestamps in `unreal/Saved/Profiling/CSV/` are091615,091702,091819,091903
on20260925 respectively. All runs exited0. The last candidate's drift record
shows1.368m/s, wet1, support delta0 and penetration0; this is sampled motion,
not continuous collision or visual acceptance.

Both orders favor the default, including the targeted normals stage. Reject
promotion and remove the candidate/helper/test extensions from source; the
three source files are restored to their pre-experiment contents. The rebuilt
editor still contains the unused opt-in branch until the next rebuild; default
behavior is unchanged. The installed packaged executable was never replaced.
Do not repeat this unchanged scheduling candidate. These short editor controls
do not supersede the packaged performance failure or establish river acceptance.
