"""Backend registry and selection helpers."""

from __future__ import annotations

from .base import BackendUnavailableError, PhysicsBackend
from .chrono import ProjectChronoBackend
from .pure_python import PurePythonBackend

BACKEND_CLASSES = {
    "chrono": ProjectChronoBackend,
    "project-chrono": ProjectChronoBackend,
    "pychrono": ProjectChronoBackend,
    "python": PurePythonBackend,
    "pure-python": PurePythonBackend,
}


def create_backend(name: str) -> PhysicsBackend:
    try:
        backend_class = BACKEND_CLASSES[name.lower()]
    except KeyError as error:
        supported = ", ".join(sorted(BACKEND_CLASSES))
        raise ValueError(f"Unknown physics backend '{name}'. Supported backends: {supported}") from error
    return backend_class()


def backend_statuses():
    seen: set[type] = set()
    statuses = []
    for backend_class in BACKEND_CLASSES.values():
        if backend_class in seen:
            continue
        seen.add(backend_class)
        statuses.append(backend_class().status())
    return tuple(statuses)


def select_backend(preferred: tuple[str, ...] = ("chrono", "python")) -> PhysicsBackend:
    """Return the first available backend from a preference list."""

    unavailable: list[str] = []
    for name in preferred:
        backend = create_backend(name)
        status = backend.status()
        if status.available:
            return backend
        unavailable.append(f"{status.name}: {status.reason}")

    raise BackendUnavailableError("No requested physics backend is available. " + " | ".join(unavailable))
