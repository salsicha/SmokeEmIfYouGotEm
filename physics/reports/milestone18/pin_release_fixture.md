# Milestone 18 Pin/Release Fixture

Schema: `raftsim.milestone18.pin_release_fixture.v0`

Decision: **PASS**

Fixture: `midstream_wrap_pin_release`
Obstruction: `midstream_wrap_rock`
Station: `42` m
Lateral offset: `0.85` m
Action window: `0.75` s
Feature forcing scale: `0`

## Proxy Separation

- Excluded proxy families: `['shallow_shelf', 'boulder_impacts']`
- Distinct obstruction geometry: `True`
- Passed: `True`

## Flow Cases

| Flow | Discharge | Depth | Pin force | Side load | Wrap depth | Result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| low_scrape | 38 | 0.48 | 2350 | 1450 | 0.16 | PASS |
| runnable_sticky | 82 | 0.92 | 3825 | 3300 | 0.58 | PASS |
| high_washout | 146 | 1.42 | 2750 | 2600 | 0.24 | PASS |

## Response Paths

### low_scrape

| Path | Outcome | Delay | Pin margin | Release margin | Window margin | Result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| no_action_scrape | scraped_clear | n/a | -850 | -1854 | n/a | PASS |

### runnable_sticky

| Path | Outcome | Delay | Pin margin | Release margin | Window margin | Result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| no_action_pin | pinned | n/a | 625 | -1085 | n/a | PASS |
| timed_high_side_release | released | 0.42 | -184.832 | 3273.38 | 0.33 | PASS |
| late_high_side_failed_rescue | failed_rescue | 1.05 | -184.832 | 3273.38 | -0.3 | PASS |

### high_washout

| Path | Outcome | Delay | Pin margin | Release margin | Window margin | Result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| no_action_washout | flushed_washout | n/a | -450 | -1438 | n/a | PASS |

## Notes

- Feature forcing is recorded but left off for this closure fixture; release behavior comes from flow band, pin load, crew weight distribution, and rescue timing.
- The runnable_sticky band is intentionally the sticky band: low flow scrapes through and high flow washes out.

