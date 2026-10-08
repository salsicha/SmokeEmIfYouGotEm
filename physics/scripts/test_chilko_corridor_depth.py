import unittest
import tempfile
import json
from unittest.mock import patch
from pathlib import Path
import numpy as np
from build_chilko_corridor_depth import build,fit_depth_amplitude,constrain_source_amplitude
from chilko_corridor_bed import load_available_depth
from mosaic_lidarbc_crops import sha


class AvailableChannelDepthTests(unittest.TestCase):
    def test_depth_builder_keeps_default_and_explicit_source_assumptions(self):
        for arguments,expected in [((),(45.,.045)),((33.5,.06),(33.5,.06))]:
            with tempfile.TemporaryDirectory() as tmp, \
                    patch('build_chilko_corridor_depth.CorridorBed',side_effect=RuntimeError('stop before sampling')) as model:
                out=Path(tmp)/'fresh'
                with self.assertRaisesRegex(RuntimeError,'stop before sampling'):
                    build('terrain','profile',out,*arguments,origin=[0.,0.])
                model.assert_called_once_with('terrain','profile',*expected)
                self.assertFalse(out.exists())

    def test_nondefault_discharge_and_roughness_set_capacity(self):
        for discharge,roughness in [(29.6,.045),(33.5,.06),(45.,.045)]:
            depth,_,capacity=fit_depth_amplitude(np.full((1,10),100.),np.full((1,10),100.),
                np.ones((1,10),bool),np.ones((1,10)),np.array([.05]),np.array([.01]),discharge,roughness)
            np.testing.assert_allclose(capacity,discharge,atol=1e-8)
            self.assertAlmostEqual(depth[0],(discharge*roughness/(10*.1))**.6,places=8)

    def test_geographic_envelope_satisfies_all_overlapping_cell_constraints(self):
        station=np.arange(0.,32.,4.);original=np.array([1.,1.,3.,1.,1.,1.,1.,1.])
        points=np.array([0.,1.,3.9,4.,5.,9.,9.,19.99,20.])
        required=np.array([.5,2.,1.5,2.4,2.1,3.2,2.,1.8,1.1])
        result=constrain_source_amplitude(station,original.copy(),points,required)
        self.assertTrue((result>=original).all())
        self.assertTrue((np.interp(points,station,result)>=required).all())
        # An unrelated downstream bend receives no constraint from this section.
        np.testing.assert_array_equal(result[6:],original[6:])

    def test_geographic_envelope_refuses_unbounded_or_unlocated_constraints(self):
        for point,required in [(-1,1),(21,1),(float('nan'),1),(2,11),(2,0)]:
            with self.assertRaises(ValueError):constrain_source_amplitude(
                np.arange(0.,24.,4.),np.ones(6),np.array([point]),np.array([required]))

    def test_geographic_envelope_does_not_truncate_fractional_depth_into_integer_nodes(self):
        station=np.arange(0.,24.,4.)
        for amplitude in (np.ones(6,dtype=int),np.full(6,11.),np.broadcast_to(1.,(6,))):
            with self.assertRaises(ValueError):constrain_source_amplitude(
                station,amplitude,np.array([5.]),np.array([1.25]))

    def test_depth_receipt_rejects_wrong_source_changed_bytes_or_station(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);station=np.array([0.,4.,8.]);previous=np.ones(3)
            np.savez(p/'depth.npz',station_m=station,previous_depth_amplitude_m=previous,
                     depth_amplitude_m=np.full(3,2.))
            expected=dict(source_profile_sha256='source',hydraulic_solution=False)
            m=dict(expected,depth_sha256=sha(p/'depth.npz'))
            (p/'manifest.json').write_text(json.dumps(m))
            amplitude,receipt=load_available_depth(p,station,previous,expected)
            np.testing.assert_array_equal(amplitude,2.)
            self.assertEqual(receipt['depth_sha256'],sha(p/'depth.npz'))
            for source,stations in [(dict(expected,source_profile_sha256='other'),station),
                                    (expected,station+1)]:
                with self.assertRaises(ValueError):load_available_depth(p,stations,previous,source)
            with (p/'depth.npz').open('ab') as f:f.write(b'changed')
            with self.assertRaises(ValueError):load_available_depth(p,station,previous,expected)

    def test_actual_available_width_sets_capacity_not_bar_width(self):
        ground=np.full((2,10),100.);stage=ground.copy();owned=np.ones((2,10),bool)
        owned[1,2:8]=False
        d,before,after=fit_depth_amplitude(ground,stage,owned,np.ones((2,10)),
                                         np.array([.2,.2]),np.array([.01,.01]),45.,.045)
        self.assertGreater(d[1],d[0])
        self.assertAlmostEqual(d[1]/d[0],(10/4)**.6,places=8)
        np.testing.assert_allclose(after,45.,atol=1e-8)
        ground[1,2:8]=200.
        again=fit_depth_amplitude(ground,stage,owned,np.ones((2,10)),
                                 np.array([.2,.2]),np.array([.01,.01]),45.,.045)[0]
        np.testing.assert_array_equal(d,again)

    def test_existing_deeper_source_is_not_raised(self):
        d,before,after=fit_depth_amplitude(np.zeros((1,10)),np.full((1,10),10.),
            np.ones((1,10),bool),np.ones((1,10)),np.array([.2]),np.array([.01]),45.,.045)
        self.assertEqual(d[0],.2)
        self.assertGreater(before[0],45.)
        np.testing.assert_array_equal(before,after)

    def test_unsupported_or_excessive_depth_is_refused(self):
        for owned,shape in [(np.zeros((1,10),bool),np.ones((1,10))),
                            (np.ones((1,10),bool),np.zeros((1,10)))]:
            with self.assertRaises(ValueError):
                fit_depth_amplitude(np.full((1,10),100.),np.full((1,10),100.),owned,shape,
                                    np.array([.2]),np.array([.01]),45.,.045)

    def test_dry_missing_reference_never_contributes_to_capacity(self):
        ground=np.full((1,4),100.);stage=np.array([[np.nan,100.,100.,np.nan]])
        owned=np.array([[False,True,True,False]])
        d,_,after=fit_depth_amplitude(ground,stage,owned,np.ones((1,4)),
                                    np.array([.2]),np.array([.01]),10.,.045)
        self.assertTrue(np.isfinite(d).all());np.testing.assert_allclose(after,10.,atol=1e-8)
        stage[0,1]=np.nan
        with self.assertRaises(ValueError):
            fit_depth_amplitude(ground,stage,owned,np.ones((1,4)),np.array([.2]),np.array([.01]),10.,.045)


if __name__=='__main__':unittest.main()
