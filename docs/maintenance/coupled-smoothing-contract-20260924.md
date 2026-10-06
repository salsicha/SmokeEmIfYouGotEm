# Coupled smoothing regression contract

The historical Hance source-text test required smoothing to be render-only and
looked for its numeric kernel inside the surface actor. The current architecture
delegates that wrapper to `URaftSimWaterRuntimeAdapter`, also used by raft support.
Reproduced the old test failure before changing it. Restoring render-only behavior
would contradict the requested visible/physical surface consistency.

The source test now checks that delegation, support configuration, adapter kernel
and support call site. It does not declare scene acceptance. An independent
native numeric test exercises162 affine-plane combinations across heights,
slopes, strength clamping and both kernel branches, checking plane preservation
and exact render-wrapper/support-kernel equality. Twenty impulse cases pin the
ordinary .44/.14 and directional .25/.25/.125 spatial responses against analytic
expectations. The existing wet-mask/boundary and four-pass hydraulic preservation
test remains unchanged and is run alongside it.

Verification:

- Editor build succeeds47.18s:
  `tmp/coupled-smoothing-contract-editor-v1-20260924.log`.
- Native kernel and smoothing-elision tests:2 passed,0 failed,0 warnings:
  `tmp/coupled-smoothing-contract-native-v1-20260924/index.json`.
- Entire affected Python module:8 passed,2 failed:
  `tmp/coupled-smoothing-hance-v1-20260924.xml`. The remaining failures are
  `test_hance_v3_terrain_ecology_review_is_hash_locked_and_honest` and
  `test_hance_transmitting_water_v2_review_is_hash_locked_and_honest`.
  Historical artifact hashes/acceptance records were not changed or waived.

This closes one obsolete implementation expectation, not the other source-text
or provenance failures in the material-source-split report. It changes tests
only: no water geometry, production solver, captured data, saved scene or optical
parameter changed. Function-level equality does not establish complete runtime
support/contact equivalence or actual scene motion. No standalone Game rebuild,
new visual delivery, FPS measurement or river acceptance is claimed. South Fork
remains first unfinished; this shared regression work does not advance Colorado
reconstruction ahead of it. Original cook36692 continues alone.
