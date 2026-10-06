# Chili Bar canopy in normal South Fork play

September 18, 2026. Visible integration progress, **not** complete scene,
photoreal water, tree-art, 30 FPS, or release acceptance.

The ordinary put-in previously showed bare slopes even though the retained
registered NAIP image shows wooded banks. The existing captured canopy covered
only the Troublemaker survey area. The normal FullReach map now adds 5,244
source-supported inferred canopy instances near Chili Bar, split among twelve
256 m spatial ownership groups. No separate rapid scenario was added.

## Source and inference

The retained source is under
`physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/chili_bar/canopy_20260918`.

- [NOAA survey metadata](https://www.fisheries.noaa.gov/inport/item/66639)
  identifies the original USGS survey and its alternate EPT delivery.
- The working alternate endpoint is
  [USGS EPT metadata](https://usgs-lidar-public.s3.amazonaws.com/CA_UpperSouthAmerican_Eldorado_2019/ept.json).
  Per-tile provider lineage, original CRS, reprojection pipeline, bounds,
  hierarchy pages, URL/byte/hash receipts, and node scale/offset records are
  retained. The source node cache stays in ignored `tmp`.
- All 936 intersecting ancestor/leaf nodes were fetched. The independently
  replayed full hierarchy contains 47,931,181 points before the exact imagery
  crop. All 34,614,725 retained non-withheld records reproduce provider XYZ
  integers, transformed XY/Z, classifications, GPS time, and point-source IDs
  exactly. There is no resolution/depth shortcut or invented missing-node fill.
- These are provider-reprojected, millimetre-quantized EPT returns, **not** the
  original LAS integer coordinates or original LAS record ordering. Provider
  node/record identity is preserved explicitly. Metadata and bounds confirm
  NAVD88 survey-foot-to-metre conversion, without a fitted vertical offset.
- 4,997,859 dry class-2 returns compared with the retained survey raster have
  median signed difference 0.00060205 m and absolute p95 0.05492827 m. This
  verifies consistency, not a new accuracy certification or local survey tie.
- The original large-tile downloader was LIVE and making progress despite
  stale zero-byte directory entries: direct open-file inspection found
  87,031,808 bytes and a LASF header in one file. After the alternate crop's
  full independent audit passed, only that now-redundant owned downloader
  (PID 23976, start UTC 2026-09-18T10:33:24.8982323Z) was stopped. Partial files
  remain in ignored `tmp`; no timeout-driven duplicate original job was started.
- The alternate fetch initially exited on WinError 10054. Its next run reused
  hash-verified completed nodes and used bounded transient-request retries.

Placement uses the retained green-imagery evidence, at least twelve qualifying
class 1/3/4/5 returns per 3 m group, captured crown-top estimates, deterministic
separation, a conservative dry collar of at least 2 m, and an upward ground
normal of at least 0.55. All roots follow the original rendered coarse triangles,
not bilinear ground. 26,076 supported candidates yield 5,244 instances, with
heights 3.6095..29.9856 m. Three existing project-authored live-oak forms are
reused. Species, crown forms, trunk positions and orientations remain inferred;
this is **not a surveyed tree inventory**, coincident-date observation, or
verified solid-tree collision. No terrain or hydraulic geometry was changed.

## Engine integration

The first installer attempt failed on a Python path-expression typo during
preflight, before loading/mutating the target map; its log is retained under
`unreal/Saved/Logs/chili-bar-canopy-integration-v1-20260918.log`. The map hash
remained unchanged and no backup/mutation had started. The corrected second
attempt completed, then a separate fresh-editor read-only audit passed.

All 5,244 roots were checked against engine collision before saving, after
level reload, and again in the fresh editor. Maximum root error:
**0.003904159 cm**. External actors increase from 457 to 469. All 457 previous
external packages, including terrain, boulders, hydraulic configuration and
the rapid canopy, remain byte-identical. Source assets and the user profile
also remain unchanged. New canopy is spatially loaded, non-editor-only, and
has no tick, overlap or collision. Map backup and package hashes are retained.

The fresh engine catalog verifies all five South Fork entries share FullReach:
upper, Coloma, gorge, lower, full descent. No Troublemaker scenario ID exists.
`integration_audit.json` is the durable fresh-process receipt, not just a saved
Python intention. The `.umap` and twelve external actor packages are included.

## Player-view and motion evidence

Exact copies of the ordinary put-in captures:

![Before: bare normal-start banks](chili-bar-canopy/before-player-view.png)

![After: source-supported inferred canopy in normal play](chili-bar-canopy/after-player-view.png)

The capture wrapper now supports `-NormalScenarioStart`; it omits the usual
8330 m diagnostic station and rejects contradictory station overrides. Its
existing diagnostic default remains unchanged. No preview map, optical-control
override, altered time scale, or different camera was used.

Both complete videos decoded to 469 encoded frames. Before: 212 actual source
frames / 15.620 s; after: 200 / 15.646 s. Encoding repeats frames, so **30 fps
encoding is not 30 fps gameplay**. Unmodified 3 s and 13 s decoded frames were
inspected, alongside the ordinary clean screenshot and retained aerial image.
The raft progresses from approximately river km 0.12 to 0.14 with canopy visible
throughout the sampled player view. This is not full-reach traversal acceptance.
The recordings themselves remain local under `unreal/Saved/VideoCaptures`;
their filenames and hashes are in [review.json](chili-bar-canopy/review.json).

The view is visibly less barren. However, the repeated angular crown cards,
uniform inferred species, dark understorey, missing finer vegetation and
structures do **not** match the real bank closely enough for photoreal acceptance.
Neither the flowing surface, breaking waves nor froth was improved in this pass.
The decoder's historic rapid-view ROI names are not semantic put-in measurements;
no image-gradient statistic is used as realism or physical-motion acceptance.

## Performance and checks

Separate actual D3D12 game captures, 1280x720, normal start, same archive and
four solver lanes; 900 rows each, unchanged zero-based window 60..840 inclusive.
The exact running cook was suspended/resumed by the existing guarded wrapper.
Source processing and the editor audit were terminal before timing captures.

| Ordinary put-in | Mean FPS | p95 frame ms | 30 FPS / 33.333333 ms |
| --- | ---: | ---: | --- |
| Before canopy | 23.740287 | 49.2505 | FAIL |
| After canopy | 23.460393 | 49.7534 | FAIL |

This pair is not a speed win, causal performance attribution, sustained
packaged benchmark, or release acceptance. No quality, physical, timing or
performance gate was weakened. Both CSVs, process receipts and complete timing
audits are retained in the review folder.

54 focused Python canopy/terrain/capture tests PASS; PowerShell identity,
mode, timing, and normal-start override tests PASS. The complete point replay,
engine root probes, fresh reload and actual gameplay captures are additional
evidence, not substitutes for outstanding full-project regressions or releases.
No native code change or native rebuild was required. Historical optional
engine tooling/import warnings in the baseline logs remain unwaived.

The active hydraulic cook remains separate. Completed 8600, 8650, 8700, and 8750
snapshots passed BOTH full-state and artificial-bank audits. All 86,720 bank
face cells remain exactly dry. These are **NOT settled**; installed 4950 water
data stays unchanged. Do not promote these snapshots solely because these
diagnostics pass.
Cook PID 8900/start UTC 2026-09-18T06:34:59.2598919Z is verified LIVE after
captures, CPU time 96,510.515625 s at the last identity check. Next is
8800/local22000, requiring its completion marker and BOTH audits. The 8750
maximum depth is 3.7808036502 m, maximum speed 5.3527386939 m/s; outflow remains
about 100.01717 m3/s versus 45.30695 m3/s inflow, so this is not steady-state
acceptance. Reports remain in ignored `tmp/control-ablation-8750s-*-v1-20260918.json`.

Next: substantive single-surface breaking/froth and refresh/performance work,
remaining South Fork terrain/context/art, then Colorado, Pacuare, Futaleufu;
Chilko/Zambezi and all-scene reviews, crew realism/fit/animation, normalization,
outstanding regressions and release gates remain open. Nonlinear runtime stays
OFF until qualified. This canopy delivery does not shrink that goal.
