"""Small analytic shared-atlas loader fixtures; not river acceptance evidence."""
import copy
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]/"tmp/cartesian-atlas-fixture-v1"


def array(name, ny, nx, formula, dtype="<f8"):
    header = repr(dict(descr=dtype, fortran_order=False, shape=(ny, nx))).encode("ascii")
    header += b" "*((-10-len(header)-1) % 64)+b"\n"
    fmt = {"<f8": "<d", "<f4": "<f", "|u1": "B"}[dtype]
    data = b"\x93NUMPY\x01\x00"+struct.pack("<H", len(header))+header
    data += b"".join(struct.pack(fmt, formula(r, c)) for r in range(ny) for c in range(nx))
    (ROOT/name).write_bytes(data)
    return dict(file="../"+name, sha256=hashlib.sha256(data).hexdigest(), dtype=dtype, shape=[ny, nx])


def json_file(path, value):
    text = json.dumps(value, indent=2)+"\n"
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ROOT.mkdir(exist_ok=True)
    formulas = dict(bed=lambda r, c: 100.+.031*r+.017*c+.007*((r+2*c) % 5),
                    h=lambda r, c: 1.5+.003*r+.005*c,
                    u=lambda r, c: -.3+.001*r+.01*((r+c) % 3),
                    v=lambda r, c: .5+.002*c)
    packet_bed = array("packet_bed.npy", 29, 31, formulas["bed"])
    shifted_bed = array("shifted_bed.npy", 29, 31, lambda r, c: formulas["bed"](r, c+1))
    bad_bed = array("bad_bed.npy", 29, 31, lambda r, c: formulas["bed"](r, c)+(.1 if (r, c)==(12, 12) else 0.))
    captured = array("captured.npy", 29, 31, lambda r, c: 1, "|u1")
    dry_exterior = array("dry_exterior.npy", 29, 31, lambda r, c: int(r<24 and c<24), "|u1")
    bad_mask = array("bad_mask.npy", 29, 31, lambda r, c: 2 if (r, c)==(12, 12) else 1, "|u1")
    tile = 12
    def global_rc(r, c):
        owner, row = divmod(r, tile)
        return row+(owner//2)*tile, c+(owner % 2)*tile
    atlas_arrays = {key: array("atlas_"+key+".npy", 48, 12,
                               lambda r, c, f=f: f(*global_rc(r, c))) for key, f in formulas.items()}
    float_h = array("atlas_h_f4.npy", 48, 12, lambda r, c: formulas["h"](*global_rc(r, c)), "<f4")
    nan_u = array("atlas_u_nan.npy", 48, 12, lambda r, c: float("nan") if (r, c)==(0, 0) else formulas["u"](*global_rc(r, c)))
    atlas = dict(schema="raftsim.cartesian_state_atlas.v1", tile_shape=[12, 12], grid_spacing_m=1.,
                 source_elevation_datum_m=220., dry_tolerance=1.e-6, arrays=atlas_arrays,
                 tiles=[dict(origin_m=[-5432.+(i % 2)*12, 3600.+(i//2)*12]) for i in range(4)],
                 physical_exterior_faces=[dict(tile_index=i, edge=edge) for i in range(4)
                     for edge in (("west" if i % 2==0 else "east"), ("south" if i//2==0 else "north"))])
    reference = {}
    for name in ("valid", "bad_array_hash", "duplicate_tile", "wet_artificial_edge", "fractional_tile", "float32", "nonfinite",
                 "dry_island", "missing_northeast"):
        candidate = copy.deepcopy(atlas)
        if name=="bad_array_hash": candidate["arrays"]["h"]["sha256"] = "0"*64
        if name=="duplicate_tile": candidate["tiles"][1] = copy.deepcopy(candidate["tiles"][0])
        if name=="wet_artificial_edge": candidate["physical_exterior_faces"] = []
        if name=="fractional_tile": candidate["tiles"][1]["origin_m"][0] += .5
        if name=="float32": candidate["arrays"]["h"] = float_h
        if name=="nonfinite": candidate["arrays"]["u"] = nan_u
        if name=="dry_island":
            for key in ("h", "u", "v"):
                candidate["arrays"][key] = array("island_"+key+".npy", 48, 12,
                    lambda r, c, f=formulas[key]: 0. if all(8<=i<=10 for i in global_rc(r, c)) else f(*global_rc(r, c)))
        if name=="missing_northeast":
            candidate["tiles"] = candidate["tiles"][:3]
            candidate["arrays"] = {key: array("missing_"+key+".npy", 36, 12,
                lambda r, c, f=f: f(*global_rc(r, c))) for key, f in formulas.items()}
            candidate["physical_exterior_faces"] = [face for face in candidate["physical_exterior_faces"] if face["tile_index"]<3]
            candidate["physical_exterior_faces"] += [dict(tile_index=1, edge="north"), dict(tile_index=2, edge="east")]
        directory = ROOT/("atlas_"+name)
        directory.mkdir(exist_ok=True)
        digest = json_file(directory/"manifest.json", candidate)
        reference[name] = dict(manifest="../atlas_"+name+"/manifest.json", sha256=digest)
    dense = json.loads((ROOT.parent/"cartesian-runtime-crop-fixture-v1/valid/manifest.json").read_text())
    for name in ("valid", "shifted_packet", "physical_dry_exterior", "bad_bed", "bad_mask", "wrong_grid", "wrong_datum", "wrong_tolerance",
                 "legacy", "mixed_dense", "bad_manifest_hash", "bad_array_hash", "duplicate_tile", "wet_artificial_edge",
                 "fractional_tile", "float32", "nonfinite", "dry_island", "missing_northeast"):
        candidate = copy.deepcopy(dense)
        band = candidate["bands"][0]
        band["arrays"] = dict(bed=packet_bed, captured_water_mask=captured)
        band["shared_cartesian_state"] = copy.deepcopy(reference.get(name, reference["valid"]))
        if name=="shifted_packet":
            candidate["grid"]["origin_x_m"] += 1.
            band["arrays"]["bed"] = shifted_bed
        if name=="bad_bed": band["arrays"]["bed"] = bad_bed
        if name=="bad_mask": band["arrays"]["captured_water_mask"] = bad_mask
        if name=="physical_dry_exterior": band["arrays"]["captured_water_mask"] = dry_exterior
        if name=="wrong_grid": candidate["grid"]["dx_m"] = 2.
        if name=="wrong_datum": candidate["source_elevation_datum_m"] = 221.
        if name=="wrong_tolerance": candidate["solver"]["dry_tolerance"] = 1.e-5
        if name=="legacy": candidate["solver"]["runtime_cartesian_coupled_config"] = False
        if name=="mixed_dense": band["arrays"]["h"] = dense["bands"][0]["arrays"]["h"]
        if name=="bad_manifest_hash": band["shared_cartesian_state"]["sha256"] = "0"*64
        directory = ROOT/name
        directory.mkdir(exist_ok=True)
        json_file(directory/"manifest.json", candidate)
    print("Prepared shared-atlas fixtures (analytic only): "+str(ROOT))


if __name__=="__main__":
    main()
