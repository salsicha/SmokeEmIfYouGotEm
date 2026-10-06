# World-aligned live water sampling — September 13

The prior turn optimized the normal breaking-vertex pass. This turn fixes a
registration problem in the actual playable mean/source inputs: the half-metre
moving output window previously moved its one-metre coarse sampling lattice
with it. Re-interpolating uneven terrain on a different lattice phase can
change the sampled bed at a retained world position.

## Implementation and numerical evidence

`FRaftSimDetailSampleGrid` fixes the65x65coarse samples to integer east/north
metres and resamples the128x128half-metre output at its actual phase. Negative
coordinates use floor, not truncation. The final positive-phase edge copies
node64 exactly; it neither clamps to63.5 nor relies on a cancellation-prone
lerp with alpha1. Unsupported quarter-cell/nonfinite origins are refused.

Normal moving detail uses this registration for its field queries, existing
mean/entrainment inputs, paired capture geometry and unmasked total-depth source.
The immutable source packet records and validates its coarse origin. Nonmoving
review sampling retains its existing local basis. Live h/M continues updating;
no frozen mean, depth masking change, physics-frequency reduction or evolving
state reset is introduced. This is point-grid sampling, not a conservative FV
remap, newly measured bathymetry or full terrain reconstruction.

Native `RaftSim.WaterDetail.DetailSampleGrid` compares485,464retained cells across
all four half-cell phases, signed/east/north/diagonal shifts, large overlap
changes and last-corner cases. State h/hu/hv/foam, physical bed and reference
surface are bit-exact for a frozen manufactured world field. A triangular
one-metre bed-wave fixture reproduces0.5m error with the historical moving
lattice and0with the fixed lattice. The0.5m is a manufactured regression result,
NOT a measured South Fork bed discrepancy. Thin positive water remains covered.

Build64924 succeeded82.80s. Native77931 closed exit0:75passes, zero automation
warnings/failures/unrun,17.603611s. Existing engine-startup warnings remain in
the log; this is not a claim of a warning-free full editor startup.
Report: `tmp/south-fork-world-sample-grid-native-v1-20260913/index.json`.
No new CPU PDE replay or whole-solver stability qualification was performed.

Grid header SHA256: `beca512d7895fe89a897704e32b5c53fa980e448dc9a5988b8ae5892580ff16f`.
Source header SHA256: `6ccd17ea2a5278badd05eb49af72a7142cc5bf11df2da79ae52857718f1c3377`.
Component SHA256: `2da5df92c65569b07d429e1f59262760cfec02265749ad66695418469f5183f4`.
Raft DLL SHA256: `ea61b3e7d9f7e65e1828414c5ec4c8992999eb9e2e9979c34c0c187cb4ceaf27`.

## Actual normal-game remaps and paired contact

Normal audit88219 closed exit0. All six overlapping live moves logged zero
changed bed cells and maximum bed difference0, including half-metre phases.
The initial explicit no-overlap relocation is recorded separately, not claimed
as retained-state evidence. Query time advances; this check does not freeze flow.

The actual contact and GPU audits share detail frame182:

- 2,021wet contact points,950with nonzero detail; no dry/unavailable points.
  Maximum support/carrier error0.000047678516cm, RMS0.000024104079cm.
- 4,226GPU material-helper queries versus the uploaded CPU contact payload:
  maximum RGBA error5.960464478e-8; GPU audit passed.

Reports: `tmp/south-fork-world-grid-contact-v1-20260913.json` and
`tmp/south-fork-world-grid-gpu-v1-20260913.json`.
SHA256s respectively:
`77a4c46f808b9d79ebef9f7aab976e758b7f75fbd280e14bc70d9dac29ffac92`,
`f9502e37a1db7591bf8417566925c979e55205a164700fba6975a213f4ae20d5`.
This bounded sample is not full traversal, latency, visual or scene acceptance.

The profiling script now accepts an optional argument array as well as its
previous single argument. Both audit flags reached the actual game separately;
PowerShell parsing succeeds. No shell-constructed game command is used.

## Clean performance capture and visual limits

Normal default85277 closed exit0 without contact-audit overhead. It logs five
overlapping moves with zero bed changes,736paired commits/1hold,
34.033335simulated seconds and0.007808s backlog. Both profile runs verified the
same cook29104 identity and returned suspend/resume status0; no build/native
test ran concurrently with either isolated capture.

CSV rows60–240 at1280x720 measure22.252858FPS/p9551.2054ms, game thread44.699752ms,
GPU15.128121ms: still FAIL30FPS/p9533.333ms. Resolution, quality, timestep policy,
solver/memory budgets and geometry/contact tolerances are unchanged. Previous
21.509721FPS/p9553.5233ms remains history; differing trajectories and refreshes
do not establish a causal FPS gain from this registration correction.
Report: `tmp/south-fork-world-sample-grid-performance-v1-20260913.json`.
Current CSV SHA256: `5097dcf456ab104cb1538ea55a19ec841ca3a086e40ecd260a5d856e7854bd59`.

Audit and default screenshots were both inspected. Smooth broad crests,
extensive soft white foam and incomplete scene/crew appearance remain unaccepted.
Default: `unreal/Saved/Screenshots/south-fork-world-sample-grid-default-v1-20260913.png`,
SHA256 `12e7437a9a70e16a7b4cd75981afceaaad484317b0ac142ed1eae2051ae64a5f`.
No continuous-motion recording or new reference-video playback this turn.
Map, material and user-save hashes remain unchanged. South Fork remains the
scenario; Troublemaker remains a rapid and stays off-menu.

## Process cleanup and remaining work

An accidental test launch1260 used `.unproject` rather than `.uproject` and
started editor27332 plus SDK-check descendants. Exact identities were inspected;
Stop-Process failed, then Windows management terminated only the owned mistaken
editor and its SDK checks. All descendants were subsequently confirmed absent;
1260 closed exit1. Correct native77931 waited for their build lock, then completed
without restarting. No project/source/evidence files were deleted. In-place
edits to the component files initially failed; scoped apply_patch move/edit/
move-back preserved their other changes. No temporary edit files remain.

Cook96057/PID29104 is confirmed live again at3881s/local37620.3800s remains the
latest BOTH-audited finite/dry-artificial-bank checkpoint, still settling.
Runtime600s fields are unchanged;3900/local38000 needs its complete marker
and both audits. Persistent total-depth ownership, physical open boundaries,
conservative source/window exchange, evolved wet render/contact eligibility,
and convincing breaking/froth generation remain unfinished. All terrain/rapid,
later river, crew,30FPS, release and final-commit requirements remain active.
