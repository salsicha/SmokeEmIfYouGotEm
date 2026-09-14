# Actual river samples outside the detail window — September 13

Normal moving Cartesian play now acquires and uploads the actual exterior depth,
east/north momentum and physical bed needed by the new boundary transport API.
This closes the missing source-data connection. It does **not** switch normal
play to the total-depth evolution owner, supply nonhydrostatic pressure boundary
conditions, or establish convincing breaking/froth and 30 FPS acceptance.

## Implementation and invariants

The source query lattice is now67x67 at1m spacing: the existing65x65 interior
nodes plus one coarse-node ring,264 extra hydraulic queries per8Hz refresh.
Its corner is the registered integer coarse origin minus(1,1)m. World registration
is still fixed under half-metre window moves. `InterpolateHalo` supports output
indices-1 through128, with explicit endpoint copying and no clamped exterior.
The existing mean/entrainment/timestep path still receives its original65x65
interior samples. Nonmoving legacy maps retain their original65x65 path.

`FRaftSimTotalDepthSource::Build` requires paired67x67 input; an interior-only
packet is no longer sufficient. It interpolates conserved h/hu/hv, not h times
interpolated velocity, and keeps independently stored positive depth even when
surface-bed rounds to zero or presentation wetness is false. Physical bed remains
independent. This is point interpolation, not new surveyed bathymetry or a
conservative finite-volume remap. No state/velocity floor or cap was added.

Every immutable source revision contains512 actual half-metre ghost centres in
west/east/south/north order, and uploads five paired GPU buffers instead of three.
Exterior State/Bed add10,240 represented GPU bytes per revision, excluding
allocator overhead. Source observation time remains explicit. Refreshing source
inputs never resets evolving interior water; no solver timestep policy changed.
The source API supplies no foam, so exterior foam is explicitly zero, not invented
from a presentation mask. Temporal boundary policy and pressure closure remain open.

## Native and actual-play evidence

Build58789 CLOSED exit0,70.48s. Native D3D12 run40776 CLOSED exit0:
76 passes,0 automation warnings/failures/unrun,15.706357s. Existing engine startup
warnings remain in the log. Report:
`tmp/south-fork-live-exterior-source-native-v1-20260913/index.json`.

The fixed-world tests retain485,464 interior h/M/bed/reference cells bit-exact
across signed shifts and phases. They also compare11,688 ghost/interior exchanges
at the same world positions and65,536 old-versus-expanded interior interpolation
samples, all exact. These are manufactured fields, not measured terrain errors.
The source uploader test reads all five actual uploaded buffers back bit-exact,
checks deduplication/stale-revision refusal and directly feeds those registered
GPU buffers into the exterior transport shader with clean diagnostics. No copied
CPU FV rate is substituted for the native transport calculation.

Ordinary FullReach1280x720 profiles, without builds/tests running concurrently:

- Audit54470 CLOSED0, label`south-fork-live-exterior-source-audit-v1-20260913`.
  Five overlapping moves compare1,171 exterior positions to prior interior bed,
  all exactly equal. Source240uploads/revision241,512 exterior cells,253 positive
  and49 positive at or below1cm.692 presentation commits/1hold;34.025002 simulated
  seconds,0.005229s backlog. Mean source preparation2.631412ms/max3.995299ms.
- Default52402 CLOSED0, label`south-fork-live-exterior-source-default-v1-20260913`.
  Six overlapping moves compare1,406 exterior positions to prior interior bed,
  all exactly equal. Source239uploads/revision240,512 exterior cells,244 positive
  and29 positive at or below1cm.687 commits/1hold;34.066668 simulated seconds,
  0.000661s backlog. Mean source preparation2.657939ms/max3.947500ms.

The initial nonoverlapping relocation in each run is recorded separately, not
counted as overlap evidence. Actual h/M remain time-varying; only fixed bed is
compared across these live sample times. Both runs record no source fallback or
reset. Both verified cook suspension and resumption return0; the cook was not
restarted, and the profile's ephemeral save policy preserves user progression.

