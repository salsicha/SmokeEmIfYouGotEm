# Milestone 16 Runtime Profile

Schema: `raftsim.milestone16.runtime_profile.v0`

Decision: **PASS**

| Artifact | Mode | Rep | ms/tick | Desktop | VR | Handheld | Replay hash |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| geoclaw_cpp/flat_pool/reduced | reduced | 0 | 0.1755 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/reduced | reduced | 1 | 0.4005 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/finite_volume | finite_volume | 0 | 0.3190 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/finite_volume | finite_volume | 1 | 0.2479 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/uniform_channel/finite_volume | finite_volume | 0 | 0.2543 | PASS | PASS | PASS | `57b88376e2b0` |
| geoclaw_cpp/uniform_channel/finite_volume | finite_volume | 1 | 0.2538 | PASS | PASS | PASS | `57b88376e2b0` |
| geoclaw_cpp/wet_dry_shoreline/reduced | reduced | 0 | 0.1519 | PASS | PASS | PASS | `19a9beaf451d` |
| geoclaw_cpp/wet_dry_shoreline/reduced | reduced | 1 | 0.1531 | PASS | PASS | PASS | `19a9beaf451d` |
| geoclaw_cpp/wet_dry_shoreline/finite_volume | finite_volume | 0 | 0.2953 | PASS | PASS | PASS | `6b40d1ce3ab4` |
| geoclaw_cpp/wet_dry_shoreline/finite_volume | finite_volume | 1 | 0.2988 | PASS | PASS | PASS | `6b40d1ce3ab4` |
| geoclaw_cpp/sloping_manning_channel/reduced | reduced | 0 | 0.1812 | PASS | PASS | PASS | `d19f8a9161db` |
| geoclaw_cpp/sloping_manning_channel/reduced | reduced | 1 | 0.1693 | PASS | PASS | PASS | `d19f8a9161db` |
| geoclaw_cpp/sloping_manning_channel/finite_volume | finite_volume | 0 | 0.2842 | PASS | PASS | PASS | `9816ca338c88` |
| geoclaw_cpp/sloping_manning_channel/finite_volume | finite_volume | 1 | 0.2721 | PASS | PASS | PASS | `9816ca338c88` |
| geoclaw_cpp/south_fork_cascading_low_runnable/finite_volume | finite_volume | 0 | 0.7646 | PASS | PASS | PASS | `f1dde4f4d486` |
| geoclaw_cpp/south_fork_cascading_low_runnable/finite_volume | finite_volume | 1 | 0.7715 | PASS | PASS | PASS | `f1dde4f4d486` |
| geoclaw_cpp/south_fork_cascading_median_runnable/finite_volume | finite_volume | 0 | 0.8625 | PASS | PASS | PASS | `51867977a426` |
| geoclaw_cpp/south_fork_cascading_median_runnable/finite_volume | finite_volume | 1 | 0.7987 | PASS | PASS | PASS | `51867977a426` |
| geoclaw_cpp/south_fork_cascading_high_runnable/finite_volume | finite_volume | 0 | 0.7792 | PASS | PASS | PASS | `32e4cef8287f` |
| geoclaw_cpp/south_fork_cascading_high_runnable/finite_volume | finite_volume | 1 | 0.7625 | PASS | PASS | PASS | `32e4cef8287f` |

## Deterministic Replay

| Artifact | Status | Hashes |
| --- | --- | --- |
| geoclaw_cpp/flat_pool/reduced | PASS | `41fd98410faa, 41fd98410faa` |
| geoclaw_cpp/flat_pool/finite_volume | PASS | `41fd98410faa, 41fd98410faa` |
| geoclaw_cpp/uniform_channel/finite_volume | PASS | `57b88376e2b0, 57b88376e2b0` |
| geoclaw_cpp/wet_dry_shoreline/reduced | PASS | `19a9beaf451d, 19a9beaf451d` |
| geoclaw_cpp/wet_dry_shoreline/finite_volume | PASS | `6b40d1ce3ab4, 6b40d1ce3ab4` |
| geoclaw_cpp/sloping_manning_channel/reduced | PASS | `d19f8a9161db, d19f8a9161db` |
| geoclaw_cpp/sloping_manning_channel/finite_volume | PASS | `9816ca338c88, 9816ca338c88` |
| geoclaw_cpp/south_fork_cascading_low_runnable/finite_volume | PASS | `f1dde4f4d486, f1dde4f4d486` |
| geoclaw_cpp/south_fork_cascading_median_runnable/finite_volume | PASS | `51867977a426, 51867977a426` |
| geoclaw_cpp/south_fork_cascading_high_runnable/finite_volume | PASS | `32e4cef8287f, 32e4cef8287f` |
