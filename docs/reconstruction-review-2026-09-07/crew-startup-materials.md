# Crew material readiness at normal South Fork startup

September 18, 2026. Default editor-play initialization improvement, not river,
crew realism, photographic, collision, 30 FPS or release acceptance.

## Delivered

`ARaftSimCrewAvatarActor::ConfigureAppearance` now synchronously prepares any
incomplete shaders of the visible selected body and gear after production visual
activation. It runs only in an editor build, on the game thread in a game world;
cooked games retain their cooked shaders. No Tick work, hidden actors, screenshot
delay, material/pose/geometry edits, or frame-rate/quality relaxation is added.
The editor and standalone Development targets both rebuilt successfully (16.05
and 87.10 seconds). This is not a packaged-content release.

Ordinary editor play needs no enable flag. `-RaftSimDeferredCrewMaterials` restores
the previous asynchronous behavior for diagnosis; `-RaftSimCrewMaterialAudit`
logs completeness without changing the default. The initial candidate capture
used the now-removed `-RaftSimPrepareCrewMaterials` opt-in. Only that older binary
understood it; the final default capture has no preparation enable flag.

## Actual engine checks

All three runs launch the normal South Fork full-descent scenario at its start,
not Troublemaker as a separate scenario or an isolated crew fixture. Each has
24 engine PNGs. [Receipts](crew-startup-materials/receipts.json) retain log hashes,
arguments, sampled image hashes, changed-resource observations and cook receipts.

| Run | Incomplete before / observations | Incomplete after | Preparation seconds |
| --- | ---: | ---: | ---: |
| Original control | 128 / 128 | 128 | 0.000136 (audit only) |
| Prepared candidate | 22 / 128 | 0 | 4.184962 |
| Rebuilt default | 22 / 128 | 0 | 1.007468 |

All observations occur at engine frame zero. Repeated appearance configuration
means these are observations, not 128 distinct resources. There are no logged
preparation failures. This establishes readiness before rendering, not universal
elimination of all color/shading transitions: the control already rendered
colored gear this time, so the earlier grey-to-colored pop was intermittent.
No consistent visual before/after improvement is claimed from these captures.

The final normal-start recording has 236 actual source frames over 15.582 seconds.
All 467 encoded frames decode with increasing timestamps; 30 decoded frames after
the first second are exact duplicates. This is not evidence of 30 game FPS.
Inspected engine images 000/012 and the unmodified decoded 13-second frame show
colored helmets/PFDs from the first image and continued movement. Patchy shading,
clothing fit and soft water remain visible. Full continuous-motion/crew-physics
acceptance is still open. The movie is local under
`unreal/Saved/VideoCaptures/RaftSim_20260918-161145.mp4`; decode outputs are under
`tmp/crew-material-motion-v2-20260918`.

The unchanged native `RaftSim.M5.CrewAvatarPoseProduction` asset/pose regression
passes: one success, zero warnings/failures/skipped/in-progress tests. It does
not itself test shader readiness or the rescue loop. No native assertion was
weakened; the broader runtime helmet-fit assertion noted during inspection
still needs reconciliation with the previously reviewed role-specific fits.

## Cost and limitations

A separate 900-frame ordinary FullReach rapid capture at station 8,330, without
screenshots or material audit, measures every CSV row 60 through 840 at the
unchanged 30 FPS target: **23.697381 FPS, mean 42.198757 ms, p95 50.9549 ms**.
The gate fails. This single run is slower than the preceding default runs; it
is not a paired causal comparison and does not establish that startup-only work
causes a steady-state slowdown. No whole-frame performance improvement is claimed.
The wrapper confirms UE's nonlegacy frame timing; water-scope grouping uses the
one-row offset. Do not sum nested timings. [Delivery evidence](crew-startup-materials/delivery.json)
retains metrics, binary/native-report hashes and fully decoded motion statistics.

The sole existing cook13584 was identity-checked, suspended and resumed with
status zero for each capture; games exited zero without timeout. The final
startup CPU bracket is unchanged; the cost run's bracket includes 0.109375 seconds
before suspension completes. No duplicate cook or terrain experiment was started.
Last observed baseline progress was local54540/time11727 seconds, not settlement
acceptance; next unaudited snapshot remains11400/local48000, requiring BOTH audits.

Installed terrain/map/4950 fields and all captured evidence are unchanged.
Nonlinear solver stays OFF. The pending cap source-interpretation decision is
not answered or bypassed. South Fork remains first and unfinished; Colorado,
Pacuare and Futaleufu have not been promoted or accepted. Generated recordings,
binaries and raw logs remain ignored, not committed.
