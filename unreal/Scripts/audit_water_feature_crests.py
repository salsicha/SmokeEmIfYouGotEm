"""Read cached liquid profiles to distinguish a stationary crest from a surge.

This is a geometry diagnostic, not a conservation or turbulence validation.
Median transverse profiles suppress individual spray droplets but can still
include detached liquid; inspect the rendered view as well as this report.
"""
import argparse
import json
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--frames', nargs='+', type=int, default=list(range(168, 241, 6)))
    parser.add_argument('--crest-zone', nargs=2, type=float, default=[1.65, 2.95],
                        help='Fixed physical search region; defaults to the authored bump footprint')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if not all(np.isfinite(args.crest_zone)) or not 0 <= args.crest_zone[0] < args.crest_zone[1] <= 6:
        parser.error('Crest zone must be ordered within the 6 m flume')
    if args.output.exists():
        raise FileExistsError(args.output)
    xs = np.linspace(.6, 5.3, 95)
    rows = []
    for frame in args.frames:
        scene = bpy.context.scene
        if not scene.frame_start <= frame <= scene.frame_end:
            raise ValueError('Frame outside bake')
        scene.frame_set(frame)
        obj = bpy.data.objects['Feature liquid'].evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = obj.to_mesh()
        try:
            if len(mesh.vertices) <= 8:
                raise ValueError('Liquid mesh missing')
            bvh = BVHTree.FromPolygons([obj.matrix_world @ v.co for v in mesh.vertices],
                                      [list(p.vertices) for p in mesh.polygons])
            heights = []
            for x in xs:
                zs = []
                for y in [-.4, -.2, 0., .2, .4]:
                    hit, _, _, _ = bvh.ray_cast(Vector((x, y, 3.)), Vector((0., 0., -1.)))
                    if hit is not None:
                        zs.append(hit.z)
                heights.append(float(np.median(zs)) if len(zs) == 5 else None)
            if any(z is None for z in heights):
                raise ValueError('Incomplete transverse water coverage')
            # A three-point average only reduces one-mesh-cell noise. Retain
            # raw samples and do not assume any detected maximum is a wave.
            smooth = np.convolve(heights, np.ones(3)/3, mode='valid')
            sx = xs[1:-1]
            peaks = [dict(x_m=float(sx[i]), z_m=float(smooth[i]))
                     for i in range(1, len(smooth)-1)
                     if 1.5 <= sx[i] <= 4.8 and smooth[i] > smooth[i-1]
                     and smooth[i] >= smooth[i+1]]
            main_peak = max(peaks, key=lambda p: p['z_m']) if peaks else None
            zone_peaks = [p for p in peaks if args.crest_zone[0] <= p['x_m'] <= args.crest_zone[1]]
            zone_peak = max(zone_peaks, key=lambda p: p['z_m']) if zone_peaks else None
            rows.append(dict(frame=frame, seconds=(frame-1)/scene.render.fps,
                             median_z_m=heights, local_maxima=peaks, highest_peak=main_peak,
                             highest_peak_in_fixed_zone=zone_peak))
        finally:
            obj.to_mesh_clear()
    peaks = [r['highest_peak'] for r in rows if r['highest_peak'] is not None]
    summary = dict(frames_with_peak=len(peaks), total_frames=len(rows),
                   highest_peak_x_range_m=[min(p['x_m'] for p in peaks), max(p['x_m'] for p in peaks)] if peaks else None,
                   highest_peak_z_range_m=[min(p['z_m'] for p in peaks), max(p['z_m'] for p in peaks)] if peaks else None)
    zone_peaks = [r['highest_peak_in_fixed_zone'] for r in rows if r['highest_peak_in_fixed_zone'] is not None]
    summary.update(fixed_crest_zone_m=args.crest_zone, frames_with_zone_peak=len(zone_peaks),
                   zone_peak_x_range_m=[min(p['x_m'] for p in zone_peaks), max(p['x_m'] for p in zone_peaks)] if zone_peaks else None,
                   zone_peak_z_range_m=[min(p['z_m'] for p in zone_peaks), max(p['z_m'] for p in zone_peaks)] if zone_peaks else None)
    report = dict(source_blend=bpy.data.filepath, x_m=xs.tolist(), frames=rows,
                  summary=summary, accepted=False,
                  limitations='Highest local maximum may switch identity. No automatic stationary-wave acceptance; verify full profiles, flow-through and animation.')
    args.output.write_text(json.dumps(report, indent=2))
    print('CREST_SUMMARY', json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
