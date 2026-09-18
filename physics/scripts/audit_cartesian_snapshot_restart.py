"""Independently verify native restart output, original overlap and added sources."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def verify_retained_inputs(previous, current, *, scenario=False):
    """Only explicitly regenerated restart bookkeeping may differ.

    Compare complete remaining dictionaries, not a physical-field whitelist:
    a newly introduced solver setting must not silently escape this audit.
    Source-file and geometry-manifest hashes are checked separately.
    """
    if scenario:
        ignored = {'metadata'}
        metadata_ignored = {'generator', 'description', 'provenance'}
        assert ({k: v for k, v in previous['metadata'].items() if k not in metadata_ignored}
                == {k: v for k, v in current['metadata'].items() if k not in metadata_ignored}), 'Retained scenario identity changed'
    else:
        ignored = {'initial_time_seconds', 'initial_velocity_method', 'inputs', 'packages',
                   'initialization_is_fresh_not_restart', 'settled_hydraulics',
                   'normal_map_integrated', 'maximum_initial_depth_m',
                   'maximum_initial_speed_mps', 'restart', 'geometry_manifest',
                   'geometry_manifest_sha256'}
        assert current['initialization_is_fresh_not_restart'] is False
        assert current['settled_hydraulics'] is False
        assert current['normal_map_integrated'] is False
        assert current['dt_seconds'] > 0 and np.isfinite(current['dt_seconds'])
    assert ({k: v for k, v in previous.items() if k not in ignored}
            == {k: v for k, v in current.items() if k not in ignored}), 'Retained physical inputs changed'


def sha(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cook", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    assert not args.report.exists()
    root = args.cook.resolve()
    input_path = Path((root/"input_manifest_path.txt").read_text().strip())
    manifest = json.loads(input_path.read_text())
    assert sha(input_path) == sha(root/"input_manifest.json")
    restart = manifest["restart"]
    previous_path = Path(restart["source_manifest"])
    assert sha(previous_path) == restart["source_manifest_sha256"]
    previous = json.loads(previous_path.read_text())
    verify_retained_inputs(previous, manifest)
    source_frame = Path(restart["source_frame"])
    before = json.loads((source_frame/"complete.json").read_text())
    after = json.loads((root/"frame_000000/complete.json").read_text())
    assert before["snapshot"] and after["snapshot"] and after["step"] == 0
    assert before["time_seconds"] == after["time_seconds"] == manifest["initial_time_seconds"] == restart["source_time_seconds"]
    original_count = len(previous["packages"])
    assert manifest["packages"][:original_count] == previous["packages"]
    assert manifest["boundary_probes"] == previous["boundary_probes"]
    geometry_path = ROOT/manifest["geometry_manifest"]
    assert sha(geometry_path) == manifest["geometry_manifest_sha256"]
    geometry = json.loads(geometry_path.read_text())
    assert [r["name"] for r in geometry["regions"]] == manifest["packages"]
    fields = {}
    old_fields = {}
    for name in ("h", "u", "v"):
        path = source_frame/f"{name}.npy"
        assert sha(path) == restart["arrays"][name]
        old_fields[name] = np.load(path, mmap_mode="r", allow_pickle=False)
        fields[name] = np.load(root/f"frame_000000/{name}.npy", mmap_mode="r", allow_pickle=False)
        assert old_fields[name].dtype == fields[name].dtype == np.dtype("<f8")
        assert np.array_equal(fields[name][:old_fields[name].shape[0]], old_fields[name]), name
    verified_cells = added_cells = 0
    volume = added_volume = 0.
    input_records = {record["name"]: record for record in manifest["inputs"]}
    for i, name in enumerate(manifest["packages"]):
        package = input_path.parent/name
        for filename, expected in input_records[name]["files"].items():
            assert sha(package/filename) == expected
        scenario = json.loads((package/"scenario.json").read_text())
        grid = scenario["grid"]
        nx, ny = grid["nx"], grid["ny"]
        bed = np.load(package/"bed.npy", allow_pickle=False)
        with np.load(package/"initial_state.npz", allow_pickle=False) as state:
            for field, key in (("h", "depth"), ("u", "u"), ("v", "v")):
                assert np.array_equal(state[key], fields[field][i*ny:(i+1)*ny]), (name, key)
            for momentum, velocity in (("hu", "u"), ("hv", "v")):
                assert np.array_equal(state[momentum], state["depth"]*state[velocity])
            volume += float(state["depth"].sum()*grid["dx"]*grid["dy"])
            if i < original_count:
                old_scenario = json.loads((previous_path.parent/name/"scenario.json").read_text())
                verify_retained_inputs(old_scenario, scenario, scenario=True)
                assert scenario["grid"] == old_scenario["grid"]
                assert scenario["boundaries"] == old_scenario["boundaries"]
                assert scenario["roughness"] == old_scenario["roughness"]
                assert sha(package/"bed.npy") == sha(previous_path.parent/name/"bed.npy")
                for retained_file in ("features.json", "probes.json"):
                    assert sha(package/retained_file) == sha(previous_path.parent/name/retained_file)
                verified_cells += nx*ny
            else:
                record = geometry["regions"][i]
                source_path = ROOT/record["source_geometry_file"]
                assert sha(source_path) == record["source_geometry_sha256"]
                geometry_file = ROOT/record["geometry_file"]
                assert sha(geometry_file) == record["geometry_sha256"]
                row, col = record["source_slice_row_column"]
                with np.load(source_path, allow_pickle=False) as captured, np.load(geometry_file, allow_pickle=False) as retained:
                    for field in ("bed_navd88_m", "captured_surface_navd88_m", "captured_water_mask", "terrain_owner"):
                        assert np.array_equal(retained[field], captured[field][row:row+ny, col:col+nx])
                    assert np.array_equal(bed, retained["bed_navd88_m"]-manifest["vertical_datum_navd88_m"])
                    inferred = np.where(retained["captured_water_mask"].astype(bool),
                                        np.maximum(retained["captured_surface_navd88_m"]-retained["bed_navd88_m"], 0.), 0.)
                    assert np.array_equal(state["depth"], inferred)
                    assert np.all(state["u"] == 0.) and np.all(state["v"] == 0.)
                added_volume += float(state["depth"].sum()*grid["dx"]*grid["dy"])
                added_cells += nx*ny
    assert abs(volume-after["volume_m3"]) < 1.e-6
    assert abs(volume-before["volume_m3"]-added_volume) < 1.e-6
    assert added_volume == restart["added_initial_water_volume_m3"]
    result = dict(schema="raftsim.cartesian_restart_audit.v1", passed=True,
                  manifest_sha256=sha(input_path), previous_manifest_sha256=sha(previous_path),
                  original_cells_bit_exact=verified_cells, added_source_exact_cells=added_cells,
                  added_initial_water_volume_m3=added_volume, source_time_seconds=before["time_seconds"],
                  native_restart_time_seconds=after["time_seconds"], volume_m3=volume,
                  restart_volume_error_m3=volume-before["volume_m3"]-added_volume,
                  original_grid_bed_roughness_and_boundaries_unchanged=True,
                  all_retained_physical_settings_features_and_probes_unchanged=True,
                  settling_accepted=False, normal_map_integrated=False)
    args.report.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
