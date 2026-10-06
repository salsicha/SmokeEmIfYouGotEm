# Normal-play source packing capacity reuse

September 15, 2026. This reduces CPU work in the existing playable surface.
It does not complete breaking-wave shape, froth, front physics or 30 FPS.

## Enabled change and rejected candidate

The actor previously allocated a fresh complete source-vertex array on every
publication. Downstream shoreline code reads/copies that source; it does not
retain ownership. The actor now retains scratch capacity. The unchanged packer
assigns every position, normal, color, tangent and all four UV channels before
each submission. No field value is reused without being rewritten. If a future
consumer moves the array, the moved-from scratch safely regrows on the next call.
Capacity is bounded by that actor's peak source grid, not accumulated per frame.

Normal play enables this path. `-RaftSimFreshSourcePacking` restores the original
fresh-array control. No geometry, vertex count, clipping, foam amount, timestep,
cadence, tolerance, physical height, collision or contact rule changes.

A separate four-channel vector color conversion is exact but NOT qualified for
normal play. It remains opt-in with `-RaftSimVectorSourceColors`. Its native
test compares 503,112 four-channel colors against engine `ToFColor(false)`,
including half-byte neighbors, NaNs, infinities, signed zeros and subnormals.
The original engine clamp, separate multiply/add and BGRA byte order are retained;
other CPU/byte-order combinations use the original engine conversion.

Actual vector-color comparison: 64 exact pairs / 3,240,000 complete vertices.
Overall means 2.462884 ms original / 2.381387 ms vector, BUT vector-first means
2.420215 / 2.452697 ms. It fails the both-order timing gate and is NOT enabled.
Capture `tmp/source-packing-pair-v1-20260915.json`, SHA-256
`3b40a8a29a0e4f4ab62ca3bf0a3a71a2ff879481b073b187eea16b73fae5784b`.

## Paired live evidence for capacity reuse

Both runs use the playable South Fork map at review station 8330. Each compares
64 alternating-order pairs after two warm calls. Original packing allocates a
fresh output; the candidate retains output capacity and uses ORIGINAL color
math. Every complete vertex attribute is checked against the other path AND
the current production output. Comparisons are outside the timed region. Audit
outputs are never published. The optional capture switch is
`-RaftSimSourcePackingReuseAudit=ABSOLUTE_JSON_PATH` and refuses to overwrite.

| Run/order | Fresh packing ms | Retained packing ms | Faster pairs |
| --- | --- | --- | --- |
| Candidate, all | 2.337986 | 1.225974 | 64/64 |
| Candidate, fresh first | 2.380969 | 1.155359 | 32/32 |
| Candidate, retained first | 2.295004 | 1.296588 | 32/32 |
| Rebuilt normal default, all | 2.311875 | 1.217355 | 64/64 |
| Default, fresh first | 2.375281 | 1.162716 | 32/32 |
| Default, retained first | 2.248469 | 1.271994 | 32/32 |

All 128 pairs are exact and faster, 6,480,000 vertices total. The isolated saving
is about 1.1 ms per packing call, NOT a whole-game FPS attribution.

- Candidate capture: `tmp/source-packing-reuse-pair-v1-20260915.json`, SHA-256
  `da7600d210e113b0580c6fe9fc915ebebe710322e2d776caf0e199d3e0010ea2`.
- Default capture: `tmp/source-packing-default-pair-v1-20260915.json`, SHA-256
  `dab70821e9a5ccb3df58406f7f4dfda91ff59d65a0bf58b702ea1553dd860a94`.

`audit_source_packing_pair.py` validates schema/candidate identity, all 64
numbered alternating records, multi-frame history, exactness, finite counts and
positive timings. A losing order, missing measurement or any mismatch cannot
be hidden by the overall mean. V1 vector-color reports remain readable.

## Builds, native tests and ordinary performance

Builds pass in 45.45 s (vector candidate), 102.02 s (retained-buffer candidate),
and 40.87 s (enabled default, six actions). The broader builds retained the two
existing D6 damping conversion warnings; the final build introduced none.

Initial native/D3D12 report: 27 PASS. Final default: 28 PASS, zero failed,
warning, unrun or in-process results. Actor-level verification now checks
retained allocation across refresh/interpolation along with existing actual
carrier, dry island, ground occlusion, positive-film and support/contact checks.
Existing full-field packing tests cover poisoned reusable buffers, empty/shrink/
regrow cases, both geographic orientations and invalid-input nonmutation.
The selected crest, conforming topology and GPU-surface regressions remain.
26 packing/frame/stage evidence-parser tests PASS. No physics gate was weakened;
the prior full physics suite's 13 failures remain unresolved.

Final native report: `tmp/source-packing-default-native-v1-20260915/index.json`,
SHA-256 `5a48e6fe3dd920c6034509f0fabf5042037359007d4386a7fef124931e3886af`.
Final Raft DLL SHA-256:
`fc12a62f587380aa487bd06d9968b90f55e643cd08d0dbd38dd6bf3e3f2d0c18`.

Clean ordinary 300-frame run has NO paired audit or stage-timing flag:
`tmp/source-packing-default-performance-v1-20260915.json`.
CSV `unreal/Saved/Profiling/CSV/source-packing-default-ordinary-v1-20260915.csv`,
SHA-256 `6e6133953091f83d9870b9a008bf2f89d3d95be38eeaac15da064be2035eb638`.
Original 1280x720/D3D12/Development/WindowsEditor settings remain. Samples
120–250: **24.225877 FPS**, mean **41.278176 ms**, **p95 47.78 ms: FAIL** versus
the unchanged 30 FPS / 33.333333 ms frame budget.

Packing averages 1.315729 ms; publication 13.730822 ms; refresh 9.589760 ms
(66 positive samples); selection 3.951418 ms (65 positive samples). These are
nested scopes and cannot be added. Earlier ordinary results were 22.429181 FPS /
p95 54.7266 ms, with 68 refreshes and 69 selections. Different trajectories and
host load prevent assigning the entire whole-frame difference to this change.
Only repeated same-input packing pairs isolate the approximately 1.1 ms saving.
This is not sustained, packaged or release acceptance.

## Fresh capture and remaining work

`unreal/Saved/VideoCaptures/RaftSim_20260915-122947.mp4`, SHA-256
`80d85a9f012527b3bbd8aa7459a2e5c17457aea8f224b44f2a56808e05ceddae`:
105 source frames / 5.896 seconds, 177 decoded frames through PTS 5.866667 s.
Encoding cadence is NOT game FPS. Original still `_001` and the decoded
five-second frame were inspected, not just image-change statistics. The raft
leaves the fixed view; broad white froth, smooth green faces and broad rock
flanks remain. No new convincing-breaking, froth or full-motion acceptance.

Original still `unreal/Saved/Screenshots/source-packing-default-motion-v1-20260915_001.png`,
SHA-256 `138c37e00cc95d87ec71c3f7e80bd501e9546cffa10a3868f9be0994b8ff8e22`.
Decoded frames/report: `tmp/source-packing-motion-decode-v1-20260915`.
All 464 protected source/actor hashes match; all owned jobs are terminal.
Generated outputs and local build/capture files remain ignored.

NEXT: remaining runtime publication/refresh costs, actual crest/froth shape and
reference qualification; inlet crossings/overlap, one-sided forces and complete
rational front/time coupling with native single-surface integration. South Fork
remains incomplete. Colorado → Pacuare → Futaleufu, Chilko/Zambezi/all-scene water,
crew, normalization, regressions and release remain OPEN. Troublemaker remains
a rapid within South Fork, not its own menu scenario.
