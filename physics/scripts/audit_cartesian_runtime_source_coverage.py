"""Prove all declared continuous live-center rectangles have runtime state coverage.

Includes native physical-wet-exterior exclusions, not only captured-water masks.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--streaming-manifest", type=Path)
    parser.add_argument("--repair", type=Path, help="Write a fresh repaired streaming manifest after full-footprint validation")
    args = parser.parse_args()
    assert not args.report.exists()
    if args.repair: assert not args.repair.exists()
    directory = args.export.resolve()
    stream_path = args.streaming_manifest.resolve() if args.streaming_manifest else directory/"streaming_manifest.json"
    stream = json.loads(stream_path.read_text())
    atlas_path = directory/"atlas/manifest.json"
    atlas = json.loads(atlas_path.read_text())
    ny, nx = atlas["tile_shape"]
    dx = atlas["grid_spacing_m"]
    assert dx == stream["grid_spacing_m"] == 1.
    h_path = atlas_path.parent/atlas["arrays"]["h"]["file"]
    assert sha(h_path) == atlas["arrays"]["h"]["sha256"]
    h = np.load(h_path, mmap_mode="r", allow_pickle=False)
    origins = np.asarray([tile["origin_m"] for tile in atlas["tiles"]])
    excluded = []
    edges = dict(west=(-1, 0), east=(1, 0), south=(0, -1), north=(0, 1))
    for face in atlas["physical_exterior_faces"]:
        i, edge = face["tile_index"], face["edge"]
        tile = h[i*ny:(i+1)*ny]
        values = dict(west=tile[:, 0], east=tile[:, -1], south=tile[0], north=tile[-1])[edge]
        for along in np.flatnonzero(values != 0.):
            col = (0 if edge=="west" else nx-1) if edge in ("west", "east") else along
            row = (0 if edge=="south" else ny-1) if edge in ("south", "north") else along
            excluded.append(origins[i]+np.asarray([col, row])+edges[edge])
    excluded = np.asarray(excluded).reshape(-1, 2)
    failures = []
    rectangles = 0
    extra_excluded_cells = 0
    repaired_windows = []
    for window in stream["windows"]:
        path = ROOT/window["cooked_fields_manifest"]
        packet = json.loads(path.read_text())
        band = packet["bands"][0]
        assert band["shared_cartesian_state"]["sha256"] == sha(atlas_path)
        mask_path = path.parent/band["arrays"]["captured_water_mask"]["file"]
        assert sha(mask_path) == band["arrays"]["captured_water_mask"]["sha256"]
        captured = np.load(mask_path, allow_pickle=False)
        grid = packet["grid"]
        origin = np.array([grid["origin_x_m"], grid["origin_y_m"]])
        assert captured.shape == (grid["ny"], grid["nx"])
        modeled = np.zeros(captured.shape, dtype=bool)
        offsets = origins-origin
        assert np.max(np.abs(offsets-np.rint(offsets))) < 1.e-7
        offsets = np.rint(offsets).astype(int)
        for x, y in offsets[np.all(offsets < 321, axis=1) & np.all(offsets+np.array([nx, ny]) > 0, axis=1)]:
            modeled[max(0, y):min(321, y+ny), max(0, x):min(321, x+nx)] = True
        unknown = (captured != 0) & ~modeled
        for col, row in np.rint(excluded-origin).astype(int):
            if 0 <= row < grid["ny"] and 0 <= col < grid["nx"]:
                assert not modeled[row, col]
                extra_excluded_cells += int(not unknown[row, col])
                unknown[row, col] = True
        half = np.asarray(stream["live_window_extent_m"])*.5
        window_failed = False
        for index, bounds in enumerate(window["valid_live_center_bounds_m"]):
            rect = np.asarray(bounds)
            low = np.floor((rect[:2]-half)-origin).astype(int)-2
            high = np.ceil((rect[2:]+half)-origin).astype(int)+2
            assert np.all(low >= 0) and high[0] < grid["nx"] and high[1] < grid["ny"]
            missing = int(unknown[low[1]:high[1]+1, low[0]:high[0]+1].sum())
            if missing:
                failures.append(dict(window_id=window["window_id"], rectangle_index=index, missing_cells=missing))
                window_failed = True
            rectangles += 1
        if window_failed and args.repair:
            from prepare_south_fork_live_center_coverage import rectangles as merge_rectangles
            assert captured.shape == (321, 321) and np.array_equal(half, [112., 112.])
            x, y = np.meshgrid(np.arange(115, 206), np.arange(115, 206))
            integral = np.pad(unknown.astype(np.int32).cumsum(0).cumsum(1), ((1, 0), (1, 0)))
            missing = integral[y+115, x+115]-integral[y-114, x+115]-integral[y+115, x-114]+integral[y-114, x-114]
            safe = missing == 0
            quads = safe[:-1, :-1] & safe[1:, :-1] & safe[:-1, 1:] & safe[1:, 1:]
            covered = np.zeros(safe.shape, dtype=bool)
            for dy in (0, 1):
                for dx in (0, 1): covered[dy:dy+90, dx:dx+90] |= quads
            bounds = list(merge_rectangles(quads))
            for row in range(91):
                for a, _, b, _ in merge_rectangles((safe & ~covered)[row:row+1]):
                    bounds.append((a, row, b-1, row))
            window["valid_live_center_bounds_m"] = [(np.asarray(b)+np.tile(origin+115, 2)).tolist() for b in bounds]
            for bounds in window["valid_live_center_bounds_m"]:
                rect = np.asarray(bounds)
                low = np.floor((rect[:2]-half)-origin).astype(int)-2
                high = np.ceil((rect[2:]+half)-origin).astype(int)+2
                assert not unknown[low[1]:high[1]+1, low[0]:high[0]+1].any()
            repaired_windows.append(window["window_id"])
    result = dict(schema="raftsim.cartesian_runtime_source_coverage_audit.v1", passed=not failures,
                  streaming_manifest_sha256=sha(stream_path), atlas_manifest_sha256=sha(atlas_path),
                  source_windows=len(stream["windows"]), continuous_center_rectangles=rectangles,
                  physical_wet_exterior_cells=len(excluded), additional_unavailable_packet_cell_appearances=extra_excluded_cells,
                  failed_rectangles=failures, settling_accepted=False, normal_map_integrated=False)
    if args.repair:
        import rasterio
        from scipy.spatial import cKDTree
        base = ROOT/"physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach"
        route = json.loads((base/"playable_route/coordinate_map.json").read_text())
        with rasterio.open(base/"unknown_submerged_bed_mask.tif") as dataset:
            rows, cols = np.nonzero(dataset.read(1) == 1)
            water = np.column_stack((dataset.transform.c+(cols+.5)*2., dataset.transform.f-(rows+.5)*2.))-route["origin_utm_m"]
        packet_centers = np.asarray([(np.asarray(w["hydraulic_bounds_m"][:2])+w["hydraulic_bounds_m"][2:])*.5 for w in stream["windows"]])
        _, nearest = cKDTree(packet_centers).query(water, p=np.inf)
        unshifted = np.zeros(len(water), dtype=bool)
        all_rects = []
        for i, window in enumerate(stream["windows"]):
            probes = np.flatnonzero(nearest == i)
            rects = np.asarray(window["valid_live_center_bounds_m"]).reshape(-1, 4)
            all_rects.extend(rects)
            for rect in rects:
                unshifted[probes] |= np.all(water[probes] >= rect[:2], axis=1) & np.all(water[probes] <= rect[2:], axis=1)
        all_rects = np.asarray(all_rects)
        minimum_margin, maximum_shift = 112., 0.
        for point in water[~unshifted]:
            candidates = np.maximum(all_rects[:, :2], np.minimum(point, all_rects[:, 2:]))
            shift2 = np.square(candidates-point).sum(axis=1)
            center = candidates[np.argmin(shift2)]
            minimum_margin = min(minimum_margin, 112.-float(np.max(np.abs(center-point))))
            maximum_shift = max(maximum_shift, float(np.sqrt(shift2.min())))
        assert len(water) == 406823 and minimum_margin >= stream["minimum_raft_interior_margin_m"]
        result.update(passed=True, repaired_windows=repaired_windows, original_water_probes=len(water),
                      unchanged_water_centers=int(unshifted.sum()), shifted_water_centers=int((~unshifted).sum()),
                      minimum_raft_interior_margin_m=minimum_margin, maximum_center_shift_m=maximum_shift,
                      repaired_continuous_center_rectangles=len(all_rects))
        result["input_failed_rectangles"] = result.pop("failed_rectangles")
        result["failed_rectangles"] = []
        args.repair.write_text(json.dumps(stream, indent=2)+"\n", encoding="utf-8")
        result["repaired_streaming_manifest_sha256"] = sha(args.repair)
    args.report.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if failures and not args.repair: raise SystemExit(1)


if __name__=="__main__":
    main()
