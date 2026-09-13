"""Deterministic analytic loader fixture; never a river flow/visual acceptance cook.

Uses only the standard library. Run from any directory before the Unreal
RaftSim.M3.CartesianCropBoundaries regression. Retained in tmp, not staged in game.
"""
import hashlib
import json
import struct
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[2] / "tmp/cartesian-runtime-crop-fixture-v1"
    root.mkdir(parents=True, exist_ok=True)
    nx, ny = 31, 29
    formulas = {
        "bed": lambda r, c: 100.0 + .031*r + .017*c + .007*((r+2*c) % 5),
        "h": lambda r, c: 1.5 + .003*r + .005*c,
        "u": lambda r, c: -.3 + .001*r + .01*((r+c) % 3),
        "v": lambda r, c: .5 + .002*c,
        "wet_mask": lambda r, c: 1,
    }
    arrays = {}
    for name, formula in formulas.items():
        wet = name == "wet_mask"
        dtype = "|u1" if wet else "<f8"
        header = repr(dict(descr=dtype, fortran_order=False, shape=(ny, nx))).encode("ascii")
        header += b" " * ((-10-len(header)-1) % 64) + b"\n"
        payload = b"".join(struct.pack("B" if wet else "<d", formula(r, c))
                           for r in range(ny) for c in range(nx))
        data = b"\x93NUMPY\x01\x00" + struct.pack("<H", len(header)) + header + payload
        (root / f"{name}.npy").write_bytes(data)
        arrays[name] = dict(file=f"../{name}.npy", sha256=hashlib.sha256(data).hexdigest(),
                            dtype=dtype, shape=[ny, nx])
    manifest = dict(schema="raftsim.cooked_flow_fields.v1",
                    coordinate_system="cartesian_east_north_m", source_elevation_datum_m=220.,
                    provenance="Analytic loader regression only; not measured or solved river water",
                    grid=dict(nx=nx, ny=ny, dx_m=1., dy_m=1., origin_x_m=-5432., origin_y_m=3600.),
                    solver=dict(runtime_cartesian_coupled_config=True, solver_mode="finite_volume",
                                flux_scheme="hll", spatial_order=2, fixed_dt_s=.05, cfl=.2,
                                dry_tolerance=1.e-6, roughness_manning=.035, roughness_scale=1.,
                                bed_slope_source_scale=1., feature_strength_scale=0., preserve_initial_mass=False),
                    bands=[dict(band_id="analytic", arrays=arrays)])
    variants = {
        "valid": {}, "wrong_frame": {"coordinate_system": "station_lateral_m"},
        "replay_conflict": {"runtime_replay_offline_config": True},
        "physical_inlet": {"experimental_west_discharge_m3s": 45.},
        "first_order": {"spatial_order": 1}, "mass_correction": {"preserve_initial_mass": True},
        "forced": {"feature_strength_scale": 1.}, "wrong_roughness": {"roughness_manning": .041},
        "legacy": {"runtime_cartesian_coupled_config": False},
    }
    for name, changes in variants.items():
        candidate = json.loads(json.dumps(manifest))
        for key, value in changes.items():
            (candidate if key == "coordinate_system" else candidate["solver"])[key] = value
        directory = root / name
        directory.mkdir(exist_ok=True)
        (directory / "manifest.json").write_text(json.dumps(candidate, indent=2)+"\n", encoding="utf-8")
    print(f"Prepared {len(variants)} analytic manifests and five hashed arrays in {root}")


if __name__ == "__main__":
    main()
