# Pressure geometry of the evolving local dry-front profile

2026-09-18 UTC. This supplies a missing pressure-geometry component on the
existing local affine-bed predictor. It does not enable the nonlinear runtime
or claim a complete spatially varying inlet, river update or visible improvement.

## Implemented geometry and time work

The hydrostatic pool helper integrates water below one horizontal stage.
The finite-time dry-fan predictor instead has quadratic depth across its fan.
Reconstructing that profile from its volume or mean depth loses the second and
third depth moments required by the existing vertical kinetic form.

`subcell_affine_front_metric.py` integrates M0 through M3, where Mk is the
integral of h^k on the fixed original terrain polygon. It retains the existing
completed-square form, not a new dispersion fit:

    h (h D - 1.5 b.u)^2 + 0.75 h (b.u)^2

Its unnormalised 3x3 Gram matrix on (D, u_x, u_y) uses M3 in the divergence
entry, -1.5 M2 times the original bed slope in the cross terms, and 3 M1
times the original slope outer product in the velocity block. No source vertex,
bed slope, water depth or positive sub-float fragment is rounded away.

The analytic physical-time derivative integrates k h^(k-1) h_t for k=1..3.
The moving dry edge contributes zero because h=0; moving fan-head terms cancel
because depth agrees on both sides. That argument does NOT provide the wet-area
rate, which is not claimed. Metric-time work and supplied velocity-jet work
are both retained. This derivative is not the old hydrostatic volume derivative
and cannot be substituted for it or appended as a residual pressure force.

## Validation

- Final focused suite: **63 PASS**, no skips, 17.83 seconds. Independent branch
  quadrature checks moments and completed-square energy; refined centered time
  differences check metric and jet work. A separate positive tensor quadrature
  checks the oblique-bed cross terms in two dimensions. Source splitting, winding, exact mass
  flux, dry/sub-float controls and a mean-depth counterexample are included.
- Deliberately corrupted rates, including a 1e-400 dry ghost, fail the time
  check. Historical-provenance controls reject changed input arrays, imported
  physics code, wrong historical bytes, unknown paths and moving Git refs.
- Broader 60-module physical regression run: **746 PASS / 13 FAIL**,
  759 tests, no errors/skips, one existing JUnit warning, 225.04 seconds.
  The final additional oblique quadrature check was added after this run's
  collection and is covered by the final 63-test focused run above.
  Failure identities are exactly the earlier four constant-velocity energy,
  eight paired nonlinear energy and one storage/face representation failures.
  They remain unresolved and are not waived or reclassified.
- The first focused run exposed unsupported algebraic abs/power operations in
  the new implementation/test. Direct algebraic triangle integration and
  multiplication corrected these without altering gates; failed evidence remains.

Reports:
`tmp/affine-front-metric-focused-v6-20260918.xml`, SHA256
`dfcdde850dd83c8ab38890a11cf7d1fa89247949c3a2fed17fd6b16b3732489b`;
`tmp/affine-front-metric-full-suite-v2-20260918.xml`, SHA256
`ec412d256e8a7348dd055222f279e1dc2a008248a47092bcab2449a6746a1a5d`.

## Recorded original-terrain cases

All eleven supported local predictors retain their exact original depth,
velocity, plane, time and binary gravity. The two unsupported original branches
remain unsupported. All eleven pass exact whole/wet/dry moment and matrix
partitions. Their first-moment time derivative equals the independently
computed prior boundary mass flux exactly. All show that the cubic moment is
strictly different from a uniform mean-depth replacement.

Independent time checks pass at divisors 256 and 512 with the unchanged 1e-10
relative tolerance and no floating-point scale floor. The final v3 check scales
by exact gross local moment-time work, splitting where h_t changes sign.
Earlier v1/v2 moment/time normalization was rejected as unnecessarily permissive
when the original probe time is tiny; those reports are preserved, not final
qualification. The largest final gross-work-scaled error is
6.703849129367507e-26. These probe intervals test derivatives; they do
not change the river solver's timestep. An independent serialized reload
preserves 281 preceding record fields, verifies partitions/symmetry/moment
positivity, and checks all 622 current source/implementation hashes.

Audit: `tmp/south-fork-affine-front-metric-v3-20260918.json`, SHA256
`1a9ada8ba96006bd43c31d17ea5835ddad4edf6d82f2ddd629207493cbb2403f`.

The first audit correctly stopped on changed historical tool bytes. Of 620
inherited provenance entries, 617 still match current bytes. Three unused
tools changed in later commits: CSV timing-scope documentation, offline worker
comparison options and lazy joint-preview imports. Their original recorded
hashes are verified against these exact Git versions, not rewritten:

| Historical tool | Verified original commit |
| --- | --- |
| audit_unreal_frame_csv.py | 184e2b6fec29fa731d925d08d82548114aae2fe6 |
| compare_cartesian_cook_binaries.py | eb93e59251a5cac562a5435eb471d5e60174269e |
| prepare_south_fork_joint_preview.py | 14beafd278da86598c6675eb60bf5e9ad8c1f217 |

The report retains both old and current hashes and explicitly states that these
historical tools are not used in this computation. Data and imported physics
code cannot take this exception. Source data and original captured/inferred
authority labels remain unchanged. Exact arithmetic does not increase survey
precision or turn inferred bathymetry into measured geometry.

## Remaining integration and acceptance

The evolving profile now supplies the local unnormalised pressure metric and
its time derivative. The common intercell derivative and its moving-profile
time work, physical/canonical mass normalisation, nonlinear force closure,
actual varying inlet, interacting fronts and bed-slope junctions remain to be
coupled consistently. Do not replace that work with a uniform-state model or
insert these terms into the known-broken pressure update.

No Unreal code, installed binaries, scenes, materials, collision or source water
changed. No new engine motion, reference-video comparison or FPS claim is made.
The last ordinary profile remains 34.854890 FPS / p95 38.0726 ms, FAIL30.
The hydraulic 5950/6000/6050-second checkpoints pass state and dry-bank audits but
are not settled or promoted; see the continuation record. The full South Fork
then Colorado, Pacuare, Futaleufu queue, Chilko/Zambezi reviews, crew,
normalization, regressions and release remain open. Troublemaker is a rapid
within South Fork, never a menu scenario.
