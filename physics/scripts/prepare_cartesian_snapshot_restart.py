"""Prepare an immutable, exact-state restart with optional source-exact bank context.

This does not run or stop a solver. Added terrain uses existing samples only;
water outside the prior domain is explicitly inferred from captured surface,
initially at rest, and its added inventory is reported separately.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
FIELDS = ("bed_navd88_m", "captured_surface_navd88_m", "captured_water_mask", "terrain_owner")
DELTAS = dict(west=(-1, 0), east=(1, 0), south=(0, -1), north=(0, 1))


def sha(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2)+"\n", encoding="utf-8")


def make_restart_manifest(manifest, source_time):
    """Preserve physical inputs, never inherit a cold-start or old-state claim."""
    if type(source_time) not in (int, float) or not np.isfinite(source_time) or source_time < 0:
        raise ValueError('Finite nonnegative checkpoint time required')
    result = copy.deepcopy(manifest)
    result.update(initial_time_seconds=source_time, inputs=[], packages=[],
                  initialization_is_fresh_not_restart=False,
                  initial_velocity_method="Bit-exact native checkpoint on retained cells; inferred zero velocity on added context only",
                  settled_hydraulics=False, normal_map_integrated=False)
    for key in ('maximum_initial_depth_m', 'maximum_initial_speed_mps', 'restart'):
        result.pop(key, None)
    return result


def validate_bank_observation(audit, manifest_sha, source_step, observed_h_sha, allow_later=False):
    """Later edge wetting may select context for an earlier clean checkpoint.

    It must belong to the very same immutable cook input. Its state is never
    substituted for the selected restart arrays. Default remains same-step.
    """
    assert audit['input_manifest_sha256'] == manifest_sha
    assert audit['h_sha256'] == observed_h_sha
    assert audit['step'] == source_step or (allow_later and audit['step'] > source_step)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cook", type=Path)
    parser.add_argument("step", type=int)
    parser.add_argument("output", type=Path)
    parser.add_argument("--exterior-bank-audit", type=Path)
    parser.add_argument("--allow-later-bank-observation", action="store_true",
        help="Use a later verified edge audit only to select terrain context; restart from the requested earlier state")
    args = parser.parse_args()
    assert not args.allow_later_bank_observation or args.exterior_bank_audit
    output = args.output.resolve()
    assert not output.exists(), "Never overwrite prior input or a live cook"
    root = args.cook.resolve()
    original = Path((root/"input_manifest_path.txt").read_text().strip())
    if not original.is_absolute(): original = ROOT/original
    assert sha(original) == sha(root/"input_manifest.json")
    manifest = json.loads(original.read_text())
    inputs = {record["name"]: record for record in manifest["inputs"]}
    scenarios = []
    for package in manifest["packages"]:
        for name, expected in inputs[package]["files"].items():
            assert sha(original.parent/package/name) == expected, (package, name)
        scenarios.append(json.loads((original.parent/package/"scenario.json").read_text()))
    shapes = {(s["grid"]["ny"], s["grid"]["nx"], s["grid"]["dx"], s["grid"]["dy"]) for s in scenarios}
    assert len(shapes) == 1
    ny, nx, dx, dy = shapes.pop()
    frame = root/f"frame_{args.step:06d}"
    complete = json.loads((frame/"complete.json").read_text())
    assert complete["step"] == args.step and complete["snapshot"]
    arrays = {name: np.load(frame/f"{name}.npy", mmap_mode="r", allow_pickle=False) for name in ("h", "u", "v")}
    for values in arrays.values():
        assert values.shape == (len(scenarios)*ny, nx) and values.dtype == np.dtype("<f8")
        assert np.isfinite(values).all()
    assert arrays["h"].min() >= 0 and arrays["h"].max() <= 10
    assert np.hypot(arrays["u"], arrays["v"]).max() <= 20
    prior_volume = float(arrays["h"].sum(dtype=np.float64)*dx*dy)
    assert abs(prior_volume-complete["volume_m3"]) < 1.e-6
    geometry_path = ROOT/manifest["geometry_manifest"]
    assert sha(geometry_path) == manifest["geometry_manifest_sha256"]
    geometry = json.loads(geometry_path.read_text())
    assert [r["name"] for r in geometry["regions"]] == manifest["packages"]
    additions = []
    if args.exterior_bank_audit:
        assert (ny, nx, dx, dy) == (80, 80, 1., 1.)
        audit = json.loads(args.exterior_bank_audit.read_text())
        observation_frame = root/f"frame_{audit['step']:06d}"
        observation_complete = json.loads((observation_frame/'complete.json').read_text())
        assert observation_complete['step'] == audit['step'] and observation_complete['snapshot']
        assert observation_complete['time_seconds'] == audit['time_seconds']
        validate_bank_observation(audit, sha(original), args.step,
            sha(observation_frame/'h.npy'), args.allow_later_bank_observation)
        source_path = (ROOT/geometry["regions"][0]["source_geometry_file"]).parent/"manifest.json"
        assert sha(source_path) == geometry["source_manifest_sha256"]
        source = json.loads(source_path.read_text())
        source_centers = np.asarray([r["center_utm_m"] for r in source["regions"]])
        records = {r["name"]: r for r in geometry["regions"]}
        occupied = {tuple(r["center_utm_m"]) for r in records.values()}
        requested = set()
        for edge in audit["wet_bank_edges"]:
            record = records[edge["package"]]
            requested.add(tuple(np.asarray(record["center_utm_m"])+80*np.asarray(DELTAS[edge["edge"]])))
        assert not requested.intersection(occupied), "Audit incorrectly marked a shared face as exterior"
        all_centers = occupied | requested
        # Never accidentally absorb or relocate an authored physical inlet/outlet.
        for probe in manifest["boundary_probes"]:
            record = geometry["regions"][probe["tile_index"]]
            outside = tuple(np.asarray(record["center_utm_m"])+80*np.asarray(DELTAS[probe["edge"]]))
            assert outside not in all_centers
        for i, center in enumerate(sorted(requested)):
            candidates = np.flatnonzero(np.max(np.abs(source_centers-center), axis=1) <= 120)
            assert len(candidates), f"No complete captured source for added core {center}; no extrapolation allowed"
            owner = min(candidates, key=lambda j: np.max(np.abs(source_centers[j]-center)))
            record = source["regions"][owner]
            path = ROOT/record["geometry_file"]
            assert sha(path) == record["geometry_sha256"]
            col, row = map(int, np.asarray(center)-40-(source_centers[owner]-160))
            with np.load(path, allow_pickle=False) as packet:
                fields = {name: packet[name][row:row+80, col:col+80].copy() for name in FIELDS}
            assert all(v.shape == (80, 80) for v in fields.values())
            assert all(np.isfinite(v).all() for v in fields.values())
            additions.append(dict(name=f"context_{len(scenarios)+i:04d}", center_utm_m=list(map(int, center)),
                                  grid_origin_local_m=(np.asarray(center)-40-geometry["world_origin_utm_m"]).tolist(),
                                  source_geometry_file=record["geometry_file"], source_geometry_sha256=record["geometry_sha256"],
                                  source_slice_row_column=[row, col], copied_without_interpolation=True, fields=fields))
    # Reserve space for input arrays, diagnostic snapshots and the ongoing cook.
    assert shutil.disk_usage(output.parent).free > arrays["h"].nbytes*8 + 1024**3
    output.mkdir()
    result = make_restart_manifest(manifest, complete["time_seconds"])
    restart = dict(source_manifest=str(original), source_manifest_sha256=sha(original),
                   source_frame=str(frame), source_step=args.step, source_time_seconds=complete["time_seconds"],
                   arrays={n: sha(frame/f"{n}.npy") for n in arrays},
                   prior_cells=int(arrays["h"].size), prior_volume_m3=prior_volume,
                   overlap_state_is_exact=True, added_context_count=len(additions),
                   added_water_initialization="Captured-surface-minus-source-bed depth, zero initial velocity; inferred, not evolved or measured")
    result["restart"] = restart
    if args.exterior_bank_audit:
        restart["exterior_bank_audit_sha256"] = sha(args.exterior_bank_audit)
        restart['bank_observation'] = dict(step=audit['step'], time_seconds=audit['time_seconds'],
            h_sha256=audit['h_sha256'], later_geometry_selection_only=audit['step'] != args.step)
    geometry = copy.deepcopy(geometry)
    added_volume = 0.
    for i in range(len(scenarios)+len(additions)):
        is_old = i < len(scenarios)
        if is_old:
            name = manifest["packages"][i]
            scenario = copy.deepcopy(scenarios[i])
            h, u, v = (arrays[n][i*ny:(i+1)*ny].copy() for n in ("h", "u", "v"))
            bed = np.load(original.parent/name/"bed.npy", allow_pickle=False)
            record = geometry["regions"][i]
        else:
            addition = additions[i-len(scenarios)]
            name = addition["name"]
            fields = addition["fields"]
            datum = manifest["vertical_datum_navd88_m"]
            bed = fields["bed_navd88_m"]-datum
            h = np.where(fields["captured_water_mask"].astype(bool),
                         np.maximum(fields["captured_surface_navd88_m"]-fields["bed_navd88_m"], 0.), 0.)
            u = np.zeros_like(h); v = np.zeros_like(h)
            added_volume += float(h.sum()*dx*dy)
            scenario = copy.deepcopy(scenarios[0])
            scenario["grid"].update(origin_x=addition["grid_origin_local_m"][0], origin_y=addition["grid_origin_local_m"][1])
            scenario["boundaries"] = [dict(edge=edge, kind="bank") for edge in DELTAS]
            record = {k: val for k, val in addition.items() if k != "fields"}
            record["geometry_file"] = (output/name/"geometry.npz").relative_to(ROOT).as_posix()
            geometry["regions"].append(record)
        package = output/name
        package.mkdir()
        if is_old:
            for file in ("bed.npy", "features.json", "probes.json"):
                shutil.copyfile(original.parent/name/file, package/file)
        else:
            np.savez_compressed(package/"geometry.npz", **fields)
            record["geometry_sha256"] = sha(package/"geometry.npz")
            np.save(package/"bed.npy", bed)
            write_json(package/"features.json", dict(features=[]))
            write_json(package/"probes.json", dict(probes=[]))
        np.savez_compressed(package/"initial_state.npz", depth=h, eta=bed+h, u=u, v=v,
                            hu=h*u, hv=h*v, wet=h>1.e-6)
        # Verify serialized restart state, not only the in-memory copy.
        with np.load(package/"initial_state.npz", allow_pickle=False) as saved:
            for key, values in (("depth", h), ("u", u), ("v", v), ("hu", h*u), ("hv", h*v)):
                assert np.array_equal(saved[key], values), (name, key)
        scenario["metadata"].update(scenario_id=name, generator="prepare_cartesian_snapshot_restart.py",
                                    description="Exact checkpoint continuation with explicitly inferred added context; not accepted")
        scenario["metadata"]["provenance"] = dict(source_geometry_file=record["geometry_file"],
            source_geometry_sha256=record["geometry_sha256"], terrain_geometry_modified=False,
            checkpoint_overlap_state_exact=is_old, added_context_inferred_initial_state=not is_old,
            submerged_bed_is_uncalibrated_inference=True, normal_map_integrated=False)
        write_json(package/"scenario.json", scenario)
        result["packages"].append(name)
        result["inputs"].append(dict(name=name, source_geometry_sha256=record["geometry_sha256"],
            files={file: sha(package/file) for file in ("scenario.json", "bed.npy", "initial_state.npz", "features.json", "probes.json")}))
    restart.update(added_initial_water_volume_m3=added_volume, restart_initial_volume_m3=prior_volume+added_volume)
    if additions:
        geometry.update(core_count=len(result["packages"]), cell_count=len(result["packages"])*nx*ny,
                        captured_wet_cell_count=geometry["captured_wet_cell_count"]+sum(int(a["fields"]["captured_water_mask"].sum()) for a in additions),
                        added_restart_context_core_count=geometry.get("added_restart_context_core_count", 0)+len(additions),
                        hydraulic_state_solved=False, normal_map_integrated=False,
                        extension_from_manifest_sha256=manifest["geometry_manifest_sha256"],
                        new_exterior_wet_geometry_not_yet_audited=True)
        geometry.pop("remaining_interior_wet_exterior_faces", None)
        write_json(output/"geometry_manifest.json", geometry)
        result.update(geometry_manifest=(output/"geometry_manifest.json").relative_to(ROOT).as_posix(),
                      geometry_manifest_sha256=sha(output/"geometry_manifest.json"))
    write_json(output/"manifest.json", result)
    print(json.dumps(restart, indent=2))


if __name__ == "__main__":
    main()
