# Source-supported scalar boundary action — September 14, 2026

Research implementation only. No native/playable solver, visual, or 30 FPS
acceptance. The preceding goal turn made progress by verifying the actual wider
source capture; this turn uses that source to address its missing scalar support.

## Implemented

`physics/scripts/source_supported_scalar_boundary.py` combines the CURRENT
evolving interior with the supplied three-ring conserved source stencil. It
never installs the captured interior as evolving state. The extended geometry
supplies constant-null scalar derivatives and first-ghost velocity/divergence/
bed-velocity traces. Ghost divergence uses the independently captured interface
normal velocities. Original interior pressure D/E, signed force adjoints,
geometry rates and affine face velocity/time-rate remain caller-owned.

Exactly dry entering cells require actual conserved rates: original FV rates
inside, captured temporal source rates outside. The analytic velocity limit is
M_t/h_t; conserved h/M remain exactly zero. Directional geometry supplies its
right-limit coefficients. Missing directions, negative dry mass rates and
inconsistent interior tangents are rejected, never repaired. This is not a
proof of mechanical-energy closure, outgoing-wave conditions or nonlinear
wetting stability.

## Verified and failed controls

Flat-water affine scalar derivatives are exact at every edge/corner for
8/16/32 cells, replacing the earlier candidate's non-refining 0.5 derivative.
Smooth-field errors refine at second order. Independent explicit face matrices,
time-varying prescribed traces, original pressure work, exact current-interior
retention, invalid-source rejection and flat-bed entering-ray tests pass.

Final combined scalar/source suite: **26 PASS, 1 FAIL (9.49 s)**; retained XML
`tmp/south-fork-source-supported-scalar-controls-v1-20260914.xml`. The failed
variable-bed entering-ray test is retained with its original probes/tolerance:
Q error 11.405668861 at epsilon 2^-24, C error 0.00976562503; Adv error
7.3761e-8. No assertion was weakened to produce a green suite.

Independent diagnosis retains those probes and adds 2^-48/2^-64:
`tmp/south-fork-source-boundary-wetting-ray-v3-20260914.json`.
The non-dyadic test bed has exact represented reconstructed gaps of
-1/288230376151711744 m and +1/144115188075855872 m. At h_t=1/8 m/s,
their crossover times are 2.77556e-17 and 5.55112e-17 s. Original probes do
not approach the zero-depth cut branch at these faces. At 2^-64, Q error is
0, C error 1.11023e-16 and Adv error 2.45526e-20. This supports the analytic
limit, NOT uniform finite-depth/wetting qualification. The finite-depth test
failure and the earlier difference candidate's three broader control failures
remain visible; no bed gap or source depth was erased.

## Actual captured South Fork evaluation

Final process35768 TERMINAL exit0. Report:
`tmp/south-fork-source-supported-scalar-boundary-v3-20260914.json`.
Source SHA256:129a7a9de42d2f5559f8b0e777cfe38d36b4e7f6c43aa933d0292888ccb4d7de.
Both revisions2/3 evaluate with all8 entering dry cells preserved. Original
source/bed registration is checked. Compared with the earlier difference
candidate, maximum Q/C/Adv changes at revision2 are3.21329489/0.42230545/
2.60275692. Revision3 changes are3.21241443/0.42229618/2.60232936.

Adv changes are confined to two boundary cells. Applying unchanged D/E to
Adv adds a third dependency layer for Q/C; all values beyond these derived
regions are exact. An earlier audit incorrectly assumed two layers for Q/C
and rejected the run; the corrected dependency radius follows the composed
stencil, not a relaxed numerical tolerance.

Scalar work is decomposed into exterior work, changed scalar-geometry work and
constant-null correction. Identity errors are0 and9.09495e-13. The large
nonzero terms do NOT constitute a mechanical-energy or stability pass.
An initial stationary-dry evaluation correctly rejected actual wetting cells;
the successful run uses their analytic conserved-ray limits instead.

## Next required work

Qualify finite-depth transitions across the represented cut branches and the
complete pressure/boundary mechanical-energy balance before evolving/promoting
this closure. Use fresh wider-source history provenance; old recordings cannot
be extended or spliced. Full nonlinear moving histories, native cost, actual
breaking/froth/contact, terrain, crew, later rivers, release and final commit
remain open. Latest isolated gameplay performance remains18.899245 FPS FAIL;
latest inspected actual capture remains visually FAIL. No appearance change
was made this turn.

All five original long jobs were directly confirmed live. At the last poll:
main0.733333372s, observer0.511859913s, earlier scalar candidate0.750000038s;
the separate failure-clock diagnostic also remains live. Original cook reached
COMPLETE8500/local10000; BOTH state/artificial-bank audits PASS:5,382,400 finite
cells,86,720 bank cells exactly dry, snapshot/driver difference2.79397e-9m3.
Outflow102.452874602 vs inflow45.306954547m3/s remains UNSETTLED.
Next COMPLETE8600/local12000 requires both audits.
All417/422 guarded implementation hashes were unchanged. No job restarted.
