# Milestone 16 Runtime Profile

Schema: `raftsim.milestone16.runtime_profile.v0`

Decision: **PASS**

| Artifact | Mode | Rep | ms/tick | Desktop | VR | Handheld | Replay hash |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| geoclaw_cpp/flat_pool/reduced | reduced | 0 | 0.1754 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/reduced | reduced | 1 | 0.1736 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/finite_volume | finite_volume | 0 | 0.2390 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/finite_volume | finite_volume | 1 | 0.2404 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/uniform_channel/reduced | reduced | 0 | 0.1949 | PASS | PASS | PASS | `6654f124f858` |
| geoclaw_cpp/uniform_channel/reduced | reduced | 1 | 0.1932 | PASS | PASS | PASS | `6654f124f858` |
| geoclaw_cpp/uniform_channel/finite_volume | finite_volume | 0 | 0.2540 | PASS | PASS | PASS | `57b88376e2b0` |
| geoclaw_cpp/uniform_channel/finite_volume | finite_volume | 1 | 0.2547 | PASS | PASS | PASS | `57b88376e2b0` |
| geoclaw_cpp/dam_break/reduced | reduced | 0 | 0.2011 | PASS | PASS | PASS | `80fe5c254357` |
| geoclaw_cpp/dam_break/reduced | reduced | 1 | 0.2127 | PASS | PASS | PASS | `80fe5c254357` |
| geoclaw_cpp/dam_break/finite_volume | finite_volume | 0 | 0.2828 | PASS | PASS | PASS | `a8c17d4d14cc` |
| geoclaw_cpp/dam_break/finite_volume | finite_volume | 1 | 0.4865 | PASS | PASS | PASS | `a8c17d4d14cc` |
| geoclaw_cpp/bed_step/finite_volume | finite_volume | 0 | 0.2864 | PASS | PASS | PASS | `0c1dd5102349` |
| geoclaw_cpp/bed_step/finite_volume | finite_volume | 1 | 0.2954 | PASS | PASS | PASS | `0c1dd5102349` |
| geoclaw_cpp/wet_dry_shoreline/reduced | reduced | 0 | 0.1751 | PASS | PASS | PASS | `19a9beaf451d` |
| geoclaw_cpp/wet_dry_shoreline/reduced | reduced | 1 | 0.1753 | PASS | PASS | PASS | `19a9beaf451d` |
| geoclaw_cpp/wet_dry_shoreline/finite_volume | finite_volume | 0 | 0.3130 | PASS | PASS | PASS | `6b40d1ce3ab4` |
| geoclaw_cpp/wet_dry_shoreline/finite_volume | finite_volume | 1 | 0.3143 | PASS | PASS | PASS | `6b40d1ce3ab4` |
| geoclaw_cpp/sloping_manning_channel/reduced | reduced | 0 | 0.1848 | PASS | PASS | PASS | `d19f8a9161db` |
| geoclaw_cpp/sloping_manning_channel/reduced | reduced | 1 | 0.1843 | PASS | PASS | PASS | `d19f8a9161db` |
| geoclaw_cpp/sloping_manning_channel/finite_volume | finite_volume | 0 | 0.2677 | PASS | PASS | PASS | `9816ca338c88` |
| geoclaw_cpp/sloping_manning_channel/finite_volume | finite_volume | 1 | 0.2634 | PASS | PASS | PASS | `9816ca338c88` |
| geoclaw_cpp/drop_ledge/finite_volume | finite_volume | 0 | 0.2893 | PASS | PASS | PASS | `052822709f8c` |
| geoclaw_cpp/drop_ledge/finite_volume | finite_volume | 1 | 0.3032 | PASS | PASS | PASS | `052822709f8c` |
| geoclaw_cpp/south_fork_cascading_low_runnable/finite_volume | finite_volume | 0 | 0.7879 | PASS | PASS | PASS | `f1dde4f4d486` |
| geoclaw_cpp/south_fork_cascading_low_runnable/finite_volume | finite_volume | 1 | 0.7928 | PASS | PASS | PASS | `f1dde4f4d486` |
| geoclaw_cpp/south_fork_cascading_median_runnable/finite_volume | finite_volume | 0 | 0.9347 | PASS | PASS | PASS | `51867977a426` |
| geoclaw_cpp/south_fork_cascading_median_runnable/finite_volume | finite_volume | 1 | 0.7822 | PASS | PASS | PASS | `51867977a426` |
| geoclaw_cpp/south_fork_cascading_high_runnable/finite_volume | finite_volume | 0 | 0.8063 | PASS | PASS | PASS | `32e4cef8287f` |
| geoclaw_cpp/south_fork_cascading_high_runnable/finite_volume | finite_volume | 1 | 0.7924 | PASS | PASS | PASS | `32e4cef8287f` |

## Deterministic Replay

| Artifact | Status | Hashes |
| --- | --- | --- |
| geoclaw_cpp/flat_pool/reduced | PASS | `41fd98410faa, 41fd98410faa` |
| geoclaw_cpp/flat_pool/finite_volume | PASS | `41fd98410faa, 41fd98410faa` |
| geoclaw_cpp/uniform_channel/reduced | PASS | `6654f124f858, 6654f124f858` |
| geoclaw_cpp/uniform_channel/finite_volume | PASS | `57b88376e2b0, 57b88376e2b0` |
| geoclaw_cpp/dam_break/reduced | PASS | `80fe5c254357, 80fe5c254357` |
| geoclaw_cpp/dam_break/finite_volume | PASS | `a8c17d4d14cc, a8c17d4d14cc` |
| geoclaw_cpp/bed_step/finite_volume | PASS | `0c1dd5102349, 0c1dd5102349` |
| geoclaw_cpp/wet_dry_shoreline/reduced | PASS | `19a9beaf451d, 19a9beaf451d` |
| geoclaw_cpp/wet_dry_shoreline/finite_volume | PASS | `6b40d1ce3ab4, 6b40d1ce3ab4` |
| geoclaw_cpp/sloping_manning_channel/reduced | PASS | `d19f8a9161db, d19f8a9161db` |
| geoclaw_cpp/sloping_manning_channel/finite_volume | PASS | `9816ca338c88, 9816ca338c88` |
| geoclaw_cpp/drop_ledge/finite_volume | PASS | `052822709f8c, 052822709f8c` |
| geoclaw_cpp/south_fork_cascading_low_runnable/finite_volume | PASS | `f1dde4f4d486, f1dde4f4d486` |
| geoclaw_cpp/south_fork_cascading_median_runnable/finite_volume | PASS | `51867977a426, 51867977a426` |
| geoclaw_cpp/south_fork_cascading_high_runnable/finite_volume | PASS | `32e4cef8287f, 32e4cef8287f` |
