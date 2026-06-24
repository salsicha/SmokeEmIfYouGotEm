from raftsim.raft2d import Raft2DSimulation, default_forward_paddle_commands
from raftsim.river2d import River2DParameters, generate_river_2d
from raftsim.sim import SimulationConfig


def test_raft_moves_downstream_and_records_telemetry():
    river = generate_river_2d(River2DParameters(seed=4, length=90.0, sample_count=41))
    sim = Raft2DSimulation(river, backend="python", sim_config=SimulationConfig(fixed_dt=1.0 / 30.0))
    start_x = sim.state.position.x

    results = sim.run(2.0, default_forward_paddle_commands())

    assert len(results) == 60
    assert sim.state.position.x > start_x
    assert sim.telemetry.frames
    assert any(row["name"] == "water.drag" for row in sim.telemetry.force_rows())


def test_raft_auto_backend_falls_back_to_python_without_pychrono():
    river = generate_river_2d(River2DParameters(seed=5, length=90.0, sample_count=41))
    sim = Raft2DSimulation(river, backend="auto")

    assert sim.backend_name in {"python", "chrono"}
    sim.step(default_forward_paddle_commands())
    assert sim.step_index == 1
