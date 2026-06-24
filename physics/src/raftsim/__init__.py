"""Headless physics foundation for the rafting simulator."""

from .math3d import Quaternion, Vec3
from .math2d import Vec2
from .raft2d import (
    PaddleCommand2D,
    Raft2DConfig,
    Raft2DSimulation,
    Raft2DState,
    Raft2DStepResult,
    default_forward_paddle_commands,
)
from .river2d import (
    GeneratedRiver2D,
    River2DParameters,
    RiverFeature2D,
    RiverSample2D,
    RiverValidation2D,
    generate_river_2d,
)
from .sim import Simulation, SimulationConfig, SimulationSystem
from .state import BodyState
from .telemetry import ForceContribution, TelemetryFrame, TelemetryRecorder
from .backends import (
    BackendCapabilities,
    BackendStatus,
    BackendUnavailableError,
    ChronoSimulation,
    PhysicsBackend,
    ProjectChronoBackend,
    PurePythonBackend,
    backend_statuses,
    create_backend,
    select_backend,
)

__all__ = [
    "BackendCapabilities",
    "BackendStatus",
    "BackendUnavailableError",
    "BodyState",
    "ChronoSimulation",
    "ForceContribution",
    "PhysicsBackend",
    "ProjectChronoBackend",
    "PurePythonBackend",
    "Quaternion",
    "Simulation",
    "SimulationConfig",
    "SimulationSystem",
    "TelemetryFrame",
    "TelemetryRecorder",
    "Vec3",
    "Vec2",
    "PaddleCommand2D",
    "Raft2DConfig",
    "Raft2DSimulation",
    "Raft2DState",
    "Raft2DStepResult",
    "GeneratedRiver2D",
    "River2DParameters",
    "RiverFeature2D",
    "RiverSample2D",
    "RiverValidation2D",
    "backend_statuses",
    "create_backend",
    "default_forward_paddle_commands",
    "generate_river_2d",
    "select_backend",
]
