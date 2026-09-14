"""Experimental cardinal-front hybrid SGN/shallow-water breaking closure.

Trigger/range source: Filippini, Kazolea & Ricchiuto (2016), section 6,
https://www.math.u-bordeaux.fr/~mricchiu/GN1D.pdf . This raster extension is NOT
their validated 1D scheme or a calibrated South Fork model. It detects contained
monotone free-surface fronts along both grid axes; a boundary-truncated front is
reported, not invented. No velocity/depth is capped, smoothed or repaired.
"""
import numpy as np
from fractions import Fraction


def surface_jumps(h,bed,axis):
    """Same represented free-surface difference with exact cancellation fallback."""
    other_h=np.roll(h,-1,axis);other_bed=np.roll(bed,-1,axis)
    dh=other_h-h;db=other_bed-bed;result=dh+db
    scale=abs(h)+abs(other_h)+abs(db)
    risk=(abs(result)<=64*np.finfo(h.dtype).eps*scale)&((h!=other_h)|(bed!=other_bed))
    for p in map(tuple,np.argwhere(risk)):
        result[p]=float(Fraction(float(other_h[p]))-Fraction(float(h[p]))+
                        Fraction(float(other_bed[p]))-Fraction(float(bed[p])))
    return result


def plateau_signs(jumps, graph):
    """Join exact-flat internal faces only between equal nonzero directions.

    A zero face is not an extremum. Opposing slopes, disconnected boundaries
    and entirely flat components remain separate; no small slope is rounded.
    """
    sign = np.sign(jumps).astype(np.int8); result = sign.copy(); n = len(sign)
    for i in np.flatnonzero(graph & (sign == 0)):
        before = (int(i)-1)%n
        for _ in range(n):
            if not graph[before] or sign[before] != 0: break
            before = (before-1)%n
        if not graph[before] or sign[before] == 0: continue
        after = (int(i)+1)%n
        for _ in range(n):
            if not graph[after] or sign[after] != 0: break
            after = (after+1)%n
        if graph[after] and sign[after] == sign[before]: result[i] = sign[before]
    return result


