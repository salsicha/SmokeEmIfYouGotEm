import unittest
import json
import tempfile
from pathlib import Path
import numpy as np
from calibrate_chilko_corridor_depth import depth_step
from chilko_corridor_bed import verify_calibrated_depth
from mosaic_lidarbc_crops import sha
from warm_start_chilko_depth_cook import depth_state


class GeographicCalibrationTests(unittest.TestCase):
    def test_depth_restart_preserves_mass_momentum_and_only_moves_surface(self):
        bed=np.full((2,3),900.);depth=np.array([[0.,1.,2.],[0.,1.,2.]])
        frame=dict(h=depth,eta=bed+depth,u=depth*.2,v=-depth*.1,
            hu=depth**2*.2,hv=-depth**2*.1,wet=(depth>0).astype(float))
        new=bed.copy();new[0,1]-=.5
        grid=dict(nx=3,ny=2,dx=2.,dy=2.)
        state,stats=depth_state(frame,bed,new,grid)
        for key in ('depth','u','v','hu','hv','wet'):
            np.testing.assert_array_equal(state[key],frame['h' if key=='depth' else key])
        np.testing.assert_allclose(state['eta']-state['depth'],new,rtol=0,atol=1e-10)
        self.assertEqual(stats['added_water_volume_m3'],0.)
        for invalid in (bed+.1,bed-1.,bed,np.full_like(bed,np.nan)):
            with self.assertRaises(ValueError):depth_state(frame,bed,invalid,grid)

    def fixture(self):
        station=np.arange(0.,2001.,4.);points=np.arange(400.,1600.,2.)
        return station,np.full(len(station),2.),points,np.full(len(points),.5),np.full(len(points),.5),[400.,1600.]

    def test_bounded_deepening_tapers_and_preserves_outside_interval(self):
        args=self.fixture();delta,report=depth_step(*args);station=args[0]
        self.assertTrue((delta>=0).all());self.assertLessEqual(delta.max(),.75)
        self.assertAlmostEqual(delta[len(delta)//2],.7,places=7)
        self.assertTrue((delta[(station<=400)|(station>=1600)]==0).all())
        self.assertLess(np.max(abs(np.diff(delta))),.04)
        self.assertGreater(report['changed_source_nodes'],0)

    def test_negative_errors_never_raise_the_bed(self):
        args=list(self.fixture());args[3]*=-1
        delta,_=depth_step(*args);np.testing.assert_array_equal(delta,0.)

    def test_geographic_sample_order_not_numerical_rows(self):
        args=list(self.fixture());expected=depth_step(*args)[0]
        for i in (2,3,4):args[i]=args[i][::-1]
        np.testing.assert_array_equal(depth_step(*args)[0],expected)

    def test_missing_samples_and_tiny_bank_shape_do_not_create_constraints(self):
        args=list(self.fixture());keep=(args[2]<800)|(args[2]>1200)
        for i in (2,3,4):args[i]=args[i][keep]
        delta,report=depth_step(*args)
        self.assertEqual(delta[len(delta)//2],0.)
        self.assertIn(None,report['raw_step_m'])
        args[4][:]=.01
        with self.assertRaisesRegex(ValueError,'Insufficient'):depth_step(*args)

    def test_amplitude_cap_and_invalid_source_refused(self):
        args=list(self.fixture());args[1][:]=9.9
        delta,_=depth_step(*args);self.assertLessEqual((args[1]+delta).max(),10.)
        args[2][0]=np.nan
        with self.assertRaises(ValueError):depth_step(*args)

    def test_loader_binds_parent_and_refuses_unbounded_or_outside_edits(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);station=np.arange(0.,2001.,4.);parent=np.full(station.shape,2.)
            np.savez(p/'depth.npz',station_m=station,previous_depth_amplitude_m=parent,
                     depth_amplitude_m=parent)
            common=dict(source_profile_sha256='p',source_terrain_sha256='t',source_route_sha256='r',
                source_planform_sha256='w',ownership_policy='owned',discharge_m3s=45.,manning_n=.045)
            (p/'manifest.json').write_text(json.dumps(dict(common,depth_sha256=sha(p/'depth.npz'))))
            (p/'review.json').write_text('{}');(p/'frame.csv').write_text('native')
            receipt=dict(parent_manifest=str(p/'manifest.json'),parent_manifest_sha256=sha(p/'manifest.json'),
                parent_depth_sha256=sha(p/'depth.npz'),review=str(p/'review.json'),review_sha256=sha(p/'review.json'),
                frame=str(p/'frame.csv'),frame_sha256=sha(p/'frame.csv'),statistics=dict(bounds_m=[400,1600]),
                requires_fresh_canonical_export_and_native_review=True)
            manifest=dict(common,native_calibration=receipt)
            step=np.where((station>400)&(station<1600),.5,0.)
            arrays=dict(station_m=station,previous_depth_amplitude_m=parent,
                calibration_parent_depth_amplitude_m=parent,calibration_step_m=step,depth_amplitude_m=parent+step)
            verify_calibrated_depth(manifest,arrays)
            for index,value in [(0,.1),(200,-.1),(200,.76)]:
                bad={k:v.copy() for k,v in arrays.items()};bad['calibration_step_m'][index]=value
                bad['depth_amplitude_m']=parent+bad['calibration_step_m']
                with self.subTest(index=index,value=value),self.assertRaises(ValueError):
                    verify_calibrated_depth(manifest,bad)
            changed=dict(manifest,source_route_sha256='another route')
            with self.assertRaisesRegex(ValueError,'source identity'):verify_calibrated_depth(changed,arrays)
            (p/'frame.csv').write_text('changed native')
            with self.assertRaisesRegex(ValueError,'lineage'):verify_calibrated_depth(manifest,arrays)


if __name__=='__main__':unittest.main()
