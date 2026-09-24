# Exact fine-profile slot cache: not promoted

September24,2026. Supporting performance experiment; no playable improvement.

Tested per-slot reuse only when the complete existing profile key, exact XY,
and non-boundary eligibility match. Source, boundary, changed profile and reset
invalidate reuse. No evolving hydraulic values, geometry tolerance or timing
cadence was changed. Candidate never supplied the normal staged game.

Editor build142.85s. Native cache test passed under NullRHI, but the existing
ShorelineFineCrest real rendering-proxy assertion failed in that environment.
Retained that failed report; reran with D3D12, assertions unchanged:
`tmp/fine-profile-cache-native-d3d12-20260924/index.json` has2success,
0warnings/failures. Geometry sampled110448 points per crest sign with maximum
error0.491445cm against the unchanged2cm gate.

Normal-menu/FullReach live comparison:64exact paired inputs, alternating
execution order. After including a candidate output copy, reference-first
mean reference/candidate0.156894/0.075041ms; candidate-first0.144707/0.100557ms.
Both groups32pairs. Log `tmp/fine-profile-cache-live-copy-pairs-20260924.log`,
SHA256`d401c854c2228b5619a82e170b5101ead216af85097a8cc1832a3b5484ad154a`.
Earlier no-copy comparison is preserved separately and not the qualification.
Copy-audit build14.18s; explicit whole-frame trial build13.76s.

## Whole-frame comparison

Same editor Game binary, default Boot/menu-handler/FullReach, ephemeral profile,
1280x720 offscreen D3D12. Only candidate flag differs.900post-travel frames each,
strict unmodified CSV audits, rows60..840(781), nonlegacy timing confirmed,
offset1. No concurrent build/cook/test. All four runs exited0. No physical menu
input, visual or full-route collision acceptance is inferred.

| Run | Mean frame ms | p95 ms |
| --- | ---: | ---: |
| Control a |30.308925|40.9239|
| Candidate a |34.799469|42.9898|
| Candidate b |29.660164|39.7146|
| Control b |32.253309|41.4223|

Reports `tmp/fine-profile-cache-{control-a,candidate-a,candidate-b,control-b}-audit-20260924.json`
include exact raw CSV paths/hashes; corresponding run logs omit `-audit`.
Every run fails33.333333ms. First pair loses, reverse pair wins; no repeatable
whole-frame benefit or causal regression conclusion. Do not use the earlier
packaged83.9472ms result as this editor candidate's control.

Candidate implementation, opt-ins and temporary test were removed. Existing
crest source/header restored to their pre-experiment contents; reports remain.
Restoration editor build TERMINAL SUCCESS143.09s, log
`tmp/fine-profile-cache-removal-build-20260924.log`. Existing two C4305
double-to-float warnings in the unchanged D6 Chaos runner remain. The Game
binary/stage never contained this candidate and requires no rollback.
Do not repeat this unchanged cache experiment. South Fork water/geometry and
performance remain unfinished; no default candidate or stage promotion.
