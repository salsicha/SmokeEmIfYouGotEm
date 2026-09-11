# Pointwise terrain-bed outlet integration — in progress

September 10, 2026. South Fork and the full requested queue remain incomplete.

The prior turn identified a false below-bed rejection: the particle was2cm above
the actual triangle mesh but below the bed sampled at a boundary-cell midpoint.
The prepared face curves now enter the native GPU exit plan. The classifier
binary-searches the original triangle-intersection knots at the first actual
crossing. The finite-volume row still supplies stage and signed normal flow.
Invalid origins, wrong routes, first floor/roof intersections, tied corners,
non-outgoing/dry faces, and genuine below-bed hits remain rejected.

The optional exact-bed input must cover all four physical faces, have strictly
increasing finite knots and complete endpoints, and use the validated parent
frame. Legacy small fixtures retain their original row-bed behavior. Dense
reconstruction requires the new pointwise profile. The editor loader checks
parent axes/lower bounds/extents/cells and source mesh/boundary SHA256 hashes
against the contact geometry and actual source bytes, not only labels.

GPU regression now includes a sloping-bed pair: a valid trajectory rejected by
the old row bed becomes approved, and a formerly approved but actually below-bed
trajectory is rejected. Counts and payload remain exact. Malformed coverage,
offsets, duplicate knots and incomplete faces are rejected at construction.
CPU crossing reference supports an independent pointwise terrain callback;
tests also retain incoming/dry/nonfinite rejection. The full-step diagnostic
uses the original barycentric mesh sampler, not the same uploaded knot table.

## Evidence and current process

- Initial build8812 failed on a C++ declaration syntax issue; fixed.
- Build41259 succeeded. `engine-liquid-exact-exit-bed` session65117 is terminal0:
  all13 engine regressions pass, including the sloping-bed pair. One unrelated
  Google generate_204 HTTP timeout warning, no test failures or RHI errors.
- `liquid-native-exact-bed-flow-v1` session92728 terminal exit1 is REJECTED before
  simulation: Windows UE's generic `GetSHA256Signature` asserts that it has no
  implementation. This is a source-validation startup failure, not flow evidence.
- The loader now uses the engine's bundled OpenSSL SHA256, following the same
  desktop dependency used by BuildPatchServices. No validation was removed.
- Build6053 finished successfully (1104.07s). Incremental build38222 succeeded
  (11.12s), compiling the new source-profile test.
- `engine-liquid-face-bed-source`, session50288 terminal0, exposed an extent
  validation bug: `(1/3 * 100) * 24` is799.9999999999999, while the prepared
  height is800cm. The other13 tests passed; this run is not all-green.
- Extent validation now permits only8 double-epsilon relative arithmetic
  roundoff. Source hashes, exact axes/lower/cell counts and float32 knot coverage
  are unchanged. A negative test rejects even a1e-6cm altered extent.
- Build95743 succeeded22.17s. `engine-liquid-face-bed-source-v2`, session79198
  terminal0:14 tests pass,13 clean and1 with an unrelated Google HTTP timeout.
  No test failures or RHI errors. Actual source hashes and malformed-source,
  frame, extent and knot rejection now execute successfully on Windows.
- 301 liquid Python tests pass. No visual/performance acceptance or promotion.

## Dense replay: next physical boundary inconsistency exposed

`liquid-native-exact-bed-flow-v2`, session84596 terminal0, captured120 native
steps/118 commits/6424 stage groups with exact bed installed. It is REJECTED by
`audit_liquid_native_transfer.py`: first failed atomic commit is step30,
control `[0,64,718008,54]`. Later candidate exits are not committed flow. The
capture driver's `complete=true` means readbacks completed, not physics success.

`liquid-native-exact-bed-exit-debug`, session85816 terminal0, retains full step30
and independently samples the original contact triangles. Its first failing
step is also30 (earlier compact commits pass). `exit-diagnosis-v2.json` finds53
approved trajectories and one correctly forbidden crossing:

- Owner7, east physical face, row277, tangent5795.40354cm.
- Particle crosses from station24499.93114cm to24500.10861cm.
- Hit Z506.35536cm, exact terrain409.88318cm:96.47218cm clear of the bed.
- Stage647.81785cm: this is a wet opening, not a terrain collision.
- Prescribed inward velocity is+3.1862347cm/s, but the actual segment moves
  outward0.1774747cm. The non-outgoing condition alone rejects it.

The pointwise bed fix works for the earlier false terrain rejection; this is
a separate discrepancy between prescribed inlet flow and native particle
advection. `InstallRegisteredPressureBoundary` currently sets inlet velocity
only outside the physical domain (virtual grid boundary). Before changing
anything, trace how that ghost velocity reaches physical-face interpolation and
particle advection. Enforce a consistent inlet condition at the physical plane
and audit momentum/volume; do not authorize reverse exits just to pass the gate,
delete rejected water, or flatten the terrain. A proper open-boundary coupling
redesign would also require consistent stage/flux/source accounting, not merely
changing this predicate. All existing river/visual/raft/FPS requirements remain.

No build or Unreal process remains from this pass. No saved map promotion,
commit or push. Next: fix the physical inlet/advection inconsistency, rerun the
original full-density replay, then continue surface/foam/raft/reference/FPS.
