# Guided candidate traversal and single-carrier breaking experiment

The reconstruction queue is **not complete**. All work here is on the isolated
`SouthForkSurveyPlayable` candidate. Production maps, measured terrain, collision
geometry and cooked hydraulic arrays were not changed in this pass.

**Later correction:** the historical single-carrier assertion below did not
exclude `RapidFoamMesh`. That sheet was still drawing above the carrier. The
next pass removes it and strengthens the assertion; see
[single-foam-carrier findings](single-foam-carrier-review.md). Do not describe
these older passes as proof that only one foam response was rendering.

## Normal-paddle traversal

`RaftSim.Survey.SouthForkGuidedTraversal` now follows a diagnostic route using
existing crew forward/pivot commands and guide paddle strokes. It does not
teleport the raft, inject velocity, directly step physics or weaken contact.
The original unpowered diagnostic remains separate.

The route planner checks a downstream-aligned 4.7 x 2.4 m envelope (actual raft
plus 20 cm on each side), including bilinear grid extrema. It forbids dry
diagonal shortcuts. The flow-aware version weights attainable travel time
using the existing 2.2 m/s over-water paddle governor. Yawed clearance is not
guaranteed by this planner; actual gameplay checks sample six tube probes.
The resulting 174-point route has a minimum planning-envelope depth of
0.727 m. These depths are **inferred**, not measured bathymetry. This is not
a real-river navigation line or advice.

Eight planner tests plus three parameterized subcases pass. They cover
footprint clearance, obstacle/disconnected-channel handling, current direction,
invalid velocity fields and nonmutation of input arrays.
Two additional ledger tests prevent early outlet-only successes or invalid
metrics from being promoted to bounded traversal passes.

All iterations are retained in [the machine-readable ledger](guided-review.json):

| Controller/run | Outlet | Maximum route error | Verdict |
| --- | --- | --- | --- |
| Initial guide-only pursuit | No | 9.35 m | Failed |
| Flow compensation, early test | Yes | 39.28 m | Early engine success rejected by stricter criterion |
| Flow-aware route and crew pivots | Yes | 5.76 m | Failed |
| Nearest-track feedback | No; grounded upstream | 4.04 m | Failed |
| Two-second pursuit, baseline | Yes, 81.13 s | 4.97 m | One bounded pass |
| Shared breaking, first run | Yes, 81.74 s | 5.86 m | Failed |
| Shared breaking, forced fresh map | Yes, 80.11 s | 4.62 m | One bounded pass |

The baseline pass has 730 wet samples, no missed ground queries or grounded
samples, and 44.89 cm minimum sampled tube-to-ground clearance. Its margin to
the 5 m tracking limit is small. It is **not** repeated robustness acceptance,
continuous swept-hull clearance, full-route gameplay acceptance or a verified
rapid reconstruction.

Running contact/replay/traversal together revealed that `AutomationOpenMap`
defaults to reusing the same PIE map. That let the raft continue drifting during
earlier tests, changing traversal start station from about -55.6 to -50.7 m.
Both traversal tests now force a fresh map load. The pre-correction combined
run remains in `engine-shared-breaking-final`; the corrected run is recorded
separately in `engine-shared-breaking-fresh-map` and the ledger.

## Breaking-water experiment: opt-in, not accepted

The candidate's surface-lit carrier was incorrectly using the old overlay's
15 m interior margin for breaking-site ownership. The initial log accepted
only two sites and rejected 57 edge candidates, including an intensity-1
candidate at 4.5 m clearance. Those counts alone do not prove every rejected
site is physically valid.

`-RaftSimSurveyBreakingReview` now selects the existing shared crest/support
helper and local site envelopes **only** on this exact review map and candidate
package. It uses the single-carrier 3 m minimum clearance and 0.55 coverage
threshold, preserves wet-vertex and shoreline displacement gates, and disables
separate lip/roller surfaces. Generic periodic standing waves remain off.
No production material or binary map was saved. Omit the flag for the unchanged
baseline. This is bounded hydraulic-derived presentation, not a resolved
overturning fluid simulation.

The instrumented combined run found up to ten persistent breaking sites and
confirmed one visible surface-lit carrier, no visible volume core/lip/roller,
and the shared relief scale throughout. Candidate replay and captured-ground
contact pass. Its traversal still failed the 5 m tracking criterion. The
fresh-map rerun is authoritative for the corrected test harness.

The corrected combined run passes all **3/3** engine checks. Its guided report
`SouthForkGuidedTraversal_20260907_075032.json` starts at -55.184 m and ends at
110.020 m in 80.106 seconds, with 4.615 m maximum route error, 724 wet samples,
zero missed ground queries/grounded samples and 37.553 cm minimum sampled
tube-to-ground clearance. It retains one carrier and the shared scale throughout,
with up to ten persistent sites. This is a bounded pass, not repeated robustness
or full-scene acceptance; the earlier failed runs remain visible in the ledger.

### Actual fixed-camera comparison

Both bursts focus on station 9 m, lateral -7 m, from the same side-camera
position, at 6/9/12 seconds. The camera's logged Z differs by only 0.02 cm;
the raw solver stage is the same to the logged precision. No raft relocation
is used for these images.

Baseline:

![Baseline candidate drop](C:/Users/salsi/repos/SmokeEmIfYouGotEm/unreal/Saved/Screenshots/SurveyFixedBreakingBaseline20260907_000.png)

Shared single-carrier experiment:

![Shared candidate drop](C:/Users/salsi/repos/SmokeEmIfYouGotEm/unreal/Saved/Screenshots/SurveyFixedBreakingShared20260907_000.png)

The comparison removes the isolated upright foam sheet and changes the main
crest geometry. It **does not pass visual acceptance**: the raised ridge is
angular, the foam remains bright and streaked, and the captured terrain is
still plain diagnostic geometry. Frames six seconds apart show changing foam
and spray, not proof that the intervening animation is artifact-free.

Clean 1280 x 720 offscreen performance (20 s, 5 s warmup, no concurrent build or
capture) is **21.423 ms mean / 28.024 ms p95**, 934 frames, versus the earlier
baseline 19.024 / 25.501 ms. Both fail budget. These are single engineering runs,
not statistical or packaged release qualification. The experiment is not
enabled by default because visual and performance acceptance remain unmet,
and guided tracking is not yet repeatedly robust. See
[performance report](survey_performance_shared_breaking.json).

## Next work

Improve the narrowly scoped breaking renderer's crest silhouette, foam shading
and CPU cost, and make the diagnostic pilot robust to the coupled surface
without weakening its criteria. Do not repeat the already-completed initial
cook/import or relabel failed runs. Full-reach migration, rapid identity/layout
verification, resolution convergence and the Colorado/Pacuare/Futaleufu queue
remain outstanding. No commit or push was made in this pass.
