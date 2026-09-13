# Moving persistent detail: playable integration — September 12

## Current verified state — integration works, realism/performance fail

Corrected late-frame owner build55575 exits0 (67.50s), RaftDLL
`041f79a1f04bd9a51decf293c2b88424a205873e7c54c18e520e0189bce4a4e3`.
MainDLL01e59a34… and installed material e4e9b2f3… unchanged. Final regression
34113 exits0:54successes, zero warnings/failures/unrun; report
`unreal/Saved/RaftSimValidation/south-fork-moving-owner-regressions-v2-20260912/index.json`.
Python compile checks and scoped whitespace checks pass. No terrain/map/save
changes; mapdb3080cc… and save181d1e57… were rehashed unchanged.

Actual normal-map run27891 exits0, with persistent detail ACTIVE, two exact
window remaps, zero post-initialization teleports,178 rendered-frame history
copies,20.966668 simulated seconds. Current/previous texture registration is
now used by the actual single clipped carrier, not only GPU fixtures. The
initial review-station relocation occurs before the first simulation dispatch.
The game still logs nonfatal engine editor-toolset Python startup errors;
this is not a clean all-project release pass.

Capture `south-fork-moving-owner-v2-20260912`:40 unique PNGs spanning12.189
sampled game seconds, fixed camera. Frames000/039 actually inspected: broad
white coverage is reduced, but the crest faces remain smooth and foam is too
sparse/linear to accept as convincing breaking water. Movie
`unreal/Saved/VideoCaptures/RaftSim_20260912-153101.mp4`, SHA256
`2609379dab1f408ee9ce88fc84919a4f500a274f52cf19ffa93d32945ac2479c`.
82 source frames/16.840s is capture evidence, not FPS or continuous viewing.
Motion report `tmp/south-fork-moving-owner-motion-v2-20260912.json`.

Opt-in actual GPU snapshots in `tmp/south-fork-moving-owner-snapshots-v2-20260912`
independently reproduce resolve within1.028144477e-7 across height/slopes/foam.
Wet-interior detail RMS5.0–6.6mm, extrema-5.76/+7.31cm across three snapshots;
this is not an overturning fluid surface. At10.036s, simulation10.033s; repeated
PNG/video/readback capture then lags, ending5.713s behind. Do NOT claim the
diagnostic clip shows correctly paced physics throughout.

Actual shared-crest gate still passes:1,550,016 interior samples, target error
0.600780725cm<=2cm, source vertex change0, fine-correction tracking0.000201703cm.
Report `tmp/south-fork-moving-owner-crest-v2-20260912.json.cartesian-mesh.json`.
This excludes GPU perturbations, macro temporal lag and other base relief.
**GPU/raft contact and total shaded surface alignment remain unaccepted.**

Isolated profile89117 exits0, cook suspension AND resume return0.300 CSV rows,
same inclusive100..250 interval, Development D3D12 WindowsEditor1280x720 RT0.
Mean76.807868ms = **13.019499FPS**, p9583.2087ms: regression from23.130356FPS
and FAIL60FPS. GPU23.661591ms; CPU crest update31.014888ms, including selection
19.511018ms on all151 sampled frames. Never add nested scopes. Profile
`tmp/south-fork-moving-owner-performance-v1-20260912.json`; CSV SHA256
`4bacfdddab9918cecf32e4ffd7c09fd9550c93fb8c58a756a6b8753406790e6b`.
In this non-snapshot run, detail advances34.075002s over34.083s with7.581ms
backlog, three exact remaps and429 history copies: the severe recording lag
is not reproduced in this short ordinary-play interval. Sustained/whole-river
performance and lifecycle acceptance are still open.

NEXT: eliminate unnecessary fine-mesh selection/reconstruction and GPU cost
without lowering geometry, cadence or60FPS gates; improve physical crest/
overfall shape and persistent entrainment/optics (not just suppress white
coverage); validate actual contact, ordinary motion and full-river handoffs.
Continue real-reference comparison when playback is available. Current v3
hydraulic cook29308 is live, observed1885/local3700; audited1800 state AND
banks pass, next complete1900/local4000. Runtime600s remains unchanged.
All later rivers, crew, normalization, release and final commit remain open.

## Implementation and retained failure history

The moving owner is now implemented in `URaftSimStatefulDetailComponent` and
connected to the normal Cartesian single-surface actor, selected only when
the material exposes the registered-detail marker. It follows the actual
raft, fixes the basis to east/north, snaps centres to half-metres, and moves
after8m drift. Routine overlapping moves use exact GPU remapping; nonoverlapping
teleports explicitly reset. Current and previous textures include their own
origin metadata. Legacy fixed review-map initialization remains supported.

