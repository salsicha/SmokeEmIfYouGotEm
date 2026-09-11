import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_liquid_affine_transfer import compare,shader_text
from liquid_affine_transfer import to_particles


class AffineAuditTests(unittest.TestCase):
    def test_quadratic_moment_is_not_a_trilinear_derivative(self):
        rows,grid,boundary,extents=self.fixture()
        grid=np.random.default_rng(30).normal(size=grid.shape)*100
        points=rows[:,1:4]+[extents[0]/2,extents[1]/2,0]
        _,moment=to_particles(points,grid.transpose(2,1,0,3),extents/np.array(grid.shape[:3][::-1]),quadratic=True)
        rows[:,4:13]=moment.transpose(0,2,1).reshape(-1,9)
        self.assertTrue(compare(rows,grid,boundary,extents,quadratic=True)['gradient_parity'])
        self.assertFalse(compare(rows,grid,boundary,extents)['gradient_parity'])

    def test_quadratic_requires_its_complete_three_point_support(self):
        rows,grid,boundary,extents=self.fixture()
        rows[:,1:4]=[6-extents[0]/2,35-extents[1]/2,35]
        self.assertEqual(compare(rows,grid,boundary,extents)['supported_particles'],2)
        self.assertEqual(compare(rows,grid,boundary,extents,quadratic=True)['supported_particles'],0)

    def test_engine_utf16_and_utf8_shader_encoding(self):
        code='// RiverAffineGridToParticle'
        for encoding in ('utf-16','utf-8','utf-8-sig'):
            self.assertEqual(shader_text(code.encode(encoding)),code)

    def fixture(self):
        shape=(8,7,6);extents=np.array([80.,91.,66.]);h=extents/shape
        xyz=np.stack(np.meshgrid(*[(np.arange(n)+.5)*d for n,d in zip(shape,h)],indexing='ij'),axis=-1)
        c=np.array([[0.,-2.,.3],[2.,.1,.2],[.4,-.5,.6]])
        grid=np.einsum('ij,...j->...i',c,xyz).transpose(2,1,0,3)
        points=np.array([[30.,35.,35.],[50.,45.,45.]])
        local=points-[extents[0]/2,extents[1]/2,0]
        rows=np.column_stack([np.arange(2),local,np.tile(c.T.reshape(1,9),(2,1))])
        return rows,grid,np.zeros((*grid.shape[:3],4)),extents

    def test_exact_affine_state(self):
        report=compare(*self.fixture())
        self.assertTrue(report['gradient_parity'])
        self.assertLess(report['gradient_max_error_per_s'],1e-12)

    def test_zero_gradients_are_rejected(self):
        rows,grid,boundary,extents=self.fixture();rows[:,4:]=0
        self.assertFalse(compare(rows,grid,boundary,extents)['gradient_parity'])

    def test_actual_unit_coordinates_not_ideal_inverse(self):
        rows,grid,boundary,extents=self.fixture()
        unit=(rows[:,1:4]+[extents[0]/2,extents[1]/2,0])/extents
        rows=np.column_stack([rows,unit]);rows[:,1:4]+=1
        report=compare(rows,grid,boundary,extents)
        self.assertTrue(report['actual_gpu_sampling_coordinates'])
        self.assertTrue(report['gradient_parity'])

    def test_inactive_zero_sample_positions_are_rejected(self):
        rows,grid,boundary,extents=self.fixture();rows[:,1:]=0;rows[:,3]=-350
        report=compare(rows,grid,boundary,extents)
        self.assertFalse(report['gradient_parity']);self.assertEqual(report['supported_particles'],0)

    def test_transposed_gradient_is_rejected(self):
        rows,grid,boundary,extents=self.fixture();rows[:,4:]=rows[:,4:].reshape(-1,3,3).transpose(0,2,1).reshape(-1,9)
        self.assertFalse(compare(rows,grid,boundary,extents)['gradient_parity'])

    def test_solid_support_requires_zero_gradient(self):
        rows,grid,boundary,extents=self.fixture();boundary[...,3]=1
        report=compare(rows,grid,boundary,extents)
        self.assertFalse(report['gradient_parity']);self.assertGreater(report['unsupported_gradient_max_per_s'],0)


if __name__=='__main__':unittest.main()
