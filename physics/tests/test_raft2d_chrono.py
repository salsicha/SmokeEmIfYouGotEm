import types

import pytest

from raftsim.backends import chrono as chrono_backend_module
from raftsim.math2d import Vec2
from raftsim.raft2d import Raft2DSimulation, Raft2DState, default_forward_paddle_commands
from raftsim.river2d import River2DParameters, generate_river_2d
from raftsim.sim import SimulationConfig


class MockVector:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z


class MockQuaternion:
    def __init__(self, w=1.0, x=0.0, y=0.0, z=0.0):
        self.w = w
        self.x = x
        self.y = y
        self.z = z


class MockBody:
    def __init__(self, *args):
        self.position = MockVector()
        self.velocity = MockVector()
        self.angular_velocity = MockVector()
        self.force = MockVector()
        self.torque = MockVector()

    def SetMass(self, value):
        self.mass = value

    def SetInertiaXX(self, value):
        self.inertia = value

    def EnableCollision(self, value):
        self.collision = value

    def SetFixed(self, value):
        self.fixed = value

    def SetPos(self, value):
        self.position = value

    def SetRot(self, value):
        self.rotation = value

    def SetLinVel(self, value):
        self.velocity = value

    def SetAngVelParent(self, value):
        self.angular_velocity = value

    def EmptyAccumulators(self):
        self.force = MockVector()
        self.torque = MockVector()

    def AccumulateForce(self, force, point, local):
        self.force = force

    def AccumulateTorque(self, torque, local):
        self.torque = torque

    def GetPos(self):
        return self.position

    def GetLinVel(self):
        return self.velocity

    def GetAngVelParent(self):
        return self.angular_velocity


class MockSystem:
    def __init__(self):
        self.body = None

    def Add(self, body):
        self.body = body

    def DoStepDynamics(self, dt):
        if self.body is None:
            return
        self.body.velocity = MockVector(
            self.body.velocity.x + self.body.force.x * dt / 420.0,
            0.0,
            self.body.velocity.z + self.body.force.z * dt / 420.0,
        )
        self.body.position = MockVector(
            self.body.position.x + self.body.velocity.x * dt,
            0.0,
            self.body.position.z + self.body.velocity.z * dt,
        )
        self.body.angular_velocity = MockVector(0.0, self.body.angular_velocity.y + self.body.torque.y * dt / 1550.0, 0.0)


def test_chrono_integrator_falls_back_to_plain_body(monkeypatch):
    def incompatible_easy_box(*args):
        raise TypeError("constructor signature differs")

    mock_chrono = types.SimpleNamespace(
        ChSystemSMC=MockSystem,
        ChBodyEasyBox=incompatible_easy_box,
        ChBody=MockBody,
        ChVector3d=MockVector,
        ChQuaterniond=MockQuaternion,
        CHRONO_VERSION="mock-version",
    )
    monkeypatch.setattr(
        chrono_backend_module,
        "_import_chrono_module",
        lambda: ("pychrono.core", mock_chrono),
    )

    river = generate_river_2d(River2DParameters(seed=8, length=70.0, sample_count=31))
    sim = Raft2DSimulation(river, backend="chrono", sim_config=SimulationConfig(fixed_dt=0.1))

    assert sim.backend_name == "chrono"
    assert isinstance(sim.integrator._body, MockBody)


def test_raft_can_step_with_mocked_pychrono(monkeypatch):
    mock_chrono = types.SimpleNamespace(
        ChSystemSMC=MockSystem,
        ChBodyEasyBox=MockBody,
        ChVector3d=MockVector,
        ChQuaterniond=MockQuaternion,
        CHRONO_VERSION="mock-version",
    )
    monkeypatch.setattr(
        chrono_backend_module,
        "_import_chrono_module",
        lambda: ("pychrono.core", mock_chrono),
    )

    river = generate_river_2d(River2DParameters(seed=6, length=100.0, sample_count=41))
    sim = Raft2DSimulation(
        river,
        state=Raft2DState(position=river.start_position + Vec2(2.0, 0.0)),
        backend="chrono",
        sim_config=SimulationConfig(fixed_dt=0.1),
    )
    result = sim.step(default_forward_paddle_commands())

    assert sim.backend_name == "chrono"
    assert result.state.position.x > river.start_position.x
    assert sim.telemetry.force_rows()
