import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_liquid_surface_snapshot import verify_computed_surface


class ComputedSurfaceAuditTest(unittest.TestCase):
    def test_saved_gpu_result_and_scalar_identity(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root)
            phi=np.array([-1,1],dtype='<f4')
            phi.tofile(root/'input_phi.r32f')
            expected=np.array([[-2,0,0,0],[2,0,0,0]],dtype='<f2')
            expected.tofile(root/'surface.rgba16f')
            manifest=dict(grid_cells=[2,1,1],input_scalar_sha256=hashlib.sha256(phi.tobytes()).hexdigest())
            expected.tofile(root/'gpu_surface.rgba16f')
            self.assertTrue(verify_computed_surface(root,manifest,root))
            for index,value in ((0,float('nan')),(0,2),(0,-3),(1,1)):
                bad=expected.copy()
                bad.flat[index]=value
                bad.tofile(root/'gpu_surface.rgba16f')
                self.assertFalse(verify_computed_surface(root,manifest,root))
            expected.tofile(root/'gpu_surface.rgba16f')
            (-phi).tofile(root/'input_phi.r32f')
            self.assertFalse(verify_computed_surface(root,manifest,root))


if __name__=='__main__':
    unittest.main()
