"""Scoped simulation-stage completion of omitted occupancy kernel centres.

Experimental: not a surface-foam or entrainment model. Never modifies particles,
types, emission potentials, original liquid fields or installed Blender files.
"""
import ctypes
import gc
import types
import manta
import numpy as np
from probe_water_feature_solver_stages import grid_array
from probe_eddy_secondary_classifier import int_grid
from water_feature_neighbor_ratio import complete_omitted_fluid_cells


def write_owned_real_grid(grid, values):
    shape = (grid.getSizeX(), grid.getSizeY(), grid.getSizeZ())
    if manta.DOUBLEPRECISION or values.shape != shape or not np.isfinite(values).all():
        raise ValueError('Supported finite float32 grid required')
    pointer = grid.getDataPointer()
    address = int(pointer, 16) if isinstance(pointer, str) else int(pointer)
    if address <= 0:
        raise ValueError('Null owned grid pointer')
    target = np.ctypeslib.as_array((ctypes.c_float*int(np.prod(shape))).from_address(address))
    target[:] = values.transpose(2, 1, 0).ravel()
    np.testing.assert_array_equal(grid_array(grid, shape), values)


class BoundaryCompletion:
    def __init__(self):
        self.original = manta.flipComputeSecondaryParticlePotentials
        self.calls, self.total_omitted, self.total_changed = 0, 0, 0
        self.maximum_completed_ratio = 0.
        self.namespaces = []
        self.callback = self.compute

    def compute(self, *args, **kwargs):
        if args:
            raise ValueError('Named installed-stage arguments required')
        result = self.original(**kwargs)
        flags, ratio, radius = kwargs['flags'], kwargs['neighborRatio'], kwargs['radius']
        shape = (flags.getSizeX(), flags.getSizeY(), flags.getSizeZ())
        integers = int_grid(flags, shape)
        for bit in (1, 2, 4, 8, 16):
            assert flags.countCells(flag=bit) == int(((integers & bit) != 0).sum())
        before = grid_array(ratio, shape)
        completed, omitted = complete_omitted_fluid_cells(integers, before, radius, 1, 2 | 8 | 16)
        write_owned_real_grid(ratio, completed)
        self.calls += 1
        self.total_omitted += int(omitted.sum())
        self.total_changed += int(np.sum(completed != before))
        self.maximum_completed_ratio = max(self.maximum_completed_ratio,
            float(completed[omitted].max()) if omitted.any() else 0.)
        return result

    def install(self):
        if manta.flipComputeSecondaryParticlePotentials is not self.original:
            raise ValueError('Another phase hook already exists')
        manta.flipComputeSecondaryParticlePotentials = self.callback
        # Existing evaluated domains use a separate native Python namespace.
        # Newly allocated domains import the temporarily patched manta function.
        for item in gc.get_objects():
            if (isinstance(item, types.ModuleType)
                    and item.__dict__.get('__file__') == '<manta_namespace>'):
                values = item.__dict__
                if values.get('flipComputeSecondaryParticlePotentials') is self.original:
                    self.namespaces.append(values)
                    values['flipComputeSecondaryParticlePotentials'] = self.callback

    def restore(self):
        manta.flipComputeSecondaryParticlePotentials = self.original
        for values in self.namespaces:
            values['flipComputeSecondaryParticlePotentials'] = self.original
        self.namespaces.clear()
        for item in gc.get_objects():
            if (isinstance(item, types.ModuleType)
                    and item.__dict__.get('__file__') == '<manta_namespace>'
                    and item.__dict__.get('flipComputeSecondaryParticlePotentials') is self.callback):
                item.__dict__['flipComputeSecondaryParticlePotentials'] = self.original

    def report(self):
        return dict(method='bounded occupancy completion at omitted interior-fluid kernel centres',
            native_compute_calls=self.calls, omitted_fluid_cell_visits=self.total_omitted,
            changed_cell_visits=self.total_changed, maximum_completed_ratio=self.maximum_completed_ratio,
            original_interior_ratios_preserved=True, thresholds_unchanged=True,
            particle_positions_or_types_directly_edited=False,
            scope='Correction applied before native particle generation/transport, not post-hoc relabeling. Does not constrain foam to interface or qualify bubble forces, generation rate, optical density or hydraulics.')
