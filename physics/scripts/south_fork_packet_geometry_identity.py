"""Standard-library-only packet/geometry identity gate, including Unreal Python."""
from pathlib import Path
from package_runtime_bundle import sha

ROOT=Path(__file__).resolve().parents[2]


def verify_packet_geometry_identity(source, geometry, root=ROOT):
    """Reject stale packets before payload export or normal-scene mutation.

    Actual per-cell atlas and native collision checks remain mandatory.
    """
    retained=geometry['discharge_bed']
    path=(root/retained['retained_geometry_manifest']).resolve()
    if not path.is_relative_to(root.resolve()) or sha(path)!=retained['retained_geometry_manifest_sha256']:
        raise ValueError('Retained hydraulic geometry changed')
    if (source.get('hydraulic_geometry_manifest')!=retained['retained_geometry_manifest'] or
            source.get('hydraulic_geometry_manifest_sha256')!=retained['retained_geometry_manifest_sha256'] or
            not geometry.get('terrain_union') or source.get('terrain_union')!=geometry['terrain_union']):
        raise ValueError('Source packets belong to a different registered bed/rock union')
    for key in ('world_origin_utm_m','vertical_datum_navd88_m','grid_spacing_m'):
        if source.get(key)!=geometry[key]:
            raise ValueError('Source packet frame/lattice mismatch: '+key)
