# Milestone 19 Chaos-vs-Jolt Comparison

Decision: `blocked_pending_measured_runtime_telemetry`

Do not select Chaos or Jolt for scoring-critical raft/contact/swimmer authority yet. Run the generated Chaos automation fixtures and native Jolt smoke harness, replace placeholder frames with measured telemetry, then regenerate this comparison.

## Dimension Rankings

- `determinism`: insufficient_measured_evidence (determinism_hash_mismatch_count, contact_event_sequence_mismatch_count, outcome_mismatch_count).
- `cpu_cost`: insufficient_measured_evidence (mean_cpu_ms_per_step, p95_cpu_ms_per_step, max_cpu_ms_per_step, telemetry_bytes_per_second).
- `contact_quality`: insufficient_measured_evidence (peak_contact_impulse_n_s, max_bed_penetration_m, scrape_impulse_n_s, pin_duration_seconds).
- `outcome_stability`: insufficient_measured_evidence (bounce_scrape_or_pin_classification, release_or_stick_outcome, flip_or_release_outcome, outcome_mismatch_count).
- `swimmer_state`: insufficient_measured_evidence (ejection_trigger_step, crew_state_sequence, swimmer_position_error_m, time_to_water_contact_seconds).
- `authoring_debug_ergonomics`: insufficient_measured_evidence (debug_overlay_capture, headless_summary, fixture_iteration_time, replay_explainability).

## Fixture Coverage

- Fixture coverage match: `True`.
- Measured evidence available: `False`.
- Authority selection allowed: `False`.
