"""Partition the captured full Colorado profile into overlapping source tiles.

Core intervals cover every source metre exactly once. Halos overlap for later
hydraulic/terrain handoff; they are not a claim that independently cooked water
already matches. No distance compression, synthetic rapid point or bed extrusion.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np

from build_colorado_catalog_windows import DEFAULT_SOURCE, PROFILE, read_profile, sha


def partition(profile, core_m=1200., halo_m=300.):
    if not (np.isfinite(core_m) and np.isfinite(halo_m) and
            200 <= core_m <= 2000 and 100 <= halo_m <= 500):
        raise ValueError('Bounded core/halo dimensions required')
    xy = np.array([[r['easting'], r['northing']] for r in profile], dtype=float)
    if len(xy) < 2 or not np.isfinite(xy).all():
        raise ValueError('Invalid source profile')
    delta = np.linalg.norm(np.diff(xy, axis=0), axis=1)
    if np.any(delta <= 0) or np.any(delta > 40):
        raise ValueError('Duplicate or disconnected source profile')
    station = np.r_[0., np.cumsum(delta)]
    products = []
    for i, start in enumerate(np.arange(0., station[-1], core_m)):
        finish = min(start + core_m, station[-1])
        lo = max(0, np.searchsorted(station, max(0, start-halo_m), side='right')-1)
        hi = min(len(station)-1, np.searchsorted(station, min(station[-1], finish+halo_m)))
        rows = []
        for j in range(lo, hi+1):
            row = dict(profile[j])
            kind = row['ws_final_source']
            if kind not in ('applanix', 'r10', 'DSM', 'interpolate - select', 'interpolate - no data'):
                raise ValueError('Unknown source evidence kind')
            row.update(local_arc_station_m=float(station[j]-station[lo]),
                global_arc_station_m=float(station[j]), source_profile_index=j,
                local_east_m=float(xy[j, 0]-xy[lo, 0]),
                local_north_m=float(xy[j, 1]-xy[lo, 1]),
                water_evidence_kind=('interpolated' if kind.startswith('interpolate') else
                                     'dsm_derived' if kind == 'DSM' else 'surveyed_gnss'))
            rows.append(row)
        products.append(dict(schema='raftsim.colorado_continuous_source_window.v1',
            name=f'Colorado continuous {i:04d}', tile_id=f'colorado_continuous_{i:04d}',
            source_core_interval_m=[float(start), float(finish)],
            source_halo_interval_m=[float(station[lo]), float(station[hi])],
            source_profile_indices=[int(lo), int(hi)],
            core_local_interval_m=[float(start-station[lo]), float(finish-station[lo])],
            horizontal_crs='EPSG:6404',
            vertical_datum='NAD83(2011) ellipsoid; only ws_final_navd88 is NAVD88',
            origin_east_north_m=xy[lo].tolist(), length_m=float(station[hi]-station[lo]),
            bounds_epsg6404=[*xy[lo:hi+1].min(axis=0).tolist(), *xy[lo:hi+1].max(axis=0).tolist()],
            rapid_point_local_station_m=None, construction_bounds_only=True,
            rapid_entry_exit_bounds_verified=False,
            profile_survey_flow_cfs_approx=8400, runtime_target_flow_cfs=8000,
            water_source_counts=dict(Counter(r['ws_final_source'] for r in rows)),
            samples=rows))
    return products


def build(source, registered_windows, out, core_m=1200., halo_m=300.):
    if out.exists():
        raise ValueError('Fresh output required')
    registered = json.loads((registered_windows/'index.json').read_text())
    profile_path = source/PROFILE
    source_digest = sha(profile_path)
    hashes = {str(k).replace('\\', '/').rsplit('/', 1)[-1]: v
              for k, v in registered['inputs_sha256'].items()}
    if (hashes.get(PROFILE.name) != source_digest or
            registered['source_rights'] != 'CC0 1.0 Universal'):
        raise ValueError('Profile identity/rights mismatch')
    products = partition(read_profile(profile_path), core_m, halo_m)
    out.mkdir(parents=True)
    for row in products:
        (out/(row['tile_id']+'.json')).write_text(json.dumps(row, indent=1, allow_nan=False)+'\n')
    result = dict(schema='raftsim.colorado_continuous_source_index.v1',
        source_profile_sha256=source_digest, source_doi=registered['source_doi'],
        source_rights=registered['source_rights'], source_rights_url=registered['source_rights_url'],
        route_length_m=products[-1]['source_core_interval_m'][1],
        core_length_m=core_m, halo_length_m=halo_m, runtime_ready=False,
        coverage='Entire captured profile; exact playable Pearce Ferry takeout remains separately registered',
        limitations=['Tile margins are not named rapid bounds.',
                     'Profile bed statistics are not full-width bathymetry.',
                     'Source overlap is not proof of matching cooked hydraulics or terrain seams.'],
        windows=[{k:v for k,v in row.items() if k != 'samples'} for row in products])
    (out/'index.json').write_text(json.dumps(result, indent=1, allow_nan=False)+'\n')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, default=DEFAULT_SOURCE)
    p.add_argument('--registered-windows', type=Path,
                   default=DEFAULT_SOURCE.parent/'catalog_construction_windows_2026_10_v1')
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    result = build(a.source, a.registered_windows, a.out)
    print(json.dumps(dict(tile_count=len(result['windows']), route_length_m=result['route_length_m'])))
