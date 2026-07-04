# Milestone 16 Runtime Profile

Schema: `raftsim.milestone16.runtime_profile.v0`

Decision: **PASS**

| Artifact | Mode | Rep | ms/tick | Desktop | VR | Handheld | Replay hash |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| geoclaw_cpp/flat_pool/reduced | reduced | 0 | 0.6225 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/reduced | reduced | 1 | 0.5993 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/finite_volume | finite_volume | 0 | 0.6494 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/finite_volume | finite_volume | 1 | 0.6643 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/uniform_channel/reduced | reduced | 0 | 0.6215 | PASS | PASS | PASS | `6654f124f858` |
| geoclaw_cpp/uniform_channel/reduced | reduced | 1 | 0.6488 | PASS | PASS | PASS | `6654f124f858` |
| geoclaw_cpp/uniform_channel/finite_volume | finite_volume | 0 | 0.6930 | PASS | PASS | PASS | `57b88376e2b0` |
| geoclaw_cpp/uniform_channel/finite_volume | finite_volume | 1 | 0.7193 | PASS | PASS | PASS | `57b88376e2b0` |
| geoclaw_cpp/dam_break/reduced | reduced | 0 | 0.6699 | PASS | PASS | PASS | `80fe5c254357` |
| geoclaw_cpp/dam_break/reduced | reduced | 1 | 0.6206 | PASS | PASS | PASS | `80fe5c254357` |
| geoclaw_cpp/dam_break/finite_volume | finite_volume | 0 | 0.6938 | PASS | PASS | PASS | `a8c17d4d14cc` |
| geoclaw_cpp/dam_break/finite_volume | finite_volume | 1 | 0.6887 | PASS | PASS | PASS | `a8c17d4d14cc` |
| geoclaw_cpp/bed_step/reduced | reduced | 0 | 0.6102 | PASS | PASS | PASS | `c785c35de3a2` |
| geoclaw_cpp/bed_step/reduced | reduced | 1 | 0.6303 | PASS | PASS | PASS | `c785c35de3a2` |
| geoclaw_cpp/bed_step/finite_volume | finite_volume | 0 | 0.7380 | PASS | PASS | PASS | `0c1dd5102349` |
| geoclaw_cpp/bed_step/finite_volume | finite_volume | 1 | 0.6964 | PASS | PASS | PASS | `0c1dd5102349` |
| geoclaw_cpp/constriction/reduced | reduced | 0 | 0.5719 | PASS | PASS | PASS | `8b00406e0e22` |
| geoclaw_cpp/constriction/reduced | reduced | 1 | 0.5697 | PASS | PASS | PASS | `8b00406e0e22` |
| geoclaw_cpp/constriction/finite_volume | finite_volume | 0 | 0.5682 | PASS | PASS | PASS | `8b00406e0e22` |
| geoclaw_cpp/constriction/finite_volume | finite_volume | 1 | 0.5686 | PASS | PASS | PASS | `8b00406e0e22` |
| geoclaw_cpp/wet_dry_shoreline/reduced | reduced | 0 | 0.5927 | PASS | PASS | PASS | `19a9beaf451d` |
| geoclaw_cpp/wet_dry_shoreline/reduced | reduced | 1 | 0.5964 | PASS | PASS | PASS | `19a9beaf451d` |
| geoclaw_cpp/wet_dry_shoreline/finite_volume | finite_volume | 0 | 0.7366 | PASS | PASS | PASS | `6b40d1ce3ab4` |
| geoclaw_cpp/wet_dry_shoreline/finite_volume | finite_volume | 1 | 0.7716 | PASS | PASS | PASS | `6b40d1ce3ab4` |
| geoclaw_cpp/sloping_manning_channel/reduced | reduced | 0 | 0.6193 | PASS | PASS | PASS | `d19f8a9161db` |
| geoclaw_cpp/sloping_manning_channel/reduced | reduced | 1 | 0.6056 | PASS | PASS | PASS | `d19f8a9161db` |
| geoclaw_cpp/sloping_manning_channel/finite_volume | finite_volume | 0 | 0.6771 | PASS | PASS | PASS | `9816ca338c88` |
| geoclaw_cpp/sloping_manning_channel/finite_volume | finite_volume | 1 | 0.6745 | PASS | PASS | PASS | `9816ca338c88` |
| geoclaw_cpp/drop_ledge/reduced | reduced | 0 | 0.6151 | PASS | PASS | PASS | `64acc38547f1` |
| geoclaw_cpp/drop_ledge/reduced | reduced | 1 | 0.5952 | PASS | PASS | PASS | `64acc38547f1` |
| geoclaw_cpp/drop_ledge/finite_volume | finite_volume | 0 | 0.6963 | PASS | PASS | PASS | `052822709f8c` |
| geoclaw_cpp/drop_ledge/finite_volume | finite_volume | 1 | 0.6953 | PASS | PASS | PASS | `052822709f8c` |
| geoclaw_cpp/boulder_garden/reduced | reduced | 0 | 0.8603 | PASS | PASS | PASS | `718dbcc050df` |
| geoclaw_cpp/boulder_garden/reduced | reduced | 1 | 0.8600 | PASS | PASS | PASS | `718dbcc050df` |
| geoclaw_cpp/boulder_garden/finite_volume | finite_volume | 0 | 0.8740 | PASS | PASS | PASS | `718dbcc050df` |
| geoclaw_cpp/boulder_garden/finite_volume | finite_volume | 1 | 0.8568 | PASS | PASS | PASS | `718dbcc050df` |
| geoclaw_cpp/cascading_wave_train/reduced | reduced | 0 | 0.8625 | PASS | PASS | PASS | `fb2dc4d5cfb9` |
| geoclaw_cpp/cascading_wave_train/reduced | reduced | 1 | 0.8612 | PASS | PASS | PASS | `fb2dc4d5cfb9` |
| geoclaw_cpp/cascading_wave_train/finite_volume | finite_volume | 0 | 0.8602 | PASS | PASS | PASS | `fb2dc4d5cfb9` |
| geoclaw_cpp/cascading_wave_train/finite_volume | finite_volume | 1 | 0.8729 | PASS | PASS | PASS | `fb2dc4d5cfb9` |
| geoclaw_cpp/hydraulic_hole_downstream_boil/reduced | reduced | 0 | 0.8587 | PASS | PASS | PASS | `550cd3799d8d` |
| geoclaw_cpp/hydraulic_hole_downstream_boil/reduced | reduced | 1 | 0.8668 | PASS | PASS | PASS | `550cd3799d8d` |
| geoclaw_cpp/hydraulic_hole_downstream_boil/finite_volume | finite_volume | 0 | 0.8621 | PASS | PASS | PASS | `550cd3799d8d` |
| geoclaw_cpp/hydraulic_hole_downstream_boil/finite_volume | finite_volume | 1 | 0.8619 | PASS | PASS | PASS | `550cd3799d8d` |
| geoclaw_cpp/lateral_wave/reduced | reduced | 0 | 0.8602 | PASS | PASS | PASS | `5918bb4fa3a9` |
| geoclaw_cpp/lateral_wave/reduced | reduced | 1 | 0.8587 | PASS | PASS | PASS | `5918bb4fa3a9` |
| geoclaw_cpp/lateral_wave/finite_volume | finite_volume | 0 | 0.8573 | PASS | PASS | PASS | `5918bb4fa3a9` |
| geoclaw_cpp/lateral_wave/finite_volume | finite_volume | 1 | 0.8595 | PASS | PASS | PASS | `5918bb4fa3a9` |
| geoclaw_cpp/eddy_line_shear/reduced | reduced | 0 | 0.8662 | PASS | PASS | PASS | `98bff2647418` |
| geoclaw_cpp/eddy_line_shear/reduced | reduced | 1 | 0.8613 | PASS | PASS | PASS | `98bff2647418` |
| geoclaw_cpp/eddy_line_shear/finite_volume | finite_volume | 0 | 0.8674 | PASS | PASS | PASS | `98bff2647418` |
| geoclaw_cpp/eddy_line_shear/finite_volume | finite_volume | 1 | 0.8634 | PASS | PASS | PASS | `98bff2647418` |
| geoclaw_cpp/south_fork_cascading_low_runnable/finite_volume | finite_volume | 0 | 1.0249 | PASS | PASS | PASS | `f1dde4f4d486` |
| geoclaw_cpp/south_fork_cascading_low_runnable/finite_volume | finite_volume | 1 | 1.0278 | PASS | PASS | PASS | `f1dde4f4d486` |
| geoclaw_cpp/south_fork_cascading_median_runnable/finite_volume | finite_volume | 0 | 1.0347 | PASS | PASS | PASS | `51867977a426` |
| geoclaw_cpp/south_fork_cascading_median_runnable/finite_volume | finite_volume | 1 | 1.0356 | PASS | PASS | PASS | `51867977a426` |
| geoclaw_cpp/south_fork_cascading_high_runnable/finite_volume | finite_volume | 0 | 1.0428 | PASS | PASS | PASS | `32e4cef8287f` |
| geoclaw_cpp/south_fork_cascading_high_runnable/finite_volume | finite_volume | 1 | 1.0422 | PASS | PASS | PASS | `32e4cef8287f` |

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
| geoclaw_cpp/south_fork_cascading_low_runnable/finite_volume | PASS | `f1dde4f4d486, f1dde4f4d486` |
| geoclaw_cpp/south_fork_cascading_median_runnable/finite_volume | PASS | `51867977a426, 51867977a426` |
| geoclaw_cpp/south_fork_cascading_high_runnable/finite_volume | PASS | `32e4cef8287f, 32e4cef8287f` |
