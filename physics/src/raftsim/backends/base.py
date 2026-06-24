"""Shared backend contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class BackendUnavailableError(RuntimeError):
    """Raised when a requested optional physics backend is not installed."""


@dataclass(frozen=True, slots=True)
class BackendCapabilities:
    """Capability flags used to compare candidate physics backends."""

    name: str
    rigid_bodies: bool = False
    collision: bool = False
    compliant_bodies: bool = False
    fluid_solid_interaction: bool = False
    free_surface_water: bool = False
    particle_fluids: bool = False
    differentiable: bool = False
    gpu_acceleration: bool = False
    python_api: bool = False
    notes: str = ""


@dataclass(frozen=True, slots=True)
class BackendStatus:
    """Runtime availability information for an optional backend."""

    name: str
    available: bool
    reason: str = ""
    module_name: str | None = None
    version: str | None = None


class PhysicsBackend(Protocol):
    """Protocol implemented by raftsim physics backends."""

    name: str
    capabilities: BackendCapabilities

    def status(self) -> BackendStatus:
        """Return runtime availability information."""

    def create_simulation(self, **kwargs: Any) -> Any:
        """Create a backend-specific simulation object."""
