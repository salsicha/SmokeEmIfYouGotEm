# Inline slope reset: not promoted

2026-09-24. Supporting South Fork performance investigation, not a delivered
playable change or river acceptance.

The candidate moves the six MUSCL slope resets from a serial array fill into
each reconstruction worker before dry-cell early exit. Both isolated Release
builds passed all six native tests. Normal build behavior is unchanged unless
RAFTSIM_INLINE_SLOPE_RESET=1 is explicitly compiled.

The initial four-pair comparison ran out of disk space. Its report is empty
and later CSV exports are incomplete; it is invalid. Exactly 37 SHA256-matching
duplicate CSVs were removed, recoverable from its retained 0-baseline frames.
Logs, incomplete differing exports and captured source data remain intact.
Recovery details: tmp/solver-inline-slope-cartesian-pairs-20260924/recovery.md.

A fresh four-pair, 600-step alternating-order retry completed with all eight
processes successful and every saved frame bitwise identical:

| Pair | Baseline solve/capture seconds | Candidate seconds |
| --- | ---: | ---: |
| 0 | 1.10136 | 1.13332 |
| 1 | 1.15557 | 1.18531 |
| 2 | 1.20148 | 1.12499 |
| 3 | 1.21324 | 1.16772 |

Median solve/capture improves 2.376%, but two pairs regress and two improve.
Whole-process median improves only 0.164%. This does not establish a repeatable
engine-frame benefit. Do not promote or repeat this unchanged candidate.
No engine rebuild, installed executable, cooked field, geometry or water
setting changed. South Fork remains first and unfinished; the latest existing
normal-play p95 is 41.6848ms, failing the 33.333333ms requirement.

Raw retry: tmp/solver-inline-slope-cartesian-retry-20260924/report.json;
SHA256 59bc46763ddcafe07529f773b2532856fa007634883f10f8afb4af63a2f112b0.

Cleanup limitation: attempts to remove the two macro-gated source edits with
apply_patch failed with 'Failed to write file', including an escalated direct
patch executable attempt. Source files were checked intact, not truncated.
The experiment remains disabled by default in solver_runtime.cpp and
solver_stage_scratch.hpp. Remove only those inline-reset hunks when write
access is restored; preserve all unrelated working-tree changes.
