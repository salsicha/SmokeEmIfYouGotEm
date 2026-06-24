from raftsim.math3d import Vec3
from raftsim.sim import Simulation, SimulationConfig


class ConstantForceSystem:
    def __init__(self, force: Vec3):
        self.force = force

    def step(self, simulation: Simulation, dt: float) -> None:
        simulation.record_force(
            "test.constant_force",
            self.force,
            torque=Vec3(0.0, 0.0, 0.25),
            metadata={"dt": dt},
        )


def test_fixed_step_simulation_is_deterministic():
    config = SimulationConfig(fixed_dt=0.1, seed=42)
    first = Simulation(config=config, systems=[ConstantForceSystem(Vec3(1.0, 0.0, 0.0))])
    second = Simulation(config=config, systems=[ConstantForceSystem(Vec3(1.0, 0.0, 0.0))])

    first.step(3)
    second.step(3)

    assert first.time == second.time == 0.30000000000000004
    assert first.step_index == second.step_index == 3
    assert first.telemetry.force_rows() == second.telemetry.force_rows()


def test_run_for_requires_duration_to_match_fixed_timestep():
    sim = Simulation(config=SimulationConfig(fixed_dt=0.25))

    sim.run_for(0.5)
    assert sim.step_index == 2

    try:
        sim.run_for(0.1)
    except ValueError as error:
        assert "integer multiple" in str(error)
    else:
        raise AssertionError("Expected non-integral duration to be rejected.")
