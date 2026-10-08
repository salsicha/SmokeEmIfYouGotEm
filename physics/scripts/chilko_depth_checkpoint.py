"""Atomic, source/code/configuration-bound checkpoints for long depth fits.

A checkpoint is supporting construction state, never an accepted depth asset.
Only the normal builder may publish a complete profile after every section fits.
"""
import hashlib
import json
import os
from pathlib import Path
import tempfile

import numpy as np
import scipy
import shapely


def array_digest(values):
    values=np.ascontiguousarray(values)
    digest=hashlib.sha256()
    digest.update(str(values.dtype).encode())
    digest.update(str(values.shape).encode())
    digest.update(values.tobytes())
    return digest.hexdigest()


def checkpoint_binding(model,frame,grid,discharge,roughness):
    # Pin the complete local script dependency set. An unrelated script edit
    # may conservatively invalidate a checkpoint; stale code must never reuse it.
    scripts=Path(__file__).resolve().parent
    return dict(schema='raftsim.chilko_depth_checkpoint.v1',source=model.receipt,
        grid=grid,discharge_m3s=discharge,manning_n=roughness,
        frame={key:array_digest(value) for key,value in sorted(frame.items())},
        initial_depth_sha256=array_digest(model.depth),
        implementation={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(scripts.glob('*.py'))},
        libraries=dict(numpy=np.__version__,scipy=scipy.__version__,shapely=shapely.__version__),
        batch_size=32,lateral_spacing_m=1.,lateral_half_extent_m=256.)


class DepthCheckpoint:
    def __init__(self,folder,binding,initial_depth,total_rows):
        self.folder=Path(folder)
        self.binding=json.dumps(binding,sort_keys=True,allow_nan=False)
        self.initial=np.asarray(initial_depth,dtype=float)
        self.total=int(total_rows)
        self.discharge=float(binding['discharge_m3s'])
        self.batch_size=int(binding['batch_size'])

    def validate(self,completed,depth,before,after,width):
        if (not 0<completed<=self.total or (completed!=self.total and completed%self.batch_size)
                or depth.shape!=self.initial.shape or np.any(depth<self.initial) or np.any(depth>10.)
                or any(a.shape!=(completed,) for a in (before,after,width))
                or not all(np.isfinite(a).all() for a in (depth,before,after,width))
                or np.any(before<0.) or np.any(after<self.discharge) or np.any(width<=0.)):
            raise ValueError('Invalid or incomplete depth checkpoint state')

    def load(self):
        path=self.folder/'latest.npz'
        if not path.exists():
            return 0,self.initial.copy(),[],[],[]
        with np.load(path,allow_pickle=False) as z:
            if str(z['binding'].item())!=self.binding:
                raise ValueError('Depth checkpoint source, code, grid or configuration changed; use a fresh checkpoint directory')
            completed=int(z['completed'].item())
            depth,before,after,width=[z[key].copy() for key in ('depth','before','after','width')]
        self.validate(completed,depth,before,after,width)
        return completed,depth,before.tolist(),after.tolist(),width.tolist()

    def save(self,completed,depth,before,after,width):
        depth,before,after,width=[np.asarray(a,dtype=float) for a in (depth,before,after,width)]
        self.validate(completed,depth,before,after,width)
        self.folder.mkdir(parents=True,exist_ok=True)
        # Keep the previous complete checkpoint until all new bytes are flushed.
        # A crash leaves only a uniquely named .partial, never a partial latest.
        with tempfile.NamedTemporaryFile(dir=self.folder,suffix='.partial',delete=False) as f:
            partial=Path(f.name)
            np.savez_compressed(f,binding=self.binding,completed=completed,depth=depth,
                before=before,after=after,width=width)
            f.flush();os.fsync(f.fileno())
        os.replace(partial,self.folder/'latest.npz')
