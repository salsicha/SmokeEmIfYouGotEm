# Shallow-bank reconstruction correction

South Fork remains the active reconstruction. This pass reproduces and fixes
specific offline numerical failures; it does not certify all rapids, bathymetry,
photorealism or the complete task queue. See [remaining work](../plans/remaining-work.md).

## Reproduction and controlled experiments

A full-domain restart from the saved 80-second half-metre frame reproduces the
original 23.750433 m/s bank spike at 100 seconds exactly. One-second snapshots
also expose a 20.3686 m/s spike at 90 seconds missed by the old 20-second cadence.
No source terrain, forcing, CFL, roughness or safety limit was changed.

The solver switched from hydrostatic reconstruction to a non-augmented f-wave
at bed jumps above 10 cm. Separately, independently averaged face beds could
give shallow cells reconstructed face depths inconsistent with their stored
depth. A narrow interface guard and smaller adaptive timesteps did not cure
the failures; their evidence is retained, and neither experiment is active.

| Numerical candidate | Initialization saved peak (m/s) | 80–101 s saved peak (m/s) | Decision |
| --- | ---: | ---: | --- |
| Original solver | Not replayed here | 23.7504 | Rejected |
| Only guard emerging steps | Not replayed | 39.2539 | Rejected |
| Hydrostatic interfaces, old face beds | 23.1024 | 13.7534 | Rejected overall |
| Above plus adaptive/two-direction CFL | 28.0321 | 25.0123 | Rejected |
| Hydrostatic interfaces, cell bed, limited stage slopes | 7.5883 | 11.0514 | Passes both bounded histories |

Initialization covers 0–30 seconds except the adaptive test, which covers
0–10 seconds and already fails at 3 seconds. These are independent restart
histories, not a continuous long-duration fine-grid qualification. Saved
one-second samples do not bound unsaved extrema. Wall times include output,
and some independent runs overlap: they are not FPS/performance comparisons.

[Every experiment, source/binary identity and failure](bank-spike-experiments.json).

## Implemented numerical change

The **uncalibrated MUSCL path** now uses hydrostatic interface reconstruction
consistently, keeps each side's stored cell bed during face construction, and
limits free-surface half-slopes to the local depth. Before hydrostatic clipping,
opposite face depths are nonnegative and average to the cell depth. The source
bed/collision geometry is unchanged; this is a numerical reconstruction change.
Historical calibrated f-wave/bed averaging paths remain unchanged. The failed
adaptive-CFL experiment was reverted, retaining the original timestep policy.

