# Native prescribed-normal correction recovered

Recorded 2026-09-17 UTC. This closes the remaining selected native SM5 position
regression, not the physical, visual, playable-scene or 30 FPS acceptance gates.
Implementation and exact hardware harness are committed in `5da59d280`.

## Actual native discrepancy

After the compensated-clock correction, 32 of the same 33 native tests passed.
LiquidPrescribedNormalGPU cases 44 and 56 still failed. A separate temporary
diagnostic encoded the output coordinate bits; it was restored before the final
acceptance replay. Actual output Y was `0x4060793d` / `0xc060793d`; the unchanged
oracle requires `0x4060793e` / `0xc060793e`. The former lies outside the prescribed
plane by 5.633705946195278e-9 normal units; one inward representable step gives
a positive residual of 2.1609553169099627e-7. The failure was not log formatting.

The direct-FXC harness uses captured engine-preprocessed DoubleFloat definitions
and the current production function/test kernel. Its rational plane oracle agrees
with the unchanged native CPU oracle for all 65 original positions. Baseline and
IEEE-strict baseline each fail six coordinate words on both hardware and WARP.
A non-FMA product candidate passes all 577 standalone positions per backend but
still fails the same two native cases. Those failures remain recorded, not waived.

The final implementation computes the plane dot residual with portable rounded
products and compensated additions, using the existing integer-arithmetic
helpers. Projection, dominant-axis choice, prescribed travel, exact comparison,
inward next-representable correction and exit-classifier gates are unchanged.
An unrolled version exceeded FXC's code-size/unroll limit; the final three-axis
loop compiles. Its runtime cost is not yet qualified for physical-water playback.

## Final evidence

- Native replay 74430 / editor 21532 is terminal: **33 passed, zero warnings,
  failures, skipped/not-run or in-progress tests**, D3D12 SM5. All 64 shader input
  hashes match its launch witness. No live shader freeze remains.
- Native report `tmp/sm5-prescribed-normal-native-v2-20260917/index.json`, SHA256
  `ec05bd1bf0ff2b6cfb71986fc791f779f24d257d6669b5a387e2d5ee1b1d58b8`.
- Standalone final normal tests: **9 passed** (65 original and 512 seeded
  projected positions on each backend, exact oracle, malformed fixtures and a
  last-output-word negative test). This is bounded physical-scale coverage,
  not exhaustive floating-point/subnormal proof or native compiler reproduction.
- Final normal CSO SHA256
  `9b0fd717e3d55dd3d10228bccd88d8560844f2aaa1302cab9f6a95b340cf427f`.
- Combined normal, clock, transport, pressure, arithmetic and binding suite:
  **69 passed, no skips**, 102.468 seconds. Report
  `tmp/sm5-prescribed-normal-regression-v1-20260917.xml`.

The selected native failures are recovered. The broad nonlinear energy/geometry
regressions, compatible finite-time front physics, normal playable integration,
real-reference motion comparison, sustained frame budget and ordered river/crew/
release work remain separate requirements. Do not enable a known-unaccepted
solver on the strength of these tests.
