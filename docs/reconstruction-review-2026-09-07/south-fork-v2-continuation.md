# South Fork v2: bounded exact-state continuation

September27,2026. Completed through450s; not a playable delivery or acceptance.

The preceding regional audit showed substantial opposing storage changes in
the existing v2 fields. The next experiment holds geometry and forcing fixed
and advances time, rather than changing the bed based on an unsigned transport
proxy. This tests whether the identified regional changes decay with continued
evolution. A better global inflow/outflow total alone will not qualify it.

## Completed process: do not restart

- Native solver PID28988; terminal session49009.
- Durable process identity/start time/status receipt:
  `tmp/discharge-bed-v2-300to450-process-20260927.json`.
- Input: `tmp/discharge-bed-v2-restart300-input-20260927/manifest.json`.
- Output: `tmp/discharge-bed-v2-300to450-20260927`.
- Wrapper: `tmp/continue-south-fork-v2-300to450-20260927.ps1`.
- Source: existing v2 `frame_006000`, cook clock300seconds.
- Bounded3000 steps at unchanged0.05seconds, target cook clock450seconds.
- Save interval1500steps: initial,375s and450s; eight qualified offline lanes.
- No engine/build/solver was active at guarded launch. Other processes are
  never stopped. A90minute wall limit and initialization-audit failure stop
  only this owned process and preserve its evidence.

PID28988 and terminal49009 completed successfully with exit0. The completion
marker and durable receipt both confirm completion. Final snapshot step3000
has clock450.000000000068seconds; native elapsed wall time1485.03seconds.
The follow-up state/bank/storage audit session85331 also completed with exit0.
Do not restart this finished interval or repeat its unchanged snapshot checks.

## Verified restart boundary

The native restart audit passes:5,382,400 original h/u/v cells are bit-exact,
zero added cells or initial water, retained grid/bed/roughness/boundaries and
all retained physical settings/features/probes unchanged. Native clock matches
the source300.00000000003394seconds; volume difference-4.66e-10m3. All four
initial numerical exterior fluxes exactly match the previous final snapshot.

| Evidence | SHA-256 |
| --- | --- |
| Restart manifest | `039d22e3898f184ccadf95a735effd62f15b788253292512b360efd4bcef1b0c` |
| Previous manifest | `ca87e200775cdf7348593a2267e056eb4e5041991e0ff0919d42275122f1f963` |
| `tmp/discharge-bed-v2-restart300-native-20260927.json` | `b6c8675cc1c15359103ad71c4d03cbd0be8a10db430d0f1b0b59fcf07b070bbd` |
| Qualified standalone solver | `458a1fcd3f2f12391012032398d29a4b2eadb792df2e9ee09b88dff263abc8e4` |

The executable is the previously qualified offline worker-limited solver from
`tmp/solver-worker-limit-v1-20260917`; this is not an experimental gameplay
solver. Its finite-state,10m-depth,20m/s-speed and0.001m3/s per-step conservation
rejection gates remain intact. Those generous numerical safety bounds are not
physical realism or settling criteria. No current game solver was toggled.

## Verification and promotion boundary

After the completion marker and successful process exit, independently verify
snapshot state, artificial-bank dryness and integrated storage/boundary closure.
Use the same1km regional partition at local steps0,1500,3000, comparing its
375-450s interval against the previous225-300s interval. Do not rerun the old
unchanged snapshots or confuse regional storage rates with section discharge.
Check the28-29km gain and13-14km loss, and all other bands rather than selecting
only improving locations. Preserve failure outputs if any gate fails.

Only then decide whether improved fields merit a separately versioned runtime
export, normal-scene integration, rebuilt game and actual motion/shoreline/
collision/performance checks. Geometry, measured source data, cooked fields
currently shipped in the game, and the packaged v4 game are untouched.
The underwater bed remains inferred. South Fork and the full queue are not
accepted; the20FPS performance and visible water-realism requirements remain.

The checks specified above are now complete; their results follow. The
promotion boundary remains in force, not a request to repeat the checks.

## Intermediate375s checkpoint

The same live process reached local step1500/375seconds. Independent snapshot
and exterior-bank checks pass:5,382,400 finite/nonnegative cells, maximum depth
3.0188664m, speed8.2078873m/s and maximum step residual1.21e-8m3. All86,720
artificial-bank face cells remain exactly dry. Reports:
`tmp/discharge-bed-v2-375-state-20260927.json` and
`tmp/discharge-bed-v2-375-banks-20260927.json`.

The first75s of continuation adds421.8505m3 (mean5.6247m3/s). Final instantaneous
inflow is45.307 versus outflow40.310m3/s. Neither is a regional settling pass;
the final375-450s interval remains unavailable until the same cook completes.
No additional cook, field export, scene import or package build was started.

Separately, calibration-tool correction2aa30574f passes18 regressions. It does
not modify this cook's immutable inputs or the current game. The retained
300s analysis was used only to verify that corrected signed transport differs
from the old unsigned magnitude proxy; no fitted bed was installed.

## Completed450s validation and comparison

All5,382,400 cells pass independent finite/nonnegative state checks. Maximum
depth3.02143375m, maximum speed4.62129081m/s; maximum step conservation residual
1.2094e-8m3. All86,720 artificial-bank face cells remain exactly dry. The
continuation adds774.94414264m3 over150s. The final instantaneous boundary
inflow45.306955m3/s and outflow41.380050m3/s are not interval storage rates.

The same route hash and1km partition were checked before comparison. All34
bands are included, including endpoint context and wetting/drying cells.

