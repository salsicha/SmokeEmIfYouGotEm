# Milestone 16 Runtime Profile

Schema: `raftsim.milestone16.runtime_profile.v0`

Decision: **PASS**

| Artifact | Mode | Rep | ms/tick | Desktop | VR | Handheld | Replay hash |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| geoclaw_cpp/flat_pool/reduced | reduced | 0 | 0.7445 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/reduced | reduced | 1 | 0.8299 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/finite_volume | finite_volume | 0 | 0.8061 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/finite_volume | finite_volume | 1 | 0.8016 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/uniform_channel/reduced | reduced | 0 | 0.7469 | PASS | PASS | PASS | `6654f124f858` |
| geoclaw_cpp/uniform_channel/reduced | reduced | 1 | 0.7559 | PASS | PASS | PASS | `6654f124f858` |
| geoclaw_cpp/uniform_channel/finite_volume | finite_volume | 0 | 0.8109 | PASS | PASS | PASS | `57b88376e2b0` |
| geoclaw_cpp/uniform_channel/finite_volume | finite_volume | 1 | 0.8101 | PASS | PASS | PASS | `57b88376e2b0` |
| geoclaw_cpp/dam_break/reduced | reduced | 0 | 0.7595 | PASS | PASS | PASS | `80fe5c254357` |
| geoclaw_cpp/dam_break/reduced | reduced | 1 | 0.7611 | PASS | PASS | PASS | `80fe5c254357` |
| geoclaw_cpp/dam_break/finite_volume | finite_volume | 0 | 0.8268 | PASS | PASS | PASS | `a8c17d4d14cc` |
| geoclaw_cpp/dam_break/finite_volume | finite_volume | 1 | 0.8245 | PASS | PASS | PASS | `a8c17d4d14cc` |
| geoclaw_cpp/bed_step/reduced | reduced | 0 | 0.7454 | PASS | PASS | PASS | `c785c35de3a2` |
| geoclaw_cpp/bed_step/reduced | reduced | 1 | 0.7500 | PASS | PASS | PASS | `c785c35de3a2` |
| geoclaw_cpp/bed_step/finite_volume | finite_volume | 0 | 0.8793 | PASS | PASS | PASS | `0c1dd5102349` |
| geoclaw_cpp/bed_step/finite_volume | finite_volume | 1 | 0.8281 | PASS | PASS | PASS | `0c1dd5102349` |
| geoclaw_cpp/constriction/reduced | reduced | 0 | 0.7156 | PASS | PASS | PASS | `8b00406e0e22` |
| geoclaw_cpp/constriction/reduced | reduced | 1 | 0.7035 | PASS | PASS | PASS | `8b00406e0e22` |
| geoclaw_cpp/constriction/finite_volume | finite_volume | 0 | 0.7098 | PASS | PASS | PASS | `8b00406e0e22` |
| geoclaw_cpp/constriction/finite_volume | finite_volume | 1 | 0.7090 | PASS | PASS | PASS | `8b00406e0e22` |
| geoclaw_cpp/wet_dry_shoreline/reduced | reduced | 0 | 0.7297 | PASS | PASS | PASS | `19a9beaf451d` |
| geoclaw_cpp/wet_dry_shoreline/reduced | reduced | 1 | 0.7266 | PASS | PASS | PASS | `19a9beaf451d` |
| geoclaw_cpp/wet_dry_shoreline/finite_volume | finite_volume | 0 | 0.8541 | PASS | PASS | PASS | `6b40d1ce3ab4` |
| geoclaw_cpp/wet_dry_shoreline/finite_volume | finite_volume | 1 | 0.8508 | PASS | PASS | PASS | `6b40d1ce3ab4` |
| geoclaw_cpp/sloping_manning_channel/reduced | reduced | 0 | 0.7504 | PASS | PASS | PASS | `d19f8a9161db` |
| geoclaw_cpp/sloping_manning_channel/reduced | reduced | 1 | 0.7421 | PASS | PASS | PASS | `d19f8a9161db` |
| geoclaw_cpp/sloping_manning_channel/finite_volume | finite_volume | 0 | 0.8107 | PASS | PASS | PASS | `9816ca338c88` |
| geoclaw_cpp/sloping_manning_channel/finite_volume | finite_volume | 1 | 0.8083 | PASS | PASS | PASS | `9816ca338c88` |
| geoclaw_cpp/drop_ledge/reduced | reduced | 0 | 0.7029 | PASS | PASS | PASS | `64acc38547f1` |
| geoclaw_cpp/drop_ledge/reduced | reduced | 1 | 0.7088 | PASS | PASS | PASS | `64acc38547f1` |
| geoclaw_cpp/drop_ledge/finite_volume | finite_volume | 0 | 0.8301 | PASS | PASS | PASS | `052822709f8c` |
| geoclaw_cpp/drop_ledge/finite_volume | finite_volume | 1 | 0.8369 | PASS | PASS | PASS | `052822709f8c` |
| geoclaw_cpp/boulder_garden/reduced | reduced | 0 | 0.9657 | PASS | PASS | PASS | `718dbcc050df` |
| geoclaw_cpp/boulder_garden/reduced | reduced | 1 | 0.9610 | PASS | PASS | PASS | `718dbcc050df` |
| geoclaw_cpp/boulder_garden/finite_volume | finite_volume | 0 | 0.9628 | PASS | PASS | PASS | `718dbcc050df` |
| geoclaw_cpp/boulder_garden/finite_volume | finite_volume | 1 | 0.9578 | PASS | PASS | PASS | `718dbcc050df` |
| geoclaw_cpp/cascading_wave_train/reduced | reduced | 0 | 0.9686 | PASS | PASS | PASS | `fb2dc4d5cfb9` |
| geoclaw_cpp/cascading_wave_train/reduced | reduced | 1 | 0.9694 | PASS | PASS | PASS | `fb2dc4d5cfb9` |
| geoclaw_cpp/cascading_wave_train/finite_volume | finite_volume | 0 | 0.9672 | PASS | PASS | PASS | `fb2dc4d5cfb9` |
| geoclaw_cpp/cascading_wave_train/finite_volume | finite_volume | 1 | 0.9735 | PASS | PASS | PASS | `fb2dc4d5cfb9` |
| geoclaw_cpp/hydraulic_hole_downstream_boil/reduced | reduced | 0 | 0.9665 | PASS | PASS | PASS | `550cd3799d8d` |
| geoclaw_cpp/hydraulic_hole_downstream_boil/reduced | reduced | 1 | 0.9687 | PASS | PASS | PASS | `550cd3799d8d` |
| geoclaw_cpp/hydraulic_hole_downstream_boil/finite_volume | finite_volume | 0 | 0.9613 | PASS | PASS | PASS | `550cd3799d8d` |
| geoclaw_cpp/hydraulic_hole_downstream_boil/finite_volume | finite_volume | 1 | 0.9618 | PASS | PASS | PASS | `550cd3799d8d` |
| geoclaw_cpp/lateral_wave/reduced | reduced | 0 | 0.9670 | PASS | PASS | PASS | `5918bb4fa3a9` |
| geoclaw_cpp/lateral_wave/reduced | reduced | 1 | 0.9680 | PASS | PASS | PASS | `5918bb4fa3a9` |
| geoclaw_cpp/lateral_wave/finite_volume | finite_volume | 0 | 0.9713 | PASS | PASS | PASS | `5918bb4fa3a9` |
| geoclaw_cpp/lateral_wave/finite_volume | finite_volume | 1 | 0.9637 | PASS | PASS | PASS | `5918bb4fa3a9` |
| geoclaw_cpp/eddy_line_shear/reduced | reduced | 0 | 0.9705 | PASS | PASS | PASS | `98bff2647418` |
| geoclaw_cpp/eddy_line_shear/reduced | reduced | 1 | 0.9752 | PASS | PASS | PASS | `98bff2647418` |
| geoclaw_cpp/eddy_line_shear/finite_volume | finite_volume | 0 | 0.9686 | PASS | PASS | PASS | `98bff2647418` |
| geoclaw_cpp/eddy_line_shear/finite_volume | finite_volume | 1 | 0.9771 | PASS | PASS | PASS | `98bff2647418` |
| geoclaw_cpp/shallow_shelf/reduced | reduced | 0 | 0.9718 | PASS | PASS | PASS | `7e0e263b2bf1` |
| geoclaw_cpp/shallow_shelf/reduced | reduced | 1 | 0.9631 | PASS | PASS | PASS | `7e0e263b2bf1` |
| geoclaw_cpp/shallow_shelf/finite_volume | finite_volume | 0 | 0.9713 | PASS | PASS | PASS | `7e0e263b2bf1` |
| geoclaw_cpp/shallow_shelf/finite_volume | finite_volume | 1 | 0.9695 | PASS | PASS | PASS | `7e0e263b2bf1` |
| geoclaw_cpp/south_fork_low_runnable/reduced | reduced | 0 | 0.5940 | PASS | PASS | PASS | `7b52727eb1fd` |
| geoclaw_cpp/south_fork_low_runnable/reduced | reduced | 1 | 0.5901 | PASS | PASS | PASS | `7b52727eb1fd` |
| geoclaw_cpp/south_fork_low_runnable/finite_volume | finite_volume | 0 | 0.5877 | PASS | PASS | PASS | `7b52727eb1fd` |
| geoclaw_cpp/south_fork_low_runnable/finite_volume | finite_volume | 1 | 0.5880 | PASS | PASS | PASS | `7b52727eb1fd` |
| geoclaw_cpp/south_fork_median_runnable/reduced | reduced | 0 | 0.5896 | PASS | PASS | PASS | `e6f430ac6a34` |
| geoclaw_cpp/south_fork_median_runnable/reduced | reduced | 1 | 0.5955 | PASS | PASS | PASS | `e6f430ac6a34` |
| geoclaw_cpp/south_fork_median_runnable/finite_volume | finite_volume | 0 | 0.5862 | PASS | PASS | PASS | `e6f430ac6a34` |
| geoclaw_cpp/south_fork_median_runnable/finite_volume | finite_volume | 1 | 0.5928 | PASS | PASS | PASS | `e6f430ac6a34` |
| geoclaw_cpp/south_fork_high_runnable/reduced | reduced | 0 | 0.5887 | PASS | PASS | PASS | `a8374052c90d` |
| geoclaw_cpp/south_fork_high_runnable/reduced | reduced | 1 | 0.6137 | PASS | PASS | PASS | `a8374052c90d` |
| geoclaw_cpp/south_fork_high_runnable/finite_volume | finite_volume | 0 | 0.5931 | PASS | PASS | PASS | `a8374052c90d` |
| geoclaw_cpp/south_fork_high_runnable/finite_volume | finite_volume | 1 | 0.5863 | PASS | PASS | PASS | `a8374052c90d` |
| geoclaw_cpp/south_fork_cascading_low_runnable/finite_volume | finite_volume | 0 | 1.1281 | PASS | PASS | PASS | `f1dde4f4d486` |
| geoclaw_cpp/south_fork_cascading_low_runnable/finite_volume | finite_volume | 1 | 1.1228 | PASS | PASS | PASS | `f1dde4f4d486` |
| geoclaw_cpp/south_fork_cascading_median_runnable/finite_volume | finite_volume | 0 | 1.1393 | PASS | PASS | PASS | `51867977a426` |
| geoclaw_cpp/south_fork_cascading_median_runnable/finite_volume | finite_volume | 1 | 1.1388 | PASS | PASS | PASS | `51867977a426` |
| geoclaw_cpp/south_fork_cascading_high_runnable/finite_volume | finite_volume | 0 | 1.1397 | PASS | PASS | PASS | `32e4cef8287f` |
| geoclaw_cpp/south_fork_cascading_high_runnable/finite_volume | finite_volume | 1 | 1.1433 | PASS | PASS | PASS | `32e4cef8287f` |

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
| geoclaw_cpp/south_fork_low_runnable/finite_volume | PASS | `7b52727eb1fd, 7b52727eb1fd` |
| geoclaw_cpp/south_fork_median_runnable/reduced | PASS | `e6f430ac6a34, e6f430ac6a34` |
| geoclaw_cpp/south_fork_median_runnable/finite_volume | PASS | `e6f430ac6a34, e6f430ac6a34` |
| geoclaw_cpp/south_fork_high_runnable/reduced | PASS | `a8374052c90d, a8374052c90d` |
| geoclaw_cpp/south_fork_high_runnable/finite_volume | PASS | `a8374052c90d, a8374052c90d` |
| geoclaw_cpp/south_fork_cascading_low_runnable/finite_volume | PASS | `f1dde4f4d486, f1dde4f4d486` |
| geoclaw_cpp/south_fork_cascading_median_runnable/finite_volume | PASS | `51867977a426, 51867977a426` |
| geoclaw_cpp/south_fork_cascading_high_runnable/finite_volume | PASS | `32e4cef8287f, 32e4cef8287f` |
