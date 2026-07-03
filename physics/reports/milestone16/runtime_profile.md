# Milestone 16 Runtime Profile

Schema: `raftsim.milestone16.runtime_profile.v0`

Decision: **PASS**

| Artifact | Mode | Rep | ms/tick | Desktop | VR | Handheld | Replay hash |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| geoclaw_cpp/flat_pool/reduced | reduced | 0 | 0.2730 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/reduced | reduced | 1 | 0.4766 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/finite_volume | finite_volume | 0 | 0.3438 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/finite_volume | finite_volume | 1 | 0.3547 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/uniform_channel/reduced | reduced | 0 | 0.3037 | PASS | PASS | PASS | `6654f124f858` |
| geoclaw_cpp/uniform_channel/reduced | reduced | 1 | 0.2995 | PASS | PASS | PASS | `6654f124f858` |
| geoclaw_cpp/uniform_channel/finite_volume | finite_volume | 0 | 0.3540 | PASS | PASS | PASS | `57b88376e2b0` |
| geoclaw_cpp/uniform_channel/finite_volume | finite_volume | 1 | 0.3559 | PASS | PASS | PASS | `57b88376e2b0` |
| geoclaw_cpp/dam_break/reduced | reduced | 0 | 0.2976 | PASS | PASS | PASS | `80fe5c254357` |
| geoclaw_cpp/dam_break/reduced | reduced | 1 | 0.3066 | PASS | PASS | PASS | `80fe5c254357` |
| geoclaw_cpp/dam_break/finite_volume | finite_volume | 0 | 0.3884 | PASS | PASS | PASS | `a8c17d4d14cc` |
| geoclaw_cpp/dam_break/finite_volume | finite_volume | 1 | 0.3841 | PASS | PASS | PASS | `a8c17d4d14cc` |
| geoclaw_cpp/bed_step/reduced | reduced | 0 | 0.2932 | PASS | PASS | PASS | `c785c35de3a2` |
| geoclaw_cpp/bed_step/reduced | reduced | 1 | 0.2883 | PASS | PASS | PASS | `c785c35de3a2` |
| geoclaw_cpp/bed_step/finite_volume | finite_volume | 0 | 0.3744 | PASS | PASS | PASS | `0c1dd5102349` |
| geoclaw_cpp/bed_step/finite_volume | finite_volume | 1 | 0.3811 | PASS | PASS | PASS | `0c1dd5102349` |
| geoclaw_cpp/constriction/reduced | reduced | 0 | 0.2468 | PASS | PASS | PASS | `8b00406e0e22` |
| geoclaw_cpp/constriction/reduced | reduced | 1 | 0.2434 | PASS | PASS | PASS | `8b00406e0e22` |
| geoclaw_cpp/constriction/finite_volume | finite_volume | 0 | 0.3842 | PASS | PASS | PASS | `8b00406e0e22` |
| geoclaw_cpp/constriction/finite_volume | finite_volume | 1 | 0.3009 | PASS | PASS | PASS | `8b00406e0e22` |
| geoclaw_cpp/wet_dry_shoreline/reduced | reduced | 0 | 0.2844 | PASS | PASS | PASS | `19a9beaf451d` |
| geoclaw_cpp/wet_dry_shoreline/reduced | reduced | 1 | 0.2785 | PASS | PASS | PASS | `19a9beaf451d` |
| geoclaw_cpp/wet_dry_shoreline/finite_volume | finite_volume | 0 | 0.4103 | PASS | PASS | PASS | `6b40d1ce3ab4` |
| geoclaw_cpp/wet_dry_shoreline/finite_volume | finite_volume | 1 | 0.3996 | PASS | PASS | PASS | `6b40d1ce3ab4` |
| geoclaw_cpp/sloping_manning_channel/reduced | reduced | 0 | 0.2858 | PASS | PASS | PASS | `d19f8a9161db` |
| geoclaw_cpp/sloping_manning_channel/reduced | reduced | 1 | 0.2966 | PASS | PASS | PASS | `d19f8a9161db` |
| geoclaw_cpp/sloping_manning_channel/finite_volume | finite_volume | 0 | 0.3719 | PASS | PASS | PASS | `9816ca338c88` |
| geoclaw_cpp/sloping_manning_channel/finite_volume | finite_volume | 1 | 0.3711 | PASS | PASS | PASS | `9816ca338c88` |
| geoclaw_cpp/drop_ledge/reduced | reduced | 0 | 0.2477 | PASS | PASS | PASS | `64acc38547f1` |
| geoclaw_cpp/drop_ledge/reduced | reduced | 1 | 0.2484 | PASS | PASS | PASS | `64acc38547f1` |
| geoclaw_cpp/drop_ledge/finite_volume | finite_volume | 0 | 0.3903 | PASS | PASS | PASS | `052822709f8c` |
| geoclaw_cpp/drop_ledge/finite_volume | finite_volume | 1 | 0.3828 | PASS | PASS | PASS | `052822709f8c` |
| geoclaw_cpp/boulder_garden/reduced | reduced | 0 | 0.6644 | PASS | PASS | PASS | `718dbcc050df` |
| geoclaw_cpp/boulder_garden/reduced | reduced | 1 | 0.8164 | PASS | PASS | PASS | `718dbcc050df` |
| geoclaw_cpp/boulder_garden/finite_volume | finite_volume | 0 | 0.6982 | PASS | PASS | PASS | `718dbcc050df` |
| geoclaw_cpp/boulder_garden/finite_volume | finite_volume | 1 | 0.6778 | PASS | PASS | PASS | `718dbcc050df` |
| geoclaw_cpp/south_fork_cascading_low_runnable/finite_volume | finite_volume | 0 | 0.8503 | PASS | PASS | PASS | `f1dde4f4d486` |
| geoclaw_cpp/south_fork_cascading_low_runnable/finite_volume | finite_volume | 1 | 0.8766 | PASS | PASS | PASS | `f1dde4f4d486` |
| geoclaw_cpp/south_fork_cascading_median_runnable/finite_volume | finite_volume | 0 | 0.8495 | PASS | PASS | PASS | `51867977a426` |
| geoclaw_cpp/south_fork_cascading_median_runnable/finite_volume | finite_volume | 1 | 1.0598 | PASS | PASS | PASS | `51867977a426` |
| geoclaw_cpp/south_fork_cascading_high_runnable/finite_volume | finite_volume | 0 | 0.8559 | PASS | PASS | PASS | `32e4cef8287f` |
| geoclaw_cpp/south_fork_cascading_high_runnable/finite_volume | finite_volume | 1 | 0.8717 | PASS | PASS | PASS | `32e4cef8287f` |

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
| geoclaw_cpp/constriction/reduced | PASS | `8b00406e0e22, 8b00406e0e22` |
| geoclaw_cpp/constriction/finite_volume | PASS | `8b00406e0e22, 8b00406e0e22` |
| geoclaw_cpp/wet_dry_shoreline/reduced | PASS | `19a9beaf451d, 19a9beaf451d` |
| geoclaw_cpp/wet_dry_shoreline/finite_volume | PASS | `6b40d1ce3ab4, 6b40d1ce3ab4` |
| geoclaw_cpp/sloping_manning_channel/reduced | PASS | `d19f8a9161db, d19f8a9161db` |
| geoclaw_cpp/sloping_manning_channel/finite_volume | PASS | `9816ca338c88, 9816ca338c88` |
| geoclaw_cpp/drop_ledge/reduced | PASS | `64acc38547f1, 64acc38547f1` |
| geoclaw_cpp/drop_ledge/finite_volume | PASS | `052822709f8c, 052822709f8c` |
| geoclaw_cpp/boulder_garden/reduced | PASS | `718dbcc050df, 718dbcc050df` |
| geoclaw_cpp/boulder_garden/finite_volume | PASS | `718dbcc050df, 718dbcc050df` |
| geoclaw_cpp/south_fork_cascading_low_runnable/finite_volume | PASS | `f1dde4f4d486, f1dde4f4d486` |
| geoclaw_cpp/south_fork_cascading_median_runnable/finite_volume | PASS | `51867977a426, 51867977a426` |
| geoclaw_cpp/south_fork_cascading_high_runnable/finite_volume | PASS | `32e4cef8287f, 32e4cef8287f` |
