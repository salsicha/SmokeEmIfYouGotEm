# South Fork control-prior comparison

September 16, 2026. **No new normal-game visual improvement or acceptance is
claimed.** This identifies a physical source of steep water geometry and
prepares a source-preserving candidate for the shared playable path. The
full-map shader cook is still active; its inputs have not been modified.

## Corrected submitted-shape attribution

Commit `d2412e3ca` corrects source interpolation to match native shoreline
triangles A-C-D / A-D-B. The former B-C diagonal creates an apparent error on
nonplanar quads. Seventeen focused tests pass, including both reflected world-Y
conventions and nonplanar refined triangles.

Reanalysis of the identical 1700-second actual-game capture examines the same
22,869 nearby triangles. On the fully wet 30–60 degree subset, source gradient
contributes 0.8012019004, target-minus-source 0.0956974419, and
submitted-base-minus-target only 0.0000004558. Three triangles above 60 degrees
have a submitted-base-minus-target contribution of -0.0000239929. These replace
the invalid v1 source split, not the captured geometry.

Corrected report: `tmp/landward-1700s-carrier-shape-v2-20260916.json`, SHA256
`618facc740f93f86b000a99681266ce6ed9e4d4c2399301cb77f423f2d6c99de`.
The v1 artifact remains unchanged. This is not a GPU-normal or pixel-ID audit.

Ten water-only rays using the logged comparison camera put the sampled steep
faces over the uncalibrated submerged prior. Nearby source vertices are
authority 2. These rays exclude terrain/raft occlusion and use a different
capture time from screenshot002; they are approximate visual attribution,
not exact pixel correspondence. Actual registered bed sampling, rather than
a change to temporal blending, is the next relevant intervention.

The original builder explicitly adds an analytic shelf and plunge at local
east/north (-9, 1) metres. Its stated 0.7-metre shelf depth and additional
0.7-metre plunge are hypotheses awaiting calibration, not surveyed bathymetry.
The accessible Qweniden bank-side reference at 0:19 again shows locally
separated rock-controlled drops and irregular crests. It does not measure the
underwater bed or establish a calibrated camera/flow match.

## Isolated physical candidate and paired solve

`prepare_troublemaker_control_ablation.py` first reproduces the original
float32/NAVD88 bed formula exactly. It refuses to proceed if any editable
registered vertex no longer equals that original prior. It then removes only
the shelf/plunge term from authority-2 vertices, retaining the older
shore-distance depth prior. No measured vertex, registered XY, connectivity,
return index, captured surface, or inferred rock-flank vertex changes.

Candidate: `tmp/troublemaker-control-ablation-v1-20260916`.
Mesh SHA256: `8edf8a7fbfb675a22ac6736db600a3300f018f1c9037b1c0674bc1c376cfcca7`.
2,132 inferred vertices change, by [-1.48974609375, +0.699951171875] metres.
This is a causal comparison, **not a calibrated replacement bed**. All original
assets are retained. No evolved old-bed state is transferred to the candidate.

Both fresh solves completed with exit0 using the same registered-triangle
sampler, 271-by-161-metre rotated domain, one-metre cells, dt0.1, CFL0.38,
roughness0.035, open inlet/outlet and 45.3069545472 m3/s target. Native solver
SHA256: `1bbf29bda937e7e9cd19b8baf41113529df36d5ce7dcf0ef50e9606f2621ae4c`.
Sessions21033 and39469 are terminal, not pending jobs.

Reproducible commands (repository root; Python dependencies on PYTHONPATH):

