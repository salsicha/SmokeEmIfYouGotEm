# South Fork control-centred liquid review — September 9

South Fork remains **incomplete**. This is a 21 m review window, not the
whole rapid or production route. Realism, natural traversal, full-scene cost,
hydraulic convergence and rapid identity are not accepted.

## Correct the part of the candidate being simulated

The previously reviewed domain ended at station 10.5 m, while the centre of
the inferred plunge pool was at 13.7376 m. The shelf was near the outlet.
It was not a complete simulation of the hypothesized drop and pool.

`recenter_south_fork_liquid_window.py` rebases the coordinate origin by
10 m downstream and 2 m laterally. The inferred shelf and pool centres become
(-3.26244, 0.37804) and (3.73756, 0.37804) m. Both are now inside the window.
This does **not** move real terrain or claim surveyed submerged bathymetry.
The independent [rebase audit](liquid-control-centered-rebase-audit.json)
verifies identical elevations, triangle indices, authority labels, captured
rock-return indices, and hydraulic array bytes. XY restoration error is below
1.5e-14 m. The water floor stays at 350 cm in the same vertical datum.

The separate review package is
`unreal/SourceArt/RaftSim/SouthForkLiquidControlCentered20260909`.
The new collision mesh is imported under the matching `/Game/RaftSim/Environment/`
folder. [Actual import traces](liquid-control-centered-engine-import.json)
hit all 5,040 top triangles, with maximum height error 0.000898 cm.
The saved contact system and registered playable map are not replaced.
At runtime the explicit `-RaftSimLiquidControlCentered` flag installs the new
source, initial-state, boundary and contact profiles into an unsaved system.
The review terrain actor is translated by the same origin offset, without
saving the level. Default profile selection is unchanged.

The unchanged numerical state supplies 47.19667 m³/s of incoming flux; this
is **not a measured river discharge**. The new native-face audit agrees with
storage change within 6.54e-7 m³/s. Incoming particle-source weights preserve
that discharge. The initial state contains 70,923 particles. An outgoing,
unresolved dry-face residual of -1.567e-9 m³/s is explicitly recorded under
the existing 1e-7 per-face noise allowance, not represented as wet flow.
Positive inflow without wet support still fails at any magnitude.

Earlier (8,0) and (10,0) shifts failed wet boundary support and are retained
under the `liquid-plunge-*` review directories. The first (10,2) generator
attempt also failed on that outgoing dry residual; subsequent individual
profile generation succeeded after fixing its reporting/handling. There is
no fabricated successful top-level `recenter_review.json`; the independent
rebase audit is the coordinate-consistency evidence.

## Live evidence and precision repair

`liquid-control-centered-12s` uses the new data but three capture metadata
fields incorrectly named old profiles. It is retained, not rewritten.
`liquid-control-centered-provenance-12s` repeats the capture with those paths
fixed. Its foam audit correctly fails: maximum source error is 0.00133660
against the unchanged 0.001 tolerance. Coverage and pause checks pass.

At the worst source voxel, GPU rate was 0.55867815/s versus the independent
float64 rate 0.56001475/s. Rounding interpolated samples to half precision
reproduces 0.55867824/s there. RGBA16F hardware filtering before differentiation
is insufficiently precise for the fixed source stencil.

The source stencil now loads exact half texels and interpolates in float with
the exact quarter-cell weights of the aligned 2x grid. SDF derivatives load
the exact +/-2 render-cell samples. Source equations, thresholds, decay,
grid sizes, physical extent and the independent float64 auditor are unchanged.
History still uses RK2 advection, and GPU elapsed time remains authoritative.
No extra visible surface, primary particle mutation or CPU per-frame readback
was added.

The new `liquid-control-centered-float-stencil-12s` capture completes 750 GPU
updates and 30 distinct motion images. Its [foam audit](liquid-control-centered-float-stencil-12s/current_foam_audit.json)
passes with maximum source error **7.836e-7/s**, coverage error 0.0009765625,
and exact paused coverage. Independent velocity and boundary data match.
The [live pipeline audit](liquid-control-centered-float-stencil-12s/live_audit.json)
finds finite current particle input, maximum position error 1.401e-6 m and no
engine errors. Separate GPU runs are not deterministic paired trajectories;
population/coverage differences alone do not prove improved physics.

