"""Fresh experimental secondary simulation with a bounded kernel correction."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
from water_feature_secondary_boundary import BoundaryCompletion
from bake_aligned_eddy_particles import main


if __name__ == '__main__':
    # A prepared independent cache is mandatory inside main. No installed-file
    # patch, source-cache write, particle lift/relabel, force/radius tuning.
    if Path(bpy.data.filepath).resolve().parent.name != 'eddy-v4-boundary-completed':
        raise ValueError('Only the explicitly prepared fresh candidate is in scope')
    hook = BoundaryCompletion()
    try:
        hook.install()
        main(secondary_model=hook)
    finally:
        hook.restore()
