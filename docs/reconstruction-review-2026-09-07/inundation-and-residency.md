# Transient inundation and native terrain residency

The later bank flooding is present in the hydraulic state, not merely an optical
artifact. The original terrain actor retains its revised mesh through a real-tick
10 km streaming-view round trip. However, the longer game run exposes a separate
detail-domain failure before a hydraulic crop handoff. **South Fork remains
unaccepted and is not promoted to normal gameplay by these results.**

## Hydraulic storage explains the excessive local discharge

The same fresh 841-core solve remains live, session46094 / PID22940; it was not
restarted. The zero-step native inspector reconstructs its actual MUSCL/HLL
neighbour boundaries, checks all checkpoint h/u/v values before and after
inspection, and checks the recorded whole-domain volume. All selected internal
faces cancel exactly. No solver step, clock change or input write occurs.

The Python wrapper hashes all declared package inputs, copied manifest, selected
source geometry, executable and h/u/v snapshots. It verifies original source
bed, grid origin/spacing/shape/datum, frame-zero depth and actual array references.
Nineteen compiled-CLI integration tests plus the helper and adjacent regressions
run, **54 passed**. This is numerical/provenance evidence, not hydraulic calibration.

For cores0628–0631, the 40 m circle is centered at field coordinates
(-5437.499999998952,3606.5)m. Circle metrics cover selected cells inside it;
only the full four-tile region has the numerical face-flux measurement.

| Source age (s) | Four-tile volume (m3) | Instantaneous net inflow (m3/s) | Circle volume outside historical water mask (m3) |
| ---: | ---: | ---: | ---: |
| 0 | 10927.15 | 17.82 | 0.00 |
| 50 | 10983.13 | 41.37 | 34.05 |
| 100 | 12533.15 | 34.62 | 204.18 |
| 150 | 13309.13 | 3.68 | 354.99 |
| 200 | 13251.21 | -5.05 | 349.93 |
| 250 | 12878.19 | -9.28 | 308.52 |
| 300 | 12377.31 | -9.90 | 256.06 |
| 350 | 11906.31 | -8.77 | 210.64 |
| 400 | 11488.31 | -8.08 | 173.04 |
| 450 | 11106.46 | -7.25 | 142.40 |

The observed samples peak around150–200s and subsequently drain. The historical
source mask is not a calibrated current-flow shoreline; its dry cells do not all
represent measured bank surfaces. This does not prove that eventual water levels
or inferred submerged geometry are correct.

A second control volume includes all203 tiles with origin_x >= -5517m. It includes
the two prescribed inlet faces on core0825 and neither downstream outlet. Its only
nonzero west-cut faces at450s are core0628 and core0629, near the rapid.

| Source age (s) | East-side stored water (m3) | Net inflow (m3/s) | West-cut outflow (m3/s) |
| ---: | ---: | ---: | ---: |
| 0 | 696644.98 | 19.00 | 26.31 |
| 150 | 685572.09 | -111.74 | 157.05 |
| 450 | 656125.42 | -76.12 | 121.42 |

The east-side loss is40,519.555906m3 by450s. With the unchanged prescribed
45.3069545472m3/s inlet, storage balance implies a mean cut outflow135.350412m3/s.
That mean is derived from endpoint storage, not directly time-integrated face
telemetry. The instantaneous450s cut outflow is measured by the native flux
routine. Together these demonstrate substantial release of initialized upstream
storage. Do not tune banks or roughness to suppress this transient flood, or call
the450s snapshot a settled45.3m3/s reconstruction.

Rapid report `tmp/control-ablation-inundation-history-v3-20260916.json`:
`d58c0ce0b23c76ff5d37b84291602deff5d4be83adfcccf3c0897af1d7963468`.
V3 reruns the final spacing/datum checks and is byte-identical to V2.
East-side report `tmp/control-ablation-east-control-history-v1-20260916.json`:
`c8abda397217216779e2b2b81a3edcc268a14a184e998d6df97524acb1c85301`.

## Whole-domain gates through500s

400,450 and500s all pass the5,382,400-cell finite/depth/speed/conservation checks
AND all86,720 artificial bank-face checks. Every artificial bank face is exactly
dry. At500s maximum depth4.854464m, speed12.046148m/s and maximum step mass
residual1.376286e-8m3. Outlet48.176008 versus inlet45.306955m3/s still does not
establish settling, particularly given the much larger internal redistribution.

| Local report prefix in tmp/ | State SHA256 | Bank SHA256 |
| --- | --- | --- |
| control-ablation-400s-*-v1-20260916.json | d023ed47ede94b97ad0417d128df4aec815527c3f38f184ae7f268a9020ec8c2 | e3fe3a53734ba631c73b9c752c87c805a135542332ba613c0092ceafb09336d9 |
| control-ablation-450s-*-v1-20260916.json | 81649d30d5c6591a94b5d48c9d501a06b020bfaae06cce004f86d516eaa326c0 | ceb259a2796dd0d3465f06c0577c387e54fa0e93812dfb852a171574902c11ce |
| control-ablation-500s-*-v1-20260916.json | 871d55b1cab9e15a87b098f16113d02f8ad5b38109b99a9df1f45125a9574180 | 1fe481ec0cfb1287fc25f1008e1b5e2b8d94fd9b7e461c54dc4a198cd4cf2bc9 |

Next completed snapshot11000/550s requires both audits. At actual600s terminal,
assess settling before deciding on a source-exact continuation; do not restart
the still-running solve or transplant this state onto another bed.

