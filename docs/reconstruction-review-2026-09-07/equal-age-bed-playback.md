# Same-age South Fork bed comparison

Both original and revised full-river inputs now have actual 1280x720 game
captures starting from 50-second hydraulic states. The original still has the
deep central green bowl; the revised case does not show that central bowl in
the matched view. Broad white froth and steep bank-side streaks remain. This
is useful comparative evidence, **not visual acceptance or a calibrated bed**.

## Controls and limitations

`compare_south_fork_bed_cooks.py` hashes every declared input and verifies the
same common physical scenarios, timestep, discharge, outlet stage, datum,
initialization method, cap solid and source age. Four rapid cores differ in
552 bed cells in these actual solver inputs. The five appended context tiles
are exactly dry and motionless initially and at 50 seconds. Intermediate
context wetness and solver-binary identity are not established by this audit.
Initial depth differs in 540 common cells and each velocity component in
3,835; these are fresh bed-consistent initializations, not old-state transplants.

Report `tmp/equal-age-50s-bed-inputs-v1-20260916.json` passes, SHA256
`480bca34d7301573c3f024e2736cc77bf0ebb15c3e20f068772bb8ff2eb817f7`.
The exact-center runtime-window option refuses out-of-bounds centers and keeps
the four-cell query margin. Nineteen focused Python tests pass; source commit
`35da744f3`. No gate, crop, timestep or resolution was reduced.

The fresh original-bed native proof uses the same current retained rock asset
as the revised case and region0190 centered at (-5437.499999998952,3606.5)m.
Original descriptor `tmp/original-bed-50s-matched-preview-v1-20260916.json`,
SHA256 `e6b95d8c24de39e9e186677fe27686ee9f7074001030c714ab7de8a6f38a92f9`,
has 3,258 hashed dependencies. Revised descriptor and native evidence are in
[native terrain residency](native-terrain-residency.md). Both flows remain
unsettled. The game evolves asynchronously after loading; captures are not
identical simulation trajectories, raft poses, or precisely matched world times.

## Actual game evidence

Original session25065 finished with exit0. The isolated native loader reports
successful activation before BeginPlay; actual screenshots are 1280x720.
Camera is (-545900,-362700,2000)cm, pitch -35.27, yaw46.85, FOV90 in both runs.
Original captures occur at world12.585/22.285/32.566s, reaching station8354.820m;
the revised third capture is world32.251s, station8355.991m. Original shared
hull/render checks log zero error at revisions9 and1209. Neither run uses a
normally relinked project DLL; the baseline v1 path also lacks the v2 terrain
residency change. No saved map, scenario, actor or profile was promoted.

- Original log `tmp/original-bed-50s-matched-play-v1-20260916.log`, SHA256
  `26d3d1c0274336b36ca5b89b7cfc9c83d46e056b3943444ef4b4631abd7837ad`.
- Original screenshot `unreal/Saved/Screenshots/original-bed-50s-matched-v1-20260916_002.png`,
  SHA256 `f245db9ac680e46baeb64805270bb52f9dc63c4c133f01f43db385c768b1f256`.
- Revised screenshot `unreal/Saved/Screenshots/control-ablation-native-v1-20260916_002.png`,
  SHA256 `3909d9a8a1cc79b79db675ce8e9298446ef6d5df07c59fa4fbb91867be9274ca`.
- Original video `unreal/Saved/VideoCaptures/RaftSim_20260916-105136.mp4`,
  SHA256 `33e4c88635ce39172bbe150dfcfd35c0f7ca39c218da14108d1bebb0f692bd06`.

The original recording has 108 engine source frames over25.159s, decoded fully
to755 frames through25.133333s. Unmodified5/15s frames inspected: the bowl and
white blanket persist while the raft advances. Thirty-Hz encoding is not game
FPS. Whole-frame luma statistics do not isolate water, velocity or physical
wave motion. Decode report in `tmp/original-bed-50s-matched-motion-v1-20260916`,
SHA256 `44645972ba3b3a6b253118e7d91b91023b479928ee40017d4df002867cafff01`.

## Longer revised state

The same full841-core solve46094/PID22940 continues; no restart. Both250s and
300s audits pass all5,382,400 cells and all86,720 artificial-bank face cells.
At300s maximum depth4.812067m, maximum speed12.111935m/s and maximum step mass
residual1.376286e-8m3. Outflow24.074267 versus inflow45.306955m3/s means this
is still not settled.

- `tmp/control-ablation-250s-state-v1-20260916.json`:
  `3d073add7d3c545da261623f0da17796ede68c040c5f43c41d1b126ed1478ad6`.
- `tmp/control-ablation-250s-banks-v1-20260916.json`:
  `8c30dcb93da332fa15b6c447706435870344dba9045930c5497454a8a94e7178`.
- `tmp/control-ablation-300s-state-v1-20260916.json`:
  `f153e0cdd24c436c04e30c13244f3e682893f4992ab8b43fedd45d8239e5deb5`.
- `tmp/control-ablation-300s-banks-v1-20260916.json`:
  `897929a708b0de2f56d130cb8a15394f6c7a55ca3d5ee3c46032ef6a6550474b`.

The same run subsequently completed350s/step7000: both audits pass again.
Maximum depth4.896969m, speed12.111952m/s; outflow25.664812 versus
inflow45.306955m3/s still does not establish settling. Next checkpoint400s,
step8000, again requiring both audits.

