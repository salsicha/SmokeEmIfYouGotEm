import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_liquid_gpu_density import audit


class GPUDensityAuditTest(unittest.TestCase):
    def fixture(self,root):
        source=root/'source';source.mkdir()
        output=root/'output';output.mkdir()
        density=np.zeros((3,2,2));density[0]=1
        matrix=np.eye(3)[None]
        reference=source/'reference.npz'
        np.savez(reference,density=density,matrix=matrix,sample_volumes=np.ones(1),minimum=np.zeros(3),extent=np.ones(3))
        positions=np.zeros((1,4),dtype='<f4')
        positions.tofile(output/'positions.rgba32f')
        manifest=dict(reference=str(reference),reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),
                      positions_sha256=hashlib.sha256(positions.tobytes()).hexdigest(),count=1)
        (source/'report.json').write_text(json.dumps(manifest))
        report=dict(source_directory=str(source),fixed_point_scale=1048576,diagnostics=[0]*4,gpu_dispatch_and_diagnostic_copy_ms=1)
        (output/'report.json').write_text(json.dumps(report))
        (density*1048576).astype('<u4').tofile(output/'density.u32')
        rows=np.zeros((1,3,4),dtype='<f4');rows[:,:,:3]=matrix;rows[0,0,3]=1
        rows.tofile(output/'kernels.rgba32f')
        (.5-density).astype('<f4').tofile(output/'scalar_readback.r32f')
        return output,rows,density

    def test_accepts_exact_field_and_rejects_bad_scalar_readback(self):
        with tempfile.TemporaryDirectory() as path:
            output,_,density=self.fixture(Path(path))
            self.assertTrue(audit(output)['numerical_parity_passed'])
            (.6-density).astype('<f4').tofile(output/'scalar_readback.r32f')
            self.assertFalse(audit(output)['numerical_parity_passed'])

    def test_kernel_and_provenance_checks_are_independent_of_surface(self):
        with tempfile.TemporaryDirectory() as path:
            output,rows,_=self.fixture(Path(path))
            rows[0,0,0]=2
            rows.tofile(output/'kernels.rgba32f')
            self.assertFalse(audit(output)['numerical_parity_passed'])
            rows[0,0,0]=1
            rows.tofile(output/'kernels.rgba32f')
            np.ones((1,4),dtype='<f4').tofile(output/'positions.rgba32f')
            self.assertFalse(audit(output)['numerical_parity_passed'])


if __name__=='__main__':
    unittest.main()
