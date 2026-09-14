# Smooth pressure helps temporal regularity; coupled transport fails physics

September 14, 2026. Research evidence, **not gameplay acceptance**. The full
remaining-work objective and Desktop30FPS/p95 33.333 ms remain open. The prior
30 FPS confirmation turn was NO PROGRESS toward reconstruction (existing
settings/checks were reverified); this continuation adds independent reversal
and reflection evidence and retained regressions.

## Pressure component and qualified scope

`physics/scripts/smooth_pressure_geometry.py` replaces MC pressure polynomials
in a separate strictly-positive periodic candidate. With centered undivided
depth/surface slopes c,e it uses f=4h²/(4h²+c²), dh=f*c, deta=f*e.
The depth endpoints are at least h/2; cell averages are unchanged. This is a
relative reconstruction constraint, not an absolute depth floor. Dry and open
domains are rejected. The reconstructed numerical bed/cut geometry changes;
unchanged source bed arrays do not imply unchanged reconstructed geometry.

The transmitted A coefficients and combined shared-bottom coefficient are C1
across the hydrostatic cut branches for positive reconstructed columns. The
individual Ca/Cb coefficients need not be C1 at zero bed jump. An explicit
rational tangent is independent of the reverse derivative. Both original
dispersion poles and 40-CG/independent derivative gates remain. Flat fully-wet
integrated/shared operators agree with the old geometry.

The candidate stage couples this to the continuous-envelope donor mass
transport. Original recorded models remain separate. No native shader,
material, map, terrain, captured source, or gameplay mode was changed here.

## Evidence already produced, re-inspected this continuation

- `tmp/south-fork-smooth-rational-evolution-v1-20260914.json`: all 16 original
  64/128-cell energy-direction gates pass, worst final probe error
  7.105459554068715e-10. All eight original synthetic short evolutions use
  the same .008 s horizon and 4/8/16 steps. Depth ratios range
  3.9987408492202148–4.248504944475681, canonical-velocity ratios
  3.996060088710619–4.001841115218358. These resolve the earlier measured
  temporal defect on these controls, not the nine-second captured history.
- `tmp/south-fork-smooth-pressure-crossings-v1-20260914.json`: all eight old
  EP trajectory endpoints preserved exactly. Across 29 recorded branch
  segments, 100x input reduction gives approximately 100x force-gap reduction.
  Independent gradient error <=7.105427357601002e-15. Candidate probes use
  the same **canonical** states; recovered physical velocities may differ
  because the metric changed. Do not claim both were preserved.
- `tmp/south-fork-smooth-pressure-refinement-v1-20260914.json`: unchanged
  manufactured 32–1024-cell probes give pressure L1 orders 1.986664–1.999963.
  Flat constant integrated-pressure response is exactly zero. Variable-bed
  constant-pressure error decays but is not identically zero.
- `tmp/south-fork-smooth-stage-momentum-v1-20260914.json`: all eight original
  flat-bed profiles FAIL momentum conservation. Constant-mode preservation
  verifies integral h*v = integral h*u, and independent physical-momentum
  directional probes agree with the nonzero canonical rate. At 64 cells,
  rates are 0.000658135, 0.000491985, 0.000452518, 0.000423783. The one-cell
  transverse width varies with resolution; do not compare raw integrated
  64/128 quantities without width normalization.

Provenance: the main evolution/crossing audits recorded geometry SHA256
`c754e1673df95fdef8f29de81e635f9f21b656bda21a273f9477f28a7f78e765`.
A subsequent storage-range validation changed it to
`74bc739ba1b9e6c4b34cb185e3066817b1b249b391e5bd87ef5e9efda403ba55`:
nonzero exact polynomial values may no longer silently underflow on conversion.
This added an unrepresentable 2^-1070 control; normal-profile conversions are
unchanged. Spatial refinement and current combined tests use the latter hash.
Do not relabel the earlier reports as executions of the later file.

## New exact zero-flow/reversal counterexample

`audit_smooth_stage_reversal.py` and `test_smooth_stage_reversal.py` check both
spatial axes using periodic flat-bed depth [1,2,4], dx=.5 and constant canonical
velocity ±epsilon. The pressure metric preserves this physical constant mode.
An independent Fraction oracle uses explicit slopes [0,3/2,0]; it does not call
the stage's pressure or transport assembly.

At rest, the energy derivative is g*h and depth rate is zero. The current
frozen-donor adjoint gives net momentum rate

    -g*dx*sum(face_retained_height * (h_neighbor - h_owner)).

