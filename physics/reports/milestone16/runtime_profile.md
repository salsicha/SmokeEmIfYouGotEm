# Milestone 16 Runtime Profile

Schema: `raftsim.milestone16.runtime_profile.v0`

Decision: **PASS**

| Artifact | Mode | Rep | ms/tick | Desktop | VR | Handheld | Replay hash |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| geoclaw_cpp/flat_pool/reduced | reduced | 0 | 0.1840 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/reduced | reduced | 1 | 0.1848 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/finite_volume | finite_volume | 0 | 0.2688 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/finite_volume | finite_volume | 1 | 0.2781 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/uniform_channel/reduced | reduced | 0 | 0.2263 | PASS | PASS | PASS | `6654f124f858` |
| geoclaw_cpp/uniform_channel/reduced | reduced | 1 | 0.2251 | PASS | PASS | PASS | `6654f124f858` |
| geoclaw_cpp/uniform_channel/finite_volume | finite_volume | 0 | 0.4753 | PASS | PASS | PASS | `57b88376e2b0` |
| geoclaw_cpp/uniform_channel/finite_volume | finite_volume | 1 | 0.3779 | PASS | PASS | PASS | `57b88376e2b0` |
| geoclaw_cpp/dam_break/reduced | reduced | 0 | 0.2665 | PASS | PASS | PASS | `80fe5c254357` |
| geoclaw_cpp/dam_break/reduced | reduced | 1 | 0.2570 | PASS | PASS | PASS | `80fe5c254357` |
| geoclaw_cpp/dam_break/finite_volume | finite_volume | 0 | 0.3574 | PASS | PASS | PASS | `a8c17d4d14cc` |
| geoclaw_cpp/dam_break/finite_volume | finite_volume | 1 | 0.3605 | PASS | PASS | PASS | `a8c17d4d14cc` |
| geoclaw_cpp/bed_step/reduced | reduced | 0 | 0.2385 | PASS | PASS | PASS | `c785c35de3a2` |
| geoclaw_cpp/bed_step/reduced | reduced | 1 | 0.2357 | PASS | PASS | PASS | `c785c35de3a2` |
| geoclaw_cpp/bed_step/finite_volume | finite_volume | 0 | 0.3412 | PASS | PASS | PASS | `0c1dd5102349` |
| geoclaw_cpp/bed_step/finite_volume | finite_volume | 1 | 0.3395 | PASS | PASS | PASS | `0c1dd5102349` |
| geoclaw_cpp/constriction/finite_volume | finite_volume | 0 | 0.1809 | PASS | PASS | PASS | `8b00406e0e22` |
| geoclaw_cpp/constriction/finite_volume | finite_volume | 1 | 0.1810 | PASS | PASS | PASS | `8b00406e0e22` |
| geoclaw_cpp/wet_dry_shoreline/reduced | reduced | 0 | 0.2178 | PASS | PASS | PASS | `19a9beaf451d` |
| geoclaw_cpp/wet_dry_shoreline/reduced | reduced | 1 | 0.2093 | PASS | PASS | PASS | `19a9beaf451d` |
| geoclaw_cpp/wet_dry_shoreline/finite_volume | finite_volume | 0 | 0.3698 | PASS | PASS | PASS | `6b40d1ce3ab4` |
| geoclaw_cpp/wet_dry_shoreline/finite_volume | finite_volume | 1 | 0.6161 | PASS | PASS | PASS | `6b40d1ce3ab4` |
| geoclaw_cpp/sloping_manning_channel/reduced | reduced | 0 | 0.2610 | PASS | PASS | PASS | `d19f8a9161db` |
| geoclaw_cpp/sloping_manning_channel/reduced | reduced | 1 | 0.2468 | PASS | PASS | PASS | `d19f8a9161db` |
| geoclaw_cpp/sloping_manning_channel/finite_volume | finite_volume | 0 | 0.3193 | PASS | PASS | PASS | `9816ca338c88` |
| geoclaw_cpp/sloping_manning_channel/finite_volume | finite_volume | 1 | 0.3161 | PASS | PASS | PASS | `9816ca338c88` |
| geoclaw_cpp/drop_ledge/finite_volume | finite_volume | 0 | 0.3429 | PASS | PASS | PASS | `052822709f8c` |
| geoclaw_cpp/drop_ledge/finite_volume | finite_volume | 1 | 0.3295 | PASS | PASS | PASS | `052822709f8c` |
| geoclaw_cpp/south_fork_cascading_low_runnable/finite_volume | finite_volume | 0 | 0.9107 | PASS | PASS | PASS | `f1dde4f4d486` |
| geoclaw_cpp/south_fork_cascading_low_runnable/finite_volume | finite_volume | 1 | 0.8119 | PASS | PASS | PASS | `f1dde4f4d486` |
| geoclaw_cpp/south_fork_cascading_median_runnable/finite_volume | finite_volume | 0 | 0.7509 | PASS | PASS | PASS | `51867977a426` |
| geoclaw_cpp/south_fork_cascading_median_runnable/finite_volume | finite_volume | 1 | 0.7186 | PASS | PASS | PASS | `51867977a426` |
| geoclaw_cpp/south_fork_cascading_high_runnable/finite_volume | finite_volume | 0 | 0.7154 | PASS | PASS | PASS | `32e4cef8287f` |
| geoclaw_cpp/south_fork_cascading_high_runnable/finite_volume | finite_volume | 1 | 0.7183 | PASS | PASS | PASS | `32e4cef8287f` |

