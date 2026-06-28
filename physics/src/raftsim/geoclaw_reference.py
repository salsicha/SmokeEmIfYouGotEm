"""GeoClaw reference-solver setup checks and transition utilities."""

from __future__ import annotations

import importlib
import json
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path


class GeoClawUnavailableError(RuntimeError):
    """Raised when GeoClaw is required but not available locally."""


@dataclass(frozen=True, slots=True)
class GeoClawAvailability:
    """Machine-readable status for the optional GeoClaw research runtime."""

    available: bool
    reason: str
    required_modules: tuple[str, ...]
    missing_modules: tuple[str, ...] = ()
    module_paths: dict[str, str] = field(default_factory=dict)
    clawpack_version: str | None = None
    required_executables: tuple[str, ...] = ()
    missing_executables: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class GeoClawSetupReport:
    """Install/setup guidance attached to a GeoClaw availability check."""

    availability: GeoClawAvailability
    install_hint: str
    system_dependency_hint: str
    reference_docs: tuple[str, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "availability": self.availability.to_json_dict(),
            "install_hint": self.install_hint,
            "system_dependency_hint": self.system_dependency_hint,
            "reference_docs": list(self.reference_docs),
        }


GEOCLAW_REQUIRED_MODULES = (
    "clawpack",
    "clawpack.geoclaw",
    "clawpack.clawutil",
    "clawpack.pyclaw",
)
GEOCLAW_RECOMMENDED_EXECUTABLES = ("make", "gfortran")
GEOCLAW_REFERENCE_DOCS = (
    "https://www.clawpack.org/geoclaw.html",
    "https://www.clawpack.org/setrun_geoclaw.html",
    "https://www.clawpack.org/topo.html",
    "https://www.clawpack.org/fgout.html",
)
GEOCLAW_INSTALL_HINT = 'Install the optional research extra with: python -m pip install -e ".[research]"'
GEOCLAW_SYSTEM_DEPENDENCY_HINT = (
    "GeoClaw runs normally compile Fortran kernels; install a local compiler toolchain "
    "with make and gfortran before running full reference simulations."
)


def check_geoclaw_availability() -> GeoClawAvailability:
    """Return whether the optional Clawpack/GeoClaw runtime can be imported."""

    missing_modules: list[str] = []
    module_paths: dict[str, str] = {}
    imported_modules: dict[str, object] = {}
    for module_name in GEOCLAW_REQUIRED_MODULES:
        try:
            module = importlib.import_module(module_name)
        except Exception:  # pragma: no cover - exact import failure varies by install.
            missing_modules.append(module_name)
            continue
        imported_modules[module_name] = module
        module_file = getattr(module, "__file__", None)
        if module_file:
            module_paths[module_name] = str(module_file)

    missing_executables = tuple(
        executable for executable in GEOCLAW_RECOMMENDED_EXECUTABLES if shutil.which(executable) is None
    )
    clawpack = imported_modules.get("clawpack")
    version = str(getattr(clawpack, "__version__", "")) or None if clawpack is not None else None

    if missing_modules:
        return GeoClawAvailability(
            False,
            "Missing required Python modules: " + ", ".join(missing_modules),
            required_modules=GEOCLAW_REQUIRED_MODULES,
            missing_modules=tuple(missing_modules),
            module_paths=module_paths,
            clawpack_version=version,
            required_executables=GEOCLAW_RECOMMENDED_EXECUTABLES,
            missing_executables=missing_executables,
        )
    if missing_executables:
        return GeoClawAvailability(
            False,
            "Missing recommended GeoClaw build executables: " + ", ".join(missing_executables),
            required_modules=GEOCLAW_REQUIRED_MODULES,
            module_paths=module_paths,
            clawpack_version=version,
            required_executables=GEOCLAW_RECOMMENDED_EXECUTABLES,
            missing_executables=missing_executables,
        )
    return GeoClawAvailability(
        True,
        "GeoClaw modules and recommended build executables are available.",
        required_modules=GEOCLAW_REQUIRED_MODULES,
        module_paths=module_paths,
        clawpack_version=version,
        required_executables=GEOCLAW_RECOMMENDED_EXECUTABLES,
    )


def build_geoclaw_setup_report(availability: GeoClawAvailability | None = None) -> GeoClawSetupReport:
    """Build a setup report for CLI checks and readiness artifacts."""

    return GeoClawSetupReport(
        availability=availability or check_geoclaw_availability(),
        install_hint=GEOCLAW_INSTALL_HINT,
        system_dependency_hint=GEOCLAW_SYSTEM_DEPENDENCY_HINT,
        reference_docs=GEOCLAW_REFERENCE_DOCS,
    )


def write_geoclaw_setup_report(directory: str | Path, availability: GeoClawAvailability | None = None) -> Path:
    """Write a machine-readable GeoClaw setup report."""

    output_dir = Path(directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_geoclaw_setup_report(availability)
    path = output_dir / "geoclaw_setup_report.json"
    path.write_text(json.dumps(report.to_json_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return path
