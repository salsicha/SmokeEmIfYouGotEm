"""Optional Project Chrono backend.

This adapter intentionally keeps Chrono behind a lazy import boundary. PyChrono
is distributed primarily through Anaconda packages, and most development
environments will not have it installed by default.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any

from ..sim import SimulationConfig
from .base import BackendCapabilities, BackendStatus, BackendUnavailableError


CHRONO_IMPORT_CANDIDATES = ("pychrono.core", "pychrono")


def _import_chrono_module():
    import_errors: list[str] = []
    for module_name in CHRONO_IMPORT_CANDIDATES:
        try:
            module = importlib.import_module(module_name)
        except ImportError as error:
            import_errors.append(f"{module_name}: {error}")
            continue

        if any(hasattr(module, attr) for attr in ("ChSystem", "ChSystemSMC", "ChSystemNSC")):
            return module_name, module
        import_errors.append(f"{module_name}: module loaded but no ChSystem class was found")

    raise BackendUnavailableError(
        "Project Chrono/PyChrono is not available. Install PyChrono from the "
        "Project Chrono distribution before using the 'chrono' backend. "
        f"Import attempts: {'; '.join(import_errors)}"
    )


def _chrono_version(module: Any) -> str | None:
    for attr in ("CHRONO_VERSION", "__version__", "chrono_version"):
        version = getattr(module, attr, None)
        if version is not None:
            return str(version)
    return None


def _make_chrono_system(module: Any):
    for class_name in ("ChSystemSMC", "ChSystemNSC", "ChSystem"):
        system_class = getattr(module, class_name, None)
        if system_class is not None:
            return system_class()
    raise BackendUnavailableError("Loaded PyChrono, but no supported ChSystem class was found.")


@dataclass(slots=True)
class ChronoSimulation:
    """Minimal fixed-step wrapper around a PyChrono system."""

    system: Any
    config: SimulationConfig
    module_name: str
    chrono_module: Any
    time: float = 0.0
    step_index: int = 0

    def step(self, count: int = 1) -> None:
        if count < 0:
            raise ValueError("count must be non-negative.")
        for _ in range(count):
            self.system.DoStepDynamics(self.config.fixed_dt)
            self.time += self.config.fixed_dt
            self.step_index += 1


class ProjectChronoBackend:
    """Backend for Chrono multibody and FSI work."""

    name = "chrono"
    capabilities = BackendCapabilities(
        name=name,
        rigid_bodies=True,
        collision=True,
        compliant_bodies=True,
        fluid_solid_interaction=True,
        free_surface_water=True,
        particle_fluids=True,
        differentiable=False,
        gpu_acceleration=False,
        python_api=True,
        notes=(
            "Selected backend for raft/water simulation because Chrono combines "
            "multibody dynamics, collision/contact, flexible bodies, Python access, "
            "and Chrono::FSI fluid-solid interaction support. Acceleration and "
            "specific FSI module availability depend on the installed Chrono build."
        ),
    )

    def status(self) -> BackendStatus:
        try:
            module_name, module = _import_chrono_module()
        except BackendUnavailableError as error:
            return BackendStatus(name=self.name, available=False, reason=str(error))
        return BackendStatus(
            name=self.name,
            available=True,
            reason="PyChrono import succeeded.",
            module_name=module_name,
            version=_chrono_version(module),
        )

    def create_simulation(self, **kwargs: Any) -> ChronoSimulation:
        module_name, module = _import_chrono_module()
        config = kwargs.pop("config", None) or SimulationConfig()
        if kwargs:
            unsupported = ", ".join(sorted(kwargs))
            raise TypeError(f"Unsupported Chrono simulation arguments: {unsupported}")
        return ChronoSimulation(
            system=_make_chrono_system(module),
            config=config,
            module_name=module_name,
            chrono_module=module,
        )
