"""Export hash-verified shared flow state and exact source packets for runtime QA.

Diagnostic only: normal-map integration and settling acceptance are never set.
Snapshot arrays remain immutable external dependencies; a release must stage
these exact dependencies explicitly, not this entire acquisition/cook directory.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2)+"\n", encoding="utf-8")


def array_meta(path, relative_to, shape, dtype):
    return dict(file=Path(os.path.relpath(path, relative_to)).as_posix(), sha256=sha(path), shape=list(shape), dtype=dtype)


def verified_packet_dependencies(reuse_root, record, origin, datum, expected):
    """Reuse immutable source arrays only, never state, centers or acceptance.

    The prior manifest's label/hash is insufficient: compare each decoded value
    to the freshly verified captured source in the current export's datum.
    """
    directory = reuse_root/record["name"]
    manifest = json.loads((directory/"manifest.json").read_text())
    assert manifest["schema"] == "raftsim.cooked_flow_fields.v1"
    assert manifest["coordinate_system"] == "cartesian_east_north_m"
    assert manifest["source_geometry_sha256"] == record["geometry_sha256"]
    assert manifest["source_elevation_datum_m"] == datum
    grid = manifest["grid"]
    assert (grid["nx"], grid["ny"], grid["dx_m"], grid["dy_m"]) == (321, 321, 1., 1.)
    assert np.array_equal([grid["origin_x_m"], grid["origin_y_m"]], origin)
    bands = [band for band in manifest["bands"] if band["band_id"] == "median_runnable"]
    assert len(bands) == 1
    result = {}
    for name, source in expected.items():
        meta = bands[0]["arrays"][name]
        path = (directory/meta["file"]).resolve()
        assert sha(path) == meta["sha256"], (record["name"], name, "dependency hash")
        values = np.load(path, mmap_mode="r", allow_pickle=False)
        assert meta["shape"] == list(source.shape) and np.dtype(meta["dtype"]) == source.dtype
        assert values.dtype == source.dtype and values.shape == source.shape
        assert np.array_equal(values, source), (record["name"], name, "source values")
        result[name] = path
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cook", type=Path)
    parser.add_argument("step", type=int)
    parser.add_argument("output", type=Path)
    parser.add_argument("--bank-audit", type=Path, required=True)
    parser.add_argument("--centers", type=Path, required=True)
    parser.add_argument("--source-union-manifest",type=Path,
                        help="Explicit source-verified compound packets matching this cook's terrain union")
    parser.add_argument("--reuse-source-packets", type=Path,
                        help="Reference verified unchanged bed/mask arrays from a prior export; do not copy them")
    args = parser.parse_args()
    output = args.output.resolve()
    assert not output.exists()
    cook = args.cook.resolve()
    flow_path = Path((cook/"input_manifest_path.txt").read_text().strip())
    assert sha(flow_path) == sha(cook/"input_manifest.json")
    flow = json.loads(flow_path.read_text())
    geometry_path = ROOT/flow["geometry_manifest"]
    assert sha(geometry_path) == flow["geometry_manifest_sha256"]
    geometry = json.loads(geometry_path.read_text())
    assert [r["name"] for r in geometry["regions"]] == flow["packages"]
    source_path = (ROOT/geometry["regions"][0]["source_geometry_file"]).parent/"manifest.json"
    assert sha(source_path) == geometry["source_manifest_sha256"]
    source = json.loads(source_path.read_text())
    centers = json.loads(args.centers.read_text())
    assert centers["source_manifest_sha256"] == sha(source_path)
    assert [r["window_id"] for r in centers["windows"]] == [r["name"] for r in source["regions"]]
    if geometry.get('terrain_union'):
        if not args.source_union_manifest:raise ValueError('Compound terrain requires explicit matching source packets')
        from south_fork_rock_union_packets import verify
        source=verify(args.source_union_manifest,geometry_path)
        # The old center evidence is retained, not relabelled. The verifier
        # proves identical packet grids, captured masks and declared coverage.
        assert source['retained_source_manifest_sha256']==centers['source_manifest_sha256']
    elif args.source_union_manifest:
        raise ValueError('A retained-terrain cook cannot use different union packets')
    frame = cook/f"frame_{args.step:06d}"
    complete = json.loads((frame/"complete.json").read_text())
    audit = json.loads(args.bank_audit.read_text())
    assert complete["step"] == args.step and complete["snapshot"]
    assert audit["step"] == args.step and audit["input_manifest_sha256"] == sha(flow_path)
    assert audit["h_sha256"] == sha(frame/"h.npy") and audit["all_artificial_banks_exactly_dry"]
    state = {name: np.load(frame/f"{name}.npy", mmap_mode="r", allow_pickle=False) for name in ("h", "u", "v")}
    count = len(flow["packages"])
    assert all(a.dtype == np.dtype("<f8") and a.shape == (count*80, 80) and np.isfinite(a).all() for a in state.values())
    assert state["h"].min() >= 0 and state["h"].max() <= 10 and np.hypot(state["u"], state["v"]).max() <= 20
    # Preserve >=1GiB after output, in addition to the remaining native frames.
    reuse_root = args.reuse_source_packets.resolve() if args.reuse_source_packets else None
    new_packets=sum(not reuse_root or 'terrain_union' in r for r in source['regions'])
    expected_bytes = new_packets*321*321*9 + count*80*80*8 + 12*1024**2
    assert shutil.disk_usage(output.parent).free > expected_bytes + 1024**3
    output.mkdir()
    atlas_dir = output/"atlas"
    atlas_dir.mkdir()
    bed = np.empty_like(state["h"])
    tiles = []
    for i, (record, checked) in enumerate(zip(geometry["regions"], flow["inputs"])):
        assert record["name"] == checked["name"]
        package = flow_path.parent/record["name"]
        assert sha(package/"bed.npy") == checked["files"]["bed.npy"]
        assert sha(package/"scenario.json") == checked["files"]["scenario.json"]
        scenario = json.loads((package/"scenario.json").read_text())
        grid = scenario["grid"]
        assert (grid["ny"], grid["nx"], grid["dx"], grid["dy"]) == (80, 80, 1., 1.)
        assert [grid["origin_x"], grid["origin_y"]] == record["grid_origin_local_m"]
        assert scenario["roughness"] == .035
        bed[i*80:(i+1)*80] = np.load(package/"bed.npy", allow_pickle=False)
        tiles.append(dict(origin_m=record["grid_origin_local_m"], source_geometry_sha256=record["geometry_sha256"]))
    np.save(atlas_dir/"bed.npy", bed)
    atlas_arrays = dict(bed=array_meta(atlas_dir/"bed.npy", atlas_dir, bed.shape, "<f8"))
    atlas_arrays.update({name: array_meta(frame/f"{name}.npy", atlas_dir, values.shape, "<f8") for name, values in state.items()})
    atlas = dict(schema="raftsim.cartesian_state_atlas.v1", tile_shape=[80, 80], grid_spacing_m=1.,
                 source_elevation_datum_m=flow["vertical_datum_navd88_m"], dry_tolerance=1.e-6,
                 tiles=tiles, arrays=atlas_arrays, physical_exterior_faces=flow["boundary_probes"],
                 source_frame=str(frame), source_time_seconds=complete["time_seconds"],
                 input_manifest_sha256=sha(flow_path), bank_audit_sha256=sha(args.bank_audit),
                 settled_hydraulics=False, normal_map_integrated=False)
    if geometry.get('terrain_union'):
        atlas['terrain_union']=geometry['terrain_union']
        atlas['source_union_manifest_sha256']=sha(args.source_union_manifest)
    write_json(atlas_dir/"manifest.json", atlas)
    atlas_hash = sha(atlas_dir/"manifest.json")
    origins = np.asarray([t["origin_m"] for t in tiles])
    validation = []
    streaming = dict(schema="raftsim.cartesian_water_streaming.v1", grid_spacing_m=1., advance_m=80.,
                     roughness_manning=.035, source_context_cells=3, minimum_raft_interior_margin_m=8.,
                     live_window_extent_m=[224., 224.], windows=[], settled_hydraulics=False, normal_map_integrated=False)
    verified_intersections = 0
    reused_packet_bytes = 0
    reused_dependencies = {}
    for i, (record, center_record) in enumerate(zip(source["regions"], centers["windows"])):
        source_file = ROOT/record["geometry_file"]
        assert sha(source_file) == record["geometry_sha256"]
        with np.load(source_file, allow_pickle=False) as packet:
            packet_bed = packet["bed_navd88_m"]-flow["vertical_datum_navd88_m"]
            captured = packet["captured_water_mask"].copy()
        assert packet_bed.dtype == np.dtype("<f8") and packet_bed.shape == (321, 321)
        assert captured.dtype == np.dtype("uint8") and np.all(captured <= 1)
        origin = np.asarray(record["grid_origin_local_m"])
        relative = origins-origin
        assert np.max(np.abs(relative-np.rint(relative))) < 1.e-7
        relative = np.rint(relative).astype(int)
        modeled = np.zeros((321, 321), dtype=bool)
        gathered = {name: np.zeros((321, 321)) for name in state} if i in (0, 400, 798) else None
        for tile in np.flatnonzero(np.all(relative < 321, axis=1) & np.all(relative+80 > 0, axis=1)):
            x, y = relative[tile]
            x0, y0 = max(0, x), max(0, y)
            x1, y1 = min(321, x+80), min(321, y+80)
            dest = np.s_[y0:y1, x0:x1]
            src = np.s_[tile*80+y0-y:tile*80+y1-y, x0-x:x1-x]
            assert not modeled[dest].any()
            assert np.array_equal(packet_bed[dest], bed[src]), record["name"]
            modeled[dest] = True
            verified_intersections += int((y1-y0)*(x1-x0))
            if gathered is not None:
                for name in state: gathered[name][dest] = state[name][src]
        directory = output/record["name"]
        directory.mkdir()
        source_arrays = dict(bed=packet_bed, captured_water_mask=captured)
        if reuse_root and 'terrain_union' not in record:
            dependencies = verified_packet_dependencies(reuse_root, record, origin,
                flow["vertical_datum_navd88_m"], source_arrays)
            reused_packet_bytes += sum(path.stat().st_size for path in dependencies.values())
            reused_dependencies[record["name"]] = {
                name: Path(os.path.relpath(path, output)).as_posix() for name, path in dependencies.items()}
        else:
            dependencies = {name: directory/f"{name}.npy" for name in source_arrays}
            for name, values in source_arrays.items(): np.save(dependencies[name], values)
        arrays = {name: array_meta(dependencies[name], directory, values.shape, values.dtype.str)
                  for name, values in source_arrays.items()}
        manifest = dict(schema="raftsim.cooked_flow_fields.v1", coordinate_system="cartesian_east_north_m",
                        source_elevation_datum_m=flow["vertical_datum_navd88_m"],
                        grid=dict(nx=321, ny=321, dx_m=1., dy_m=1., origin_x_m=float(origin[0]), origin_y_m=float(origin[1])),
                        solver=dict(runtime_cartesian_coupled_config=True, solver_mode="finite_volume", flux_scheme="hll",
                                    spatial_order=2, fixed_dt_s=.05, cfl=.2, dry_tolerance=1.e-6, roughness_manning=.035,
                                    roughness_scale=1., bed_slope_source_scale=1., feature_strength_scale=0., preserve_initial_mass=False),
                        bands=[dict(band_id="median_runnable", arrays=arrays,
                                    shared_cartesian_state=dict(manifest="../atlas/manifest.json", sha256=atlas_hash))],
                        source_geometry_sha256=record["geometry_sha256"], settled_hydraulics=False, normal_map_integrated=False)
        if 'terrain_union' in record:
            manifest['terrain_union']=record['terrain_union']
            manifest['retained_source_geometry_sha256']=record['retained_geometry_sha256']
            manifest['source_union_manifest_sha256']=sha(args.source_union_manifest)
        write_json(directory/"manifest.json", manifest)
        streaming["windows"].append(dict(window_id=record["name"],
            cooked_fields_manifest=(directory/"manifest.json").relative_to(ROOT).as_posix(),
            hydraulic_bounds_m=[*origin.tolist(), *(origin+320).tolist()],
            valid_live_center_bounds_m=center_record["valid_live_center_bounds_m"]))
        if gathered is not None and center_record["valid_live_center_bounds_m"]:
            rect = np.asarray(center_record["valid_live_center_bounds_m"][0])
            center = (rect[:2]+rect[2:])*.5
            low = np.floor(center-origin-112).astype(int)-2
            high = np.ceil(center-origin+112).astype(int)+2
            assert not ((captured != 0) & ~modeled)[low[1]:high[1]+1, low[0]:high[0]+1].any()
            dense_dir = output/(record["name"]+"_dense_reference")
            dense_dir.mkdir()
            dense = copy.deepcopy(manifest)
            dense["bands"][0].pop("shared_cartesian_state")
            dense_arrays = dict(bed=array_meta(dependencies["bed"], dense_dir, packet_bed.shape, "<f8"))
            gathered["wet_mask"] = (gathered["h"]>1.e-6).astype(np.uint8)
            for name, values in gathered.items():
                np.save(dense_dir/f"{name}.npy", values)
                dense_arrays[name] = array_meta(dense_dir/f"{name}.npy", dense_dir, values.shape, "|u1" if name=="wet_mask" else "<f8")
            dense["bands"][0]["arrays"] = dense_arrays
            write_json(dense_dir/"manifest.json", dense)
            validation.append(dict(shared=record["name"], dense=dense_dir.name, center_m=center.tolist()))
        if (i+1) % 100 == 0: print(f"Exported and verified {i+1}/{len(source['regions'])} packets", flush=True)
    write_json(output/"streaming_manifest.json", streaming)
    write_json(output/"validation_windows.json", dict(windows=validation, extent_m=[224., 224.]))
    report = dict(completed=True, source_packet_count=len(source["regions"]), atlas_tile_count=count,
                  exact_bed_intersection_cells=verified_intersections, atlas_manifest_sha256=atlas_hash,
                  source_manifest_sha256=sha(source_path), streaming_manifest_sha256=sha(output/"streaming_manifest.json"),
                  validation_window_count=len(validation), external_snapshot_dependencies={k: v["file"] for k, v in atlas_arrays.items() if k != "bed"},
                  reused_packet_count=len(reused_dependencies), reused_packet_bytes=reused_packet_bytes,
                  external_source_packet_dependencies=reused_dependencies,
                  settled_hydraulics=False, normal_map_integrated=False)
    if args.source_union_manifest:
        report['source_union_manifest_sha256']=sha(args.source_union_manifest)
        report['new_union_packet_count']=sum('terrain_union' in r for r in source['regions'])
    write_json(output/"export_audit.json", report)
    print(json.dumps({k: v for k, v in report.items() if k != "external_source_packet_dependencies"}, indent=2))


if __name__=="__main__":
    main()
