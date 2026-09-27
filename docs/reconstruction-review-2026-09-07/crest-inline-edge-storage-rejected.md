# Inline crest-edge storage rejected

September 27, 2026. Supporting performance work only; **no playable change**.
The healthy packaged rapid's 20 FPS failure remains open.

The latest healthy stage subdivision identified about 5.2 ms of assembly on
changed-input crest updates. This trial changed only edge lookup storage:
four contiguous neighbour/value slots per lower endpoint, initialized by a
separate count array, with a complete canonical-key overflow map for arbitrary
high-degree fans. It differs from the rejected single-lookup insertion and
root-incidence experiments: it retained the original contains/add calls and
triangle traversal, changing the storage locality instead. No geometry,
sampling, physics, tolerance, cadence or quality was reduced.

The candidate was default-off and used only by a paired actual-input audit.
Normal play continued using the installed bounded indexed chains. The test
compared independent retained selection histories, exact ordered midpoint
parents, triangles, owners, expanded coordinates, cache build/reuse counts
and the actual production topology. Map construction was included in timing.

## Evidence and decision

Editor Development build succeeded in 290.92 s. Three native tests pass,
zero failures or test warnings: `RaftSim.M4.CrestInlineEdges`,
`RaftSim.WaterDetail.ConformingSurfaceRefinement` and
`RaftSim.WaterDetail.RefinementTopologyCache`. The new fixture covers overflow,
self edges, repeated updates and misses, plus 36 moving/cropped/reversed roots,
flat/nonflat profiles, detail windows, 0/1/3 levels and explicit invalidation.

One isolated 600-frame D3D12 editor-hosted FullReach run at station 11,520 m
produced all 64 exact pairs after two warm builds. Execution order alternates;
all pairs are retained. Both native and gameplay processes exited 0 without
runtime Error/Fatal records. Gameplay remained healthy for 31.222 s, with
599 paired commits, zero PDE backlog and no GPU waits.

| First path | Pairs | Installed build ms | Candidate build ms | Installed assembly ms | Candidate assembly ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Installed indexed chains | 32 | 9.032004 | 9.481853 | 3.236444 | 3.673151 |
| Inline candidate | 32 | 9.542190 | 9.494272 | 3.577344 | 3.604547 |

The candidate loses assembly time in both orders and does not improve the
whole build in both orders. **Rejected, not promoted.** No audit-free FPS run,
second identical trial, recook or packaged rebuild is justified by this result.
The temporary candidate, audit and native fixture were removed with scoped
patches; the two existing runtime files are restored without reverting other
work. Do not repeat this unchanged storage hypothesis.

This direct diagnostic start is not Boot/menu validation. No new rendered
appearance, collision, shoreline, motion or river acceptance is claimed.
No sources, scene packages, cooked fields or player saves were changed.

## Retained evidence

All raw evidence remains in project-local `tmp/`:

| File | SHA-256 |
| --- | --- |
| inline-edge-pairs-20260927.json | `461005d521cff8a813580c4f6e80f098f789ee7aa4bc793684cb75d722a43407` |
| inline-edge-pairs-20260927.log | `b0a88ddaa2b06fa501f0582d613514910db25ce7d0222af10e826594c4d729b8` |
| inline-edge-native-20260927/index.json | `70ac72ec382517e2c5538983a2032565e85055c0af0c06f557161464396fa895` |

Build log: `tmp/inline-edge-build-20260927.log`. Bounded launch helper:
`tmp/run-inline-edge-20260927.ps1` (requires the now-removed trial to reproduce,
not a runnable production acceptance check). It validates completeness, exact
pair IDs, alternating order and finite stage times within the whole build.

Packaged v4 executable remains SHA-256
`12d71f2830633d51d9b8851e9b4524b58fd74be33176d331092e6fd76433e523`.
South Fork stays first; its geometry/hydraulic/visual and busy-rapid performance
gates remain open. Restoration build and recheck are recorded below when done.
