# Common pressure geometry on the evolving affine front

2026-09-18 UTC. A reference implementation component, not a complete nonlinear
solver or a playable visual improvement. No native solver, source water, terrain,
collision, material, menu, update rate or quality setting changes. The nonlinear
runtime remains OFF and all existing physical acceptance gates remain in force.

## Implemented coupling

The preceding front metric integrated the quadratic-depth profile locally, but
did not connect its velocity divergence to adjacent source regions. The new
`subcell_affine_front_pressure.py` uses that same evolving profile and the
existing pressure divergence convention:

- Integrate the shared edge's depth and its physical-time derivative before
  converting coordinates. Use the directed normal times edge length, avoiding
  independently rounded lengths and unit normals. Reversing a face reverses
  both contributions exactly. Splitting a source edge preserves their sums.
- Split original polygon edges at hanging source vertices. Shared segments
  receive one common column, not two separately rounded reconstructions.
  Reject overlapping interiors, including positive sub-float overlaps.
- Assemble the depth-column-weighted intercell divergence with each owner's
  actual evolving volume. Its time derivative includes both the column change
  and the volume-denominator change. Dry fragments own no velocity unknown.
- Form the unnormalised pressure kinetic matrix `K = J^T G J`. Here `G` is
  the original integrated completed-square Gram form and `J` maps physical
  velocities to divergence plus the two local velocity components. Its complete
  derivative is `J_t^T G J + J^T G_t J + J^T G J_t`, not just `J^T G_t J`.
  The work helper separately reports local-metric, changing-divergence and
  supplied velocity-time work. No residual force or energy redistribution is
  introduced to manufacture conservation.

This component presently connects subdivisions of ONE original local fan on
the same affine plane. The common trace is continuous, so its harmonic column
equals its actual depth. It does not substitute that equality for the unknown
solution between different interacting fronts or different bed slopes.
Reflecting outer pressure boundaries must be explicitly requested. They are a
component-test closure, not an asserted boundary condition for the real river.
No open-boundary implementation is silently supplied.

The exact geometry path already retains fragments that collapse in the old
float-vertex API. This work uses it; it does not repair or waive the separate
legacy storage/face equality regression by deleting those fragments.

## Validation

Final focused suite: **60 PASS**, no skips, 33.96 seconds. Tests include:
independent branch quadrature of oblique edge columns and analytic rates;
exact reversal/subdivision; mass-weighted shared coefficients; pressure and
time-derivative symmetry; independently refined total-energy time differences;
hanging vertices and winding; independent face/volume quadrature of the fully
assembled pressure energy; explicit dry ownership; positive sub-float
geometry; and the original constant-depth pressure limit. Negative controls
omit changing-divergence work or introduce overlapping source interiors.

The source-audit time check uses independently evaluated centered differences
and fourth-order Richardson refinement, requiring two successive probes below
the unchanged 1e-10 gross-time-work-relative gate. It does not generate the
implemented analytic rate. No pre-existing energy divided by an arbitrarily
small time is used as a permissive scale.

Report: `tmp/affine-front-pressure-focused-v3-20260918.xml`, SHA256
`753ae995dd51d9056f3ab55bd49eedb400579d5a5033a06822ad61d00c798380`.
The initial eight new tests also passed; the first expanded collection had
56 passes before three additional controls; the next run had59 passes before
the final independent assembled-energy quadrature was added.

The broader physical suite finished: **758 PASS / 13 FAIL**, 771 tests in61
modules, zero errors/skips, one existing JUnit warning, 244.50 seconds.
All13 failure identities exactly match the preceding run: four constant-velocity
energy, eight paired nonlinear energy and one legacy storage/face mismatch.
No failure is waived or relabelled. The last assembled-energy test was added
after that collection and is covered by the final60-test focused run.
Report `tmp/affine-front-pressure-full-suite-v1-20260918.xml`, SHA256
`c8504549e64e618c511929a452b3d8bafeba5450f28e3002dffa01e98f84d7d4`.

## Completed original-source component audit

`audit_south_fork_affine_front_pressure.py` consumes the qualified original
front-metric report with its exact SHA256, original mesh, local states, binary
gravity and physical times. It preserves preceding records and unsupported
cases. It splits each original source polygon at that predictor's initial
interface, checks original volume, common wet pressure support and adjoint
symmetry, then runs the independent time probes.

Input: `tmp/south-fork-affine-front-metric-v3-20260918.json`, SHA256
`1a9ada8ba96006bd43c31d17ea5835ddad4edf6d82f2ddd629207493cbb2403f`.
Output: `tmp/south-fork-affine-front-pressure-v1-20260918.json`, SHA256
`95988c6fb0ba57e937ef73b5dce980985e99c48663f67fa881888c3e1d1f2286`.
All11 supported original local predictors have two active source regions and
pass volume preservation, common pressure support, exact adjoint symmetry and
time-work checks. The initial divisor256 probe fails the unchanged1e-10 gate
for all11; both512 and1024 pass. All refinements are retained. The largest
final gross-matrix-time-work-scaled error is1.2126653848043538e-12.

Process19484/startUTC2026-09-18T01:28:10.4086618Z/session92042 is now TERMINAL,
exit0, not a timed-out or restarted job. Independent serialized reload verifies
all13 records, all347 prior record fields, symmetry of every stored matrix,
the unchanged gate, both final passing probes and all625 current input/code
hashes. The two unsupported original cases remain unsupported. Exact arithmetic
does not add survey precision or turn inferred bed/flanks into measured terrain.

## Remaining work

Physical/canonical mass normalization, both original pressure poles, nonlinear
force closure, a spatially varying inlet, interacting fronts, slope junctions,
open boundaries and native shared-surface integration remain required. Do not
enable the broken nonlinear path or treat this component as resolved energy
conservation. Actual engine motion/reference comparison and 30 FPS qualification
remain open; no new capture, FPS claim or visual improvement is made here.

6300/6350/6400 hydraulic snapshots pass state AND exact dry-bank audits but remain
unsettled and uninstalled. The full South Fork, Colorado, Pacuare, Futaleufu,
Chilko/Zambezi, crew, normalization, regression and release queue remains open.
Troublemaker is still a rapid within South Fork, never a separate scenario.
