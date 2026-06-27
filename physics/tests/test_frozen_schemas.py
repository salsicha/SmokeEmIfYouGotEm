import json
from dataclasses import fields
from pathlib import Path

from raftsim.scenario2_5d import SCENARIO_SCHEMA_VERSION
from raftsim.schema_versions import (
    PARAMETER_SCHEMA_VERSION,
    REPLAY_SCHEMA_VERSION,
    SHARED_SCHEMA_SET_VERSION,
    TELEMETRY_FORCE_SCHEMA_VERSION,
)
from raftsim.sweeps import ParameterSweepCandidate
from raftsim.telemetry import TelemetryRecorder


def test_shared_schema_manifest_references_frozen_schema_files():
    schemas_dir = Path(__file__).resolve().parents[1] / "schemas"
    manifest = json.loads((schemas_dir / "shared_schemas_manifest.json").read_text(encoding="utf-8"))

    assert manifest["schema_set_version"] == SHARED_SCHEMA_SET_VERSION
    entries = {entry["name"]: entry for entry in manifest["schemas"]}
    assert set(entries) == {"scenario2_5d", "telemetry_forces", "replay", "parameters"}
    for entry in entries.values():
        assert (schemas_dir / entry["file"]).exists()


def test_frozen_scenario_schema_matches_code_version():
    schema = _load_schema("scenario2_5d.schema.json")

    assert schema["properties"]["schema_version"]["const"] == SCENARIO_SCHEMA_VERSION
    assert "array_files" in schema["required"]
    assert schema["properties"]["array_files"]["required"] == ["bed", "initial_state", "features", "probes"]


def test_frozen_telemetry_schema_matches_force_csv_columns():
    schema = _load_schema("telemetry_forces.schema.json")

    assert schema["schema_version"] == TELEMETRY_FORCE_SCHEMA_VERSION
    assert schema["columns"] == TelemetryRecorder.FIELDNAMES


def test_frozen_replay_schema_uses_replay_version():
    schema = _load_schema("replay.schema.json")

    assert schema["properties"]["schema_version"]["const"] == REPLAY_SCHEMA_VERSION
    assert {"step_index", "time", "raft_state"}.issubset(schema["properties"]["frames"]["items"]["required"])


def test_frozen_parameter_schema_matches_sweep_candidate_fields():
    schema = _load_schema("parameters.schema.json")
    candidate_required = schema["properties"]["candidate"]["required"]
    candidate_fields = [field.name for field in fields(ParameterSweepCandidate)]

    assert schema["properties"]["schema_version"]["const"] == PARAMETER_SCHEMA_VERSION
    assert candidate_required == candidate_fields


def _load_schema(name: str) -> dict[str, object]:
    schemas_dir = Path(__file__).resolve().parents[1] / "schemas"
    return json.loads((schemas_dir / name).read_text(encoding="utf-8"))