| Interval (cook s) | Net storage (m3/s) | Sum of positive regional rates | Sum of negative regional rates |
| --- | ---: | ---: | ---: |
| 225-300, preceding cook | +6.163748 | +86.148637 | -79.984889 |
| 300-375, continuation | +5.624673 | +77.445578 | -71.820905 |
| 375-450, continuation | +4.707915 | +71.816178 | -67.108263 |

Integrated exterior-volume/storage closure is within1.81e-11m3 for the new
intervals. These are regional storage rates, not cross-section discharge.
Opposing changes decreased in aggregate but did NOT decrease everywhere:
absolute storage rates increased in bands0,2,3,5,8,9,12,14,15,16,19,21,22,27,
30,31,33 (17 of34). Selecting only the originally largest two would conceal
new or worsening transients.

| Attribution band (km) | Earlier225-300s rate | Later375-450s rate (m3/s) |
| --- | ---: | ---: |
| 28-29 | +18.396746 | +7.808714 |
| 13-14 | -17.134445 | -10.190942 |
| 8-9 | -11.849190 | -12.434415 |
| 12-13 | +9.079945 | +10.037006 |
| 14-15 | +0.392567 | -7.033751 |
| 29-30 | -12.234932 | +1.655991 |
| 30-31 | -5.097878 | -8.682400 |

The28-29km common-wet median stage change falls from+0.06001m to+0.01012m
per75s;13-14km changes from-0.02431m to-0.01818m. However8-9km drainage
increases (median-0.01244m to-0.01678m). Whole-band volume and common-wet
median stage can have different signs; neither statistic replaces the other.

No settled-hydraulics claim, bed refit, runtime export, scene change or package
replacement has been made. The exact-state continuation demonstrates partial
decay, not a uniformly improved initial state. The signed numerical exchange
check below is complete; do not rerun it on these unchanged snapshots.

| New report in `tmp/` | SHA-256 |
| --- | --- |
| `discharge-bed-v2-450-state-20260927.json` | `0d5c7d4f0b17fec520058cc0d52828a4b869ac4a78d998fb7b35159c66017bda` |
| `discharge-bed-v2-450-banks-20260927.json` | `32883f70b9cdcb28013d2dae1a952eb3091d353791ff08da6ea37ca931789054` |
| `discharge-bed-v2-450-storage-20260927.json` | `fab97ede6d7a36d433f8f36089d783b0ea6532e868334c0469c058bbab944b4c` |

## Signed native tile-face exchange

The existing zero-step inspector examined all841 tiles at375s and450s using
coupled ghost exchange, not cell-centred transport. Audit session89319 exits0.
All h/u/v hashes remain unchanged, native state-unchanged checks pass, all four
saved physical exterior flux probes match, and1,138 shared face pairs cancel
to at most4.44e-16m3/s. Independently summed interval tile storage agrees with
integrated exterior volume within3.97e-10m3. No new solver steps were run.

Largest draining tile core_0086 averages-1.509335m3/s, with instantaneous net
inward fluxes-1.518182 and-1.465765m3/s at the endpoints. Largest filling tile
core_0108 averages+2.767758m3/s, with endpoint net inward fluxes+2.809513 and
+2.561761m3/s. Endpoint rates are not interval averages or river section flows.
These observations support ongoing conservative redistribution, not a broken
tile-exchange seam. They do not establish the physical correctness of inferred
bathymetry or identify the cause of every changing region.

- Report: `tmp/discharge-bed-v2-450-face-flux-20260927.json`.
- Report SHA-256: `7cb4fe3b120af146cf7c72d0ac8335f957f90f5864fff3b673dbaa0f4ceddaa9`.
- Inspector SHA-256: `8b38ff9fa1984f18b7f2b1fa8a3c627f010c6515152807f8170e20f6acf05ff3`.

Next useful playable step is a separately versioned450s field candidate with
unchanged bed, captured masks, coverage and normal launch bindings, followed
by actual rapid motion/shoreline/collision and cost comparison against v4.
This is eligibility for an incremental trial, not permission to label the
fields settled or the river accepted. Keep the current playable baseline until
that trial demonstrates benefit; do not substitute another identical diagnostic
or infer improved breaking-wave appearance from storage decay alone.

## Versioned runtime candidate prepared (not yet integrated)

Export session83207 exited0. Candidate:
`tmp/discharge-bed-v2-runtime450-20260927`.
Its841-tile atlas and799 packets verify42,185,039 exact bed-intersection cells.
An independent comparison against `tmp/discharge-bed-runtime-v2-20260926`
then verifies all1,598 actual packet bed/mask file hashes, atlas bed, tile grids,
solver settings, physical boundary definitions and all window coverage bounds
unchanged (session7190, exit0). Only the flow state and its provenance change.
The export's798 changed-bed packets count is relative to the older source
packet input, NOT a change from the currently playable v4 bed.

- Export audit SHA-256: `27b2cfae13314a71c3a8ab84f84f22498b1b5affeb6fb75e683b66c39f02ecd3`.
- Atlas manifest SHA-256: `9bc7abc90e45aad90061d2f6fdbc0a12ca6ccf8067be3ec546b330dd2176b2d5`.
- Streaming manifest SHA-256: `ea118f9c08d59759313e5ac32e3a373e79f426d7a26f71e239884cd86753d2e3`.

No engine, saved scene, runtime bundle or packaged game was changed. Next
work is the normal-scene candidate binding, reproducible bundle/rebuild and
actual motion/collision/shoreline/performance comparison; do not mistake this
completed export for visible delivery or redo it in another directory.
