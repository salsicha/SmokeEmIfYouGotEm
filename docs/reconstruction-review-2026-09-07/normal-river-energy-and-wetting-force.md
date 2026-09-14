# Energy and physical wetting-force qualification — September 14, 2026

Research progress, NOT a playable solver update. The preceding turn added and
evaluated source-supported scalar forcing and verified the8500s river snapshot.
This turn tests full pressure forces and discrete energy, not only scalar work.

## The wetting failure reaches physical force

`physics/scripts/source_supported_pressure_reference.py` couples the new
source-supported forcing to the ORIGINAL nonlinear pressure routine. That
routine still owns both rational poles, weights, directional normalization,
pressure adjoints and40-CG true residual checks. Only the isolated process's
forcing binding changes; it is restored on success/failure. No native mode,
ongoing history, source data, depth floor or pressure tolerance changes.

Lake/restoration/rejection tests:2PASS0.76s. Actual retained test-ray pressure
report: `tmp/south-fork-source-boundary-pressure-ray-v1-20260914.json`.
SHA256:a5ccc21ac4299daa4b3b5af0e5cd8e1ed839911f37a2934d7b1c17331b8ba7c0.

Both beds use the original scalar test's state/rates/probes, plus the previously
retained smaller probes. Physical dry force at the analytic limit is exactly0.
Flat-bed maximum force error at2^-24 is7.76105210e-8, declining to7.10543e-15
at2^-64. The variable-bed case **FAILS** at2^-24:0.669219854m2/s2 momentum-rate
error, located at[1,1,0] in an originally1m-deep cell. At2^-48 the error remains
0.667310650; at2^-64 it reaches1.50990e-14. Both poles' residuals remain below
7.1e-16. This is not an incomplete linear solve or only an unused dry scalar.

The exact represented bed gaps identified previously produce a nonuniform
near-dry cut limit. The original unweighted Q/C test remains failed and unchanged.
Its error must not be dismissed merely because the very smallest probe reaches
the analytic limit. NEXT qualify/correct the joint depth/cut-geometry behavior
and its effect on wet-cell forcing, preserving all actual source values.

## Independent discrete energy derivative

`physics/scripts/reconstructed_energy_reference.py` assembles small dense face
matrices independently and differentiates the full kinetic metric using the
original actual-mass-rate geometry tangent. No numerical-energy correction is
applied. Six reference tests PASS0.88s: independently integrated SGN vertical
kinetic energy, analytic-vs-finite-difference energy rates, tangent face actions,
actual rational-pole response matrices, and rejection of unsupported dry/open
normalization.

For classical SGN, with d=D(u), e=E(u), the kinetic density is
`h|u|^2/2 + h^3 d^2/6 - h^2 d e/2 + h e^2/2`.
Potential density is `g h(h/2+b)` (the omitted fixed-bed term is constant).
This agrees with the completed-square full-bathymetry SGN energy; see
[Ranocha and Ricchiuto, Section9, equations123–124](https://arxiv.org/html/2408.02665v3#S9).
The paper does not establish energy conservation for this repository's cut-cell
FV discretization or its nonlinear two-pole blend.

For the rational model the **frozen linear** normalized response is
`S=(1-sum(weights))I + sum(weight_j A_j^-1)`.
Its inverse is the corresponding kinetic metric. Extending that metric to
nonlinear states is only a candidate energy, NOT a proven model invariant.
The new tests verify its full state-dependent derivative, including metric
variation; they do not silently substitute the single-pole SGN energy.

## Closed controls expose the rational-metric limitation

Reports:

- `tmp/south-fork-closed-energy-controls-v1-20260914.json`:32 fully positive
  periodic rough states, original/difference scalar and SGN/rational models.
  All sampled total rates negative; not a stability proof.
- `tmp/south-fork-smooth-energy-{16,32,64,128}-v1-20260914.json`:8 fixed smooth
  periodic profiles per resolution, both scalar choices and both models.
  All SGN rates negative. Rational candidate-metric rates positive in4/8 profiles
  at64cells and5/8 at128cells, for BOTH scalar choices. All pressure gates pass
  across all256 full-rate control evaluations.

Do not compare raw singleton-row energies across resolutions without their
transverse width. At seed2205, candidate rational metric rate per unit width is
+0.0654167276 at64cells and+0.0954261246 at128cells. The corresponding SGN rate
is-0.0325586016 and-0.00427056644. Density is omitted. Periodicity eliminates
external boundary energy input, but does not make the rational metric a proven
nonlinear invariant.

Independent state-space finite differences using the ACTUAL full momentum
direction verify the positive rates for seeds2204/2205 at64cells. Errors at
epsilon1e-5 are2.61475e-11 and2.53828e-10, respectively. Report:
`tmp/south-fork-rational-energy-direction-v1-20260914.json`, SHA256
38c3fb9d3d60f646865386e0a1668fef2136b6302bd069b85f70869cc700d1b2.
This rules out assuming a positive frozen linear operator automatically supplies
a nonlinear energy guarantee. It does NOT prove no other energy exists, nor
that the entire river simulation is unstable.

NEXT derive a nonlinear energy/flux closure for the actual two-pole model and
qualify the near-dry cut behavior. Do not replace the rational model with SGN
merely because the SGN controls are easier to pass. Source-supported boundary
evolution, complete moving histories, native cost, waves/froth/contact/30FPS,
terrain/crew/later-river/release/final-commit acceptance remain open.

Final combined suite:34PASS/1FAIL9.38s; retained
`tmp/south-fork-energy-pressure-controls-v1-20260914.xml`. The one failure is
the original variable-bed source-scalar ray assertion, unchanged. All417/422
frozen replay dependency hashes remain exact. Final direct polls confirm all
five original jobs LIVE: cook8549.5s, main0.757298817s, observer0.525206602s,
earlier scalar candidate0.891666712s, and the separate failure-clock diagnostic.
No full9.066667s/two-move history completed. Latest COMPLETE8500 has both audits;
next COMPLETE8600/local12000 still requires both. No process was restarted.
