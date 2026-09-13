import sys
from pathlib import Path
import unittest
import tempfile
import hashlib
import json
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from diagnose_liquid_regional_advection import pair_order,replay,validate_transport_sources


class RegionalAdvectionTest(unittest.TestCase):
    def test_transport_include_snapshot_provenance(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary)
            names=('RaftSimLiquidCompactTransport.ush','RaftSimLiquidPhysicalFrame.ush','RaftSimLiquidInterface.usf')
            hashes={}
            for name in names:
                data=b'DFDemote(DFDivide(Numerator,Denominator))'
                (directory/name).write_bytes(data);hashes[name]=hashlib.sha256(data).hexdigest()
            (directory/'transport-sources.json').write_text(json.dumps(dict(schema='raftsim.liquid_transport_sources.v1',files_sha256=hashes)))
            (directory/'capture.json').write_text(json.dumps(dict(transport_sources_unchanged=True)))
            self.assertEqual(validate_transport_sources(directory),hashes)
            (directory/names[0]).write_text('changed')
            with self.assertRaises(ValueError):validate_transport_sources(directory)
            (directory/names[0]).write_bytes(data)
            (directory/'capture.json').write_text(json.dumps(dict(transport_sources_unchanged=False)))
            with self.assertRaises(ValueError):validate_transport_sources(directory)

    def test_identity_pair_and_duplicates(self):
        ids=np.array([[0,2,5,3],[1,0,7,4],[0,1,3,6]],dtype='u4')
        other=ids[[2,0,1]]
        np.testing.assert_array_equal(other[pair_order(ids,other)],ids)
        with self.assertRaises(ValueError):pair_order(ids,ids[[0,0,2]])
        with self.assertRaises(ValueError):pair_order(ids,ids[:2])
        self.assertEqual(len(pair_order(ids[:0],ids[:0])),0)

    def test_rotated_native_frame_and_affine_grid(self):
        h=np.array([50,50,100/3]);size=np.array([12,12,12])
        axes=np.array([[.8,-.6,0],[.6,.8,0],[0,0,1.]])
        origin=np.array([10000,-3000,350])
        nodes=(np.indices(tuple(size)).transpose(1,2,3,0)+.5)*h
        c=np.diag([.2,-.1,-.1]);grid=nodes@c.T+[120,50,3]
        local=np.array([[250,220,150],[210,280,190]])
        p=(local-size*h*[.5,.5,0])@axes+origin;dt=1/60
        expected,mode,valid,j,interior,_,_=replay(p,np.zeros_like(p),grid.transpose(2,1,0,3),
            np.zeros(tuple(size[::-1])),h,axes,origin,dt)
        np.testing.assert_allclose(expected,p+dt*((local@c.T+[120,50,3])@axes),atol=1e-10)
        np.testing.assert_allclose(j,np.broadcast_to(c,j.shape),atol=1e-12)
        self.assertTrue(mode.all() and valid.all() and interior.all())

    def test_solid_and_air_remain_ballistic_not_grid_driven(self):
        p=np.array([[0,0,4.],[1,0,4.]])
        for phase in (1,2):
            expected,mode,*_=replay(p,np.ones_like(p)*3,np.ones((8,8,8,3))*100,
                np.full((8,8,8),phase),np.ones(3),np.eye(3),np.zeros(3),.1)
            np.testing.assert_allclose(expected,p+.3)
            self.assertFalse(mode.any())

    def test_native_float_half_cell_classification(self):
        cells=np.array([134,68,24]);h=np.ones(3)
        inverse=np.eye(4,dtype='f4');inverse[:3,:3]=np.diag(1/cells)
        # Choose the captured float unit coordinate that rounds to q=49.5.
        inverse[3,0]=np.float32(50/134)
        inverse[3,1:3]=.2
        types=np.zeros(tuple(cells[::-1]));types[:,:,50]=1
        result=replay(np.zeros((1,3)),np.ones((1,3)),np.zeros((*types.shape,3)),
            types,h,np.eye(3),np.zeros(3),.1,(inverse,np.eye(4)))
        self.assertEqual(result[-1][0],1)
        self.assertFalse(result[1][0])

    def test_unified_rotated_frame_midpoint_transport(self):
        cells=np.array([12,12,12]);h=np.array([50,50,100/3])
        axes=np.array([[.8,-.6,0],[.6,.8,0],[0,0,1.]])
        frame=np.eye(4,dtype='f4');frame[:3,:3]=(cells*h)[:,None]*axes
        frame[3,:3]=[10000,-3000,350]
        inverse=np.linalg.inv(frame).astype('f4')
        vector_frame=np.eye(4,dtype='f4');vector_frame[:3,:3]=axes
        local=np.array([[250,220,150],[210,280,190]])
        p=(local@axes+frame[3,:3]).astype('f4')
        nodes=(np.indices(tuple(cells)).transpose(1,2,3,0)+.5)*h
        gradient=np.diag([.2,-.1,-.1]);offset=np.array([120,50,3])
        grid=(nodes@gradient.T+offset).transpose(2,1,0,3)
        dt=1/60
        expected,mode,*_=replay(p,np.zeros_like(p),grid,np.zeros(tuple(cells[::-1])),
            h,axes,frame[3,:3],dt,(inverse,vector_frame),True,frame)
        initial=local@gradient.T+offset
        midpoint=local+.5*dt*initial
        np.testing.assert_allclose(expected,p+dt*((midpoint@gradient.T+offset)@axes),atol=.001,rtol=0)
        self.assertTrue(mode.all())

    def test_unified_solid_fallback_preserves_legacy_position(self):
        cells=np.array([12,12,12]);frame=np.eye(4,dtype='f4')
        frame[:3,:3]*=12
        inverse=np.linalg.inv(frame).astype('f4');inverse[3,0]=.1
        p=np.array([[4.2,5.2,5.2]],dtype='f4')
        types=np.zeros((12,12,12));types[:,:,4]=1
        grid=np.ones((12,12,12,3))*10;velocity=np.ones_like(p)*2
        args=(p,velocity,grid,types,np.ones(3),np.eye(3),np.zeros(3),.1,(inverse,np.eye(4)))
        legacy=replay(*args)[0]
        unified=replay(*args,True,frame)
        self.assertFalse(unified[1][0])
        np.testing.assert_array_equal(unified[0],legacy)


if __name__=='__main__':unittest.main()
