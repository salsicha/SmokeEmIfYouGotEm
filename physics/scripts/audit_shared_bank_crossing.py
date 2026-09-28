"""Exact reload of native shared-edge GPU-coordinate candidates; not scene acceptance."""
import argparse
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import struct


def number(text):
    value = float(text)
    if not math.isfinite(value):
        raise ValueError("Nonfinite coordinate or donor")
    return F(value)


def audit_case(item):
    w, d, bw, bd, h, p, fraction, retreat, width = (
        number(item[key]) for key in (
            "wet_position_cm", "dry_position_cm", "wet_bed_m", "dry_bed_m",
            "depth_m", "position_cm", "fraction", "retreat_bound_cm", "width_cm"))
    if w == d or h <= 0 or bd - bw <= h or width <= 0:
        raise ValueError("Invalid high-bank edge")
    for value in (w, d, p):
        try:
            stored = struct.unpack("f", struct.pack("f", float(value)))[0]
        except OverflowError as error:
            raise ValueError("Unrepresentable GPU coordinate") from error
        if not math.isfinite(stored):
            raise ValueError("Unrepresentable GPU coordinate")
        if F(stored) != value:
            raise ValueError("GPU conversion changes the certified coordinate")
    t = (p - w) / (d - w)
    if not 0 <= t <= 1:
        raise ValueError("Stored coordinate outside original edge")
    # No depth epsilon and no reliance on native 'success' flags.
    depth = h - (bd - bw) * t
    if depth < 0:
        raise ValueError("Stored GPU coordinate is physically dry")
    root = w + (d - w) * h / (bd - bw)
    distance = abs(root - p)
    if not distance <= retreat <= width:
        raise ValueError("Geometric retreat not bounded by the original width")
    # Attribute fraction is the exact result of the specified binary64
    # arithmetic, not another independently rounded crossing position.
    expected_fraction = (float(p) - float(w)) / (float(d) - float(w))
    if fraction != F(expected_fraction):
        raise ValueError("Attribute fraction does not use the stored coordinate")
    return dict(exact_nonnegative_depth_m=str(depth), exact_retreat_cm=str(distance))


def audit(path, expected_sha256):
    raw = Path(path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise ValueError("Native export hash mismatch")
    data = json.loads(raw)
    if data["normal_renderer_integrated"] is not False or data["gameplay_accepted"] is not False:
        raise ValueError("Candidate edge proof cannot claim normal scene acceptance")
    donors = (
        (8.45587158203125, 8.711944580078125, .061720576137304306),
        (8.5344696044921875, 8.711944580078125, .17600621283054352),
        (7.7048187255859375, 9.9083251953125, .2190435528755188),
        (0., 2., 1.e-8), (0., 2., 1.), (0., 2., 1.999999))
    expected = [(origin, origin + direction * 100., *donor)
                for origin in (0., -543000., 361100., 1000000.)
                for direction in (-1., 1.) for donor in donors]
    if len(data["cases"]) != len(expected):
        raise ValueError("Missing native cases")
    results = []
    keys = ("wet_position_cm", "dry_position_cm", "wet_bed_m", "dry_bed_m", "depth_m")
    for item, identity in zip(data["cases"], expected):
        if tuple(number(item[key]) for key in keys) != tuple(map(F, identity)):
            raise ValueError("Original case identity changed")
        if number(item["width_cm"]) != F(.1):
            raise ValueError("Original one-millimetre width changed")
        results.append(audit_case(item))
    return dict(native_export_sha256=digest, cases=results, count=len(results),
                stored_gpu_coordinates_exactly_certified=True,
                normal_renderer_integrated=False, gameplay_accepted=False,
                whole_contour_world_mapping_accepted=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--native", required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.native, args.sha256), indent=2))