For positive flow (also the exactly-zero tie), retained heights are
[1,2.75,4], net momentum rate **26.9775**. For negative flow they are
[1.25,4,1], rate **-30.65625**. The respective cell acceleration limits are
[40.548,-24.525,29.103] and [3.597,-34.335,-14.388]. Their maximum difference
is **43.491 m/s²**. Neither the pole solve nor precision is responsible.

Report `tmp/south-fork-smooth-stage-reversal-v1-20260914.json`:
epsilon 2^-12, 2^-20, 2^-28 reduces mass-rate gaps exactly 65536x but leaves
the acceleration gap unchanged (ratio 1). Exact-oracle discrepancy is at most
4.44e-16. Reflection of the resting depth profile also violates vector
reflection symmetry by 43.491 on both axes. Energy rate still cancels to
roundoff: that cancellation alone is insufficient for a physical model.
The report checks implementation hashes before/after execution.

Final current suite `tmp/smooth-pressure-reversal-controls-v1-20260914.xml`:
**25 PASS / 13 FAIL, 22.21 s**, process 35915 terminal exit 1. Failures are
the eight original momentum profiles, the resting net-force control, and
reversal/reflection in each axis. No xfail or gate relaxation. Earlier
23 PASS / 8 FAIL and separate resting failure remain archived, not superseded
by a claim of acceptance. Original MC/EP/dry-support failures also remain.

## Required next implementation direction

The frozen upwind donor coefficient must not be reused directly as the
reversible pressure force. Merely changing the zero-velocity tie, smoothing
pressure slopes, increasing CG iterations, or projecting total momentum
cannot repair the demonstrated two-sided mismatch.

A useful necessary flat-bed gravity check: a symmetric two-point pressure
coefficient whose work is a local pressure-flux difference must obey
H(a,b)*(b-a)=(b²-a²)/2, hence H=(a+b)/2 for a!=b. That identity explains
why the donor values fail, but does **not** authorize replacing all mass fluxes
by centered fluxes: positivity, rough-bed blocking, energy work, both poles,
and spatial/time accuracy must be derived and tested together. The next
coupled candidate needs local conservative momentum/pressure stress and a
compatible positive mass/energy transport, not an after-step global repair.

External method lead checked in HTML: Ranocha and Ricchiuto,
[Structure-preserving SGN approximations, sections 3 and 6](https://arxiv.org/html/2408.02665v3).
Their classical elliptic SGN split uses conservative nonhydrostatic pressure
and preserves flat-bed momentum alongside mass/energy. Remark 4 explicitly
warns their hyperbolic split does not generally preserve momentum. This is a
derivation lead, not proof for our two-pole metric, reconstructed banks, dry
states or positive transport. No single-pole/hyperbolic substitution has been
made or qualified.

## Original histories and river cook remain running

Directly polled all five original handles this continuation; none was
restarted, reset, suspended, or spliced. Source guards: 417 and 422 checked,
zero changed files in each set.

- 59896 requested original history: accepted native .8959137378196856 s,
  maximum speed 143.79127808667965 m/s, not physically accepted.
- 95666 old failure-clock diagnostic: pressure call 905, still live;
  its shorter/no-move history cannot replace requested full history.
- 97152 observation-only original history: still live at wall 23692 s;
  exact-dry/thin-film physical behavior remains unqualified.
- 41566 earlier difference-scalar history: native 1.6166831813469875 s,
  maximum speed 1405.4581686595213 m/s at depth .002173123269683295 m
  (cell [101,25]). This is not merely speed in negligible subnormal depth.
  Mass closure does not excuse this physical failure.
- 83142 expanded cook: local step 23480, native 9174 s. Latest completed
  dual-audited checkpoint remains 9100, still unsettled. The 9200/local24000
  complete marker was absent when checked; run BOTH snapshot and exterior-bank
  audits once it is complete. Target remains 10000, unchanged.

Full moving-source/wetting/entropy/native/visual/contact validation is still
required. Research stage costs do not meet the 1.6 ms production solver gate.
Latest isolated native performance remains about18.9 FPS/p95 70.33 ms, below
the revised30 FPS target. South Fork terrain/rapid/wave/froth acceptance,
Colorado then Pacuare then Futaleufu, Chilko/Zambezi reviews, crew,
normalization/regressions/release/commit all remain open. Troublemaker stays
an embedded South Fork rapid, never a menu scenario.