The guarded material installer `unreal/Scripts/integrate_south_fork_moving_detail.py`
backs up baseline094123c7… before wiring registered WPO/history and slope detail
into the SAME normal parent. Runtime initialization retires BOTH procedural
local WPO and its procedural rigid-support counterpart. Macro/shared crest
support stays intact; **GPU perturbation/contact acceptance is still required**.
The GPU foam coverage replaces the CPU foam input within the detail window,
with an edge blend and the same four existing optical consumers, not a second
foam sheet or added coverage. The installed asset, actual run and compile
results must be verified below before treating this as a working integration.

The clipped crest refinement also accepts an explicit dynamic-detail sampling
window: maximum50cm triangle axis span on the one wet carrier, preserving
source vertices, profile heights, boundary constraints and original-cell
ownership. A padded96m raft-near box covers moving64m texture domains between
rebuilds. This increases rendering work; no performance improvement is claimed.
New `RaftSim.WaterDetail.MovingDetailMeshSampling` checks moving windows, flat
macro profiles, serial/parallel exact topology, source positions, area/winding
and conforming edges. Existing2cm crest gate is unchanged.

Buildv1 session13174 fails168.63s: used a BuildGrid-local scenario boolean in
Tick. Corrected selection relies on the integrated material marker and
Cartesian/single-surface mode. Buildv2 session60739 succeeds49.89s. Current
RaftDLL `b856021fc3844ab3511b1d459e713b0953f81b678a174bb861b68e7ac0914c52`,
mainDLL `01e59a34d5e2ba3fbd8f2c04cda324f24f4f0a77e0ad4d3d4aeab9f1855d653c`.
Installer98306 was retired after direct worker output established a shader
error: default vertex-color input was RGB but the new node read `Vertex.gba`.
The exact command-line-checked owned process was stopped, original material
094123c7… unchanged, log/backup/failure report retained. This was not a timeout.
Corrected installer79369 completes graph/protected-file assertions and saves
material `e4e9b2f331c702e09f3d7a01566440da4674b88e06f283e8aa41951ae023d4c3`;
process exits1, so assertion success is not labelled a clean process pass.
Report `unreal/Saved/RaftSimValidation/south-fork-moving-detail-install-v2-20260912.json`.
Native/D3D12 regression98534 exits0:54successes, zero warnings/failures/unrun,
including the new moving geometry test and prior backend/playable regressions.
Report `unreal/Saved/RaftSimValidation/south-fork-moving-owner-regressions-v1-20260912/index.json`.
First fresh-material audit94727 exits0 BUT asserts raw graph inequality;
process-local Python wrapper addresses were not normalized. It is a failed
audit, not a pass. The corrected audit strips only addresses using the existing
canonical helper, preserving every input, asset path, code and numeric value.
Corrected fresh audit71591 exits0 and passes all six canonical graph checks,
material SHA unchanged; report `south-fork-moving-detail-fresh-v3-20260912.json`.

First actual normal-map capture12460 exits0 but FAILS integration: initialized
at the put-in, then the run manager moved the raft and hydraulic window later
in that frame. The component had retained the early actor-tick focus, so it
refused the old out-of-domain sample and disabled itself. Final simulated time
ZERO, exact remaps0, texture history242 frames. Movie152724 and40 PNGs remain
failure evidence, NOT working detail or appearance acceptance. The follow-up
reads a weak referenced raft actor directly during TG_PostUpdateWork, with
an explicit actor prerequisite; it does not delay by an arbitrary timer or
fall back to invented flow. Corrected build/capture results are recorded above.

Computer-use skill initialized again for reference playback, but both Node
and browser runtimes fail kernel assets with OS error3. Dreamflows caption
retrieved again; its JPEG fetch again fails cache miss. No new real-reference
photo or continuous video viewing is claimed. Engine work is not blocked by it.

## Previous authoritative gap (before this integration)

Before this integration, ordinary South Fork used the Cartesian single carrier, CPU-transported
foam and procedural GPU displacement. `ComputeCoupledLocalFluidHeightfieldMeters`
does not evolve a persistent fluid state, despite the historical “GPU fluid”
label. `URaftSimStatefulDetailComponent` initialization is still guarded by the
registered-rock review map and explicit stateful-review flags. Its fixed64m
window is unsuitable for a full descent without explicit transfer and history.
This explains one missing integration, not every defect in the screenshot.

Neither flipping those flags nor adding another fixed rapid-only scenario is
the solution. South Fork is the scenario; Troublemaker remains an in-river rapid.
The current pass implements the moving-state/render-history prerequisites.
At that earlier checkpoint they were **not yet wired into the normal-map owner/material**, and no new
gameplay appearance or frame-rate improvement is claimed from this pass.

