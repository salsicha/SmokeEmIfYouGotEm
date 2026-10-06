# Total-depth foam transport — September 13

The total-depth CPU reference and GPU finite-volume/RK2 path now transport
nonnegative foam density with the same numerical water-mass face flux. This
closes the previous held-foam gap; it does not enable the new solver in normal
play or qualify breaking-wave appearance.

## Implementation and limits

Each face computes `foam_flux = (water_mass_flux / donor_depth) * donor_foam`.
Both neighboring cells use that same flux with opposite signs. Dividing the
water flux before multiplying foam avoids explicitly overflowing `foam/h` in
thin films. Zero water flux transports exactly zero foam. The CPU optional
foam argument leaves the three hydrodynamic rates and CFL bound bit-identical.

GPU transport stores two face fluxes per cell in one additional 8N-byte buffer;
there is no additional transport dispatch. Both RK stages now update all four
state components. Existing finite/nonnegative-state checks reject invalid
candidates without replacing accepted water, momentum, foam or clock. The
existing CFL and pressure tolerances are unchanged. No depth/velocity cap,
foam clipping, production or decay is introduced.

First-order donor transport conserves total foam on closed/periodic domains.
Under the existing hydrostatic reconstruction and CFL, exact-arithmetic donor
outflow is bounded by the available foam. Represented-state validation remains
necessary; this is not a proof of arbitrary GPU subnormal evolution.

## Verification

Final editor build 18100 succeeded in 13.54 s. Final actual-D3D12 run 82952
closed with exit 0: 74 passes, no warnings, failures or unrun tests, 16.422503 s.
Report: `tmp/south-fork-total-foam-native-v2-20260913/index.json`.
Log: `unreal/Saved/Logs/south-fork-total-foam-native-v2-20260913.log`.
The earlier nine-fixture run 35975 also passed; its evidence is retained.

Final CPU suite 53822 closed with exit 0: 148 tests passed in 31.24 s across
15 transport, pressure, breaking, bank and fixture test files. Coverage includes
closed/periodic first/second-order conservation and positivity, hydrodynamic
passivity, resting foam patches, constant concentration and invalid inputs.
A CPU float64 1e-310 m thin-film stress passes; this is not GPU qualification.

The final step fixture contains ten cases, testing all four state components
against the represented CPU reference. It includes moving foam and an explicit
zero-foam case: transport and pressure cannot manufacture foam from zero.
Repeated accepted/rejected GPU intervals verify foam changes and conservation,
exact rejection retention and bit-exact batched/split state and clock results.
Synthetic foam patterns, including the captured-hydraulics fixture's foam,
are manufactured tests, not observed or calibrated South Fork froth.

Fixture: `tmp/south-fork-total-step-foam-fixtures-v2-20260913.bin`.
SHA256: `ff6bb7543ea7105bc8562aa75bd58e0ecceeede743652ae36d1d09aa956edeff`.
CPU bank SHA256: `bb3f7a630bfe7ddbdf9175ef216da8ed2a5180c0d36a6b3f877441fb40cc7644`.
Transport shader SHA256: `72041184089c2cb67f68ffb4ddc4a312c9ac224d71c6c796623c75798738b78e`.
Step shader SHA256: `6d340f2c40eef0d72ea36419b3d8aef983b0b8b201923f47bf02d098d3657367`.
Final WaterDetail DLL SHA256: `f0ab2d119a5f50423f6463b893cc24556b55bc1fc067c68a08f4743ced1f87b8`.
Final Raft DLL SHA256: `f07c2b63867a4397865a6b9358f0b0e7edf636c1e5e8d4f492bf66e566e0157c`.

## Remaining normal-play work

No new gameplay capture, FPS measurement or reference-video playback this turn.
Latest ordinary-play measurement remains 23.365478 FPS / p95 47.2488 ms: below
the user's 30 FPS / 33.333 ms target. Quality, physics timestep and tolerances
are unchanged. Map, water material and user save hashes remain unchanged.
South Fork remains the scenario; Troublemaker remains a rapid, not a menu item.

Persistent total-state interval ownership, physical open boundaries, conservative
source/window exchange, evolved wetness in render/contact eligibility and
breaking/foam production still need integration and qualification. Smooth
crests and broad soft foam in the latest actual screenshots remain unaccepted.
The historical pressure-surge stability concern is not resolved by passive foam.
No new long pressure replay or whole-solver cost acceptance is claimed.

Cook 96057/PID29104 continued without restart. Complete 3800 s/local 36000
passes both state and artificial-bank audits; all 86,720 artificial-face cells
remain exactly dry. Flow is still settling, so the runtime 600 s field is not
replaced. Next complete checkpoint is 3900 s/local 38000. All remaining scene,
river, crew, performance, release and final-commit work stays active.
