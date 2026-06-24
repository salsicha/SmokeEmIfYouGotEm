import types

import pytest

from raftsim.backends import (
    BackendUnavailableError,
    ProjectChronoBackend,
    PurePythonBackend,
    create_backend,
    select_backend,
)
from raftsim.backends import chrono as chrono_backend_module
from raftsim.sim import Simulation, SimulationConfig


def test_create_backend_supports_selected_aliases():
    assert isinstance(create_backend("chrono"), ProjectChronoBackend)
    assert isinstance(create_backend("pychrono"), ProjectChronoBackend)
    assert isinstance(create_backend("python"), PurePythonBackend)
    assert isinstance(create_backend("pure-python"), PurePythonBackend)


def test_select_backend_falls_back_to_pure_python_when_chrono_is_unavailable(monkeypatch):
    def unavailable():
        raise BackendUnavailableError("not installed")

    monkeypatch.setattr(chrono_backend_module, "_import_chrono_module", unavailable)

    backend = select_backend(("chrono", "python"))
    assert isinstance(backend, PurePythonBackend)
    assert isinstance(backend.create_simulation(), Simulation)


def test_select_backend_can_require_chrono(monkeypatch):
    def unavailable():
        raise BackendUnavailableError("not installed")

    monkeypatch.setattr(chrono_backend_module, "_import_chrono_module", unavailable)

    with pytest.raises(BackendUnavailableError):
        select_backend(("chrono",))


def test_chrono_backend_creates_and_steps_mocked_chrono_system(monkeypatch):
    class MockChronoSystem:
        def __init__(self):
            self.steps: list[float] = []

        def DoStepDynamics(self, dt: float) -> None:
            self.steps.append(dt)

    mock_chrono = types.SimpleNamespace(
        ChSystemSMC=MockChronoSystem,
        CHRONO_VERSION="mock-version",
    )

    monkeypatch.setattr(
        chrono_backend_module,
        "_import_chrono_module",
        lambda: ("pychrono.core", mock_chrono),
    )

    backend = ProjectChronoBackend()
    status = backend.status()
    simulation = backend.create_simulation(config=SimulationConfig(fixed_dt=0.2))
    simulation.step(3)

    assert status.available is True
    assert status.module_name == "pychrono.core"
    assert status.version == "mock-version"
    assert simulation.system.steps == [0.2, 0.2, 0.2]
    assert simulation.time == pytest.approx(0.6)
    assert simulation.step_index == 3
