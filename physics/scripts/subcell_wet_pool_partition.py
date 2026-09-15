"""Separate disconnected source-supported pools at a FIXED water snapshot.

No volume correction or point/edge welding is used. This retains initial volume
and momentum to their measured storage-inversion error, not bit-exact remapping.
Changing pool stages/topology requires a new explicit transition mechanism.
"""
import math
import numpy as np

from triangle_cell_storage import TriangleCellStorage
from subcell_pressure_kinetic_geometry import local_form
from subcell_wet_connectivity import components
from subcell_source_region_faces import internal_faces
from subcell_exact_source_faces import source_faces
from subcell_source_frames import physical_datum, pool_form, absolute_interval, inside_interval, trace_start
from subcell_source_face_section import stage_difference


class WetPoolPartition:
    def __init__(self, patch, sampler, origin, volumes, momenta, *, pressure_preconditioner='auto'):
        if pressure_preconditioner not in ('auto', 'spectral-frozen-depth'):
            raise ValueError('Unknown original-source pressure preconditioner')
        self.pressure_preconditioner = pressure_preconditioner
        origin = np.asarray(origin, float)
        v, p = np.asarray(volumes, float), np.asarray(momenta, float)
        if (origin.shape != (2,) or not np.isfinite(origin).all()
                or v.shape != patch.shape or p.shape != (*patch.shape, 2)
                or not np.isfinite(v).all() or not np.isfinite(p).all() or (v < 0).any()
                or np.any(p[v == 0] != 0)):
            raise ValueError('Original finite volume/momentum state and source origin required')
        self.patch, self.pools = patch, []
        self.sampler, self.origin = sampler, origin.copy()
        self.origin.setflags(write=False)
        self.source_face_cache = {}
        self.parent_pools = [[] for _ in patch.cells]
        self.reassembled_volumes = np.zeros_like(v).ravel()
        self.reassembled_momenta = np.zeros_like(p).reshape(-1, 2)
        self.maximum_gram_partition_error = 0.
        self.maximum_volume_tangent_partition_error = 0.
        for index, (cell, volume, momentum) in enumerate(zip(patch.cells, v.ravel(), p.reshape(-1, 2))):
            if volume == 0:
                continue
            row, col = divmod(index, patch.shape[1])
            center = origin+patch.spacing*[col, row]
            height = cell.relative_stage_for_volume(volume)
            graph = components(sampler, cell, center, patch.spacing, height)
            parent_form = local_form(cell, volume)
            velocity = momentum/volume
            combined_gram = np.zeros((3, 3))
            combined_tangent = np.zeros((3, 3))
            if hasattr(cell, 'source_datum'):
                bounds = absolute_interval(cell, height, physical_datum(cell))
                interval = [level-physical_datum(cell) for level in bounds]
            else:
                levels = np.unique(cell.relative_levels)
                if np.any(levels == height):
                    raise ValueError('Topology event requires explicit one-sided transition')
                lower = levels[levels < height]
                upper = levels[levels > height]
                interval = [float(lower.max()) if lower.size else -np.inf,
                            float(upper.min()) if upper.size else np.inf]
            for component in graph['components']:
                ids = component['source_triangle_indices']
                storage = cell.subset_sources(ids)
                pool_volume = component['volume_m3']
                if pool_volume <= 0:
                    raise ValueError('Wet source component has no represented positive volume')
                form = pool_form(storage, pool_volume)
                pool_index = len(self.pools)
                self.parent_pools[index].append(pool_index)
                self.pools.append(dict(parent=index, source_triangle_indices=ids, storage=storage,
                    volume=pool_volume, momentum=pool_volume*velocity, form=form,
                    parent_stage_offset=height, parent_datum=physical_datum(cell),
                    parent_topology_stage_interval=interval))
                if hasattr(cell, 'source_datum'):
                    self.pools[-1]['topology_absolute_stage_interval'] = absolute_interval(cell, height, physical_datum(cell))
                self.reassembled_volumes[index] += pool_volume
                self.reassembled_momenta[index] += pool_volume*velocity
                combined_gram += form['gram']
                combined_tangent += form['volume_derivative']*form['wet_area']/parent_form['wet_area']
            self.maximum_gram_partition_error = max(self.maximum_gram_partition_error,
                float(np.max(abs(combined_gram-parent_form['gram']))))
            self.maximum_volume_tangent_partition_error = max(self.maximum_volume_tangent_partition_error,
                float(np.max(abs(combined_tangent-parent_form['volume_derivative']))))
        self.reassembled_volumes = self.reassembled_volumes.reshape(v.shape)
        self.reassembled_momenta = self.reassembled_momenta.reshape(p.shape)
        self.maximum_volume_error = float(np.max(abs(self.reassembled_volumes-v)))
        self.maximum_momentum_error = float(np.max(abs(self.reassembled_momenta-p)))
        self.internal_faces = internal_faces(self)

    def with_regions(self, states):
        """Explicit candidate region state; NOT a conservative transition.

        Each record specifies parent, original source_triangle_indices, volume,
        momentum. Regions may touch but remain independent unknowns with real
        internal faces. No volume/momentum budget is invented for the caller.
        """
        result = object.__new__(type(self))
        result.__dict__ = self.__dict__.copy()
        result.pools = []
        result.parent_pools = [[] for _ in self.patch.cells]
        result.reassembled_volumes = np.zeros(self.patch.shape)
        result.reassembled_momenta = np.zeros((*self.patch.shape, 2))
        seen = set()
        for state in states:
            parent = state['parent']
            if not isinstance(parent, (int, np.integer)) or not 0 <= parent < len(self.patch.cells):
                raise ValueError('Original parent cell required')
            cell = self.patch.cells[parent]
            ids = list(state['source_triangle_indices'])
            volume, momentum = float(state['volume']), np.asarray(state['momentum'], float)
            if (not ids or any(not isinstance(i, (int, np.integer)) for i in ids)
                    or len(ids) != len(set(ids)) or not set(ids).issubset(set(cell.source_triangle_indices))
                    or any((parent, i) in seen for i in ids) or not np.isfinite(volume) or volume <= 0
                    or momentum.shape != (2,) or not np.isfinite(momentum).all()):
                raise ValueError('Disjoint original source regions with positive finite state required')
            seen.update((parent, i) for i in ids)
            storage = cell.subset_sources(ids)
            form = pool_form(storage, volume)
            row, col = divmod(parent, self.patch.shape[1])
            center = self.origin+self.patch.spacing*[col, row]
            connected = components(self.sampler, storage, center, self.patch.spacing, form['stage_offset'])
            if connected['component_count'] != 1 or set(connected['components'][0]['source_triangle_indices']) != set(ids):
                raise ValueError('Each region must be one wet connected source set; dry support needs activation')
            height = stage_difference(0., physical_datum(cell), form['stage_offset'], form['datum'])
            bounds = absolute_interval(cell, form['stage_offset'], form['datum'])
            interval = [level-physical_datum(cell) for level in bounds]
            index = len(result.pools)
            result.parent_pools[parent].append(index)
            result.pools.append(dict(parent=parent, source_triangle_indices=sorted(ids), storage=storage,
                volume=volume, momentum=momentum.copy(), form=form, parent_stage_offset=height,
                parent_datum=physical_datum(cell), parent_topology_stage_interval=interval,
                topology_absolute_stage_interval=bounds))
            result.reassembled_volumes.flat[parent] += volume
            result.reassembled_momenta.reshape(-1, 2)[parent] += momentum
        if not result.pools:
            raise ValueError('At least one positive source region required')
        for key in ('maximum_volume_error', 'maximum_momentum_error', 'maximum_gram_partition_error',
                    'maximum_volume_tangent_partition_error'):
            setattr(result, key, None)
        result.is_region_state = True
        result.internal_faces = internal_faces(result)
        return result

    def volume_probe(self, volumes):
        """Independent-stage geometry probe within the original topology interval.

        This is not an integrator or a merge/wetting transition. Original pool
        velocities are merely retained as metadata; no dynamics are inferred.
        """
        volumes = np.asarray(volumes, float)
        if volumes.shape != (len(self.pools),) or not np.isfinite(volumes).all() or (volumes <= 0).any():
            raise ValueError('One positive finite volume per existing wet pool required')
        result = object.__new__(type(self))
        result.__dict__ = self.__dict__.copy()
        result.pools = []
        result.is_volume_probe = True
        result.reassembled_volumes = np.zeros(self.patch.shape)
        result.reassembled_momenta = np.zeros((*self.patch.shape, 2))
        # Original-source partition error metrics are not measurements of this
        # deliberately perturbed state.
        for key in ('maximum_volume_error', 'maximum_momentum_error',
                    'maximum_gram_partition_error', 'maximum_volume_tangent_partition_error'):
            setattr(result, key, None)
        for old, volume in zip(self.pools, volumes):
            form = pool_form(old['storage'], volume)
            parent_height = stage_difference(0., old['parent_datum'], form['stage_offset'], form['datum'])
            low, high = old['parent_topology_stage_interval']
            if 'topology_absolute_stage_interval' in old:
                low, high = old['topology_absolute_stage_interval']
                inside = inside_interval(form['stage_offset'], form['datum'], low, high)
            else:
                inside = low < parent_height < high
            if not inside:
                raise ValueError('Volume probe crosses a source topology event; transition not implemented')
            pool = dict(old, volume=float(volume), form=form, parent_stage_offset=parent_height,
                        momentum=old['momentum']*(volume/old['volume']))
            result.pools.append(pool)
            result.reassembled_volumes.flat[pool['parent']] += volume
            result.reassembled_momenta.reshape(-1, 2)[pool['parent']] += pool['momentum']
        return result

    def boundary_segments(self, parent, axis, sign):
        """Original clipped face segments tagged by their wet pool owner.

        Segments may include a dry portion, but only wet source components are
        represented. Consumers must intersect BOTH owners' positive wet spans;
        two segments sharing a vertex alone are not a hydraulic connection.
        """
        if axis not in (0, 1) or sign not in (-1, 1):
            raise ValueError('Cartesian face direction required')
        owners = {}
        for pool_index in self.parent_pools[parent]:
            for source in self.pools[pool_index]['source_triangle_indices']:
                owners[source] = pool_index
        result = [(owners[source], segment) for source, segment in source_faces(self, parent, axis, sign) if source in owners]
        return sorted(result, key=lambda item: trace_start(item[1]))
