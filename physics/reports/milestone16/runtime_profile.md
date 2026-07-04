# Milestone 16 Runtime Profile

Schema: `raftsim.milestone16.runtime_profile.v0`

Decision: **PASS**

| Artifact | Mode | Rep | ms/tick | Desktop | VR | Handheld | Replay hash |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| geoclaw_cpp/flat_pool/reduced | reduced | 0 | 0.7905 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/reduced | reduced | 1 | 0.7776 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/finite_volume | finite_volume | 0 | 0.8429 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/finite_volume | finite_volume | 1 | 0.8421 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/uniform_channel/reduced | reduced | 0 | 0.7893 | PASS | PASS | PASS | `6654f124f858` |
| geoclaw_cpp/uniform_channel/reduced | reduced | 1 | 0.7847 | PASS | PASS | PASS | `6654f124f858` |
| geoclaw_cpp/uniform_channel/finite_volume | finite_volume | 0 | 0.8467 | PASS | PASS | PASS | `57b88376e2b0` |
| geoclaw_cpp/uniform_channel/finite_volume | finite_volume | 1 | 0.8411 | PASS | PASS | PASS | `57b88376e2b0` |
| geoclaw_cpp/dam_break/reduced | reduced | 0 | 0.7951 | PASS | PASS | PASS | `80fe5c254357` |
| geoclaw_cpp/dam_break/reduced | reduced | 1 | 0.7939 | PASS | PASS | PASS | `80fe5c254357` |
| geoclaw_cpp/dam_break/finite_volume | finite_volume | 0 | 0.8650 | PASS | PASS | PASS | `a8c17d4d14cc` |
| geoclaw_cpp/dam_break/finite_volume | finite_volume | 1 | 0.8649 | PASS | PASS | PASS | `a8c17d4d14cc` |
| geoclaw_cpp/bed_step/reduced | reduced | 0 | 0.7857 | PASS | PASS | PASS | `c785c35de3a2` |
| geoclaw_cpp/bed_step/reduced | reduced | 1 | 0.7820 | PASS | PASS | PASS | `c785c35de3a2` |
| geoclaw_cpp/bed_step/finite_volume | finite_volume | 0 | 0.8708 | PASS | PASS | PASS | `0c1dd5102349` |
| geoclaw_cpp/bed_step/finite_volume | finite_volume | 1 | 0.8716 | PASS | PASS | PASS | `0c1dd5102349` |
| geoclaw_cpp/constriction/reduced | reduced | 0 | 0.7444 | PASS | PASS | PASS | `8b00406e0e22` |
| geoclaw_cpp/constriction/reduced | reduced | 1 | 0.7455 | PASS | PASS | PASS | `8b00406e0e22` |
| geoclaw_cpp/constriction/finite_volume | finite_volume | 0 | 0.7638 | PASS | PASS | PASS | `8b00406e0e22` |
| geoclaw_cpp/constriction/finite_volume | finite_volume | 1 | 0.7417 | PASS | PASS | PASS | `8b00406e0e22` |
| geoclaw_cpp/wet_dry_shoreline/reduced | reduced | 0 | 0.7769 | PASS | PASS | PASS | `19a9beaf451d` |
| geoclaw_cpp/wet_dry_shoreline/reduced | reduced | 1 | 0.7644 | PASS | PASS | PASS | `19a9beaf451d` |
| geoclaw_cpp/wet_dry_shoreline/finite_volume | finite_volume | 0 | 0.8861 | PASS | PASS | PASS | `6b40d1ce3ab4` |
| geoclaw_cpp/wet_dry_shoreline/finite_volume | finite_volume | 1 | 0.8885 | PASS | PASS | PASS | `6b40d1ce3ab4` |
| geoclaw_cpp/sloping_manning_channel/reduced | reduced | 0 | 0.7826 | PASS | PASS | PASS | `d19f8a9161db` |
| geoclaw_cpp/sloping_manning_channel/reduced | reduced | 1 | 0.7889 | PASS | PASS | PASS | `d19f8a9161db` |
| geoclaw_cpp/sloping_manning_channel/finite_volume | finite_volume | 0 | 0.8488 | PASS | PASS | PASS | `9816ca338c88` |
| geoclaw_cpp/sloping_manning_channel/finite_volume | finite_volume | 1 | 0.8483 | PASS | PASS | PASS | `9816ca338c88` |
| geoclaw_cpp/drop_ledge/reduced | reduced | 0 | 0.7389 | PASS | PASS | PASS | `64acc38547f1` |
| geoclaw_cpp/drop_ledge/reduced | reduced | 1 | 0.7425 | PASS | PASS | PASS | `64acc38547f1` |
| geoclaw_cpp/drop_ledge/finite_volume | finite_volume | 0 | 0.8711 | PASS | PASS | PASS | `052822709f8c` |
| geoclaw_cpp/drop_ledge/finite_volume | finite_volume | 1 | 0.8713 | PASS | PASS | PASS | `052822709f8c` |
| geoclaw_cpp/boulder_garden/reduced | reduced | 0 | 0.9884 | PASS | PASS | PASS | `718dbcc050df` |
| geoclaw_cpp/boulder_garden/reduced | reduced | 1 | 1.0045 | PASS | PASS | PASS | `718dbcc050df` |
| geoclaw_cpp/boulder_garden/finite_volume | finite_volume | 0 | 0.9858 | PASS | PASS | PASS | `718dbcc050df` |
| geoclaw_cpp/boulder_garden/finite_volume | finite_volume | 1 | 0.9908 | PASS | PASS | PASS | `718dbcc050df` |
| geoclaw_cpp/cascading_wave_train/reduced | reduced | 0 | 0.9996 | PASS | PASS | PASS | `fb2dc4d5cfb9` |
| geoclaw_cpp/cascading_wave_train/reduced | reduced | 1 | 0.9978 | PASS | PASS | PASS | `fb2dc4d5cfb9` |
| geoclaw_cpp/cascading_wave_train/finite_volume | finite_volume | 0 | 1.0026 | PASS | PASS | PASS | `fb2dc4d5cfb9` |
| geoclaw_cpp/cascading_wave_train/finite_volume | finite_volume | 1 | 1.0007 | PASS | PASS | PASS | `fb2dc4d5cfb9` |
| geoclaw_cpp/hydraulic_hole_downstream_boil/reduced | reduced | 0 | 1.0318 | PASS | PASS | PASS | `550cd3799d8d` |
| geoclaw_cpp/hydraulic_hole_downstream_boil/reduced | reduced | 1 | 0.9979 | PASS | PASS | PASS | `550cd3799d8d` |
| geoclaw_cpp/hydraulic_hole_downstream_boil/finite_volume | finite_volume | 0 | 0.9992 | PASS | PASS | PASS | `550cd3799d8d` |
| geoclaw_cpp/hydraulic_hole_downstream_boil/finite_volume | finite_volume | 1 | 0.9967 | PASS | PASS | PASS | `550cd3799d8d` |
| geoclaw_cpp/lateral_wave/reduced | reduced | 0 | 0.9977 | PASS | PASS | PASS | `5918bb4fa3a9` |
| geoclaw_cpp/lateral_wave/reduced | reduced | 1 | 0.9992 | PASS | PASS | PASS | `5918bb4fa3a9` |
| geoclaw_cpp/lateral_wave/finite_volume | finite_volume | 0 | 0.9903 | PASS | PASS | PASS | `5918bb4fa3a9` |
| geoclaw_cpp/lateral_wave/finite_volume | finite_volume | 1 | 0.9922 | PASS | PASS | PASS | `5918bb4fa3a9` |
| geoclaw_cpp/eddy_line_shear/reduced | reduced | 0 | 0.9939 | PASS | PASS | PASS | `98bff2647418` |
| geoclaw_cpp/eddy_line_shear/reduced | reduced | 1 | 0.9998 | PASS | PASS | PASS | `98bff2647418` |
| geoclaw_cpp/eddy_line_shear/finite_volume | finite_volume | 0 | 0.9984 | PASS | PASS | PASS | `98bff2647418` |
| geoclaw_cpp/eddy_line_shear/finite_volume | finite_volume | 1 | 0.9975 | PASS | PASS | PASS | `98bff2647418` |
| geoclaw_cpp/shallow_shelf/reduced | reduced | 0 | 0.9951 | PASS | PASS | PASS | `7e0e263b2bf1` |
| geoclaw_cpp/shallow_shelf/reduced | reduced | 1 | 0.9950 | PASS | PASS | PASS | `7e0e263b2bf1` |
| geoclaw_cpp/shallow_shelf/finite_volume | finite_volume | 0 | 0.9964 | PASS | PASS | PASS | `7e0e263b2bf1` |
| geoclaw_cpp/shallow_shelf/finite_volume | finite_volume | 1 | 0.9854 | PASS | PASS | PASS | `7e0e263b2bf1` |
| geoclaw_cpp/south_fork_low_runnable/reduced | reduced | 0 | 0.6224 | PASS | PASS | PASS | `7b52727eb1fd` |
| geoclaw_cpp/south_fork_low_runnable/reduced | reduced | 1 | 0.6152 | PASS | PASS | PASS | `7b52727eb1fd` |
| geoclaw_cpp/south_fork_low_runnable/finite_volume | finite_volume | 0 | 0.6206 | PASS | PASS | PASS | `7b52727eb1fd` |
| geoclaw_cpp/south_fork_low_runnable/finite_volume | finite_volume | 1 | 0.6146 | PASS | PASS | PASS | `7b52727eb1fd` |
| geoclaw_cpp/south_fork_median_runnable/reduced | reduced | 0 | 0.6237 | PASS | PASS | PASS | `e6f430ac6a34` |
| geoclaw_cpp/south_fork_median_runnable/reduced | reduced | 1 | 0.6163 | PASS | PASS | PASS | `e6f430ac6a34` |
| geoclaw_cpp/south_fork_median_runnable/finite_volume | finite_volume | 0 | 0.6187 | PASS | PASS | PASS | `e6f430ac6a34` |
| geoclaw_cpp/south_fork_median_runnable/finite_volume | finite_volume | 1 | 0.6218 | PASS | PASS | PASS | `e6f430ac6a34` |
| geoclaw_cpp/south_fork_high_runnable/reduced | reduced | 0 | 0.6383 | PASS | PASS | PASS | `a8374052c90d` |
| geoclaw_cpp/south_fork_high_runnable/reduced | reduced | 1 | 0.6205 | PASS | PASS | PASS | `a8374052c90d` |
| geoclaw_cpp/south_fork_high_runnable/finite_volume | finite_volume | 0 | 0.6194 | PASS | PASS | PASS | `a8374052c90d` |
| geoclaw_cpp/south_fork_high_runnable/finite_volume | finite_volume | 1 | 0.6202 | PASS | PASS | PASS | `a8374052c90d` |
| geoclaw_cpp/south_fork_cascading_low_runnable/reduced | reduced | 0 | 0.7573 | PASS | PASS | PASS | `e54031ec8efe` |
| geoclaw_cpp/south_fork_cascading_low_runnable/reduced | reduced | 1 | 0.7210 | PASS | PASS | PASS | `e54031ec8efe` |
| geoclaw_cpp/south_fork_cascading_low_runnable/finite_volume | finite_volume | 0 | 1.1578 | PASS | PASS | PASS | `f1dde4f4d486` |
| geoclaw_cpp/south_fork_cascading_low_runnable/finite_volume | finite_volume | 1 | 1.1563 | PASS | PASS | PASS | `f1dde4f4d486` |
| geoclaw_cpp/south_fork_cascading_median_runnable/reduced | reduced | 0 | 0.7300 | PASS | PASS | PASS | `639bb9269cc9` |
| geoclaw_cpp/south_fork_cascading_median_runnable/reduced | reduced | 1 | 0.7290 | PASS | PASS | PASS | `639bb9269cc9` |
| geoclaw_cpp/south_fork_cascading_median_runnable/finite_volume | finite_volume | 0 | 1.1670 | PASS | PASS | PASS | `51867977a426` |
| geoclaw_cpp/south_fork_cascading_median_runnable/finite_volume | finite_volume | 1 | 1.1711 | PASS | PASS | PASS | `51867977a426` |
| geoclaw_cpp/south_fork_cascading_high_runnable/finite_volume | finite_volume | 0 | 1.1785 | PASS | PASS | PASS | `32e4cef8287f` |
| geoclaw_cpp/south_fork_cascading_high_runnable/finite_volume | finite_volume | 1 | 1.1780 | PASS | PASS | PASS | `32e4cef8287f` |

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
| geoclaw_cpp/south_fork_cascading_low_runnable/reduced | PASS | `e54031ec8efe, e54031ec8efe` |
| geoclaw_cpp/south_fork_cascading_low_runnable/finite_volume | PASS | `f1dde4f4d486, f1dde4f4d486` |
| geoclaw_cpp/south_fork_cascading_median_runnable/reduced | PASS | `639bb9269cc9, 639bb9269cc9` |
| geoclaw_cpp/south_fork_cascading_median_runnable/finite_volume | PASS | `51867977a426, 51867977a426` |
| geoclaw_cpp/south_fork_cascading_high_runnable/finite_volume | PASS | `32e4cef8287f, 32e4cef8287f` |
