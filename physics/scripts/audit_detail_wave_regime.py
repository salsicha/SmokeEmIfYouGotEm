"""Compare the current detail PDE's wave regime to finite-depth Airy theory.

This is a model-applicability diagnostic, NOT a phase measurement or an
overturning-wave solver. Wavelengths are explicitly requested probes, not
wavelengths inferred from a picture or snapshot. Equations 2/3 in Jeschke and
Wojtan (2023): https://doi.org/10.1145/3592098.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def phase_speeds(depth, wavelength):
    depth = np.asarray(depth, dtype=np.float64)
    if not np.isfinite(wavelength) or wavelength <= 0:
        raise ValueError("Probe wavelength must be positive and finite")
    if not np.all(np.isfinite(depth)) or np.any(depth <= 0):
        raise ValueError("Wet depths must be positive and finite")
    k = 2 * np.pi / wavelength
    return np.sqrt(9.81 * depth), np.sqrt((9.81 / k) * np.tanh(k * depth))


def analyze(flow, state, cell_m, wavelengths):
    if flow.shape != state.shape or flow.ndim != 3 or flow.shape[2] != 4:
        raise ValueError("Expected matching row-major Y/X/float4 arrays")
    if not np.all(np.isfinite(flow)) or not np.all(np.isfinite(state)):
        raise ValueError("Nonfinite captured state")
    if np.any(flow[..., 0] < 0) or np.any(state[..., 3] < 0):
        raise ValueError("Negative captured depth or foam density")
    if not np.isfinite(cell_m) or cell_m <= 0:
        raise ValueError("Invalid cell size")
    wet = flow[..., 0] > .01
    if not np.any(wet):
        raise ValueError("No wet cells to analyze")
    depth = flow[..., 0][wet].astype(np.float64)
    eta = state[..., 0][wet].astype(np.float64)
    # Squared displacement weights only locate the current detail activity.
    # They are not full wave energy (momentum is excluded) or a spectrum.
    weights = eta * eta
    weight_sum = float(weights.sum())
    probes = []
    for wavelength in wavelengths:
        sw, airy = phase_speeds(depth, wavelength)
        error = sw / airy - 1
        probes.append(dict(wavelength_m=float(wavelength), cells_per_wavelength=wavelength / cell_m,
            median_sw_speed_mps=float(np.median(sw)), median_airy_speed_mps=float(np.median(airy)),
            median_relative_speed_excess=float(np.median(error)),
            maximum_relative_speed_excess=float(np.max(error)),
            wet_fraction_above_ten_percent=float(np.mean(error > .1)),
            squared_displacement_weighted_excess=float(np.dot(error, weights) / weight_sum) if weight_sum else None))
    return dict(wet_cells=int(wet.sum()), depth_min_m=float(depth.min()), depth_median_m=float(np.median(depth)),
        depth_max_m=float(depth.max()), detail_rms_m=float(np.sqrt(np.mean(weights))),
        detail_max_abs_m=float(np.max(abs(eta))), probes=probes)


def read_snapshot(path):
    metadata = json.loads(path.read_text(encoding="utf-8-sig"))
    shape = metadata.get("shape", [])
    if (metadata.get("schema") not in ("raftsim.detail.snapshot.v1", "raftsim.detail.snapshot.v2") or
            metadata.get("arrays_complete") is not True or
            metadata.get("dtype") != "little-endian float32" or
            len(shape) != 3 or shape[2] != 4 or
            any(type(n) is not int or n <= 0 for n in shape)):
        raise ValueError("Unsupported or incomplete snapshot metadata")
    names = ["flow", "state"]
    if metadata['schema'] == 'raftsim.detail.snapshot.v2':
        if (metadata.get('mean_geometry_channels') != ['bed_m', 'sampled_surface_m', 'unmasked_depth_m', 'wet_fraction']
                or metadata.get('height_datum') != 'river_vertical_datum'
                or not isinstance(metadata.get('mean_sample_elapsed_s'), (int, float))
                or not np.isfinite(metadata['mean_sample_elapsed_s'])
                or not 0 <= metadata['mean_sample_elapsed_s'] <= metadata['elapsed_s']):
            raise ValueError('Invalid paired mean geometry metadata')
        names.append('mean_geometry')
    arrays, hashes = {}, {str(path): hashlib.sha256(path.read_bytes()).hexdigest()}
    for name in names:
        source = path.with_suffix(f".{name}.f32")
        if source.stat().st_size != int(np.prod(shape)) * 4:
            raise ValueError(f"Truncated or oversized {name} array")
        arrays[name] = np.fromfile(source, dtype="<f4").reshape(shape)
        hashes[str(source)] = hashlib.sha256(source.read_bytes()).hexdigest()
    return metadata, arrays, hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshots", nargs="+", type=Path)
    parser.add_argument("--wavelengths", nargs="+", type=float, default=[2, 4, 8, 16])
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    results = []
    for path in args.snapshots:
        metadata, arrays, hashes = read_snapshot(path)
        results.append(dict(snapshot=str(path.resolve()), metadata=metadata, sha256=hashes,
            analysis=analyze(arrays["flow"], arrays["state"], metadata["cell_m"], args.wavelengths)))
    report = dict(schema="raftsim.detail_wave_regime.v1", scene_accepted=False,
        phase_speed_measured=False, wavelength_probes_measured=False,
        scope="Intrinsic constant-depth continuum phase speeds evaluated at captured local depths. "
              "Excludes discretization, damping, current Doppler shift, variable-bed scattering, "
              "finite-amplitude breaking and overturning. Squared displacement is not full wave energy. "
              "This diagnoses model assumptions, not reference-video agreement or an implemented correction.",
        theory_source="https://doi.org/10.1145/3592098", snapshots=results)
    with args.report.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps([r["analysis"] for r in results], indent=2))


if __name__ == "__main__":
    main()
