# Pressure wetting-edge discontinuity — September 14 UTC

Follow-up: [exact pressure cut-column derivation](normal-river-pressure-cut-columns.md)
rejects the unused harmonic connection on flat-bed momentum grounds, verifies
top/blocked profile integrals on the captured edge, and records the remaining
compatible-operator implementation boundary. No solver promotion follows from
these diagnostics.

The previous goal turn made concrete progress: source-exact replay isolated
interval15/trial8, whose pressure edge opens between RK stages. This continuation
tests causality and the vanishing-wet-face limit. The full South Fork/playable/
later-river/crew/performance/release goal remains unchanged and incomplete.

## Captured source and isolated edge

Input `tmp/south-fork-unscaled-onset-stages-v1-20260914.json/.bin` retains16 trials
from the ORIGINAL failed unscaled history, with all2438 original trials replayed
and exact failed state, clock, counters and diagnostics. The input source hash is
`0114ce4611375f4e169e077d36747754306b867e67fa44bf7858ca5566f6bf10`.
Trial8 begins1.8666667640209198s and uses original dt0.008333333767950535s.
The edge joins y22/x102 to y23/x102. No pressure graph is edited in any live or
evolved state by the new diagnostic.

`physics/scripts/audit_pressure_wetting_edge.py` evaluates both actual stages,
then toggles ONLY this one pressure edge as an explicitly counterfactual operator
probe. State, bed, native hydro rate, breaking fraction and boundary trace remain
fixed within each comparison. It retains integrated pressure and bottom traction
separately, including pressure-column values without clipping negative results.

`tmp/south-fork-pressure-wetting-edge-v1-20260914.json` completes:

- First actual stage, closed edge: acceleration[-0.216260,-0.696983]m/s2.
  Same-input counterfactual open edge:[3.855476,12.655753]m/s2.
- Second actual stage, open edge:[3.896163,12.780601]m/s2.
  Same-input counterfactual closed edge:[-0.216086,-0.696147]m/s2.
- First-stage quadratic forcing19.468827 becomes862.673097 under the isolated
  opening; bottom-curvature term-0.064245 becomes18.738033. In the actual second
  stage, y-force0.4456543 consists of pressure divergence0.0341400 plus bottom
  traction0.4115143. This is a pressure-model effect, not permission to disable
  pressure or remove a physical connection.

## Continuous-input limit

`tmp/south-fork-pressure-wetting-limit-v1-20260914.json` and v2 complete. V2 adds
the per-pole positive quadratic form of the pressure matrix; this is explicitly
NOT a proven energy invariant of the rational two-pole evolution.
V2 report SHA256:
`dc8c0afd281a699810d38ec433d57889bfc19bb5f8156dcdd12506f6cb9b3ef4`.

The diagnostic uses convex inputs between the two captured stages and samples
the original source boundary inside the same time bracket. Each probe independently
recomputes hydro transport, graph and breaking fraction. These are sensitivity
probes, not a replacement trajectory or history reset. A48-iteration bracket finds
an opening at alpha in[0.4997177657979961,0.49971776579799965].

| Maximum state difference | Maximum hydro-rate difference | Pressure-force jump at owner, y |
| --- | --- | --- |
| 8.0313683e-5 | 1.0689556e-3 | 0.4671036905 |
| 8.0313682e-8 | 1.0689556e-6 | 0.4670979313 |
| 8.0313534e-11 | 1.0689485e-9 | 0.4670979255 |
| 1.7763568e-15 | 9.9475983e-14 | 0.4670979255 |

Exactly ONE graph cell changes in every pair. In the narrowest bracket, the
owning hydrostatic face changes0→7.8054086e-19m; its neighbor face remains
6.0494857e-7m. Thus the transport converges continuously while the pressure
force retains a finite jump. The code's boolean pressure connection has no
continuous vanishing-aperture limit on this actual geometry.

The owner pressure-matrix quadratic density changes0.3467629654→0.3940740715
for the first pole, and0.0335107731→0.0380828638 for the second. The corresponding
domain integrals change1029.9009614955→1029.9127892720 and
99.5284412505→99.5295842732. These matrix diagnostics are not an energy budget
for the complete open-boundary rational evolution.

## Formulation implications and next implementation boundary

The observations reject timestep tuning as a complete remedy and reject a bare
boolean wet-pressure graph as a continuous reconstruction. They do NOT establish
that a selected aperture smoothing, new depth cutoff, or pressure deactivation
would be physically correct. In particular, replacing a boolean by an arbitrary
factor while ignoring its time derivative in the kinematic terms would change
the model without preserving the identities it claims.

Next derive pressure coupling from the shared reconstructed wet-face geometry,
with a consistent divergence/negative-adjoint gradient, conservative pressure
flux and bottom traction, and the time variation of that coupling. Test the
vanishing-face limit above, exact rough/dry lakes, thin connected films, variable-
bed wave consistency, conservation and original-start full-history stability/
accuracy before any native/playable promotion. A smooth factor alone is not
qualification and may not remove the later nonlinear growth.

Primary-source cross-check: Ranocha and Ricchiuto's
[structure-preserving SGN study](https://doi.org/10.1002/num.70016), Sections2 and9,
derives energy-compatible split forms and paired derivative operators for full
variable bathymetry. Its positive-height, periodic-operator results do not prove
this project's mixed finite-volume/boolean-graph wetting scheme stable. It is a
derivation reference, not a turnkey wet/dry fix or authorization to add viscosity.

New probe tests cover exact single-edge isolation, no input alias/mutation,
positive subnormal depths without a floor, dry/wrapped-edge rejection, bounded
transition bracketing and nonbracketing rejection.32 focused tests pass in0.61s
(overlaps the previous recorded-model tests). Later tests also check actual
pressure divergence/bottom-traction decomposition, positive matrix forms,
read-only source arrays and restoration of diagnostic hooks after exceptions.
The139-test broader pressure/provenance/30FPS suite passes in9.89s;141 tests
including those input-preservation checks pass in9.06s. Additional malformed-
graph rejection tests require boolean edges, finite nonnegative2D depths, and
do not silently turn fractional edge coefficients into booleans. Final145-test
suite62420 passes in12.67s. These suites overlap and are not additive counts.
No shipping shader, solver, source
geometry, boundary, scenario menu, runtime coupling or physics timestep changed.
No new playable capture/FPS result or final commit. Desktop30FPS/p9533.333ms,
physics120Hz and production1.6ms solver budget remain unchanged; last gameplay
18.899245FPS/p9570.33ms still fails. Troublemaker stays inside South Fork.

Both7100s/local22000 full-river state and exterior-bank audits pass for the
unchanged live74818/PID41820 continuation. All5,382,400 cells are finite and
all86,720 artificial-bank cells remain exactly dry. Outlet111.411573419 versus
inlet45.306954547m3/s is still unsettled. Next COMPLETE7200s/local24000 requires
BOTH audits. No cook pause/restart, source promotion or new video inspection.
All local numerical probes and tests are terminal.