## Deterministic Replay

| Artifact | Status | Hashes |
| --- | --- | --- |
| geoclaw_cpp/flat_pool/reduced | PASS | `41fd98410faa, 41fd98410faa` |
| geoclaw_cpp/flat_pool/finite_volume | PASS | `41fd98410faa, 41fd98410faa` |
| geoclaw_cpp/uniform_channel/reduced | PASS | `6654f124f858, 6654f124f858` |
| geoclaw_cpp/uniform_channel/finite_volume | PASS | `57b88376e2b0, 57b88376e2b0` |
| geoclaw_cpp/dam_break/reduced | PASS | `80fe5c254357, 80fe5c254357` |
| geoclaw_cpp/dam_break/finite_volume | PASS | `a8c17d4d14cc, a8c17d4d14cc` |
| geoclaw_cpp/bed_step/reduced | PASS | `c785c35de3a2, c785c35de3a2` |
| geoclaw_cpp/bed_step/finite_volume | PASS | `0c1dd5102349, 0c1dd5102349` |
| geoclaw_cpp/constriction/finite_volume | PASS | `8b00406e0e22, 8b00406e0e22` |
| geoclaw_cpp/wet_dry_shoreline/reduced | PASS | `19a9beaf451d, 19a9beaf451d` |
| geoclaw_cpp/wet_dry_shoreline/finite_volume | PASS | `6b40d1ce3ab4, 6b40d1ce3ab4` |
| geoclaw_cpp/sloping_manning_channel/reduced | PASS | `d19f8a9161db, d19f8a9161db` |
| geoclaw_cpp/sloping_manning_channel/finite_volume | PASS | `9816ca338c88, 9816ca338c88` |
| geoclaw_cpp/drop_ledge/finite_volume | PASS | `052822709f8c, 052822709f8c` |
| geoclaw_cpp/south_fork_cascading_low_runnable/finite_volume | PASS | `f1dde4f4d486, f1dde4f4d486` |
| geoclaw_cpp/south_fork_cascading_median_runnable/finite_volume | PASS | `51867977a426, 51867977a426` |
| geoclaw_cpp/south_fork_cascading_high_runnable/finite_volume | PASS | `32e4cef8287f, 32e4cef8287f` |
