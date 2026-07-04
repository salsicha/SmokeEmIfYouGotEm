# Milestone 16 Runtime Profile

Schema: `raftsim.milestone16.runtime_profile.v0`

Decision: **PASS**

| Artifact | Mode | Rep | ms/tick | Desktop | VR | Handheld | Replay hash |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| geoclaw_cpp/flat_pool/reduced | reduced | 0 | 0.7034 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/reduced | reduced | 1 | 0.6918 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/finite_volume | finite_volume | 0 | 0.7479 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/finite_volume | finite_volume | 1 | 0.7568 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/uniform_channel/reduced | reduced | 0 | 0.7057 | PASS | PASS | PASS | `6654f124f858` |
| geoclaw_cpp/uniform_channel/reduced | reduced | 1 | 0.7053 | PASS | PASS | PASS | `6654f124f858` |
| geoclaw_cpp/uniform_channel/finite_volume | finite_volume | 0 | 0.7627 | PASS | PASS | PASS | `57b88376e2b0` |
| geoclaw_cpp/uniform_channel/finite_volume | finite_volume | 1 | 0.7667 | PASS | PASS | PASS | `57b88376e2b0` |
| geoclaw_cpp/dam_break/reduced | reduced | 0 | 0.7161 | PASS | PASS | PASS | `80fe5c254357` |
| geoclaw_cpp/dam_break/reduced | reduced | 1 | 0.7136 | PASS | PASS | PASS | `80fe5c254357` |
| geoclaw_cpp/dam_break/finite_volume | finite_volume | 0 | 0.7871 | PASS | PASS | PASS | `a8c17d4d14cc` |
| geoclaw_cpp/dam_break/finite_volume | finite_volume | 1 | 0.7789 | PASS | PASS | PASS | `a8c17d4d14cc` |
| geoclaw_cpp/bed_step/reduced | reduced | 0 | 0.7027 | PASS | PASS | PASS | `c785c35de3a2` |
| geoclaw_cpp/bed_step/reduced | reduced | 1 | 0.7006 | PASS | PASS | PASS | `c785c35de3a2` |
| geoclaw_cpp/bed_step/finite_volume | finite_volume | 0 | 0.7816 | PASS | PASS | PASS | `0c1dd5102349` |
| geoclaw_cpp/bed_step/finite_volume | finite_volume | 1 | 0.7791 | PASS | PASS | PASS | `0c1dd5102349` |
| geoclaw_cpp/constriction/reduced | reduced | 0 | 0.6599 | PASS | PASS | PASS | `8b00406e0e22` |
| geoclaw_cpp/constriction/reduced | reduced | 1 | 0.6675 | PASS | PASS | PASS | `8b00406e0e22` |
| geoclaw_cpp/constriction/finite_volume | finite_volume | 0 | 0.6638 | PASS | PASS | PASS | `8b00406e0e22` |
| geoclaw_cpp/constriction/finite_volume | finite_volume | 1 | 0.6603 | PASS | PASS | PASS | `8b00406e0e22` |
| geoclaw_cpp/wet_dry_shoreline/reduced | reduced | 0 | 0.6819 | PASS | PASS | PASS | `19a9beaf451d` |
| geoclaw_cpp/wet_dry_shoreline/reduced | reduced | 1 | 0.6853 | PASS | PASS | PASS | `19a9beaf451d` |
| geoclaw_cpp/wet_dry_shoreline/finite_volume | finite_volume | 0 | 0.8041 | PASS | PASS | PASS | `6b40d1ce3ab4` |
| geoclaw_cpp/wet_dry_shoreline/finite_volume | finite_volume | 1 | 0.8143 | PASS | PASS | PASS | `6b40d1ce3ab4` |
| geoclaw_cpp/sloping_manning_channel/reduced | reduced | 0 | 0.7010 | PASS | PASS | PASS | `d19f8a9161db` |
| geoclaw_cpp/sloping_manning_channel/reduced | reduced | 1 | 0.6994 | PASS | PASS | PASS | `d19f8a9161db` |
| geoclaw_cpp/sloping_manning_channel/finite_volume | finite_volume | 0 | 0.7665 | PASS | PASS | PASS | `9816ca338c88` |
| geoclaw_cpp/sloping_manning_channel/finite_volume | finite_volume | 1 | 0.7641 | PASS | PASS | PASS | `9816ca338c88` |
| geoclaw_cpp/drop_ledge/reduced | reduced | 0 | 0.6558 | PASS | PASS | PASS | `64acc38547f1` |
| geoclaw_cpp/drop_ledge/reduced | reduced | 1 | 0.6565 | PASS | PASS | PASS | `64acc38547f1` |
| geoclaw_cpp/drop_ledge/finite_volume | finite_volume | 0 | 0.7904 | PASS | PASS | PASS | `052822709f8c` |
| geoclaw_cpp/drop_ledge/finite_volume | finite_volume | 1 | 0.7886 | PASS | PASS | PASS | `052822709f8c` |
| geoclaw_cpp/boulder_garden/reduced | reduced | 0 | 0.9355 | PASS | PASS | PASS | `718dbcc050df` |
| geoclaw_cpp/boulder_garden/reduced | reduced | 1 | 0.9437 | PASS | PASS | PASS | `718dbcc050df` |
| geoclaw_cpp/boulder_garden/finite_volume | finite_volume | 0 | 0.9333 | PASS | PASS | PASS | `718dbcc050df` |
| geoclaw_cpp/boulder_garden/finite_volume | finite_volume | 1 | 0.9286 | PASS | PASS | PASS | `718dbcc050df` |
| geoclaw_cpp/cascading_wave_train/reduced | reduced | 0 | 0.9398 | PASS | PASS | PASS | `fb2dc4d5cfb9` |
| geoclaw_cpp/cascading_wave_train/reduced | reduced | 1 | 0.9391 | PASS | PASS | PASS | `fb2dc4d5cfb9` |
| geoclaw_cpp/cascading_wave_train/finite_volume | finite_volume | 0 | 0.9284 | PASS | PASS | PASS | `fb2dc4d5cfb9` |
| geoclaw_cpp/cascading_wave_train/finite_volume | finite_volume | 1 | 0.9381 | PASS | PASS | PASS | `fb2dc4d5cfb9` |
| geoclaw_cpp/hydraulic_hole_downstream_boil/reduced | reduced | 0 | 0.9649 | PASS | PASS | PASS | `550cd3799d8d` |
| geoclaw_cpp/hydraulic_hole_downstream_boil/reduced | reduced | 1 | 0.9366 | PASS | PASS | PASS | `550cd3799d8d` |
| geoclaw_cpp/hydraulic_hole_downstream_boil/finite_volume | finite_volume | 0 | 0.9378 | PASS | PASS | PASS | `550cd3799d8d` |
| geoclaw_cpp/hydraulic_hole_downstream_boil/finite_volume | finite_volume | 1 | 0.9337 | PASS | PASS | PASS | `550cd3799d8d` |
| geoclaw_cpp/lateral_wave/reduced | reduced | 0 | 0.9337 | PASS | PASS | PASS | `5918bb4fa3a9` |
| geoclaw_cpp/lateral_wave/reduced | reduced | 1 | 0.9306 | PASS | PASS | PASS | `5918bb4fa3a9` |
| geoclaw_cpp/lateral_wave/finite_volume | finite_volume | 0 | 0.9373 | PASS | PASS | PASS | `5918bb4fa3a9` |
| geoclaw_cpp/lateral_wave/finite_volume | finite_volume | 1 | 0.9320 | PASS | PASS | PASS | `5918bb4fa3a9` |
| geoclaw_cpp/eddy_line_shear/reduced | reduced | 0 | 0.9349 | PASS | PASS | PASS | `98bff2647418` |
| geoclaw_cpp/eddy_line_shear/reduced | reduced | 1 | 0.9332 | PASS | PASS | PASS | `98bff2647418` |
| geoclaw_cpp/eddy_line_shear/finite_volume | finite_volume | 0 | 0.9308 | PASS | PASS | PASS | `98bff2647418` |
| geoclaw_cpp/eddy_line_shear/finite_volume | finite_volume | 1 | 0.9303 | PASS | PASS | PASS | `98bff2647418` |
| geoclaw_cpp/shallow_shelf/reduced | reduced | 0 | 0.9372 | PASS | PASS | PASS | `7e0e263b2bf1` |
| geoclaw_cpp/shallow_shelf/reduced | reduced | 1 | 0.9305 | PASS | PASS | PASS | `7e0e263b2bf1` |
| geoclaw_cpp/shallow_shelf/finite_volume | finite_volume | 0 | 0.9346 | PASS | PASS | PASS | `7e0e263b2bf1` |
| geoclaw_cpp/shallow_shelf/finite_volume | finite_volume | 1 | 0.9359 | PASS | PASS | PASS | `7e0e263b2bf1` |
| geoclaw_cpp/south_fork_low_runnable/reduced | reduced | 0 | 0.5595 | PASS | PASS | PASS | `7b52727eb1fd` |
| geoclaw_cpp/south_fork_low_runnable/reduced | reduced | 1 | 0.5594 | PASS | PASS | PASS | `7b52727eb1fd` |
| geoclaw_cpp/south_fork_cascading_low_runnable/finite_volume | finite_volume | 0 | 1.0930 | PASS | PASS | PASS | `f1dde4f4d486` |
| geoclaw_cpp/south_fork_cascading_low_runnable/finite_volume | finite_volume | 1 | 1.0997 | PASS | PASS | PASS | `f1dde4f4d486` |
| geoclaw_cpp/south_fork_cascading_median_runnable/finite_volume | finite_volume | 0 | 1.0977 | PASS | PASS | PASS | `51867977a426` |
| geoclaw_cpp/south_fork_cascading_median_runnable/finite_volume | finite_volume | 1 | 1.1040 | PASS | PASS | PASS | `51867977a426` |
| geoclaw_cpp/south_fork_cascading_high_runnable/finite_volume | finite_volume | 0 | 1.1078 | PASS | PASS | PASS | `32e4cef8287f` |
| geoclaw_cpp/south_fork_cascading_high_runnable/finite_volume | finite_volume | 1 | 1.1157 | PASS | PASS | PASS | `32e4cef8287f` |

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
| geoclaw_cpp/lateral_wave/finite_volume | PASS | `5918bb4fa3a9, 5918bb4fa3a9` |
| geoclaw_cpp/eddy_line_shear/reduced | PASS | `98bff2647418, 98bff2647418` |
| geoclaw_cpp/eddy_line_shear/finite_volume | PASS | `98bff2647418, 98bff2647418` |
| geoclaw_cpp/shallow_shelf/reduced | PASS | `7e0e263b2bf1, 7e0e263b2bf1` |
| geoclaw_cpp/shallow_shelf/finite_volume | PASS | `7e0e263b2bf1, 7e0e263b2bf1` |
| geoclaw_cpp/south_fork_low_runnable/reduced | PASS | `7b52727eb1fd, 7b52727eb1fd` |
| geoclaw_cpp/south_fork_cascading_low_runnable/finite_volume | PASS | `f1dde4f4d486, f1dde4f4d486` |
| geoclaw_cpp/south_fork_cascading_median_runnable/finite_volume | PASS | `51867977a426, 51867977a426` |
| geoclaw_cpp/south_fork_cascading_high_runnable/finite_volume | PASS | `32e4cef8287f, 32e4cef8287f` |
