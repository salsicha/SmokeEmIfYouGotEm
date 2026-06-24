"""Pure Python raftsim backend."""

from __future__ import annotations

from typing import Any

from ..sim import Simulation
from .base import BackendCapabilities, BackendStatus


class PurePythonBackend:
    """Backend exposing raftsim's built-in deterministic simulation loop."""

    name = "python"
    capabilities = BackendCapabilities(
        name=name,
        rigid_bodies=False,
        collision=False,
        compliant_bodies=False,
        fluid_solid_interaction=False,
        free_surface_water=False,
        particle_fluids=False,
        differentiable=False,
        gpu_acceleration=False,
        python_api=True,
        notes="Always-available raftsim reference backend; hydrodynamics are implemented incrementally.",
    )

    def status(self) -> BackendStatus:
        return BackendStatus(name=self.name, available=True, reason="Built into raftsim.")

    def create_simulation(self, **kwargs: Any) -> Simulation:
        return Simulation(**kwargs)
