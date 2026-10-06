# Original-profile moment transport and gravitational exchange

September23,2026. Supporting physics implementation for South Fork. No normal
scene, material, collision, hydraulic-field, native solver or performance change.
The complete reconstruction/crew/release goal remains open.

## The missing transport terms

The completed pressure-energy audit supplies primitive depth/spatial moment
derivatives. It does not make those moments independently conserved densities.
For the same continuity equation and original velocity profile,

```
(h^k)_t + div(h^k u) = -(k-1) h^k div(u),  k=1,2,3
((x-origin)h)_t + div((x-origin)h u) = h u
```

The new `FrontMomentTransport` supplies these exchanges on the original source
polygons. It uses one directed flux per conforming shared face, debited/credited
by opposite owners. Exterior faces retain the prescribed fan flux. For the
original varying branch, direct differentiation gives `div(u)=2/(3t)`; the wet
branch's spatially constant velocity contributes zero. Exact branch integrals
supply the compression source, and the original depth-weighted momentum
integral supplies the spatial source. Neither is computed as a residual needed
to make a balance pass. Quadratic/cubic depth moments cannot use just mass-like
face advection, nor can depth-weighted spatial moments omit their volume source.

The shared geometry helper's reflecting pressure setting supplies ownership
and analytic rate comparisons only. It does not turn these exterior advective
faces into walls. No dry owner is assigned a velocity or dropped by a float
threshold. Initial source cuts remain rational; evolving fan support remains
in its original quadratic field. Captured XYZ and precision are unchanged.

## Gravitational work, not a total-energy boundary closure

For `G = g*integral(h^2/2+(bed-datum)h)`, the implementation retains three terms:

```
G_t = -boundary[g*(h^2/2+(bed-datum)h)*u.n]
      - integral(g*h^2*div(u)/2)
      + integral(g*h*u.grad(bed))
```

These are potential advection, compression/pressure work, and bed work. Their
sum agrees with the original analytic moment derivative and independent direct
branch time-rate quadrature. Opposite shared-face work cancels exactly, while
exterior exchange stays explicit. A fixed energy-datum change produces exactly
the associated mass-rate work without changing compression or bed work.

This is not the full pressure model's energy flux. In particular, it does not
repair the differences documented by the preceding
[source energy comparison](affine-total-energy-source.md), invent a momentum
force from a global energy residual, or combine reflecting pressure transport
with shallow-water traces and declare a conservative open-boundary solver.

## Validation and current source qualification

The final focused suite passes75 tests in28.26s, including26 new transport and
source-audit checks. Independent numerical volume/edge quadrature covers axial,
rotated and non-unit normals. Exact tests cover all three depth rates, both
spatial rates, gravitational exchanges, face reversal/subdivision, hanging-edge
partitioning, winding reversal, dry owners, translated coordinates,1e-400 wet
support, changed source/receipt rejection and forbidden pressure solves.

Two test-fixture failures are retained. V1 compared different domains because
the rectangle helper defaults to plus/minus0.5m laterally; explicit matching
extents correct that test, without changing the gate. V3 used the algebraic
fan-coordinate helper for the initial rational source cut, which the original
source-polygon area routine rejects. The fixture now uses the same exact rational
plane expression as the real source importer. V2 passes64 tests; V4 passes75.
No production geometry helper, protected input, tolerance or accepted test was
altered to bypass either failure. The [test receipt](front-moment-transport/tests.json)
binds both new scripts/tests and all four retained XML reports.

The new source audit uses the completed total-energy report with pinned SHA256
`2b93022e2c2d9de74001ceba1e3b6b3ff594939394cc523f9b7d3122df4bed0e`, verifies its
entire provenance chain, reconstructs each original captured source triangle,
and compares gravitational transport against both certified momentum-coordinate
work records. Unsupported records and complete original ordering are preserved.
This audit performs no pressure solve. Source run19480/session14602 is now
TERMINAL exit0. All11 supported cases across seven original triangle IDs pass;
unsupported cases2/7 remain unchanged. This is the retained local-predictor
cohort, not complete river coverage. The3,303,380-byte final report is
`tmp/south-fork-front-moment-transport-v1-20260923.json`, SHA256
`a3e96f7afb4e6601a26e1cefe7caef15df7596ade703c6c745ae471b858b7ffa`.
All641 protected and16 imported implementation entries were independently
rechecked without a mismatch. The [completion receipt](front-moment-transport/source-completion.json)
binds the report and per-case status. Do not duplicate this completed run;
older9552/6480 also remain terminal and the obsolete profiling wrapper stays off.

## Remaining work

The conservative dispersive momentum/transport law, exterior pressure/energy
coupling, interacting fronts and activation still need implementation and
validation. The native nonlinear solver remains OFF. This increment does not
rebuild the unchanged game or repeat the same startup/FPS capture. Installed
4950s fields remain intact; the last normal26.484402FPS/p9547.2133ms still fails
the30FPS gate. Full geographic coverage, source-cap interpretation, actual
rendered crest/froth motion, shore/surface continuity, collision and performance
remain open before South Fork or the later ordered rivers can be accepted.
