"""Exact whole-polygon proof after world mapping and binary32 GPU conversion."""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import re
import struct
from audit_shared_bank_crossing import number
from three_wet_bank_envelope import certificate, value


def cross(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def audit_case(item):
    bed, depth = (tuple(map(number, item[key])) for key in ("bed", "depth"))
    if len(bed) != 4 or len(depth) != 4 or depth[0] != 0 or any(
            depth[i] <= 0 or bed[0] <= bed[i]+depth[i] for i in (1, 2, 3)):
        raise ValueError("Original high-bank donor contract violated")
    origin, end = (tuple(map(number, item[key])) for key in ("origin_cm", "end_cm"))
    render_origin = tuple(map(number, item["render_origin_cm"]))
    if len(origin) != 2 or len(end) != 2 or len(render_origin) != 2:
        raise ValueError("Incomplete Cartesian coordinate map")
    delta = tuple(b-a for a, b in zip(origin, end))
    if not all(delta):
        raise ValueError("Degenerate Cartesian coordinate map")
    width = number(item["width_cm"])
    if width <= 0:
        raise ValueError("Nonpositive geometric band")
    for point in (origin, end):
        for coordinate, offset in zip(point, render_origin):
            v = coordinate-offset
            if number(struct.unpack("f", struct.pack("f", float(v)))[0]) != v:
                raise ValueError("Nonrepresentable source coordinate")

    def points(key, world):
        result = []
        for p in item[key]:
            if len(p) != 2:
                raise ValueError("Incomplete stored point")
            p = tuple(map(number, p))
            if world:
                for v in p:
                    if number(struct.unpack("f", struct.pack("f", float(v)))[0]) != v:
                        raise ValueError("GPU conversion changes submitted position")
                # Exact affine translation of actual binary32 buffer positions,
                # then exact inverse to the unchanged physical hydraulic cell.
                # No rounded native local inverse or ideal proposal is trusted.
                p = tuple((v+r-o)/d for v, r, o, d in zip(p, render_origin, origin, delta))
            if any(v < 0 or v > 1 for v in p):
                raise ValueError("Point outside original hydraulic cell")
            result.append(p)
        return tuple(result)

    boundary = points("boundary_buffer_cm", True)
    inner = points("inner_local", False)
    polygon = points("polygon_buffer_cm", True)
    if len(boundary) < 2 or len(inner) != len(boundary):
        raise ValueError("Incomplete geometric band")
    if polygon != ((F(1), F(1)), (F(1), F(0)), *boundary, (F(0), F(1))):
        raise ValueError("Polygon and stored boundary disagree")
    if boundary[0][1] != 0 or boundary[-1][0] != 0:
        raise ValueError("Lost canonical shared-edge identity")
    ideal_roots = ((1-depth[1]/(bed[0]-bed[1]), F(0)),
                   (F(0), 1-depth[2]/(bed[0]-bed[2])))
    for p, root in zip((boundary[0], boundary[-1]), ideal_roots):
        if any(v < r for v, r in zip(p, root)) or sum(abs((v-r)*d) for v, r, d in zip(p, root, delta)) > width:
            raise ValueError("Stored shared crossing is dry or outside geometric band")
    maximum_band = F(0)
    for p, q in zip(boundary, inner):
        distance_bound = max(map(abs, delta))*sum(abs(a-b) for a, b in zip(p, q))
        maximum_band = max(maximum_band, distance_bound)
        if distance_bound > width:
            raise ValueError("Stored polygon exceeds original geometric band")
    for p, q, a, b in zip(boundary, boundary[1:], inner, inner[1:]):
        if cross((0, 0), p, q) <= 0 or cross(p, q, b) < 0 or cross(p, b, a) < 0:
            raise ValueError("Invalid dry-side band partition")
        if not certificate(bed, depth, ((F(0), F(0)), a, b), -1):
            raise ValueError("Omitted area outside band not certified dry")
    triangles = item["triangles"]
    if len(triangles) != len(polygon)-2:
        raise ValueError("Incomplete stored-polygon triangulation")
    area, edges = F(0), {}
    for ids in triangles:
        if len(ids) != 3 or any(type(i) is not int or not 0 <= i < len(polygon) for i in ids):
            raise ValueError("Invalid triangle index")
        triangle = tuple(polygon[i] for i in ids)
        signed = cross(*triangle)
        if signed >= 0 or not certificate(bed, depth, triangle, 1):
            raise ValueError("Actual GPU triangle not wholly certified wet")
        area -= signed/2
        for a, b in zip(ids, (*ids[1:], ids[0])):
            edges.setdefault(tuple(sorted((a, b))), []).append((a, b))
    for (a, b), uses in edges.items():
        perimeter = b-a == 1 or (a, b) == (0, len(polygon)-1)
        if perimeter and len(uses) != 1:
            raise ValueError("Invalid perimeter incidence")
        if not perimeter and (len(uses) != 2 or uses[0] != uses[1][::-1]):
            raise ValueError("Invalid interior incidence")
    for i in range(len(polygon)):
        if tuple(sorted((i, (i+1) % len(polygon)))) not in edges:
            raise ValueError("Missing perimeter edge")
    omitted = sum(cross((0, 0), p, q)/2 for p, q in zip(boundary, boundary[1:]))
    if area+omitted != 1:
        raise ValueError("GPU polygon fails exact hydraulic-cell partition")
    return dict(segments=len(boundary)-1, triangles=len(triangles),
                exact_minimum_vertex_numerator=str(min(value(bed, depth, p) for p in polygon)),
                exact_maximum_band_cm=str(maximum_band), whole_gpu_geometry_certified=True)


def captured_rejection(path, expected_hash, frame, source=31556, dry_corner=0):
    raw = Path(path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_hash:
        raise ValueError(f"Original source{source} rejection log changed")
    pattern = (rf"\[\s*{frame}\]LogTemp: Display: CERTIFIED_BANK_REJECT source={source} dry={dry_corner} "
               r"reason=certificate stage=1 dry_xy=\(([^)]*)\) wetx_xy=\(([^)]*)\) "
               r"wety_xy=\(([^)]*)\) origin=\(([^)]*)\) bed=\(([^)]*)\) depth=\(([^)]*)\)")
    matches = re.findall(pattern, raw.decode("utf-8-sig"))
    if len(matches) != 1:
        raise ValueError(f"Missing unique original frame{frame}/source{source} donors")
    dry, wetx, wety, origin, bed, depth = (tuple(map(number, s.split(','))) for s in matches[0])
    if len(bed) != 4 or len(depth) != 4 or any(len(p) != 2 for p in (dry, wetx, wety, origin)):
        raise ValueError("Incomplete captured rejection")
    if dry[1] != wetx[1] or dry[0] != wety[0]:
        raise ValueError("Captured rejection is not Cartesian")
    return bed, depth, (dry, (wetx[0], wety[1]), origin), digest


def audit(path, expected_sha256, contact_path, rejection_path, later_rejection_path, latest_rejection_path, transition_rejection_path, axis_rejection_path):
    raw = Path(path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise ValueError("Native stored geometry hash mismatch")
    contact_raw = Path(contact_path).read_bytes()
    contact_hash = hashlib.sha256(contact_raw).hexdigest()
    if contact_hash != "bff4c53b8ad86c0003b40036862ae8c0e8e6aeb3a2e238e5e70ab0ff4dd2b74f":
        raise ValueError("Original contact capture changed")
    contact = json.loads(contact_raw)
    probes = [p for p in contact["ground_contact_probes"]
              if abs(p["x_cm"]+542609.86703267507) < 1.e-6
              and abs(p["y_cm"]+360212.23455268872) < 1.e-6]
    if len(probes) != 1 or probes[0]["raw_wet"] or probes[0]["raw_depth_m"] != 0:
        raise ValueError("Original raw-dry bank probe not retained")
    cell = probes[0]["source_cell"]
    order = (1, 0, 3, 2)
    if len(cell) != 4 or [cell[i]["source_id"] for i in order] != [26184, 26183, 26409, 26408]:
        raise ValueError("Original source-cell identity changed")
    bed = tuple(F(cell[i]["cached_bed_m"]) for i in order)
    depth = tuple(F(cell[i]["cached_depth_m"]) for i in order)
    data = json.loads(raw)
    if data["normal_renderer_integrated"] is not False or data["gameplay_accepted"] is not False:
        raise ValueError("Candidate proof cannot claim playable acceptance")
    captured_bed, captured_depth, captured_map, rejection_hash = captured_rejection(
        rejection_path, "dd457420acec052138fcc7cd50ca656e59c8ed99eb0fbcd0702d2b3f2166273a", 34)
    later_bed, later_depth, later_map, later_hash = captured_rejection(
        later_rejection_path, "709e34f3bd58baab49850200e2e2c0fe8c6d6aaddda186a116163c3ad6dcff88", 66)
    latest_bed, latest_depth, latest_map, latest_hash = captured_rejection(
        latest_rejection_path, "6293eed8a9114af3889ed27ed2113f96627285e782dc08c447ff5f80416dde89", 80)
    transition_bed, transition_depth, transition_map, transition_hash = captured_rejection(
        transition_rejection_path, "1d4d2429e1a4d7597abced20939c6a930a34361a8819b015e6781a895113fbfe", 186, 33168, 1)
    changed_bed, changed_depth, changed_map, axis_hash = captured_rejection(
        axis_rejection_path, "57820e57efb0f813f7a0058f4563bf162db1d8403fc0f3b96e35be82d9a36322", 183, 33168, 1)
    row_bed, row_depth, row_map, _ = captured_rejection(
        axis_rejection_path, "57820e57efb0f813f7a0058f4563bf162db1d8403fc0f3b96e35be82d9a36322", 292, 23259, 0)
    maps = (((-542600, -360200), (-542700, -360300), (-542600, -360200)),
            ((0, 0), (100, 100), (0, 0)),
            ((-542600, -360200), (-542500, -360300), (-542600, -360200)),
            ((361100, -543000), (361000, -542900), (361100, -543000)),
            ((-542600, -360200), (-542700, -360300), (-551000, -348600)), captured_map, later_map, latest_map, transition_map, changed_map, row_map)
    nx = cell[3]["source_id"]-cell[1]["source_id"]
    row, column = divmod(cell[1]["source_id"], nx)
    grid_origin = (F(cell[1]["field_x_m"])*100-column*100,
                   -F(cell[1]["field_y_m"])*100+row*100)
    if nx != 225 or grid_origin != maps[4][2]:
        raise ValueError("Original whole-grid render-origin binding changed")
    if len(data["cases"]) != len(maps):
        raise ValueError("Missing mapped cases")
    results = []
    for index, (item, coordinates) in enumerate(zip(data["cases"], maps)):
        expected_bed, expected_depth = ((row_bed, row_depth) if index == 10 else
                                        (changed_bed, changed_depth) if index == 9 else
                                        (transition_bed, transition_depth) if index == 8 else
                                        (latest_bed, latest_depth) if index == 7 else
                                        (later_bed, later_depth) if index == 6 else
                                        (captured_bed, captured_depth) if index == 5 else (bed, depth))
        if item["case"] != index or tuple(map(number, item["bed"])) != expected_bed or tuple(map(number, item["depth"])) != expected_depth:
            raise ValueError("Original same-call hydraulic donors changed")
        if tuple(map(number, item["origin_cm"])) != coordinates[0] or tuple(map(number, item["end_cm"])) != coordinates[1]:
            raise ValueError("Native world-coordinate test identity changed")
        if tuple(map(number, item["render_origin_cm"])) != coordinates[2]:
            raise ValueError("Explicit render translation identity changed")
        if number(item["width_cm"]) != F(.1):
            raise ValueError("Original one-millimetre budget changed")
        result = audit_case(item)
        result.update(case=index, construction_ms=item["construction_ms"])
        results.append(result)
    return dict(native_sha256=digest, contact_sha256=contact_hash, rejection_log_sha256=rejection_hash,
                later_rejection_log_sha256=later_hash, latest_rejection_log_sha256=latest_hash,
                transition_rejection_log_sha256=transition_hash, axis_rejection_log_sha256=axis_hash, cases=results,
                normal_renderer_integrated=False, gameplay_accepted=False,
                performance_accepted=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--native", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--contact", required=True)
    parser.add_argument("--rejection-log", required=True)
    parser.add_argument("--later-rejection-log", required=True)
    parser.add_argument("--latest-rejection-log", required=True)
    parser.add_argument("--transition-rejection-log", required=True)
    parser.add_argument("--axis-rejection-log", required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.native, args.sha256, args.contact, args.rejection_log,
                           args.later_rejection_log, args.latest_rejection_log, args.transition_rejection_log, args.axis_rejection_log), indent=2))