The build and 115 liquid numerical tests passed before the longer-run audit
extensions below. All 14 engine regression tests
pass in `engine-liquid-source-interpolation`; one test records an unrelated
HTTP connectivity-check timeout warning. The foam test now includes a
non-affine half-texel field checked against independent double interpolation
with a 1e-5/s source tolerance. The preceding window-selection run passed
14 tests without warnings.

## Still visibly and physically wrong

The drop is now present in the review, but water still resembles glossy cyan
material and has insufficient breaking froth. Rectangular review-domain sides
remain visible. The capture is not a photoreal river scene. Mean top-crossing
coverage is only 0.007465; it is not photographic foam coverage.

The [secondary audit](liquid-control-centered-float-stencil-12s/secondary_audit.json)
records one sampled bed penetration (0.918 cm), 12 of 179 spray particles
inside the displayed water at the final paused sample, and foam-interface
distance p95 3.905 cm, maximum 26.866 cm. Previous-completed-surface cache
timestamps and contents match, but next-step classification is not same-step
surface contact. These failures remain open; particle count is not proof of
visible spray or contact correctness.

## Runtime cost and longer flow

The [uninterrupted benchmark](liquid-control-centered-float-stencil-benchmark/benchmark_audit.json)
contains 480 frame intervals: mean 23.4416 ms, p95 25.5310 ms. Its 471 warmed
GPU samples average 6.2260 ms for reconstruction: density 5.4875 ms, distance
0.5756 ms, foam/copy/cache 0.1629 ms. The windows do not align exactly and the
GPU figure excludes Niagara's primary particle update. This remains slower
than the frame target, and is not packaged or full-scene qualification.

`liquid-control-centered-float-stencil-60s` completes 3,630 GPU updates and
30 distinct final motion images. The independent foam audit still passes
(source error 6.830e-7/s, coverage error 0.0009765625, exact pause). GPU age is
59.9990234 s. The auditors now select the requested-duration independent grid
and require corresponding update count/age, rather than hard-coding 12 seconds.
The primary population has 85,919 finite particles, no final sampled terrain
penetration, and 86 particles outside the physical domain awaiting retirement.
These counts do not establish a calibrated mass budget. Secondary contact
still fails: one 1.583 cm final bed penetration and 34/305 spray particles
inside the rendered surface.

The final liquid numerical suite passes **121 tests**, including highest-crossing
selection and duration-aware audit regressions. Scoped whitespace checks pass.
Final hashes confirm the saved contact system, registered playable map and
uproject remain unchanged. All owned build/capture processes have exited.

New source-hashed [12-second](liquid-control-centered-float-stencil-12s/longitudinal_flow.json)
and [60-second](liquid-control-centered-float-stencil-60s/longitudinal_flow.json)
longitudinal strips sample actual rendered crossings and GPU velocity against
the registered bed. At 60 s, the median surface falls from 7.687 m at station
-5 to 5.881 m at +2, before rising to 6.203 m at +4. However, all sampled
surface downstream velocities in the selected 2 m-wide strip remain positive.
Near the inferred pool centre the median surface velocity is still about
1.00 m/s downstream. The review has a drop but does not demonstrate the
required returning surface roller. Interior circulation is not measured by
this surface-only diagnostic; it must be inspected separately, not assumed
absent. The inspected 60 s image still resembles glossy cyan liquid, not the
reference's aerated breaking water. Mean top-crossing coverage is only 0.009217.

Next: inspect the drop/pool velocity cross-section and outgoing pressure/stage
coupling, then fix breaking/aeration and
secondary contact against real motion references. Do not simply increase
whitening gain or treat this bounded review as completion of South Fork.
Colorado, Pacuare, Futaleufu and the rest of the queue remain unchanged.
