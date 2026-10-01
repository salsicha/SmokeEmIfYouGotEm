"""Independent interior reconstruction of Blender 5.2's simple MAC extension.

Algorithm/flag definitions checked against Blender fbe6228777e7:
extern/mantaflow/preprocessed/fastmarch.cpp and grid.h (upstream Apache-2.0).
This is a diagnostic provenance model, NOT a qualified surface velocity field.
Boundary-copy behavior and obstacle-normal unprojection are deliberately absent.
Original cache values and flags are never changed. Unsupported values stay
numeric in the copy but must not be interpreted as velocity support.
"""
import numpy as np

FLUID, OBSTACLE = 1, 2
INTERIOR = (slice(1, -1),)*3


def reconstruct_extension(flags, velocity, distance=4, into_obstacle=False):
    """Rebuild component-wise layers from native fluid-adjacent face seeds.

Layer 1 denotes a seed, 2..distance+1 an extension, and 0 unsupported.
Native propagation does not reject obstacles; contact lineage records any
contributing obstacle-adjacent face. This is provenance, not a physical
invalidity judgment: a wall-normal zero seed can be legitimate.
"""
    flags, velocity = np.asarray(flags), np.asarray(velocity)
    if (flags.ndim != 3 or min(flags.shape) < 3 or flags.dtype != np.int32
            or velocity.shape != (*flags.shape, 3) or velocity.dtype != np.float32
            or not np.isfinite(velocity).all() or np.any(flags < 0)
            or isinstance(distance, (bool, np.bool_))
            or not isinstance(distance, (int, np.integer)) or not 0 <= distance <= 64
            or not isinstance(into_obstacle, (bool, np.bool_))):
        raise ValueError('Need matching finite float32 MAC/int32 flags, 3D grid, bounded integer distance')
    shape = flags.shape
    result = velocity.copy()
    layers = np.zeros_like(velocity, dtype=np.int32)
    lineage = np.zeros_like(velocity, dtype=bool)
    fluid, obstacle = (flags & FLUID) != 0, (flags & OBSTACLE) != 0
    # Native summation order matters in float32: +x,-x,+y,-y,+z,-z.
    neighbors = []
    for axis in range(3):
        for direction in (1, -1):
            sl = [slice(1, -1)]*3
            sl[axis] = slice(2, None) if direction == 1 else slice(None, -2)
            neighbors.append(tuple(sl))
    for component in range(3):
        preceding = [slice(1, -1)]*3
        preceding[component] = slice(None, -2)
        preceding = tuple(preceding)
        contact = obstacle[INTERIOR] | obstacle[preceding]
        seeds = fluid[INTERIOR] | fluid[preceding]
        if into_obstacle:
            seeds &= ~contact
        layer = layers[..., component]
        touched = lineage[..., component]
        values = result[..., component]
        layer[INTERIOR] = seeds.astype(np.int32)
        touched[INTERIOR] = seeds & contact
        for shell in range(1, distance+1):
            total = np.zeros(tuple(n-2 for n in shape), np.float32)
            count = np.zeros(total.shape, np.int32)
            parent_contact = np.zeros(total.shape, bool)
            for sl in neighbors:
                parents = layer[sl] == shell
                np.add(total, np.where(parents, values[sl], np.float32(0)), out=total)
                count += parents
                parent_contact |= parents & touched[sl]
            selected = (layer[INTERIOR] == 0) & (count > 0)
            # Cast divisor explicitly: float32 native Real sum / integer count.
            output = np.zeros_like(total)
            np.divide(total, count.astype(np.float32), out=output, where=count > 0)
            values[INTERIOR][selected] = output[selected]
            touched[INTERIOR][selected] = (parent_contact | contact)[selected]
            layer[INTERIOR][selected] = shell+1
    return dict(velocity=result, layers=layers, obstacle_contact_lineage=lineage,
                distance=distance, into_obstacle=bool(into_obstacle),
                boundary_supported=False, physical_accuracy_accepted=False)


def corner_provenance(reconstruction, cell_coordinate):
    """Expose all eight lower-face stencil sources per component, no sampling.

Coordinates are in native grid cells measured from the domain's lower corner.
Even zero-weight corners are retained for conservative, comparable coverage.
"""
    coordinate = np.asarray(cell_coordinate, float)
    layers = reconstruction['layers']
    if coordinate.shape != (3,) or not np.isfinite(coordinate).all():
        raise ValueError('Need finite 3D native-cell coordinate')
    bits = np.array([(i, j, k) for i in (0, 1) for j in (0, 1) for k in (0, 1)])
    rows = []
    for component in range(3):
        offset = np.full(3, .5); offset[component] = 0
        lower = np.floor(coordinate-offset).astype(int)
        ids = lower+bits
        if np.any(ids < 0) or np.any(ids >= np.asarray(layers.shape[:3])):
            return None
        ls = layers[(*ids.T, np.full(8, component))]
        touched = reconstruction['obstacle_contact_lineage'][(*ids.T, np.full(8, component))]
        rows.append(dict(component=component, corner_indices=ids.tolist(),
            layers=ls.tolist(), seed_corners=int((ls == 1).sum()),
            extrapolated_corners=int((ls > 1).sum()), unsupported_corners=int((ls == 0).sum()),
            obstacle_lineage_corners=int(touched.sum())))
    return dict(components=rows, all_corners_supported=all(r['unsupported_corners'] == 0 for r in rows),
                any_obstacle_lineage=any(r['obstacle_lineage_corners'] > 0 for r in rows),
                accepted=False)