- `tmp/control-ablation-350s-state-v1-20260916.json`:
  `a38e28968b8935e2a6c12034a757fd664efe42f2f18873ab1566e3ddfcba2403`.
- `tmp/control-ablation-350s-banks-v1-20260916.json`:
  `1b1406a3c69cd0bc546240d567c2138b3550123568e44f34acced39f32477067`.

Later-state runtime preparation session19540 completed with exit0, output
`tmp/control-ablation-runtime-350s-v1-20260916`: all841 tiles/799 packets and
42,185,039 source-bed intersections pass. It reuses791 unchanged source packets
from the50s export and rebuilds the8 union packets. Source-coverage audit passes
406,823 original-water probes with the existing explicit region0002 rectangle
repair. The minimum raft-interior margin remains10m. Exact-center expectations
contain25,600 queries on region0190, matching the50s camera-window location.
Atlas SHA256 `b1bcf071e992252a6b12f48327981e019d601971affd873975ab87fd4158c5ab`;
fields-manifest SHA256
`4437b6a7fdf3975d7582fc037435aa737c47781e1c1e8ce8e511505b4ff4cae5`.

Native saved-terrain/rock collision and field verification session92376 finished
exit0: all64,935 collision and25,600 native field queries pass, with zero native
wet mismatches. Maximum bed/surface error7.629395e-6m, depth1.192048e-7m and
velocity2.381361e-7m/s. The unchanged native1e-4m and solver1e-6m wet thresholds
explain differing wet counts; neither threshold was altered.
Proof `unreal/Saved/RaftSimValidation/control-ablation-native-runtime-350s-v1-20260916.json`,
SHA256 `74ec82d9380b7f7b9b49c39e3847deb3f15695eb2452f99304b1bdee4f43c1e3`.
Fresh3,267-dependency descriptor `tmp/control-ablation-350s-joint-preview-v1-20260916.json`,
SHA256 `4de7202df61db16d18bd42e87086fc2620681053e5210c50757db35ab68ec3c4`.

## Actual350s playback: improvement survives, acceptance still fails

Session25668 finishes exit0 with native paired activation before BeginPlay,
three actual1280x720 captures and24.952s recording. At world32.244s the raft
reaches station8360.208m. Shared hull/render checks at revisions9 and1209 log
zero error. The central bowl remains absent, but broad froth and bank-side
streaks remain; more low left-bank ground is inundated than in the50s case.
The5/15s unmodified decoded frames also show this. Do not promote this unsettled
water as a final South Fork reconstruction or infer a correct stage from appearance.

The direct support audit samples1,930 wet points at world10.0864s, including888
affected by the presented detail frame. Maximum support/carrier error is
4.766026e-5cm, RMS2.407126e-5cm, with zero unavailable points. All86
ground-occluded probes have dry support. This is sampled contact consistency,
not full traversal, independent terrain-occlusion truth, render-thread latency,
or GPU parity (the GPU audit was not requested in this run).

Submitted geometry at world13.1575s contains68,068 active vertices and50,600
triangles. The unchanged analyzer examines20,274 triangles within30m. Of those,
393 cover33.5293m2 at30–60 degrees; none exceed60 degrees. In the fully wet
source-comparable steep subset, the signed gradient along the displayed slope
is dominated by cached bed-plus-depth (.711931), not target shaping (.041170)
or temporal/refinement difference (3.96e-7). This is not a calibrated slope gate
and does not identify visible/occluded triangles. It points the remaining steep
surface work toward evolving hydraulic/source shape, not optical concealment.

- Game log `tmp/control-ablation-350s-native-play-v1-20260916.log`:
  `55121649d2be7600316863e9f753e77999c243b283d99b922e9746e6a20bd73b`.
- Contact `tmp/control-ablation-350s-contact-v1-20260916.json`:
  `2d650bfb9cf6c50e3c19f0f6e7d503e42d8f1cb017a3fbfedd6ddda32b7aeaaf`.
- Shape `tmp/control-ablation-350s-carrier-shape-v1-20260916.json`:
  `0292c3661a9c289e4e7eea74f15e60b0a94461438405a89f75382498f7c4a2f4`.
- Screenshot `unreal/Saved/Screenshots/control-ablation-350s-native-v1-20260916_002.png`:
  `f7ebd2b65429ee05536626f37d8b4b95ed6732cb3df6bdb03ea61f508c000d01`.
- Video `unreal/Saved/VideoCaptures/RaftSim_20260916-112907.mp4`:
  `e295ef63c2d6e107ccddc61d949afe2cb88b445a3b3318c5965f303ad862ff1a`.

Full video decode:116 engine source frames,749 decoded frames through24.9333s.
Report `tmp/control-ablation-350s-motion-v1-20260916/control-ablation-350s-native-play-v1-20260916.json`,
SHA256 `d05934f50ba481fe237d010cef8a959043f1620a298c7284179da2d25e63f6a8`.
As above, encoded30Hz and whole-frame changes do not establish game FPS or
physical motion. Native gameplay still uses the explicit isolated module,
not a normal project relink or menu-default promotion. Shader/cook inputs stay
unchanged while the same package build is live.

Continue physical shape/breaking/froth work and normal-play delivery, with
the unchanged30FPS/p95<=33.333ms gate. Later rivers, crew, regressions and release
remain open. Troublemaker is a rapid inside South Fork, never a menu scenario.