## Native streaming-view round trip: narrowly passes

Session29669 exits0. `RaftSim.M3.TerrainResidencyRoundTrip` runs in the actual
FullReach game with the350s paired descriptor and isolated module, at requested
1280x720/D3D12. It moves only a transient camera, not the raft or hydraulic state.
The normal player's actual streaming-source location is checked against the
camera, while the verified-terrain provider remains registered.

At world611.626339,616.715710 and621.780751s, initial/10km-away/returned checks
find the same original actor, revised mesh, transform, material and registered
collision component. Streaming completes in each phase; there is exactly one
revised terrain actor and no restored original-mesh actor. This does not repeat
the independent64,935 collision probes or verify a physical raft round trip.

The engine automation controller first waits600s for10FPS and gives up on that
startup wait before dispatching the test. The log is retained; no timeout or
performance threshold was changed. This heavily contended run is NOT30FPS
qualification. It also logs engine toolset Python startup errors concerning
AgentSkill/PythonTestRunner, so the entire game log is not claimed clean.

- Result `tmp/native-terrain-roundtrip-v1-20260916/result.json`:
  `87c29c17f629e998863b133baac69453081f87a21177e5bcbcb3c54d09e800ab`.
- Game log `tmp/native-terrain-roundtrip-v1-20260916/play.log`:
  `85727567969b5b7f78362df8d93f619851f22ce310b1fbb7f2dd4d6ce061fd29`.
- Isolated DLL SHA256:
  `9845926be2febab1732858d5b1f4220b1ca15fed2b904a1988ff2aa92135dc11`.
- Test source SHA256:
  `202616b9d322c8bc561b83541fd2fd6f9c83d3d9d89d291bc77e23064ce07e97`.

The first isolated compile failed on Unreal API types/access and was corrected;
the second compile/link and actual test pass. Existing project DLLs and shaders
were not overwritten. No saved map, material, mesh, scenario or profile changed.

## Newly exposed live-water defect: fix next

At19:01:46.052 UTC/frame175, the detailed-water component reports
`Stateful detail window left authoritative water domain; refusing fallback water`.
The next frame176 performs crop handoff5 at(-5602.193,3633.966)m. The previous
crop center was(-5522.170,3621.345)m. After sampling failure, the component sets
StatefulDetailEnable=0 and bReady=false; the subsequent handoff does not restore
it. Thus terrain residency passes while continued detailed water fails.

The current streaming contract considers raft coverage (10m minimum margin)
and80m center advance in a224m window, on a0.2s controller interval. The detailed
solver needs its entire67x67 source lattice, exterior faces, quantized moving
origin and possibly closing-window observation. A raft-center check does not
guarantee those requests remain inside the live field before the next tick.
There is also a strict floating-point boundary: the source X lattice is offset
from integer metres by about1.05e-9m, while the detail lattice is integer/half-metre
aligned; the native sampler rejects any negative fractional index. The log does
not identify the failed sample, so do not claim that epsilon alone caused it.

NEXT: reproduce the exact failing footprint and native crop, then make source
selection/recentering and tick ordering cover the full current/next detail
sampling footprint before detail updates. Preserve closing observations, native
state/clock transfer and source identity. Do not clamp missing samples, invent
fallback water, merely re-enable lost detail, shrink the domain or weaken gates.
Require a longer actual gameplay replay with detail still active across all
handoffs, plus normal project relink once the current cook is terminal.

The package remains the same session83678/cook5852, now with shader worker5104
(the old35032 finished). The same hydraulic PID22940 is live. Keep their inputs
intact. The protection audit checks464 identities:462 unchanged and two previously
verified CPU-retention-only revisions; all22 existing binary identities match.
`tmp/roundtrip-inundation-protected-v1-20260916.json` SHA256:
`7c01eea551373cefa994d70e3f9176d4b725e88860280aac67d7f619b28b2fba`.

Broad froth/bank streaks, settled hydraulics, normal-play delivery and the unchanged
30FPS/p95<=33.333ms gate remain open. Last uncontended17.819710FPS/p9581.6343ms
still fails. Colorado then Pacuare then Futaleufu, other-scene water, crew,
normalization/regressions and release remain open. Troublemaker remains only a
rapid in the South Fork scenario, never a separate menu entry.

## Detail source-coverage fix: native regression verified

The detail consumer now requests a complete native crop synchronously before
initialization and each source update. Selection includes the exact current/next
67-node source footprints (69 for pressure diagnostics), including overlapping
closing observations. Existing crop dimensions, resolution, raft margin, sampling
strictness and physics are unchanged; unavailable coverage still fails closed.

On 2026-09-16, the isolated native module compiled and all four
`RaftSim.M3.Detail` tests passed (process exit 0). The real pre-failure crop
reproduced 67 missing samples among 8,978 queries. The production detail/controller
coverage call restored all queries in one native handoff, preserved all 8,911
previously valid samples exactly, and preserved simulation and committed clocks.
Repeated coverage requests did not reload the crop. Full-route selection checked
52,689 detail/closing footprints at center and +/-12m offsets, with zero missing.

Local report: `tmp/detail-footprint-v1-20260916/native-tests-v3/index.json`, SHA256
`7eb0e17816088074467b2ab928566eac10096077d5db0ff654811672869f2d5d`.
Temporary harnesses, reports and binaries remain ignored, not release content.
This is isolated native regression evidence, not a normal project relink,
extended gameplay replay, visual acceptance or a 30FPS qualification. Those
checks remain required; existing project DLLs and shaders were not replaced.