## Exact GPU window transfer

`FRaftSimDetailWaterGPU::RemapWindow` transfers overlapping wet cells directly
on the GPU: height perturbation, both perturbation momenta, unbounded positive
foam density and optional activity. It performs no interpolation, clipping or
periodic wrapping. Newly exposed cells start at zero DETAIL (not zero bulk
water); newly dry cells lose detail consistently with the existing PDE. The
caller supplies new-domain mean flow. This does not claim global conservation
when part of the previous simulation domain is deliberately discarded.

An exact cell-aligned overlap is mandatory. Fractional shifts, nonoverlapping
teleports, implicit resizing/rescaling, changed transport/activity modes,
invalid flow and unstable CFL requests fail before mutation. Teleports require
an explicit owner reset. Ordinary `Advance` still rejects implicit origin
changes. Remapping preserves step count, elapsed simulation time and forcing
phase; runtime needs no readback.

First build49.27s succeeds (session80637 exit0; existing D6 runner float warnings
retained). GPU suite42713 exits0:16 successes, zero test warnings/failures/unrun.
Report `unreal/Saved/RaftSimValidation/south-fork-detail-remap-gpu-v1-20260912/index.json`.
Selected D3D12 adapter is NVIDIA RTX3060 Laptop GPU, not the generic integrated
GPU listed elsewhere in device metadata. New exact-transfer test checks5,304
cells across four transport/activity combinations and signed/zero/nearly-full
window shifts:1,544 retained cells with density>1,2,456 exposed,240 drying.
Existing transport, source, shore, resolve, refinement and history tests pass.

## Origin travels with rendered history

Legacy Nx-by-Ny resolve remains supported. Nx-by-(Ny+1) additionally stores
the grid origin and cell size in a metadata row. The shared registered sampler
reads that texture's own origin, with explicit data-only bilinear interpolation
and zero outside the data footprint. The metadata row must never be filtered
into water height. Copying a rendered-frame texture now also copies its spatial
registration, avoiding current-origin/previous-pixels drift after recentering.

The new GPU history fixture evolves real state, resolves it, remaps twice, and
samples both current and previous textures at fixed world-frame coordinates.
An independent CPU resolve provides expectations, including moving edge taper,
dry cells and outside queries. It also tests multiple moves before a rendered
frame and no simulation update between frame captures. A counterfactual check
requires the fixture to distinguish the wrong-origin bug.

Initial history build15381 fails on a test shared-pointer dereference (43.45s,
log retained). Corrected build60692 succeeds18.40s. No production algorithm
was changed to accommodate the compile error. Current DLL SHA256:

- WaterDetail: `0202566c21ee859bc6f39e3721f4b4bcee3c2cbc058b5ac53e370fda80eb9c56`
- Raft: `feb026b6cb816f3160beea88318ee25e0620076b8a49cdae5af4e71974edfed1`
- Main game unchanged: `40f149a155ccfd829a288961e6c5bd9c46bbc183c883d7c1123dbaf54db1b708`

Combined GPU/playable regressions61558 exit0:53successes, zero warnings,
failures or unrun. Report
`unreal/Saved/RaftSimValidation/south-fork-detail-history-regressions-v1-20260912/index.json`.
Registered GPU history compares42 world samples over six snapshots, maximum
RGBA error2.98023224e-8<unchanged1e-6. Exact transfer and all prior playable
geometry/transport/catalog/save checks also pass. No actual moving-scenario
rendering or performance acceptance follows from these fixtures.

## Next required integration, not acceptance by fixture

Connect a cell-snapped fixed Cartesian-basis owner to the actual raft/live
window; preserve overlap rather than reseeding on routine movement. Bind the
registered current/previous textures into the same clipped visible carrier,
with sufficient geometry sampling and one foam authority. Validate actual
gameplay handoffs, dry banks, raft contact, simulation lag and render motion;
compare to real reference motion and repeat isolated performance measurement.
The perturbation solver is a shallow-water detail PDE, not an overturning3D
liquid solver or measured rapid geometry. Its old review footage was still
smooth; merely enabling it will not establish convincing breaking water.

No map/material/source terrain/save changes were requested by these backend
operations. Current known visual/performance evidence remains the prior
vertex-memory capture (23.13FPS, p9554.21ms, visually unaccepted). The expanded
v3 hydraulic cook remains independent; do not promote it without complete
state AND artificial-bank audits. All broader goal items remain open.

Reference lookup during this pass retrieved the [Dreamflows caption](https://www.dreamflows.com/American/troublemaker.wavewheel.lg.php)
but the JPEG fetch failed. No new photo viewing, calibrated flow comparison
or continuous real-reference viewing is claimed.
