# Frozen-current froth departure experiment — 2026-09-17

Status: diagnostic, opt-in only. Not visual, physical, performance or release
acceptance. The installed gameplay DLL and production water material were not
replaced. Troublemaker remains a rapid within South Fork, not a menu scenario.

## Change and limits

The review material integrates optical departures with eight midpoint steps
through one frozen, paired current texture instead of a straight local-current
backtrace. It uses the existing single water carrier, coverage, phase weights
and cell scales. Filtering follows the deformed coordinates. No geometry,
collision, displacement, normals, foam production or density changes are made.
Dry/outside paths fall back to the existing optical behavior. This is not
historical fluid advection or physical foam transport.

The non-shipping actor switch requires the South Fork FullReach map and both
`-RaftSimEphemeralProfile` and `-RaftSimFrothDepartureReview`. Generate the local
V2 review asset with `create_south_fork_froth_departure_review.py`; it is ignored
by Git. Normal gameplay does not select it.

## Numerical evidence

Three complete original native snapshots were audited. At 0.75 seconds, using
the same supported foamy cohort for every method:

| Snapshot | Common foamy rows | Straight RMS (m) | Midpoint-8 RMS (m) |
| --- | ---: | ---: | ---: |
| 00 | 2526 | 0.399043 | 0.003799 |
| 01 | 2988 | 0.370247 | 0.003474 |
| 02 | 3766 | 0.325025 | 0.003059 |

The frozen-field reference refined to 256 RK4 steps at this duration, keeping
the original 0.1 mm convergence gate and stable support. Unsupported rows remain
explicit nulls; source hashes and individual/common cohorts are retained in
`tmp/froth-characteristics-source{00,01,02}-v3-20260917.json`.
These errors do not measure actual river flow or material-pixel motion.

Focused validation: 28 tests passed, no skips, including actual production
candidate HLSL on D3D11 hardware and WARP (17 variants, 2448 checked words per
backend). Affine controls test analytic convergence and registration/fallback
guards; they are not nonlinear-grid physical validation. V2 engine build and
material creation succeeded. Independent V2 commandlet reload exited zero with
zero errors and four engine warnings; protected graphs and parent hash matched.

## Playable capture and performance

Reference and candidate V2 recordings each produced 24 PNGs and a complete
decoded movie (467 and 469 encoded frames). Inspected original frame 22 from
both runs and candidate decoded 6/11-second frames still showed broad, smooth
whitewater and a sharp foreground face. Convincing localized breaking/froth
was not established. Different trajectories prevent an exact pixel comparison;
complete decoding is not equivalent to inspecting every frame.

Separate recording-free 300-frame D3D12 runs used the same candidate DLL and
1280x720 resolution. Unchanged inclusive CSV rows 60–240 gave:

| Material | Mean FPS | Mean frame (ms) | p95 frame (ms) |
| --- | ---: | ---: | ---: |
| Reference | 29.044752 | 34.429628 | 39.4775 |
| Candidate | 28.674556 | 34.874123 | 39.2346 |

Both fail 30 FPS / p95 <=33.333333 ms. This short sequential pair proves neither
a repeatable speed benefit nor absence of overhead. These are not new ordinary
installed-build results. Frame evidence is in
`tmp/froth-departure-frame-cost-v2-20260917.json`; capture labels are
`south-fork-froth-departure-{reference,candidate}-v2-20260917` and performance
labels add `-perf` before `-v2`.

## Retained failures and next work

The first reference-convergence attempt failed and was refined, not waived.
The initial standalone compiler setup lacked the Windows SDK WinRT include;
the include configuration was corrected. Two V1 editor reloads wrote passing
audit reports but then exited abnormally; they are not clean process passes.
V2 uses an independently successful commandlet reload. Optional engine Python
initialization errors remain in gameplay logs; no zero-error gameplay claim.

Do not promote this experiment on numerical backtrace evidence alone. Physical
breaking, the mean water face, time-dependent foam transport, sustained 30 FPS,
and the remaining scenario/crew/release gates remain open. Generated binaries,
captures, snapshots, local review assets and test reports stay ignored; source,
reproducible tests and this review record belong in Git.