```powershell
python physics/scripts/prepare_troublemaker_control_ablation.py --parent-manifest tmp/troublemaker-inferred-rock-flanks-20260912/manifest.json --output tmp/troublemaker-control-ablation-v1-20260916
python physics/scripts/cook_troublemaker_survey_hydraulics.py --cell 1 --steps 1800 --dt .1 --cfl .38 --mixed-inlet --geometry-dir tmp/troublemaker-inferred-rock-flanks-20260912 --bed-sampling registered_triangles --label control-prior-original-v1-20260916
python physics/scripts/cook_troublemaker_survey_hydraulics.py --cell 1 --steps 1800 --dt .1 --cfl .38 --mixed-inlet --geometry-dir tmp/troublemaker-control-ablation-v1-20260916 --bed-sampling registered_triangles --label control-prior-removed-v1-20260916
python physics/scripts/compare_troublemaker_control_ablation.py tmp/south-fork-survey-hydraulics/1m-mixed-inlet-control-prior-original-v1-20260916 tmp/south-fork-survey-hydraulics/1m-mixed-inlet-control-prior-removed-v1-20260916 --report tmp/troublemaker-control-comparison-v2-20260916.json
```

Use fresh output names for a rerun. The comparison checks matching forcing,
numerics, registration, valid frame coordinates/momentum/bed, unchanged
depth/speed limits, and a common wet stencil. At180s, on644 common crux
stencils, maximum centered stage slope changes from43.4047 to23.0980 degrees;
area above30 degrees changes from5 to0 m2. Median stage remains similar
(6.61296 versus6.62802 m); p90 changes from7.79664 to7.03223 m. Thus the
analytic prior materially creates the steep upstream/downstream structure.
It does not establish that removing it gives the correct rapid.

Comparison report: `tmp/troublemaker-control-comparison-v2-20260916.json`,
SHA256 `41e7dc7ce5374344635914b39a3c3d2b45b22cc8ec36019d86a92b7491991b99`.

All13 frames per run have valid finite/nonnegative states; artificial side
banks remain exactly dry. **Both flows remain unsettled.** At180s, section
discharges range44.1108–51.4364 and45.4647–51.6224 m3/s respectively. This is
not numerical boundary-flux closure or full-river acceptance. The bounded
comparison also excludes the later landward rock-cap union and uses a rotated
grid, unlike the current FullReach solve. Do not install its fields in the game
or replace South Fork with this bounded domain.

The source candidate and comparison have seven focused tests; together with
the17 shoreline audit tests,24 pass. Generated mesh/frames/reports remain
ignored. Tests and this candidate are not a delivered normal-menu feature.

## Full-river checkpoint and next delivery work

The separate unchanged full-river run72710/PID4608 completed1800s with exit0.
All5,382,400 cells pass state/conservation gates; all86,720 artificial-bank
faces are exactly dry. Maximum depth4.437210 m, speed7.241383 m/s, maximum
step conservation residual1.323509e-8 m3. Outflow92.233295 versus
inflow45.306955 m3/s still precludes settling acceptance.

- State: `tmp/south-fork-context5-1800-snapshot-v1-20260916.json`, SHA256
  `7efbea8ace6615b05662cec8fbd18fcbf27a8b9686adfbf5844f588e3263ca25`.
- Banks: `tmp/south-fork-context5-1800-banks-v1-20260916.json`, SHA256
  `b3f38ea2a3e4ebe24218e766a8a12a555306cfd068a85141744a8acdc0c6bf23`.

Next is a source-consistent full-map candidate: retain the actual landward
rock union, regenerate changed hydraulic/source packets and rendered/collision
terrain from the same mesh, solve fresh, and compare actual playable motion.
Do not treat the ablation as a proven final shape or omit real breaking/drop
behavior merely because it lowers a slope metric. Correct broken-water and
froth appearance alongside physical shape, then deliver verified improvements
through normal South Fork selection, not another standalone rapid scenario.

Package83678/cook5852 remains live with active shader workers8468 and35032.
Worker12788 has completed its batch; SM5 transport8,3,14 compile timings are
now logged. This is progress, not full-cook or packaged runtime acceptance.
Preserve these jobs and shader/DLL inputs until terminal. Archive identity,
444 non-editor ground-source checks, runtime closure and packaged gameplay
remain required. No fresh uncontended FPS result: last17.819710 FPS /
p9581.6343ms fails the unchanged30 FPS target. Later rivers, other-scene water,
crew, normalization, physical regressions and release are still open.
