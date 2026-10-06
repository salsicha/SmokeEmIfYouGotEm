# Playable lit-froth experiments — September 15

Both the normal-only and combined finer-coverage/lit-normal candidates are
REJECTED for ordinary gameplay after actual rendered inspection. The original
material is restored byte-for-byte; no geometry, collision, source provenance,
solver gate or default material-builder behavior changed.

## Reference and observed defect

The computer-use skill guided browser access to Qweniden's
[Trouble Maker South Fork American River 7/15/2022 — Raft California](https://www.youtube.com/watch?v=2XTbOCNDcZQ).
The actual video, not its advertisement, was accessible. Paused frames at
approximately 0:04, 0:09 and 0:14 were inspected, including the raft entering
the rapid. They show broken whitewater and exposed rough wave faces around
rocks. This is qualitative comparison, not calibrated geometry, discharge,
bubble dimensions or a claim to have watched the complete reference video.

The playable captures still show broad smooth green faces, a persistent white
band at the drop and blocky rock flanks. The normal-only candidate leaves broad
blurred white patches. Combining irregular coverage with the new normal makes
the foreground patches sharper but still flat, angular white chips. Later
decoded frames show the raft moving through and leaving the foreground while
this appearance persists. Neither result is convincing froth.

Runtime log inspection verifies `singleSurface=1` and the intended full-reach
transmission parent bound to the carrier. Runtime code already sets
`DriftFoamSurfaceGlow=0`; its nonzero saved default is not evidence of active
emission. A wrong parent or that glow setting does not explain these captures.
The candidates are not identical camera/physical states, so no pixel-difference
causal comparison or physical motion calibration is claimed.

## Implementation and qualification

`RaftSimFrothMicroNormal.ush` adds compact smooth dome slopes to the COMPLETE
current-plus-registered hydraulic normal. Coarse/fine heights of 8/2 mm and
frequencies of 8/22 cells per metre are artistic choices, NOT measurements.
The existing covered amount, committed clock and effective UV3 backtrace are
retained. No displacement, new foam source, extra water sheet or force is added.
The independent native reference differentiates scalar heights over a wider
5x5 neighborhood, rather than copying the shader's 3x3 analytic derivative.

Initial installation failed safely: the saved normal root is
`SouthForkMovingDetailNormalV1`, combining current noise with registered detail,
not the expected direct current-noise node. The corrected guard verifies the
complete saved normal graph and wraps it without bypassing hydraulic slopes.
Normal-only install14542 and fresh audit23859 PASS. Seven other output graphs
and all original nodes are unchanged; 464 protected files retain their hashes.
Candidate material SHA256:
`611b32839e01ff0f24d522ad02f3a0ac8a5a9ea56c812990f19c4596686b357e`.

Fresh native20712 completes SIX tests, all PASS: micro-normal GPU, irregular
froth GPU, existing coverage optics GPU, registered foam-clock GPU, committed
foam evolution and shoreline fine crest. Micro-normal1536 queries:
grid/phase/normal errors 1.36364014e-6 / 1.07951179e-7 / 1.46380685e-7;
unit error1.78813934e-7 and dry-normal error6.05288051e-8. Original tolerances
remain unchanged. The irregular helper's 83,377 queries retain range[0,1],
zero coordinate discrepancy and material error9.52464478e-7. These component
checks plus actual material compilation are NOT visual, physical or FPS acceptance.
Native report `tmp/combined-froth-native-v1-20260915/index.json` SHA256:
`31bdb9029f3c2a4b90c76cef6c47c9ae89dd36a5483add40b790d89944277021`.

Combined install40498 and fresh audit79293 PASS. Only the qualified irregular
coverage code and the final normal output change. All old node inputs, the
four existing optical consumers, clock, displacement and mask remain intact;
464 protected hashes are unchanged. Combined material SHA256:
`ff9e41bd4e66f822a70b3289f72597bb331b602281194f459fd40b2cc95d1e9a`.

## Actual local recordings

Both use the full South Fork scenario, review station8330, 1280x720 D3D12,
unchanged quality/physics, shore-left capture, ephemeral profile and 12-second
capture delay. Capture98503 and62373 both terminate successfully. The known
optional engine Python AgentSkill/PythonTestRunner initialization errors remain
in the game logs; these are not claimed to be error-free runs.

- Normal-only: `unreal/Saved/VideoCaptures/RaftSim_20260915-082616.mp4`,
  58 source frames over6.250s; SHA256
  `38d492c62c97108f619fc30d59504bf730c220ad117f00fd7769f3f75797e9f2`.
- Combined: `unreal/Saved/VideoCaptures/RaftSim_20260915-084116.mp4`,
  61 source frames over6.243s; SHA256
  `f2709642107d2be8b929b2fae3aa6d8606450ba3c3c9b975ba2ce27838dafa5c`.

The existing local-motion analyzer now accepts explicit logs, labels, output
directory and extraction times. Both complete recordings decode187 encoded
frames, monotonically from0 to6.2s. Unmodified1/3/5-second frames are retained
under `tmp/froth-optical-motion-decode-v1-20260915`; the combined3/5-second
frames were inspected in addition to the engine stills. Full decoding is not
the same as watching every frame. Image-change/gradient statistics are not
world-space velocity or photographic acceptance, and encoding at30Hz repeats
source frames; it does NOT prove30FPS gameplay.

## Restoration and next work

The first normal restoration crashed in UE5.8 `DeleteMaterialExpression` with
`!IsRooted()`; the on-disk candidate hash did not change. Attempting atomic
backup replacement while Unreal was open then returned Windows access denied,
also without changing the asset. The premature fresh audits failed because
no restoration report existed; those failed logs remain, not waived.

`raftsim_restore_material_backup.py` now performs exact recovery OUTSIDE Unreal,
verifying the installed target hash, the single allowed archive member, the
original bytes and both scoped paths before atomic replacement. It never
extracts arbitrary archive paths. Seven regression tests PASS, including stale
user edits, wrong backup hash, extra archive member, path escapes and existing
audit-output rejection. Neither restoration deletes unrelated files or backups.

Both candidates were recovered to the exact original SHA256
`44c07f419a3a0a9f27f420871e4f1594184e57476de0960e560337ce6a93b31d`.
Normal fresh80134 PASS; final combined fresh32513 PASS independently verifies
all eight original output graphs and464 protected hashes. No rejected node or
candidate binary remains in the playable material. All owned jobs are terminal.

Do not promote or repeat either optical combination as a presumed solution.
Next address the spatial/temporal breaking-surface and foam-deformation model
and unresolved source-front coupling, not just another normal-strength change.
No new ordinary performance measurement was taken for rejected candidates;
the last verified11.447123FPS / p9598.7482ms still FAILS the30FPS target.
The full South Fork reconstruction, later Colorado → Pacuare → Futaleufu,
Chilko/Zambezi/all-scene reviews, crew, normalization, retained regressions and
release acceptance remain OPEN. No measured geometry is relabeled as inference
or vice versa, and no acceptance threshold is weakened.
