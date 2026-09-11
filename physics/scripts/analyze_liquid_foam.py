"""Audit actual GPU foam/SDF channels; a transport sanity check, not visual acceptance."""
import argparse
import json
from pathlib import Path
import numpy as np
from analyze_liquid_grid_readback import load_fields


def audit(directory):
    directory = Path(directory)
    fields = load_fields(directory)
    foam, sdf = fields['RiverFoam'][..., 0], fields['SDF'][..., 0]
    if foam.shape != (48, 136, 136) or sdf.shape != foam.shape:
        raise ValueError('Expected registered render grid')
    finite = bool(np.isfinite(foam).all() and np.isfinite(sdf).all())
    surface = np.abs(sdf) < 800/48
    report = dict(source=str(directory), finite=finite,
                  foam_range=[float(foam.min()), float(foam.max())],
                  sdf_range_cm=[float(sdf.min()), float(sdf.max())],
                  negative_sdf_cells=int((sdf < 0).sum()),
                  positive_sdf_cells=int((sdf > 0).sum()),
                  foam_nonzero_cells=int((foam > 0).sum()),
                  surface_band_cells=int(surface.sum()),
                  surface_foam_mean=float(foam[surface].mean()) if surface.any() else None,
                  surface_foam_percentiles=np.percentile(foam[surface], [50, 90, 95, 99]).tolist() if surface.any() else [],
                  production_or_visual_acceptance=False)
    report['channel_sanity_passed'] = bool(finite and (foam >= 0).all() and (foam <= 1).all()
                                         and (foam > 0).any() and (sdf < 0).any() and (sdf > 0).any())
    # The volume-band average includes submerged cells. Report the highest
    # upward zero crossing separately; it better describes visible top coverage.
    nz = sdf.shape[0]
    top = nz-1-np.argmax((sdf < 0)[::-1], axis=0)
    valid = (sdf < 0).any(axis=0) & (top < nz-1)
    top = np.minimum(top, nz-2)
    y, x = np.indices(top.shape)
    low, high = sdf[top, y, x], sdf[top+1, y, x]
    valid &= (low < 0) & (high >= 0)
    blend = np.divide(-low, high-low, out=np.zeros_like(low), where=high != low)
    top_foam = foam[top, y, x]*(1-blend)+foam[top+1, y, x]*blend
    report['highest_surface_crossing'] = dict(column_count=int(valid.sum()),
        foam_mean=float(top_foam[valid].mean()) if valid.any() else None,
        foam_percentiles=np.percentile(top_foam[valid], [50, 90, 95, 99, 100]).tolist() if valid.any() else [],
        scope='All render-grid columns, includes patch edge; linear vertical SDF crossing, not photographic coverage')
    metadata = json.loads((directory/'grids.json').read_text())
    volumes = metadata.get('render_target_volumes', [])
    report['renderer_channels_verified'] = False
    if len(volumes) == 1 and volumes[0]['readback_saved']:
        volume = volumes[0]
        nx, ny, nz = volume['size']
        pixels = np.fromfile(directory/volume['file'], dtype='<f2').reshape(nz, ny, nx, 4).astype(float)
        report['render_volume_pixel_format'] = volume['pixel_format']
        report['render_volume_nonfinite'] = int((~np.isfinite(pixels)).sum())
        report['render_green_range'] = [float(pixels[..., 1].min()), float(pixels[..., 1].max())]
        report['render_green_foam_max_difference'] = float(np.max(np.abs(pixels[..., 1]-foam)))
        report['render_red_sdf_max_difference_cm'] = float(np.max(np.abs(pixels[..., 0]-sdf)))
        report['renderer_channels_verified'] = bool(volume['pixel_format'] == 10 and np.isfinite(pixels).all()
                                                  and np.array_equal(pixels[..., 1], foam)
                                                  and np.array_equal(pixels[..., 0], sdf))
    report['pipeline_storage_passed'] = report['channel_sanity_passed'] and report['renderer_channels_verified']
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = audit(args.directory)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['pipeline_storage_passed'] else 1)
