# Frame export failure detection

2026-09-24. The interrupted inline-slope comparison exposed a real export gap:
write_frame_csv checked opening but not subsequent writes or final close.
The solver could therefore print validation_passed=true with truncated CSVs.
That message describes the in-memory state, not successful disk persistence.

Frame serialization now checks stream flush, and the file wrapper explicitly
closes and checks the file. Failures throw with the affected path. The command
line calls write_solver_output before printing validation_passed and catches
exceptions with failure exit status. Partial files remain for diagnosis; this
is not transactional output replacement or durability against power loss.

Native tests inject a short write after 128 bytes and a final sync failure
using the production serializer. Successful serialization is also checked.
The initial injection fixture failed to intercept character-at-a-time numeric
writes; all three water tests correctly failed its assertion. The corrected
streambuf intercepts both bulk and individual-character output; the six-test
Release suite passes (7.33 seconds).

Fresh South Fork current-Cartesian input replay: 600 steps, 11 frames, exit 0.
All 11 CSV SHA256 hashes match the pre-change retry's 0-baseline output exactly.
New output: tmp/frame-export-checked-20260924/south_fork_current_cartesian_kernel.
Reference: tmp/solver-inline-slope-cartesian-retry-20260924/0-baseline.
Build/test command: tmp/build-output-failure-20260924.cmd.
The control build directory was rebuilt for this fix; its current binary is
no longer the binary identified by the earlier inline-slope comparison report.

Scope: frame CSV failures only. Probe, cross-section, diagnostic and JSON
writers need a separate persistence audit; this change does not claim all
output paths are fail-closed. No installed game, geometry, physics parameters,
captured evidence or cooked fields changed. South Fork remains unfinished and
first in queue; actual engine visual, motion and performance gates remain open.
