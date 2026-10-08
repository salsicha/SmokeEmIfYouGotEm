"""Keep inferred cuts from spreading into sampled, unmodified ground.

The Landscape vertex basis extends into six adjacent triangles. Testing
ownership only at a vertex misses protected ground inside that support. This
finite quarter-cell stencil is a construction safeguard, not a shoreline survey or a
guarantee about sub-probe features. It restores source heights; never raises
terrain above the original source or changes the source ownership classifier.
"""
import numpy as np

POLICY = 'native_2m_triangle_support_0p5m_probes_v1'


def support_policy(spacing_m=2.):
    if isinstance(spacing_m, bool) or spacing_m not in (1., 2.):
        raise ValueError('Supported canonical terrain spacing is 1 or 2 metres')
    return POLICY if spacing_m == 2. else 'native_1m_triangle_support_0p25m_probes_v1'


def support_offsets(spacing_m=2.):
    support_policy(spacing_m)
    # UE's diagonal runs (row,col)=(0,0) to (1,1). The nodal basis is
    # positive exactly inside this hexagon. Zero-weight boundary excluded.
    return np.array([(c*spacing_m/4, -r*spacing_m/4) for r in range(-3, 4) for c in range(-3, 4)
                     if abs(r-c) < 4], dtype=float)


def preserve_triangle_support(model, xy, result, *, spacing_m=2.):
    """Pure, batch/order/tile-independent guard on the declared lattice.

    Each proposed cut is retained only if all 37 positive-weight probes are
    themselves explicitly inferred by the original source model. Read global
    coordinates outside tile edges too, so adjacent exports make the same
    decision at shared vertices. Missing source support fails closed.
    """
    offsets = support_offsets(spacing_m)
    xy = np.asarray(xy, dtype=float)
    source = np.asarray(result['source_height_m'])
    height = np.asarray(result['height_m'])
    inferred = np.asarray(result['inferred_bed'])
    shape = source.shape
    if (xy.shape != shape+(2,) or height.shape != shape or inferred.shape != shape
            or inferred.dtype.kind != 'b' or not np.isfinite(xy).all()
            or not np.isfinite(source).all() or not np.isfinite(height).all()
            or not np.array_equal(inferred, height < source) or np.any(height > source)):
        raise ValueError('Finite aligned source and explicit lowering mask required')
    guarded = {k: np.array(v, copy=True) for k, v in result.items()}
    veto = np.zeros(shape, dtype=bool)
    selected = np.flatnonzero(inferred)
    for start in range(0, len(selected), 1024):
        take = selected[start:start+1024]
        queries = xy.reshape(-1, 2)[take, None, :]+offsets[None, :, :]
        probe = model.sample(queries.reshape(-1, 2))
        allowed = np.asarray(probe['inferred_bed'])
        ground = np.asarray(probe['source_height_m'])
        bed = np.asarray(probe['height_m'])
        expected = (len(take)*len(offsets),)
        if (allowed.shape != expected or allowed.dtype.kind != 'b'
                or ground.shape != expected or bed.shape != expected
                or not np.isfinite(ground).all() or not np.isfinite(bed).all()
                or not np.array_equal(allowed, bed < ground) or np.any(bed > ground)):
            raise ValueError('Incomplete or inconsistent triangle-support source')
        veto.flat[take] = ~allowed.reshape(len(take), -1).all(axis=1)
    guarded['height_m'][veto] = source[veto]
    guarded['inferred_bed'][veto] = False
    guarded['inference_support_veto'] = veto
    return guarded
