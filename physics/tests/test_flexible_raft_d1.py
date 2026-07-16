import json
import math
from pathlib import Path

import pytest

from raftsim.flexible_raft_d1 import (
    D1_COMPLIANT_TUBE_FIXTURE_RELATIVE_PATH,
    D1_COMPLIANT_TUBE_SCHEMA,
    TubeLoadD1,
    build_compliant_tube_d1_fixture,
    build_default_compliant_tube_layout_d1,
    solve_compliant_tube_d1,
    solve_compliant_tube_on_rigid_state_d1,
)
from raftsim.math3d import Quaternion, Vec3
from raftsim.raft_coupling2_5d import RaftState6DoF
from raftsim.scenario2_5d import RaftParameters2_5D


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_compliant_tube_d1_fixture_is_reproducible():
    generated = build_compliant_tube_d1_fixture()
    committed = json.loads(
        (REPO_ROOT / D1_COMPLIANT_TUBE_FIXTURE_RELATIVE_PATH).read_text(encoding="utf-8")
    )

    assert generated == committed
    assert committed["schema"] == D1_COMPLIANT_TUBE_SCHEMA
    assert committed["scoring_authority_enabled"] is False
    assert committed["model_contract"]["gameplay_scoring_authority"].startswith("disabled")


def test_default_compliant_tube_layout_forms_closed_perimeter():
    layout = build_default_compliant_tube_layout_d1(
        RaftParameters2_5D(length_m=4.2, width_m=1.8, tube_radius_m=0.28)
    )

    assert len(layout) == 12
    assert len({segment.segment_id for segment in layout}) == len(layout)
    assert layout[0].segment_id == "port_0"
    assert layout[-1].segment_id == "stern_0"
    assert all(segment.outward_normal.magnitude == pytest.approx(1.0) for segment in layout)
    assert all(segment.floor_coupling_fraction > 0.0 for segment in layout)
    assert all(segment.lacing_coupling_fraction > 0.0 for segment in layout)
    assert all(segment.frame_coupling_fraction > 0.0 for segment in layout)


def test_uniform_download_preserves_balance_and_load():
    layout = build_default_compliant_tube_layout_d1()
    loads = tuple(
        TubeLoadD1(
            load_id=f"uniform_{segment.segment_id}",
            local_position=segment.local_position,
            force_n=100.0,
        )
        for segment in layout
    )

    solve = solve_compliant_tube_d1(layout, loads)

    assert solve.scoring_authority_enabled is False
    assert solve.total_applied_load_n == pytest.approx(1_200.0)
    assert solve.total_effective_tube_load_n == pytest.approx(solve.total_applied_load_n)
    assert solve.roll_load_bias_nm == pytest.approx(0.0, abs=1.0e-9)
    assert solve.pitch_load_bias_nm == pytest.approx(0.0, abs=1.0e-9)
    assert solve.bounded_segment_count == 0


def test_compliant_tube_d1_layers_on_rigid_raft_state_transform():
    layout = build_default_compliant_tube_layout_d1()
    state = RaftState6DoF(
        position=Vec3(10.0, 2.0, 1.0),
        orientation=Quaternion.from_axis_angle(Vec3(0.0, 0.0, 1.0), math.pi * 0.5),
    )
    loads = (
        TubeLoadD1(
            load_id="port_load",
            local_position=layout[0].local_position,
            force_n=300.0,
        ),
    )

    solve = solve_compliant_tube_on_rigid_state_d1(state, layout, loads)

    assert solve.rigid_state == state
    assert solve.tube_solve.total_applied_load_n == pytest.approx(300.0)
    assert solve.world_segment_positions[0].is_close(
        state.world_point(solve.tube_solve.segment_responses[0].local_position)
    )
    assert not solve.world_segment_positions[0].is_close(layout[0].local_position)


def test_side_contact_spreads_through_lacing_floor_and_frame():
    layout = build_default_compliant_tube_layout_d1()
    load = TubeLoadD1(
        load_id="starboard_mid_contact",
        local_position=Vec3(0.35, 0.95, 0.0),
        force_n=1_450.0,
        source="test_side_contact",
    )

    solve = solve_compliant_tube_d1(layout, (load,))
    responses = {response.segment_id: response for response in solve.segment_responses}
    max_response = max(solve.segment_responses, key=lambda response: response.effective_load_n)

    assert max_response.segment_id.startswith("starboard_")
    assert max_response.direct_load_n > 0.0
    assert max_response.freeboard_loss_m == pytest.approx(solve.max_freeboard_loss_m)
    max_index = next(
        index
        for index, segment in enumerate(layout)
        if segment.segment_id == max_response.segment_id
    )
    neighbor_ids = {
        layout[(max_index - 1) % len(layout)].segment_id,
        layout[(max_index + 1) % len(layout)].segment_id,
    }
    assert all(responses[segment_id].received_lacing_load_n > 0.0 for segment_id in neighbor_ids)
    assert all(response.floor_load_n > 0.0 for response in solve.segment_responses)
    assert any(
        response.segment_id.startswith("port_") and response.frame_load_n > 0.0
        for response in solve.segment_responses
    )
    assert solve.roll_load_bias_nm > 0.0
    assert solve.total_effective_tube_load_n == pytest.approx(load.force_n)


def test_compliant_tube_d1_rejects_invalid_inputs():
    layout = build_default_compliant_tube_layout_d1()

    with pytest.raises(ValueError, match="layout"):
        solve_compliant_tube_d1((), ())
    with pytest.raises(ValueError, match="force_n"):
        TubeLoadD1("bad", Vec3(), -1.0)
    with pytest.raises(ValueError, match="unique"):
        solve_compliant_tube_d1((layout[0], layout[0]), ())
