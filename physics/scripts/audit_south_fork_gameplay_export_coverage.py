"""Audit exact coupled-state coverage before exporting gameplay source packets.

No flow is invented outside the solved tile union. This writes only a fresh
coverage/index report; it neither promotes a transient snapshot nor changes maps.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach"


def sha(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--original-water-domain", action="store_true")
    args = parser.parse_args()
    assert not args.output.exists(), "Preserve earlier audits"
    source_path = BASE / "hydraulic_regions_context/manifest.json"
    core_path = BASE / "coupled_geometry/manifest.json"
    source = json.loads(source_path.read_text())
    cores = json.loads(core_path.read_text())
    assert sha(source_path) == cores["source_manifest_sha256"]
    registry = {}
    for index, record in enumerate(cores["regions"]):
        path = ROOT / record["geometry_file"]
        assert sha(path) == record["geometry_sha256"]
        origin = tuple(int(v)-40 for v in record["center_utm_m"])
        assert origin not in registry
        with np.load(path, allow_pickle=False) as packet:
            registry[origin] = (index, packet["bed_navd88_m"])
    records, missing_integrals, unique_missing = [], {}, set()
    exact_cells = 0
    for record in source["regions"]:
        path = ROOT / record["geometry_file"]
        assert sha(path) == record["geometry_sha256"]
        with np.load(path, allow_pickle=False) as packet:
            bed = packet["bed_navd88_m"]
            captured_wet = packet["captured_water_mask"].astype(bool)
        assert bed.shape == (321, 321)
        sx, sy = (int(v)-160 for v in record["center_utm_m"])
        covered = np.zeros(bed.shape, dtype=bool)
        intersections = []
        for cy in range(((sy+40)//80)*80-40, sy+321, 80):
            for cx in range(((sx+40)//80)*80-40, sx+321, 80):
                entry = registry.get((cx, cy))
                if entry is None:
                    continue
                index, core_bed = entry
                x0, y0 = max(sx, cx), max(sy, cy)
                x1, y1 = min(sx+321, cx+80), min(sy+321, cy+80)
                region_slice = np.s_[y0-sy:y1-sy, x0-sx:x1-sx]
                core_slice = np.s_[y0-cy:y1-cy, x0-cx:x1-cx]
                assert not covered[region_slice].any(), "overlapping native core ownership"
                assert np.array_equal(bed[region_slice], core_bed[core_slice]), record["name"]
                covered[region_slice] = True
                exact_cells += (x1-x0)*(y1-y0)
                intersections.append(dict(core_index=index,
                    packet_slice=[y0-sy,y1-sy,x0-sx,x1-sx],
                    core_slice=[y0-cy,y1-cy,x0-cx,x1-cx]))
        missing = captured_wet & ~covered
        rows, columns = np.nonzero(missing)
        unique_missing.update(zip((columns+sx).tolist(), (rows+sy).tolist()))
        if missing.any():
            missing_integrals[record["name"]] = np.pad(missing.astype(np.int32).cumsum(0).cumsum(1), ((1,0),(1,0)))
        records.append(dict(name=record["name"], source_geometry_sha256=record["geometry_sha256"],
                            modeled_cells=int(covered.sum()), unmodeled_dry_cells=int((~covered & ~captured_wet).sum()),
                            unmodeled_captured_wet_cells=int(missing.sum()), intersections=intersections))
    # Replay the native current-source preference and full crop+3-cell margin
    # over the exact retained route and its +/-12m side probes.
    route = json.loads((BASE / "playable_route/coordinate_map.json").read_text())
    points = np.asarray(route["points"])
    origins = np.asarray([r["grid_origin_local_m"] for r in source["regions"]])
    upper = origins+320.
    active = None
    failures = []
    probe_count = 0
    for point in points:
        for side in (-12.,0.,12.):
            position = point[1:3]+side*point[3:5]
            margin = np.minimum(position-origins, upper-position).min(axis=1)
            eligible = margin >= 115.  # 224m crop / 2 plus 3-cell source context.
            if active is None or not eligible[active]:
                assert eligible.any(), "no native-compatible source selection"
                active = int(np.argmax(np.where(eligible,margin,-np.inf)))
            name = records[active]["name"]
            integral = missing_integrals.get(name)
            if integral is not None:
                low = np.floor(position-112.-origins[active]).astype(int)-2
                high = np.ceil(position+112.-origins[active]).astype(int)+3
                assert (low>=0).all() and (high<=321).all()
                x0,y0 = low; x1,y1 = high
                count = int(integral[y1,x1]-integral[y0,x1]-integral[y1,x0]+integral[y0,x0])
                if count:
                    failures.append(dict(station_m=float(point[0]), side_m=side, region=name,
                                         missing_captured_wet_cells=count))
            probe_count += 1
    report = dict(schema="raftsim.gameplay_export_coverage_audit.v1",
        source_manifest_sha256=sha(source_path), core_manifest_sha256=sha(core_path),
        source_packets=len(records), core_count=len(registry), exact_intersection_cells=exact_cells,
        packet_cells=sum(int(np.prod(r["shape"])) for r in source["regions"]),
        unmodeled_captured_wet_unique_cells=len(unique_missing),
        unmodeled_captured_wet_packet_cells=sum(r["unmodeled_captured_wet_cells"] for r in records),
        route_and_side_probes=probe_count, route_crop_and_ghost_failures=failures,
        all_selected_route_crops_have_captured_wet_state=not failures,
        all_full_packets_have_captured_wet_state=not unique_missing,
        source_bed_matches_every_modeled_cell=True, regions=records,
        settling_accepted=False, normal_map_integrated=False)
    if args.original_water_domain:
        import rasterio
        from scipy.spatial import cKDTree
        with rasterio.open(BASE / "unknown_submerged_bed_mask.tif") as dataset:
            rows, columns = np.nonzero(dataset.read(1) == 1)
            assert dataset.transform.a == 2. and dataset.transform.e == -2.
            water_points = np.column_stack((dataset.transform.c+(columns+.5)*2.,
                                             dataset.transform.f-(rows+.5)*2.))
        # These 2m raster centres and the 1m source samples share the integer
        # UTM lattice. A 224m crop plus two ghost layers reaches +/-114m.
        assert np.array_equal(water_points, np.rint(water_points))
        if unique_missing:
            missing_points = np.asarray(sorted(unique_missing))
            distance, nearest = cKDTree(missing_points).query(water_points, p=np.inf)
            bad = np.flatnonzero(distance <= 114.)
        else:
            bad = []
        report["original_water_domain_probes"] = len(water_points)
        report["original_water_domain_crop_ghost_failures"] = len(bad)
        report["original_water_domain_first_failures"] = [
            dict(position_utm_m=water_points[i].tolist(),
                 nearest_unmodeled_captured_wet_utm_m=missing_points[nearest[i]].tolist(),
                 chebyshev_distance_m=float(distance[i])) for i in bad[:20]]
        if len(bad):
            route_world = points[:,1:3]+np.asarray(route["origin_utm_m"])
            axis_distance, axis_index = cKDTree(route_world).query(water_points[bad])
            tangent = np.column_stack((points[:,4],-points[:,3]))
            projection = np.sum((water_points[bad]-route_world[axis_index])*tangent[axis_index],axis=1)
            classes = np.zeros(len(bad),dtype=np.uint8)
            classes[(axis_index==0)&(projection<0.)] = 1
            classes[(axis_index==len(points)-1)&(projection>0.)] = 2
            class_records = {}
            for code,name in enumerate(("beside_retained_route", "beyond_upstream_endpoint", "beyond_downstream_endpoint")):
                selected = classes==code
                record = dict(count=int(selected.sum()))
                if selected.any():
                    record.update(position_bounds_utm_m=[water_points[bad][selected].min(axis=0).tolist(),
                                                          water_points[bad][selected].max(axis=0).tolist()],
                                  nearest_station_range_m=[float(points[axis_index[selected],0].min()),
                                                            float(points[axis_index[selected],0].max())],
                                  axis_distance_range_m=[float(axis_distance[selected].min()),float(axis_distance[selected].max())],
                                  endpoint_tangent_projection_range_m=[float(projection[selected].min()),float(projection[selected].max())])
                class_records[name] = record
            failure_arrays_path = args.output.with_suffix(".failed-probes.npz")
            assert not failure_arrays_path.exists()
            failure_arrays_path.parent.mkdir(parents=True,exist_ok=True)
            np.savez_compressed(failure_arrays_path, position_utm_m=water_points[bad],
                nearest_unmodeled_wet_utm_m=missing_points[nearest[bad]],
                nearest_axis_index=axis_index, nearest_station_m=points[axis_index,0],
                axis_distance_m=axis_distance, endpoint_tangent_projection_m=projection,
                classification=classes)
            report["failure_classification"] = class_records
            report["all_failure_arrays"] = dict(file=str(failure_arrays_path),sha256=sha(failure_arrays_path),
                class_names=["beside_retained_route","beyond_upstream_endpoint","beyond_downstream_endpoint"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k not in ("regions", "route_crop_and_ghost_failures")},indent=2))
    print(f"Route crop/ghost failures: {len(failures)}; first ten: {failures[:10]}")


if __name__ == "__main__":
    main()
