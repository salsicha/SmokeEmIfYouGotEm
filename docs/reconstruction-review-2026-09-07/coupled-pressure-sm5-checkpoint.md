# Standalone coupled SM5 pressure diagnostic checkpoint

Recorded 2026-09-17 UTC. This is a diagnostic checkpoint, not a production
physics fix, completed scenario, or release acceptance.

## Source changes

The standalone transport runner now shares its reflected D3D11 dispatch
utilities with a pressure runner. Coupled mode feeds actual transport GPU
buffers directly into the production pressure and fused PCG40 phases. CPU
expected force remains an oracle, never a pressure input. Original force,
diagnostic, iteration and true-residual gates remain enforced. Phase counts
and an order checksum reject missing or reordered work, including resting
fixtures. Optional fresh-directory traces preserve intermediate buffers.

The new tests exercise both hardware and WARP against all 18 original
unscaled fixtures, plus rejection of altered expected force, invalid fraction,
swapped phases and missing bytecode. Unconfigured hosts explicitly skip.

## Results and unresolved failure

The existing transport tests pass all 13 checks. The initial coupled test
run passes five tests and fails the full hardware fixture test. WARP passes
all 18 cases; hardware fails moving cases 2-7 and 16-17 despite matching
phase tags and zero invalid-data diagnostics. The true-residual and force
checks correctly reject these results. No tolerance was relaxed or failure
marked as an expected pass.

Pre-commit verification rebuilt the current C++ sources successfully and ran
both test files together: **18 passed, 1 failed** in 92.39 seconds. The sole
failure remains the full hardware coupled fixture. Report:
`tmp/sm5-coupled-pressure-commit-check-20260917.xml`.

Case 2 hardware/WARP traces are bit-identical through pressure assembly,
PCG initialization and the first acceleration phase 5. The first divergence
is phase 6: hardware leaves Scratch zero and Partial unchanged, while WARP
writes both. Phase tags still match. This localizes the observation but does
not yet establish its cause. A local read-only Control SRV variant produces
the same failure and is not adopted. Production shaders and installed
modules are unchanged by this checkpoint.

The original engine replay has now terminated: **1 passed, 28 failed**,
despite engine exit code zero. Only RepresentedFloatArithmeticGPU passed.
The replay's shader inputs remained frozen through completion; that freeze
has ended. The separately qualified local dyadic-return correction is still
unapplied and requires subsequent integration and native qualification.

## Evidence retained locally, excluded from Git

- `tmp/sm5-coupled-pressure-tests-v1-20260917.xml`: five passed, one failed.
- `tmp/sm5-coupled-transport-regression-v1-20260917.xml`: 13 passed.
- `tmp/sm5-coupled-pressure-shaders-v1-20260917/`: original compiled pressure phases.
- `tmp/coupled-pressure-trace-hardware-v1-20260917/` and
  `tmp/coupled-pressure-trace-warp-v1-20260917/`: intermediate case 2 buffers.
- `tmp/sm5-integer-return-native-v1-20260917/index.json`: terminal engine report,
  SHA-256 `0046cecd5a4162204779d17e44be55d69f3458123da687916be365097a7ce203`.

The repository already ignores `/tmp/`, Unreal build/cache/saved directories,
Python caches and logs. No generated binaries, bytecode or bulk traces are
included in the commit; no additional ignore rule is needed for these files.

## Remaining acceptance

Next isolate phase 6 with captured inputs, resolve and qualify the actual
hardware failure, then rerun native coupled/full-step tests. No diagnostic
pass substitutes for wet-front physics, visible breaking waves and froth,
terrain/boulder/collision consistency, or normal playable integration.
Last ordinary performance remains 28.057157 FPS / p95 41.2354 ms, failing
the 30 FPS target. Troublemaker remains a rapid within South Fork, not a menu
scenario. Later rivers, crew and release work remain open.
