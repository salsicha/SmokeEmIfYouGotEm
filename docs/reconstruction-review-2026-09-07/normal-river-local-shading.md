# Local-current shading and optical renewal — September 12

Follow-up: [effective surface transport and spilling budget](normal-river-foam-transport-budget.md)
supersede UV1-only optical motion below. Local froth/normal now read UV3 with
the CPU foam backtrace's roller/eddy contributions; bulk UV1 stays unchanged.
Pocket/boil fresh foam now shares the physical crest's spilling budget. Current
material094123c7…, RaftDLL1ec2517e…. Historical artifacts below remain retained.

Incremental integration, not finished visual/hydraulic/performance acceptance.
South Fork is the playable scenario; Troublemaker is only its in-river rapid.

## Normal-only correction

The inherited `SouthForkCurrentGradientNormalV1` depended on the single
raft-sampled `RaftSimFoamAdvectionMeters` collection parameter, while optical
froth already followed local UV1 velocity. The normal branch now uses local
source-frame flow, UV0 plus its source origin exactly once, and real material
time. Two overlapping phase samples blend slopes before normalization. Each
phase computes its own pixel footprint, including local-flow deformation.
Original simplex kernel, frequencies, slope weights, strength 0.18 and
spectral antialiasing thresholds remain unchanged. Tangent handedness remains
the mesh's responsibility; source north is not reflected a second time.

This is bounded frozen-velocity **optical** detail, not a persistent particle
history or the derivative of a newly simulated height field. It neither adds
water geometry nor establishes physically correct breaking motion.
Other river material variants are unchanged.

Build `south-fork-local-normal-build-v1-20260912.log` succeeds in 42.42 s.
The guarded installer backs up the exact material before mutation, verifies
WPO, opacity mask, color, roughness and opacity dependency graphs unchanged,
and checks all 456 map actor packages, map, ground asset and user save.
Exactly two normal inputs are added (691 expressions); a second refresh is
idempotent. Report:
`unreal/Saved/RaftSimValidation/south-fork-local-normal-integration-v1-20260912.json`.
Installer command session 62856 exits 0. Initial material SHA256:
`55c30b54276dfbab3356c2712bfe112c6b449daa35fb8d02c2c105cfe58d03fc`.
Initial normal shader SHA256:
`6bf59871e27596ec3afd88aaf58ff87894cc09c7e9ae369f47a47535d23321c8`.

Fresh process graph/package assertions pass in
`south-fork-local-normal-fresh-v1-20260912.json`. That command session 31677
exits 1 without a Python traceback or material compilation error; do not
report its process exit as a pass. Separate native/D3D12 session 30884 exits 0:
**36 successes, zero warnings/failures/unrun** in
`south-fork-local-normal-regressions-v1-20260912/index.json`. Runtime Raft DLL
remains `e3e11f6b…`; the C++ change is editor material authoring.

## Actual four-second version, and why renewal was shortened

Normal full-map game session 47229 exits 0. Screenshots
`south-fork-local-normal-v1-20260912_{000,020,039}.png` inspected: terrain,
trees, local water detail and the raft are present, but broad uniform white
patches and excessive long streaks still fail the intended appearance.
No claim of photorealism or continuous reference-motion agreement.

Motion audit `tmp/south-fork-local-normal-motion-audit-v1-20260912.json`:
40 unique PNGs over 11.743 s sampled game time, fixed camera. Video
`unreal/Saved/VideoCaptures/RaftSim_20260912-133932.mp4`:
100 source frames / 16.355 s, SHA256
`b45e6ea701f7148daced5004d89aa84454a30e4016aca5eef061c09b10bfc067`.
Encoder repeat frames and screenshot I/O are not FPS evidence.
Actual crest audit `tmp/south-fork-local-normal-crest-v1-20260912.json.cartesian-mesh.json`:
712,224 samples, max 1.427266455 cm <= unchanged 2 cm gate; source vertex change
0, fine-correction tracking error 0.090407640 cm. It excludes other base relief,
macro temporal lag and GPU perturbations, as stated in the audit.

Separate isolated 300-frame profile session 87884 exits 0 and resumes the
exact live cook with status 0. Strict two-run report:
`tmp/south-fork-local-normal-performance-v1-20260912.json`.
New CSV SHA256 `06a7d8cdddb2d59d27f252d1729520184f3fe4e2b0422ccdfd8a6e631905c8d5`.
Mean frame 44.174966 ms, p95 53.1133 ms, **22.637256 FPS: FAIL 60 FPS**;
GPU mean 12.799783 ms. Prior run 46.704141 ms / GPU 13.284025 ms; this short
variable-trajectory comparison does not establish causal or sustained gains.