Audit frame184 pairs2,021 wet support queries (950 affected by detail,0 unavailable)
with4,226 actual uploaded-texture GPU queries. Maximum support/carrier error is
0.000047619839051549cm, RMS0.000023815041492311cm; maximum GPU RGBA error is
2.9802322387695312e-8, passed. No geometry/contact tolerance change.
Reports `tmp/south-fork-live-exterior-contact-v1-20260913.json` and
`tmp/south-fork-live-exterior-gpu-v1-20260913.json`; hashes respectively
`49cff474b1d4ebad06e2a99d8e42ff7b8d06125e6f363356ce4ce79862bfae0d` and
`d0aeff1ec616d5deda8fdf26e27e6612c1b90a06dac1ef5664b81c21559bb79d`.
This does not qualify full-traversal/render latency or visual realism.

## Performance, visual review and remaining work

Fresh default CSV rows60–240 measure21.496540FPS, p9554.5967ms: **fails30FPS**.
Game thread46.192560ms, GPU15.597734ms. Previous22.252858FPS/p9551.2054ms remains
history; differing trajectories/refreshes do not isolate the cause of the timing
difference. Report `tmp/south-fork-live-exterior-source-performance-v1-20260913.json`.
New CSV SHA256`5818352eec5569eb0c9c010e257b26bd4f95a3c1693293b11696c800a300fef6`.

Both actual screenshots were inspected. Broad smooth glossy crests and extensive
soft white froth remain unaccepted; terrain/vegetation/crew are still unfinished.
There is no new continuous-motion reference comparison. Default screenshot:
`unreal/Saved/Screenshots/south-fork-live-exterior-source-default-v1-20260913.png`,
SHA256`218b4ecc63e8c4181580581cfa30cc7e16d0ac4f4629ed9f912b5386425051cb`.

The reference-video retry again failed: both supplied YouTube pages returned web
cache misses; browser and native computer-use initialization both returned
`failed to write kernel assets: The system cannot find the path specified. (os error 3)`.
The computer-use skill and required guidance were read; no video was viewed or
downloaded. This does not block the independent source integration work.

Cook96057/PID29104 remains live, observed3974s/local39480 after both profiles
resumed it.3900s is still the latest BOTH-audited checkpoint, still settling;
runtime600s unchanged. Final4000/local40000 needs complete snapshot plus terminal
confirmation and both audits. Do not restart on an observation timeout.

Next: physical/nonhydrostatic boundary closure and temporal source exchange,
persistent total-state time/window owner, evolved wet render/contact eligibility,
breaking/foam and actual motion/performance qualification. All requested terrain,
rapid/scenario, later rivers, crew, normalization, release and final commit remain
active. South Fork remains the scenario; Troublemaker remains off-menu as a rapid.

## Provenance and preservation

Grid header SHA256`efbc845765d14ccf9d7b7d940493e8cbfd59690a3410f45ce86a6985b87e2a9d`.
Source header`68433d4110a4a3a43b6008f4144d5afd1034cd990bc95f4369146f06b18de82c`.
Uploader header`683c172e9f5cc6645124e3772dc0c65724689ec7ebcfdc88ecf9a168542ad32d`.
Component`1ebce433693f143603cbfc08bfee5413cdcacc5369b100bf721d9242809f8926`.
Raft DLL`7ed12e2b9e5392305ecd0dd59374a4ce778c4feb8c22f9bcef4f5f22466e711a`.
WaterDetail DLL unchanged from the exterior-transport build.

Map/material/save hashes rechecked unchanged after the final run:
`db3080cc87f82bafbcb5403757fead35ca6b7a5d4b52dc74c35548d5faf7abb6`,
`26aa5029c579afad38fd603f96df9da304bd32ed338097d2580c9a29545ea82a`,
`181d1e570485d1ec3139aec4e1d9b56d0a420fd107ce5a94218368324207f5b1`.
Scoped tracked diff/explicit new-source whitespace checks pass. An in-place
component edit was denied; the scoped apply-patch move/edit/move-back succeeded,
preserving all unrelated edits and leaving no temporary source file. No commits.
CPU PDE unchanged this turn; the prior184 CPU passes were not rerun or relabelled
as new. This turn is progress through actual-play source integration and checks,
not scene completion or full release qualification.