This follows the distinction between wet/dry-capable hydrostatic reconstruction
and non-augmented f-wave treatment; it is not a claim of universal mathematical
stability of this implementation. References: [Audusse et al.](https://publications.imp.fu-berlin.de/478/)
and [Clawpack's solver guidance](https://www.clawpack.org/v5.12.x/riemann/Shallow_water_Riemann_solvers.html).
No reference code was copied. Numerical diffusion and spatial resolution still
need review before accepting crest geometry.

New native checks cover emerging and submerged interfaces, both axes, reversed
steps, shared mass flux and pressure corrections. Three registered native
fixtures pass, as does the test executable on the actual one-metre survey
scenario, including still-water balance, conservation and contact checks.

Both passing fine-grid endpoints also pass the exact numerical face-flux audit:
inlet 45.3069545472 m3/s, zero side leakage, and volume derivatives matching net
boundary flux within 0.001 m3/s. This is conservation, **not steady flow**.
The initialization endpoint is still shedding about 25.19 m3/s of storage.

## Fresh one-metre cook

`1m-mixed-inlet-depth-limited-hydrostatic-20260907` is a fresh 600-second run
with the same triangle-sampled source, physical bounds and forcing, using the
corrected isolated executable (SHA-256
`1f010cbe7edce8eb579c2d9a040820a24d6ee6ac1615073e3afbf899cac9ba50`).
All 13 saved frames pass sanity; maximum saved speed is 5.9018 m/s.

The unchanged mean-flow screen now passes all three checks: maximum tail
section-discharge error 1.773%, storage rates +0.0923/-0.1763/+0.1544 m3/s,
and regional median-stage variation below 1 cm. Actual boundary flux also
passes: net +0.1012913 m3/s versus +0.1012959 m3/s measured volume derivative,
with zero side leakage. Local temporal variation is not zero: crux common-wet
p95 range is 1.073 cm and maximum is 10.098 cm in the saved tail.

The new package is explicitly unaccepted and includes its offline binary hash.
The starting point is station/lateral (-60,-9) m. The diagnostic route has 173
points and minimum downstream-aligned footprint depth 0.632 m; it is not a
real-river navigation route. No new fine-grid spatial convergence is claimed.

## Engine integration and remaining acceptance

The editor rebuild succeeds (158 actions, 890.63 seconds). The field-only update
is now staged in `SouthForkSurveyPlayable`; all 16 collision probes pass and
the mesh/material hashes remain unchanged. The new map SHA is
`2c53df655cd7fa83a232f40f951c4babcdc34adbd3fb7aafda8db270b64969bd`.
Its exact previous map is at
`tmp/project-cleanup/SouthForkSurveyPlayable-before-depth-limited-fields.umap`.
[Staging evidence](depth-limited-engine-integration.json). The previous
engine archive is retained at `tmp/south-fork-bank-spike-20260907/raftsim_water.engine-before.lib`.
The rebuilt archive SHA-256 is
`83f35ddf4e6ab28fc07999804e63d3ccfcd5d0d78d8f0775c96e909913910f03`;
the new staging wrapper verifies it, the offline binary identity, source assets,
map identity and the shared staging guards before saving. Do not run the old
one-off staging entry point over newer map changes.

Fifty Python checks plus 27 subtests pass across geometry, export, layout and
release fixtures. Three Windows/POSIX packaging-fixture failures are fixed
without changing the package validator; a missing-execute-bit rejection test
was added. Seven editor source-layout/provenance checks still fail and remain
recorded in `editor-layout-current.xml`; their historical hashes were not reset.

### Actual-engine results

The new candidate-specific two-second replay and captured-ground contact pass.
The first guided test fails before traversal: PowerShell splits the unquoted
`-RaftSimSurveyGuidedRoute=.../guided-route-depth-limited.json` into the stem
and a separate `.json` argument. A Python argv check reproduces that host-shell
behavior. The corrected quoted invocation is retained as a distinct run, not
an overwrite of the failed launch. Future native invocations must quote this
whole argument.

The corrected guided run reaches the outlet in **98.891 seconds**, with no
missing terrain queries or sampled ground penetration, but **12.329 m** maximum
route error fails the unchanged 5 m bound. Minimum sampled tube clearance is
36.456 cm. Normal paddle commands, one surface/foam carrier and lit material
checks pass, with at most seven breaking sites. The guided route/controller
needs review against the changed current; this is not a whole-rapid pass.
Raw evidence: `unreal/Saved/Automation/SouthForkGuidedTraversal_20260907_150623.json`.
The [ledger](guided-review.json) retains all 13 runs, including preflight failures.

Clean performance, with no concurrent cook/build/capture, is **14.669 ms mean /
19.437 ms p95** over 1,381 frames at 1280x720 / 87% on the RTX 3060 Laptop GPU.
Solver mean is **9.515 ms**. Previous matching-resolution review measured
18.990/24.632 ms and 11.274 ms solver mean. These individual runs suggest an
improvement but do not establish a repeatable speedup. The p95/frame and solver
budgets still fail; no packaged/player-performance qualification is claimed.
[Performance report](survey_performance_depth_limited.json).

Actual boat-height images still show overly smooth stretches. The fixed
station-9/lateral-minus-7 views at 6/9/12 seconds show localized relief and
changing spray, but the crests remain angular and foam looks stretched and
marbled. Plain diagnostic banks are not scenery acceptance. No continuous
animation or photorealism pass is claimed from three stills.

![Fixed rapid view, six seconds](C:/Users/salsi/repos/SmokeEmIfYouGotEm/unreal/Saved/Screenshots/SurveyDepthLimited20260907_000.png)

![Fixed rapid view, twelve seconds](C:/Users/salsi/repos/SmokeEmIfYouGotEm/unreal/Saved/Screenshots/SurveyDepthLimited20260907_002.png)

Final staging/route/failure-ledger suite: **25 tests plus 15 subtests pass**.
The next meaningful checks are a same-core half-metre refinement, review of
guided route feasibility/current compensation, and smoother localized visible
crest detail within the CPU budget. Do not repeat rejected solver variants or
weaken tracking/physics thresholds. Full-reach reconstruction, rapid identities,
all-scene visuals and the later-river queue remain unfinished. No final commit
or push has been made; pre-existing unrelated changes remain preserved.
