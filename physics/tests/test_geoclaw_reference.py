import json

import pytest

from raftsim.examples.run_geoclaw_reference import main as geoclaw_main
from raftsim.geoclaw_reference import (
    GEOCLAW_REQUIRED_MODULES,
    GeoClawAvailability,
    build_geoclaw_setup_report,
    check_geoclaw_availability,
    write_geoclaw_setup_report,
)


def test_geoclaw_availability_check_is_machine_readable():
    status = check_geoclaw_availability()

    assert isinstance(status.available, bool)
    assert status.reason
    assert status.required_modules == GEOCLAW_REQUIRED_MODULES
    assert "available" in status.to_json_dict()
    assert "missing_modules" in status.to_json_dict()
    assert "missing_executables" in status.to_json_dict()


def test_geoclaw_setup_report_includes_docs_and_install_hints():
    report = build_geoclaw_setup_report(
        GeoClawAvailability(
            False,
            "test missing",
            required_modules=GEOCLAW_REQUIRED_MODULES,
            missing_modules=("clawpack.geoclaw",),
        )
    )
    data = report.to_json_dict()

    assert "pip install" in data["install_hint"]
    assert "gfortran" in data["system_dependency_hint"]
    assert any("geoclaw" in doc for doc in data["reference_docs"])
    assert data["availability"]["missing_modules"] == ("clawpack.geoclaw",)


def test_geoclaw_cli_check_allows_unavailable_environment(tmp_path):
    exit_code = geoclaw_main(["--check", "--allow-unavailable", "--output-dir", str(tmp_path)])

    assert exit_code == 0
    assert (tmp_path / "geoclaw_setup_report.json").exists()


def test_geoclaw_setup_report_writes_json(tmp_path):
    status = GeoClawAvailability(
        False,
        "test unavailable",
        required_modules=GEOCLAW_REQUIRED_MODULES,
        missing_modules=("clawpack.geoclaw",),
    )
    report_path = write_geoclaw_setup_report(tmp_path, status)

    data = json.loads(report_path.read_text(encoding="utf-8"))
    assert data["availability"]["available"] is False
    assert data["availability"]["missing_modules"] == ["clawpack.geoclaw"]


def test_geoclaw_cli_fails_when_unavailable_without_override():
    status = check_geoclaw_availability()
    if status.available:
        pytest.skip("GeoClaw is installed; unavailable CLI path is not active.")

    assert geoclaw_main(["--check"]) == 1
