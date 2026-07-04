# Milestone 16 Runtime Profile

Schema: `raftsim.milestone16.runtime_profile.v0`

Decision: **PASS**

| Artifact | Mode | Rep | ms/tick | Desktop | VR | Handheld | Replay hash |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| geoclaw_cpp/flat_pool/reduced | reduced | 0 | 0.5178 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/reduced | reduced | 1 | 0.7215 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/finite_volume | finite_volume | 0 | 0.6052 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/finite_volume | finite_volume | 1 | 0.5934 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/uniform_channel/reduced | reduced | 0 | 0.5222 | PASS | PASS | PASS | `6654f124f858` |
| geoclaw_cpp/uniform_channel/reduced | reduced | 1 | 0.5336 | PASS | PASS | PASS | `6654f124f858` |
| geoclaw_cpp/uniform_channel/finite_volume | finite_volume | 0 | 0.6237 | PASS | PASS | PASS | `57b88376e2b0` |
| geoclaw_cpp/uniform_channel/finite_volume | finite_volume | 1 | 0.6006 | PASS | PASS | PASS | `57b88376e2b0` |
| geoclaw_cpp/dam_break/reduced | reduced | 0 | 0.5248 | PASS | PASS | PASS | `80fe5c254357` |
| geoclaw_cpp/dam_break/reduced | reduced | 1 | 0.5257 | PASS | PASS | PASS | `80fe5c254357` |
| geoclaw_cpp/dam_break/finite_volume | finite_volume | 0 | 0.6248 | PASS | PASS | PASS | `a8c17d4d14cc` |
| geoclaw_cpp/dam_break/finite_volume | finite_volume | 1 | 0.7248 | PASS | PASS | PASS | `a8c17d4d14cc` |
| geoclaw_cpp/bed_step/reduced | reduced | 0 | 0.6526 | PASS | PASS | PASS | `c785c35de3a2` |
| geoclaw_cpp/bed_step/reduced | reduced | 1 | 0.5146 | PASS | PASS | PASS | `c785c35de3a2` |
| geoclaw_cpp/bed_step/finite_volume | finite_volume | 0 | 0.6122 | PASS | PASS | PASS | `0c1dd5102349` |
| geoclaw_cpp/bed_step/finite_volume | finite_volume | 1 | 0.6196 | PASS | PASS | PASS | `0c1dd5102349` |
| geoclaw_cpp/constriction/reduced | reduced | 0 | 0.5018 | PASS | PASS | PASS | `8b00406e0e22` |
| geoclaw_cpp/constriction/reduced | reduced | 1 | 0.4955 | PASS | PASS | PASS | `8b00406e0e22` |
| geoclaw_cpp/constriction/finite_volume | finite_volume | 0 | 0.4852 | PASS | PASS | PASS | `8b00406e0e22` |
| geoclaw_cpp/constriction/finite_volume | finite_volume | 1 | 0.4785 | PASS | PASS | PASS | `8b00406e0e22` |
| geoclaw_cpp/wet_dry_shoreline/reduced | reduced | 0 | 0.5048 | PASS | PASS | PASS | `19a9beaf451d` |
| geoclaw_cpp/wet_dry_shoreline/reduced | reduced | 1 | 0.5064 | PASS | PASS | PASS | `19a9beaf451d` |
| geoclaw_cpp/wet_dry_shoreline/finite_volume | finite_volume | 0 | 0.6482 | PASS | PASS | PASS | `6b40d1ce3ab4` |
| geoclaw_cpp/wet_dry_shoreline/finite_volume | finite_volume | 1 | 0.9038 | PASS | PASS | PASS | `6b40d1ce3ab4` |
| geoclaw_cpp/sloping_manning_channel/reduced | reduced | 0 | 0.5475 | PASS | PASS | PASS | `d19f8a9161db` |
| geoclaw_cpp/sloping_manning_channel/reduced | reduced | 1 | 0.5374 | PASS | PASS | PASS | `d19f8a9161db` |
| geoclaw_cpp/sloping_manning_channel/finite_volume | finite_volume | 0 | 0.6058 | PASS | PASS | PASS | `9816ca338c88` |
| geoclaw_cpp/sloping_manning_channel/finite_volume | finite_volume | 1 | 0.5948 | PASS | PASS | PASS | `9816ca338c88` |
| geoclaw_cpp/drop_ledge/reduced | reduced | 0 | 0.4777 | PASS | PASS | PASS | `64acc38547f1` |
| geoclaw_cpp/drop_ledge/reduced | reduced | 1 | 0.4762 | PASS | PASS | PASS | `64acc38547f1` |
| geoclaw_cpp/drop_ledge/finite_volume | finite_volume | 0 | 0.6326 | PASS | PASS | PASS | `052822709f8c` |
| geoclaw_cpp/drop_ledge/finite_volume | finite_volume | 1 | 0.6161 | PASS | PASS | PASS | `052822709f8c` |
| geoclaw_cpp/boulder_garden/reduced | reduced | 0 | 0.8473 | PASS | PASS | PASS | `718dbcc050df` |
| geoclaw_cpp/boulder_garden/reduced | reduced | 1 | 1.0278 | PASS | PASS | PASS | `718dbcc050df` |
| geoclaw_cpp/boulder_garden/finite_volume | finite_volume | 0 | 0.8480 | PASS | PASS | PASS | `718dbcc050df` |
| geoclaw_cpp/boulder_garden/finite_volume | finite_volume | 1 | 0.8479 | PASS | PASS | PASS | `718dbcc050df` |
| geoclaw_cpp/cascading_wave_train/reduced | reduced | 0 | 0.8425 | PASS | PASS | PASS | `fb2dc4d5cfb9` |
| geoclaw_cpp/cascading_wave_train/reduced | reduced | 1 | 0.8498 | PASS | PASS | PASS | `fb2dc4d5cfb9` |
| geoclaw_cpp/cascading_wave_train/finite_volume | finite_volume | 0 | 1.0747 | PASS | PASS | PASS | `fb2dc4d5cfb9` |
| geoclaw_cpp/cascading_wave_train/finite_volume | finite_volume | 1 | 0.8781 | PASS | PASS | PASS | `fb2dc4d5cfb9` |
| geoclaw_cpp/hydraulic_hole_downstream_boil/reduced | reduced | 0 | 0.8542 | PASS | PASS | PASS | `550cd3799d8d` |
| geoclaw_cpp/hydraulic_hole_downstream_boil/reduced | reduced | 1 | 0.8394 | PASS | PASS | PASS | `550cd3799d8d` |
| geoclaw_cpp/hydraulic_hole_downstream_boil/finite_volume | finite_volume | 0 | 0.8591 | PASS | PASS | PASS | `550cd3799d8d` |
| geoclaw_cpp/hydraulic_hole_downstream_boil/finite_volume | finite_volume | 1 | 1.0296 | PASS | PASS | PASS | `550cd3799d8d` |
| geoclaw_cpp/lateral_wave/reduced | reduced | 0 | 0.8616 | PASS | PASS | PASS | `5918bb4fa3a9` |
| geoclaw_cpp/lateral_wave/reduced | reduced | 1 | 0.8413 | PASS | PASS | PASS | `5918bb4fa3a9` |
| geoclaw_cpp/south_fork_cascading_low_runnable/finite_volume | finite_volume | 0 | 1.0748 | PASS | PASS | PASS | `f1dde4f4d486` |
| geoclaw_cpp/south_fork_cascading_low_runnable/finite_volume | finite_volume | 1 | 1.0359 | PASS | PASS | PASS | `f1dde4f4d486` |
| geoclaw_cpp/south_fork_cascading_median_runnable/finite_volume | finite_volume | 0 | 1.2675 | PASS | PASS | PASS | `51867977a426` |
| geoclaw_cpp/south_fork_cascading_median_runnable/finite_volume | finite_volume | 1 | 1.0713 | PASS | PASS | PASS | `51867977a426` |
| geoclaw_cpp/south_fork_cascading_high_runnable/finite_volume | finite_volume | 0 | 1.0668 | PASS | PASS | PASS | `32e4cef8287f` |
| geoclaw_cpp/south_fork_cascading_high_runnable/finite_volume | finite_volume | 1 | 1.0294 | PASS | PASS | PASS | `32e4cef8287f` |

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
| geoclaw_cpp/cascading_wave_train/reduced | PASS | `fb2dc4d5cfb9, fb2dc4d5cfb9` |
| geoclaw_cpp/cascading_wave_train/finite_volume | PASS | `fb2dc4d5cfb9, fb2dc4d5cfb9` |
| geoclaw_cpp/hydraulic_hole_downstream_boil/reduced | PASS | `550cd3799d8d, 550cd3799d8d` |
| geoclaw_cpp/hydraulic_hole_downstream_boil/finite_volume | PASS | `550cd3799d8d, 550cd3799d8d` |
| geoclaw_cpp/lateral_wave/reduced | PASS | `5918bb4fa3a9, 5918bb4fa3a9` |
| geoclaw_cpp/south_fork_cascading_low_runnable/finite_volume | PASS | `f1dde4f4d486, f1dde4f4d486` |
| geoclaw_cpp/south_fork_cascading_median_runnable/finite_volume | PASS | `51867977a426, 51867977a426` |
| geoclaw_cpp/south_fork_cascading_high_runnable/finite_volume | PASS | `32e4cef8287f, 32e4cef8287f` |
