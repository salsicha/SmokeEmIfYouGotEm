# Reconstructed pressure: independent wave checks

September 14 UTC. Research qualification only. No native solver, terrain, map,
material, saved gameplay state, timestep or live-history dependency changed.

## Instantaneous restoring response

`physics/scripts/audit_reconstructed_wave_response.py` evaluates the actual
original unscaled FV rate with the reconstructed pressure adapter, rather than
manufacturing a right-hand side from the same matrix being checked. The source
is a periodic, zero-velocity cosine surface perturbation of amplitude 1e-5 m
and mean depth 1.5 m. The input remains read-only and unchanged.

The independently evaluated physical response is tanh(kh)/(kh), derived from
the linear gravity-wave dispersion relation omega² = g k tanh(kh).
[MIT marine hydrodynamics lecture 20](https://ocw.mit.edu/courses/2-20-marine-hydrodynamics-13-021-spring-2005/5d48a5937971d973fd8ca90c051a83f8_lecture20.pdf)
provides that relation. This does not establish nonlinear, variable-bed or
wetting physics. The rational model's own continuum response is separately
evaluated with its continued fraction, not imported pole weights.

Relative fundamental restoring-response errors against linear theory:

| Wavelength | 32 cells/wavelength | 64 | 128 |
| --- | ---: | ---: | ---: |
| 2 m | 1.50469% | 0.797414% | 0.619563% |
| 4 m | 0.910053% | 0.234490% | 0.0643505% |
| 12 m | 0.515031% | 0.130743% | 0.0327950% |

Errors against the rational continuum closure decrease approximately fourfold
at each refinement. At 2 m, continuum closure error itself remains about 0.56%
against linear theory: refining this discretization cannot remove model error.
Nonfundamental relative L2 content at 128 cells is 0.2181%, 0.1812%, 0.1872%
respectively; these are not pointwise-exact sinusoidal forces. Reported net
mass/momentum rates remain at roundoff, transverse force is exactly zero.
The audit additionally retains axis-swapped and 1e-6 m amplitude results and
a standard-SGN control, rather than replacing that control with the rational
model's different governing response. These are spatial checks, not motion.

Report: `tmp/south-fork-reconstructed-wave-response-v1-20260914.json`.
SHA256 `d6310e8152a82b065022f34202b776ed9b831ef7c3502fbe0ec2602d6b78b3bf`.
The report stores source hashes; the wrapper completed with exit 0.

## Actual evolution check in progress

`audit_reconstructed_wave_motion.py` starts each 2/4/12 m wave from the linear
travelling-wave initial state and evolves one physical period, 32 cells per
wavelength. It keeps the original FV, pressure, SSP-RK2, 120 Hz maximum step,
CFL/rejection handling and pressure residual gate. Checkpoints inspect actual
accepted times; they do not shorten steps or reset the state. Fourier phase
and amplitude are checked at approximately quarter-period intervals, retaining
the prior Airy audit limits of phase error <0.03 cycles and amplitude ratio
strictly between 0.9 and 1.1. Solver residual must remain below 2e-5.

First session81108 wrote
`tmp/south-fork-reconstructed-wave-motion-v1-20260914.progress.jsonl`, then its
terminal `.json`. At first observation, the 2 m wave reaches 0.2834960703 s:
phase error0.00247949 cycles, amplitude ratio0.99177014, mass residual2.78e-17 m³.
It had132 accepted steps and90 rejected trials. Those retries are retained, not
hidden; that first checkpoint was not a completed-period pass.

Session81108 subsequently reached all three full periods, but exited1 on final
JSON serialization of a NumPy boolean. Its partial `.json` and complete progress
records are retained as failed-wrapper evidence, not a successful final report.
The complete checkpoint records show final phase errors0.00913157/0.00619835/
0.00417757 cycles and amplitude ratios0.990567/0.992046/0.992754 for2/4/12m.
Accepted/rejected step counts are570/445,406/316,411/0. This checks zero-mean-current
linear waves; the prior0.4m/s-current benchmark is not silently closed.

The wrapper now uses explicit Python booleans and serializes before opening
the report. A regression exercises successful serialization with NumPy solver
scalars. No solver/evolution dependency changed. New session27013 is LIVE,
rerunning identical physical inputs into the fresh
`tmp/south-fork-reconstructed-wave-motion-v2-20260914` prefix. Poll that session
for a terminal report before claiming the audit passed. Do not edit this audit
or its hashed dependencies while it runs.

Fourteen new response/motion tests pass, including a stationary-wave and an
overdamped-wave rejection, axis/amplitude checks, source preservation, adapter
cleanup and explicit solver-failure reporting. Combined relevant pressure and
30FPS/release checks:87 pass in3.15s. Tests do not imply a completed live audit.

## Still required

### Corrected motion report completed

Session27013 is now terminal exit0. The v2 report parses, records unchanged
implementation hashes, and reports all three linear-motion checks passed.
SHA256 `5a05edeb62619e6884313dcfac4b7aaf9f644eed938b192a9c962ec734160918`.
All four checkpoints per wavelength pass the original phase/amplitude limits.
Final values match the failed v1 wrapper's retained checkpoints above. This
establishes this zero-current small-wave experiment, not current-wave,
nonlinear, wetting or scene acceptance. Follow the
[current and finite-amplitude checks](normal-river-reconstructed-nonlinear-validation.md).

Complete the current/nonlinear motion runs and original-start requested South Fork history; inspect
failures without source repair. Then independently qualify nonlinear/variable-bed
motion, wetting, open-boundary/outer-wave and foam return coupling, native
agreement and cost, contact and actual playable reference-matched motion.
The latest gameplay18.899245FPS/p9570.33ms remains below the30FPS requirement.
No new gameplay render or video access was claimed in this pass. The full river,
crew, release and final-commit scope remains open.