def dispersion_fraction(h, bed, mass_rate, pairs, dx, *, gamma=.6,
                        slope_angle_degrees=30., critical_froude=1.3, on_front=None):
    """Return cell-average nonbreaking fraction and transparent front counts.

    A contained front needs a surface-rate or slope trigger, and the depth-ratio
    bore Froude criterion. Its NSW band has width 7.5*(h_peak-h_trough), centered
    on its steepest face. Exact interval/cell overlap avoids inflating a band
    narrower than a cell. Orthogonal detections combine by maximum coverage.
    Using axis sections is a stated 2D approximation, not rotational invariance.
    Connectivity includes periodic seams only when supplied by the caller.
    """
    h, bed, ht = (np.asarray(v, dtype=float) for v in (h, bed, mass_rate))
    if (h.ndim != 2 or not h.size or bed.shape != h.shape or ht.shape != h.shape
            or not all(np.all(np.isfinite(v)) for v in (h, bed, ht)) or np.any(h < 0)
            or not np.isfinite(dx) or dx <= 0 or len(pairs) != 2
            or not np.isfinite(gamma) or not .3 <= gamma <= .65
            or not np.isfinite(slope_angle_degrees) or not 14 <= slope_angle_degrees <= 33
            or not np.isfinite(critical_froude) or critical_froude <= 1):
        raise ValueError('Invalid breaking-front inputs or physical criterion')
    coverage = np.zeros_like(h)
    stats = dict(detected_fronts=0, boundary_truncated_runs=0, subcell_fronts=0,
                 maximum_log10_bore_froude=0., maximum_band_width_m=0.)
    for axis, graph in zip((1, 0), pairs):
        graph = np.asarray(graph)
        if graph.shape != h.shape or graph.dtype != bool or np.any(graph & ((h <= 0) | (np.roll(h,-1,axis) <= 0))):
            raise ValueError('Invalid breaking-front wet connectivity')
        if h.shape[axis] == 1:
            if np.any(graph): raise ValueError('Self-connected breaking axis')
            continue
        # Differences before summation retain small water variations on a datum.
        jumps = surface_jumps(h,bed,axis)
        for row_index, (row_h, row_ht, row_graph, row_jump, row_cover) in enumerate(zip(
                np.moveaxis(h,axis,-1), np.moveaxis(ht,axis,-1),
                np.moveaxis(graph,axis,-1), np.moveaxis(jumps,axis,-1),
                np.moveaxis(coverage,axis,-1))):
            n = len(row_h); sign = plateau_signs(row_jump, row_graph)
            active = row_graph & (sign != 0)
            starts = np.flatnonzero(active & (~np.roll(active,1) | (sign != np.roll(sign,1))))
            for first in starts:
                faces = [int(first)]; last = int(first)
                while len(faces) < n:
                    following = (last+1)%n
                    if not active[following] or sign[following] != sign[first]: break
                    faces.append(following); last = following
                before, after = (first-1)%n, (last+1)%n
                if not row_graph[before] or not row_graph[after]:
                    stats['boundary_truncated_runs'] += 1
                    continue
                vertices = np.array([*faces, after], dtype=int)
                peak, trough = (after,first) if sign[first] > 0 else (first,after)
                hp, ht_depth = row_h[peak], row_h[trough]
                if hp <= ht_depth: continue
                # Log form retains genuine tiny positive troughs without
                # overflowing a squared depth ratio or imposing a depth floor.
                log_froude = float(np.log10(hp)-np.log10(ht_depth)+.5*np.log10(1+ht_depth/hp)-.5*np.log10(2))
                trigger = np.max(abs(row_jump[faces]))/dx >= np.tan(np.deg2rad(slope_angle_degrees)) or \
                    np.any(row_ht[vertices] >= gamma*np.sqrt(9.81*row_h[vertices]))
                if on_front is not None:
                    on_front(dict(axis=axis, row=row_index, first=int(first), after=int(after),
                        peak=int(peak), trough=int(trough), hp=float(hp), ht=float(ht_depth),
                        log_froude=log_froude, maximum_slope=float(np.max(abs(row_jump[faces]))/dx),
                        maximum_rate_margin=float(np.max(row_ht[vertices]-gamma*np.sqrt(9.81*row_h[vertices]))),
                        steepest=int(faces[int(np.argmax(abs(row_jump[faces])))]),
                        detected=bool(trigger and log_froude > np.log10(critical_froude))))
                if not trigger or log_froude <= np.log10(critical_froude): continue
                width = 7.5*(hp-ht_depth)
                face = faces[int(np.argmax(abs(row_jump[faces])))]
                center = (face+1)*dx  # cells have centers (i+.5)*dx
                radius = .5*width
                # Wrap the band only for a connected periodic seam. Closed
                # edge cells never receive a far-edge breaking region.
                offsets = (-n*dx,0.,n*dx) if row_graph[-1] else (0.,)
                left = np.arange(n)*dx
                band = np.zeros(n)
                for offset in offsets:
                    overlap = np.maximum(0., np.minimum(left+dx,center+offset+radius)-np.maximum(left,center+offset-radius))
                    band = np.maximum(band, overlap/dx)
                connected = np.zeros(n,dtype=bool); pending = [int(first)]
                while pending:
                    cell = pending.pop()
                    if connected[cell]: continue
                    connected[cell] = True
                    if row_graph[cell]: pending.append((cell+1)%n)
                    if row_graph[(cell-1)%n]: pending.append((cell-1)%n)
                row_cover[:] = np.maximum(row_cover, np.where(connected & (row_h>0),band,0.))
                stats['detected_fronts'] += 1
                stats['subcell_fronts'] += int(width < dx)
                stats['maximum_log10_bore_froude'] = max(stats['maximum_log10_bore_froude'],log_froude)
                stats['maximum_band_width_m'] = max(stats['maximum_band_width_m'],float(width))
    # Roundoff in interval endpoints may exceed unit coverage by a few ulps.
    # This only bounds an overlap fraction, never a state or a physical speed.
    coverage = np.minimum(coverage,1.)
    stats['breaking_cells'] = int(np.count_nonzero(coverage > 0))
    stats['fully_hydrostatic_cells'] = int(np.count_nonzero(coverage == 1))
    return 1.-coverage, stats
