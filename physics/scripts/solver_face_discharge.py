"""Exact numerical discharge through every station section of a cooked frame.

The finite-volume solver transports mass by its face fluxes. On steep, shallow
reaches with wet/dry banks (hydrostatic reconstruction at 2 m cells), the
cell-centre sum of h*u overstates the transported discharge: on the Pacuare
Huacas cook by 2-34 % (median 10 %) per section while the face flux was
uniform to 0.2 %. This helper loads a frame as the initial state of a
scratch copy of the scenario package and asks the solver for its exact face
mass fluxes (--inspect-face-fluxes, no stepping).
"""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np

SOLVER_FLAGS = ['--solver-mode', 'finite_volume', '--boundary-mode', 'scenario', '--flux-scheme', 'hll',
                '--spatial-order', '2', '--cfl', '0.2', '--bed-slope-source-scale', '1',
                '--disable-fixture-calibrations']


def face_discharge(solver, scenario_dir, frame):
    """Discharge (m3/s) through each of the nx+1 station faces; frame = dict of (ny, nx) arrays."""
    scenario_dir = Path(scenario_dir)
    with tempfile.TemporaryDirectory() as tmp:
        pkg = Path(tmp) / 'scenario'
        shutil.copytree(scenario_dir, pkg)
        state = dict(np.load(scenario_dir / 'initial_state.npz'))
        for key, name in (('depth', 'h'), ('eta', 'eta'), ('u', 'u'), ('v', 'v'), ('hu', 'hu'), ('hv', 'hv')):
            state[key] = np.asarray(frame[name], dtype=state[key].dtype)
        state['wet'] = np.asarray(frame['wet']) > 0.5
        np.savez(pkg / 'initial_state.npz', **state)
        out = subprocess.run([str(solver), '--scenario', str(pkg), *SOLVER_FLAGS, '--inspect-face-fluxes'],
                             capture_output=True, text=True, check=True).stdout
    j = json.loads(out)
    assert j['units'] == 'm2/s' and j['sign'] == 'positive_grid_axis' and j['layout'] == 'row_major'
    nx, ny = j['nx'], j['ny']
    return np.array(j['x_faces'], float).reshape(ny, nx + 1).sum(0) * j['dy_m']