## One-second revision

Both local shader clocks now renew over one second instead of four, limiting
their maximum local frozen-flow travel to one quarter while retaining the
same metres/second motion within each phase. The midpoint/reset weight is
still zero for a resetting phase. This is an appearance calibration responding
to the stretched capture, not a measured bubble lifetime or modified flow.
Ten phase/source tests pass, including half-second seams, zero flow, reversal,
bounded backtraces and unchanged coverage-after-threshold blending.

`integrate_south_fork_short_flow_renewal.py` verifies that only the two named
custom shader bodies change: all other graph code, links, parameters, physics
assets and user profile remain identical. No expressions added; refresh is
idempotent. Installer session 20379 exits 0. Report
`south-fork-short-flow-integration-v1-20260912.json` under validation.
Material SHA256 `3733e083d8e388227c82442cfbfcdc1b95a6eac8eb666ef6d9832796c3d23d4b`;
foam shader `e653648982c455b7d831305d021f1c96403762a6e4cab4782fb730bb65d9cc0b`;
normal shader `a2d269ac73fe7408dcadfc1efd0dec37a7a0b3299a8919010441132762be91e3`.
Previous materials and reports remain available; historical one-shot installers
must not be rerun against these new hashes.

Fresh reload assertions pass in `south-fork-short-flow-fresh-v1-20260912.json`;
session48781 exits1 without Python traceback/compilation error. Again, the
assertion report is evidence but not a clean process-exit pass. Actual normal
game session7882 exits0, with40 unique PNGs /11.837s sampled game time and a
fixed camera (`tmp/south-fork-short-flow-motion-audit-v1-20260912.json`).
Frames000/020/039 inspected: the one-second version has visibly shorter
streaks and more fragmented fine froth than the four-second capture. Broad
uniform white areas and breaking-profile fidelity remain unaccepted; static
samples cannot establish continuous-motion or reference agreement.

Actual movie `unreal/Saved/VideoCaptures/RaftSim_20260912-134734.mp4`,90 source
frames/16.445s, SHA256
`40576fad1eb071eaad16e1bf9e3a8aad8d9a112b12227f5b553354e6a4fd0ce4`.
Actual crest audit `tmp/south-fork-short-flow-crest-v1-20260912.json.cartesian-mesh.json`:
712,152 samples, max1.427381505cm <= unchanged2cm, source-vertex change0,
fine-correction tracking0.000274837cm. Same exclusions as the preceding audit.
Mapdb3080cc…, profile181d1e57…, runtime RaftDLLe3e11f6b… rehash unchanged.
These are shader-only changes after the36-test native suite; ten updated
phase tests and fresh saved-material checks cover the new one-second revision.
Current-version isolated profile session6848 exits0, no timeout; exact cook
suspend/resume both0. Strict completed300-row CSV audit passes in
`tmp/south-fork-short-flow-performance-v1-20260912.json` (samples100–250,
Development/D3D12/WindowsEditor,1280x720,RT off, screenshot outside interval).
CSV SHA256 `8e55fec7227aa76415bfc2f0fb2f94f560b8fd8b3cadcd80d15d965497313420`.
Mean frame44.902754ms, p9557.6281ms, **22.270349FPS: still FAIL60**;
GPU mean12.708109ms. No causal whole-frame or sustained performance claim.
Video preview request returned queued, not proof of playback or review.

No build/editor/game remains live. Same expanded cook68098/PID35952 has
advanced beyond its independently passed1700s snapshot; observed1707s/local2140.
[State and artificial-bank audits](full-river-expanded-checkpoint.md) pass at
1700s, but flow remains unsettled. Next full1800s/local4000 audit; runtime600s
unchanged. Next scene work: physical crest/trough shape, overly uniform foam
coverage/renewal artifacts, remaining CPU cost, guidance/rejoin, whole-river
scenery, then later rivers/crew/release/commit. None is silently closed here.

## Reference access

The [Dreamflows photo page](https://www.dreamflows.com/American/troublemaker.wavewheel.lg.php)
was retrieved and identifies Chris Shackleton's 2006 Troublemaker-hole photo
with Gunsight rock in the foreground. The actual linked JPEG fetch failed
with a cache miss. Search-result descriptions are not a substitute for viewing
the image: no fresh image-based geometry or motion comparison is claimed.
Previously unavailable browser video playback remains a separate limitation.
