# Milestone 16 Runtime Profile

Schema: `raftsim.milestone16.runtime_profile.v0`

Decision: **PASS**

| Artifact | Mode | Rep | ms/tick | Desktop | VR | Handheld | Replay hash |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| geoclaw_cpp/flat_pool/reduced | reduced | 0 | 0.3017 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/reduced | reduced | 1 | 0.1732 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/finite_volume | finite_volume | 0 | 0.2507 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/finite_volume | finite_volume | 1 | 0.2526 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/uniform_channel/reduced | reduced | 0 | 0.1949 | PASS | PASS | PASS | `6654f124f858` |
| geoclaw_cpp/uniform_channel/reduced | reduced | 1 | 0.1940 | PASS | PASS | PASS | `6654f124f858` |
| geoclaw_cpp/uniform_channel/finite_volume | finite_volume | 0 | 0.2557 | PASS | PASS | PASS | `57b88376e2b0` |
| geoclaw_cpp/uniform_channel/finite_volume | finite_volume | 1 | 0.2667 | PASS | PASS | PASS | `57b88376e2b0` |
| geoclaw_cpp/dam_break/reduced | reduced | 0 | 0.2013 | PASS | PASS | PASS | `80fe5c254357` |
| geoclaw_cpp/dam_break/reduced | reduced | 1 | 0.1982 | PASS | PASS | PASS | `80fe5c254357` |
| geoclaw_cpp/dam_break/finite_volume | finite_volume | 0 | 0.2764 | PASS | PASS | PASS | `a8c17d4d14cc` |
| geoclaw_cpp/dam_break/finite_volume | finite_volume | 1 | 0.2778 | PASS | PASS | PASS | `a8c17d4d14cc` |
| geoclaw_cpp/bed_step/reduced | reduced | 0 | 0.1925 | PASS | PASS | PASS | `c785c35de3a2` |
| geoclaw_cpp/bed_step/reduced | reduced | 1 | 0.1899 | PASS | PASS | PASS | `c785c35de3a2` |
| geoclaw_cpp/bed_step/finite_volume | finite_volume | 0 | 0.2842 | PASS | PASS | PASS | `0c1dd5102349` |
| geoclaw_cpp/bed_step/finite_volume | finite_volume | 1 | 0.2850 | PASS | PASS | PASS | `0c1dd5102349` |
| geoclaw_cpp/wet_dry_shoreline/reduced | reduced | 0 | 0.1690 | PASS | PASS | PASS | `19a9beaf451d` |
| geoclaw_cpp/wet_dry_shoreline/reduced | reduced | 1 | 0.1703 | PASS | PASS | PASS | `19a9beaf451d` |
| geoclaw_cpp/wet_dry_shoreline/finite_volume | finite_volume | 0 | 0.3031 | PASS | PASS | PASS | `6b40d1ce3ab4` |
| geoclaw_cpp/wet_dry_shoreline/finite_volume | finite_volume | 1 | 0.3111 | PASS | PASS | PASS | `6b40d1ce3ab4` |
| geoclaw_cpp/sloping_manning_channel/reduced | reduced | 0 | 0.1846 | PASS | PASS | PASS | `d19f8a9161db` |
| geoclaw_cpp/sloping_manning_channel/reduced | reduced | 1 | 0.1776 | PASS | PASS | PASS | `d19f8a9161db` |
| geoclaw_cpp/sloping_manning_channel/finite_volume | finite_volume | 0 | 0.4617 | PASS | PASS | PASS | `9816ca338c88` |
| geoclaw_cpp/sloping_manning_channel/finite_volume | finite_volume | 1 | 0.2716 | PASS | PASS | PASS | `9816ca338c88` |
| geoclaw_cpp/drop_ledge/finite_volume | finite_volume | 0 | 0.2992 | PASS | PASS | PASS | `052822709f8c` |
| geoclaw_cpp/drop_ledge/finite_volume | finite_volume | 1 | 0.2982 | PASS | PASS | PASS | `052822709f8c` |
| geoclaw_cpp/south_fork_cascading_low_runnable/finite_volume | finite_volume | 0 | 0.8077 | PASS | PASS | PASS | `f1dde4f4d486` |
| geoclaw_cpp/south_fork_cascading_low_runnable/finite_volume | finite_volume | 1 | 0.8373 | PASS | PASS | PASS | `f1dde4f4d486` |
| geoclaw_cpp/south_fork_cascading_median_runnable/finite_volume | finite_volume | 0 | 0.8754 | PASS | PASS | PASS | `51867977a426` |
| geoclaw_cpp/south_fork_cascading_median_runnable/finite_volume | finite_volume | 1 | 1.1206 | PASS | PASS | PASS | `51867977a426` |
| geoclaw_cpp/south_fork_cascading_high_runnable/finite_volume | finite_volume | 0 | 0.9201 | PASS | PASS | PASS | `32e4cef8287f` |
| geoclaw_cpp/south_fork_cascading_high_runnable/finite_volume | finite_volume | 1 | 0.8870 | PASS | PASS | PASS | `32e4cef8287f` |

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
| geoclaw_cpp/wet_dry_shoreline/reduced | PASS | `19a9beaf451d, 19a9beaf451d` |
| geoclaw_cpp/wet_dry_shoreline/finite_volume | PASS | `6b40d1ce3ab4, 6b40d1ce3ab4` |
| geoclaw_cpp/sloping_manning_channel/reduced | PASS | `d19f8a9161db, d19f8a9161db` |
| geoclaw_cpp/sloping_manning_channel/finite_volume | PASS | `9816ca338c88, 9816ca338c88` |
| geoclaw_cpp/drop_ledge/finite_volume | PASS | `052822709f8c, 052822709f8c` |
| geoclaw_cpp/south_fork_cascading_low_runnable/finite_volume | PASS | `f1dde4f4d486, f1dde4f4d486` |
| geoclaw_cpp/south_fork_cascading_median_runnable/finite_volume | PASS | `51867977a426, 51867977a426` |
| geoclaw_cpp/south_fork_cascading_high_runnable/finite_volume | PASS | `32e4cef8287f, 32e4cef8287f` |
