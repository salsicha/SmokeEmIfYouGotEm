# Parallel-action pressure preconditioning reference

September14 UTC. Original histories and native implementation remain unchanged.
This pass replaces neither physical equations nor captured states; it tests
lower-dependency preconditioners on the actual existing operator and RHS.

## Retained triangular-polynomial failure

`reconstructed_polynomial_sweep_reference.py` uses the fixed truncated inverse
F=I-H+H²-... of the diagonally normalized strict lower triangle, and the paired
inverse preconditioner D^-1/2 F^T F D^-1/2. It is SPD in exact arithmetic, but
that alone does not ensure useful convergence at a bounded polynomial degree.
The0.125m solitary RHS passes at degrees1/2/4/8. The2D variable-bed larger pole
FAILS at all four: residuals0.01043/0.01859/0.02077/0.04244 versus2e-5 required.
This variant is rejected for general use; the1D pass is not substituted for2D.
Report `tmp/south-fork-polynomial-sweep-2d-v1-20260914.json`, SHA256
`3cc390a16a7409998978d0f684d8189eae6eeedbdd81f7ba87e6d2e60ec8946a`.
The failed wrapper exits1 and the full results remain intact.

## Matrix-bounded damped polynomial

`reconstructed_damped_polynomial_reference.py` instead forms the symmetric
S=D^-1/2 A D^-1/2. With beta=max row-sum(|S|) and omega=1/beta, the
exact-arithmetic spectrum of B=I-omega*S lies in[0,1). The inverse preconditioner
is omega*D^-1/2*(I+B+...+B^degree)*D^-1/2, a positive polynomial of S. It has
a fixed number of sparse operations, not a grid-length triangular dependency.
This damping is part of the LINEAR PRECONDITIONER, not water damping, adjusted
forcing or relaxed physics. Original A/RHS,40CG iterations and2e-5 residual
remain unchanged. Actual residuals are measured using the original factored A.

All nonzero tested degrees1/2/4/8 pass for both poles on the solitary,2D-bed and
full ORIGINAL South Fork first-state/boundary-bracket RHS. Degree0 retains the
failing fine-wave Jacobi control. Degree1 larger-pole residuals:

| Source | Original block residual | Damped degree1 residual | Measured solve time |
| --- | ---: | ---: | ---: |
|0.125m solitary|5.44643e-5 (FAIL)|9.11377e-7|6.07ms|
|2D variable bed|6.75226e-6|5.37132e-7|6.76ms|
|Captured South Fork|5.05980e-8|6.05311e-10|74.77ms|

Captured small pole degree1 takes89.41ms, residual2.92882e-16. The captured
scaled sparse matrix stores328032 entries. These timings were taken during
other live work, not a controlled native benchmark. Both are substantially
above the production1.6ms solver budget even before assembly/physics costs.
CPU matrix assembly itself takes roughly33–45ms for degree1. No native-cost,
30FPS, evolving-history or playable pass is implied.

Reports, all terminal exit0:

- `tmp/south-fork-damped-polynomial-solitary-v1-20260914.json`, SHA256
  `d5b5efcc71ffcc0a5b4f9ffc4295182ca78b5ed31399e1ae3af8f2d650a28ee7`.
- `tmp/south-fork-damped-polynomial-2d-v1-20260914.json`, SHA256
  `b3bf6213d5125a16a7072c2942ffd10ed1c16f1b20dc0c9875848c83abb72130`.
- `tmp/south-fork-damped-polynomial-captured-v1-20260914.json`, SHA256
  `3dc62a88babd98657cc66f1e8921ea9731f213b996df75fc3b6ebc082f5caa62`;
  captured session52119 is terminal. Same original sourceSHA0114ce46...bf10,
  actual source clock0.06666667014360428 and original prescribed boundary data.
  The report retains the full source hash, original state/bed hashes and
  implementation inventory. No source resampling or fallback occurred.

Twenty new polynomial tests include explicit dense-matrix and SPD comparisons,
nilpotent complete-sweep equivalence, unchanged fine action, degree validation
and actual2D RHS rejection of the triangular approximation while accepting
the bounded polynomial. Combined relevant suite129 passes in8.05s. These are
double-reference tests, not a finite-precision GPU theorem.

## Completed nonlinear reference histories

Session39791 is now terminal exit0. Report
`tmp/south-fork-reconstructed-solitary-v1-20260914.json`, SHA256
`a17a7ea534af4e02bfbd36114fbc29ee438547cdd79403cf536cb33042e3d5d6`.
All four4s cases completed under the existing pressure gates. Implementation
hashes are unchanged and all four retained `.case-N.npy` state hashes match.
No preconditioner from this pass was installed in those histories.

| Model | dx | Surface L1 discrepancy | Peak ratio | Peak-speed discrepancy |
| --- | ---: | ---: | ---: | ---: |
|Standard SGN|0.5m|0.0371006|0.991109|0.0148487|
|Standard SGN|0.25m|0.00954507|1.000910|0.00272657|
|Rational SGN|0.5m|0.0682495|1.002015|0.0269768|
|Rational SGN|0.25m|0.0463930|1.020194|0.0139541|

Each has481 accepted steps,0 rejections and near-roundoff net momentum change.
The standard-model error decreases about fourfold. Rational-model discrepancy
persists and its peak error grows on refinement: the SGN profile is not an
exact solution of that different model. Completing this comparison is NOT
independent nonlinear physical acceptance of rational SGN or South Fork.

## Next implementation/qualification boundary

Test the fixed-degree preconditioner in an isolated native kernel against
exported original operators/RHS, preserving representability and true-residual
gates. Measure assembly/storage/dispatch costs, not just a small solve. Do not
install the expensive CPU reference or promote research water before original
history, nonlinear/variable-bed/wetting and native/contact/motion qualification.

Main59896 remains live, last accepted0.3163384986s, interval3,6 rejected trials,
step0.00393536s, max speed17.92194m/s, mass residual1.50768e-13m3. This is not
the9.0666671395s/two-move target. Diagnostic95666 remains a separate live prefix.
Cook41820 last observed7666s; latest BOTH audited7600, next COMPLETE7700/local34000
needs BOTH audits. No restart/promotion occurred. Terrain/rapid/crest/froth
coupling, later rivers, crew, release/final commit and30FPS all remain open.
