# Milestone 16 Runtime Profile

Schema: `raftsim.milestone16.runtime_profile.v0`

Decision: **PASS**

| Artifact | Mode | Rep | ms/tick | Desktop | VR | Handheld | Replay hash |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| geoclaw_cpp/flat_pool/reduced | reduced | 0 | 0.0880 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/reduced | reduced | 1 | 0.0879 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/finite_volume | finite_volume | 0 | 0.1524 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/flat_pool/finite_volume | finite_volume | 1 | 0.1511 | PASS | PASS | PASS | `41fd98410faa` |
| geoclaw_cpp/sloping_manning_channel/reduced | reduced | 0 | 0.0956 | PASS | PASS | PASS | `d19f8a9161db` |
| geoclaw_cpp/sloping_manning_channel/reduced | reduced | 1 | 0.0945 | PASS | PASS | PASS | `d19f8a9161db` |
| geoclaw_cpp/sloping_manning_channel/finite_volume | finite_volume | 0 | 0.1620 | PASS | PASS | PASS | `10e46a565019` |
| geoclaw_cpp/sloping_manning_channel/finite_volume | finite_volume | 1 | 0.1644 | PASS | PASS | PASS | `10e46a565019` |

## Deterministic Replay

| Artifact | Status | Hashes |
| --- | --- | --- |
| geoclaw_cpp/flat_pool/reduced | PASS | `41fd98410faa, 41fd98410faa` |
| geoclaw_cpp/flat_pool/finite_volume | PASS | `41fd98410faa, 41fd98410faa` |
| geoclaw_cpp/sloping_manning_channel/reduced | PASS | `d19f8a9161db, d19f8a9161db` |
| geoclaw_cpp/sloping_manning_channel/finite_volume | PASS | `10e46a565019, 10e46a565019` |
