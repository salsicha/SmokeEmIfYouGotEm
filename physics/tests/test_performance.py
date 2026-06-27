import json

import pytest

from raftsim.performance import build_baseline_performance_report
from raftsim.profiling import ProfiledSolverRun, SolverProfileReport


def test_baseline_performance_report_summarizes_profile_groups(tmp_path):
    coupling = SolverProfileReport(
        "raft_coupling",
        (
            _run("raft_coupling", "scenario_a", 0, 0.10, 0.5),
            _run("raft_coupling", "scenario_b", 0, 0.20, 1.0),
        ),
    )
    export = SolverProfileReport(
        "probe_export",
        (_run("probe_export", "scenario_a", 0, 0.30, 1.5),),
    )

    report = build_baseline_performance_report((coupling, export))
    json_path = report.write_json(tmp_path / "baseline.json")
    markdown_path = report.write_markdown(tmp_path / "baseline.md")
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = markdown_path.read_text(encoding="utf-8")

    assert report.scenario_ids == ("scenario_a", "scenario_b")
    assert len(report.runs) == 3
    assert payload["summaries"][0]["solver"] == "raft_coupling"
    assert payload["summaries"][0]["run_count"] == 2
    assert payload["summaries"][0]["scenario_count"] == 2
    assert payload["summaries"][0]["mean_runtime_seconds"] == pytest.approx(0.15)
    assert "| raft_coupling |" in markdown
    assert "| probe_export |" in markdown


def _run(solver: str, scenario_id: str, repetition: int, runtime: float, seconds_per_sim: float) -> ProfiledSolverRun:
    return ProfiledSolverRun(
        solver=solver,
        scenario_id=scenario_id,
        repetition=repetition,
        grid_cells=64,
        simulated_seconds=0.2,
        output_frames=1,
        runtime_seconds=runtime,
        seconds_per_simulated_second=seconds_per_sim,
        cell_seconds_per_simulated_second=seconds_per_sim / 64,
        validation_passed=True,
        run_status={},
    )
