import copy
import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_inlet_advection import constrain, relaxation


class InletAdvectionTest(unittest.TestCase):
    def setUp(self):
        self.profile = {'packed_vectors': [[1,0,0],[0,1,0],[100,100,0],[200,200,200],
            [50,50,50],[4,4,4],[8,8,4],[400,400,200]]+[[10,150,3]]*16}
        self.bed = lambda face,t: 10

    def test_four_faces_preserve_tangent_and_impose_inward_velocity(self):
        for face in range(4):
            axis=face//2;normal=np.eye(3)[axis]*(1 if face%2==0 else -1)
            # Coordinates below are canonical; world Y is reflected.
            a=np.array([100.,100.,100.]);a[axis]=1 if face%2==0 else 199
            b=a-2*normal+np.eye(3)[1-axis]*.5
            v=-120*normal+np.eye(3)[1-axis]*30
            a,b,v=(p*[1,-1,1] for p in (a,b,v));normal*= [1,-1,1]
            p,w,hit=constrain(a,b,v,1/60,self.profile,self.bed)
            self.assertEqual(hit,face+1)
            self.assertAlmostEqual(np.dot(p-a,normal),3/60)
            self.assertAlmostEqual(np.dot(w,normal),3)
            np.testing.assert_allclose((p-a)-normal*np.dot(p-a,normal),
                                       (b-a)-normal*np.dot(b-a,normal),atol=1e-12)
            np.testing.assert_allclose(w-normal*np.dot(w,normal),v-normal*np.dot(v,normal),atol=1e-12)

    def test_outgoing_opening_unchanged(self):
        p=copy.deepcopy(self.profile);p['packed_vectors'][8:]=[[10,150,-3]]*16
        a,b,v=[199,-100,100],[201,-100,100],[120,0,0]
        q,w,face=constrain(a,b,v,1/60,p,self.bed)
        np.testing.assert_array_equal(q,b);np.testing.assert_array_equal(w,v);self.assertEqual(face,0)

    def test_dry_invalid_origin_roof_corner_untouched(self):
        cases=[([199,-100,9],[201,-100,9]),
               ([201,-100,100],[202,-100,100]),([199,-100,199],[201,-100,203]),
               ([199,-199,100],[201,-201,100])]
        for a,b in cases:
            q,w,face=constrain(a,b,[120,0,0],1/60,self.profile,self.bed)
            np.testing.assert_array_equal(q,b);self.assertEqual(face,0)

    def test_above_stage_primary_fluid_relaxes_without_plane_reflection(self):
        a,b,v=np.array([199.,-100,160]),np.array([201.,-99,160.5]),np.array([120.,60,30])
        p,w,face=constrain(a,b,v,1/60,self.profile,self.bed)
        self.assertEqual(face,2)
        self.assertGreater(p[0],200) # Still outside: unchanged exit gate must reject.
        self.assertLess(p[0],b[0]);self.assertLess(w[0],v[0])
        np.testing.assert_array_equal(p[1:],b[1:]);np.testing.assert_array_equal(w[1:],v[1:])

    def test_interior_of_band_relaxes_before_a_crossing(self):
        p,w,face=constrain([180,-100,160],[181,-99,161],[60,60,60],1/60,self.profile,self.bed)
        self.assertEqual(face,2);self.assertLess(p[0],181);self.assertGreater(p[0],180)
        self.assertLess(w[0],60);np.testing.assert_array_equal(w[1:],[60,60])

    def test_bulk_water_beyond_band_unchanged(self):
        a,b,v=[140,-100,100],[141,-99,101],[60,60,60]
        p,w,face=constrain(a,b,v,1/60,self.profile,self.bed)
        self.assertEqual(face,0);np.testing.assert_array_equal(p,b);np.testing.assert_array_equal(w,v)

    def test_dry_inlet_row_cannot_force_above_stage_particle(self):
        profile=copy.deepcopy(self.profile);profile['packed_vectors'][8:]=[[10,5,3]]*16
        p,w,face=constrain([199,-100,100],[201,-100,100],[120,0,0],1/60,profile,self.bed)
        self.assertEqual(face,0);np.testing.assert_array_equal(p,[201,-100,100])

    def test_relaxation_exact_subdivision_for_fixed_coefficient(self):
        avg,end=relaxation(10,200,80,.1);avgh,endh=relaxation(10,200,80,.05)
        self.assertAlmostEqual(end,endh**2)
        self.assertAlmostEqual(avg*.1,avgh*.05*(1+endh))
        self.assertTrue(0<end<avg<1)

    def test_relaxation_smooth_support_and_small_dt(self):
        self.assertEqual(relaxation(200,200,80,.1),(1,1))
        self.assertEqual(relaxation(201,200,80,.1),(1,1))
        avg,end=relaxation(0,200,80,1.e-12)
        self.assertTrue(0<end<=avg<=1)
        self.assertLess(1-relaxation(199.999,200,80,.1)[1],1.e-9)

    def test_relaxation_rejects_invalid_inputs(self):
        for values in [(-1,200,80,.1),(0,0,80,.1),(0,200,0,.1),(0,200,80,0),(0,200,80,np.nan)]:
            with self.assertRaises(ValueError):relaxation(*values)

    def test_zero_normal_flow_retains_start_normal_position(self):
        p=copy.deepcopy(self.profile);p['packed_vectors'][8:]=[[10,150,0]]*16
        q,w,face=constrain([199,-100,100],[201,-99,100],[120,60,0],1/60,p,self.bed)
        np.testing.assert_array_equal(q,[199,-99,100]);np.testing.assert_array_equal(w,[0,60,0])
        self.assertEqual(face,2)

    def test_uses_actual_intersection_bed_not_midpoint(self):
        p=copy.deepcopy(self.profile);p['packed_vectors'][8:]=[[110,150,3]]*16
        q,w,face=constrain([199,-100,100],[201,-100,100],[120,0,0],1/60,p,self.bed)
        self.assertEqual(face,2)
        self.assertLess(q[0],199)

    def test_rotated_translated_frame_preserves_same_response(self):
        angle=.713;c,s=np.cos(angle),np.sin(angle)
        rotation=np.array([[c,-s,0],[s,c,0],[0,0,1]])
        translation=np.array([12500.,-7000.,300.])
        profile=copy.deepcopy(self.profile)
        profile['packed_vectors'][0]=rotation[:,0].tolist()
        profile['packed_vectors'][1]=rotation[:,1].tolist()
        profile['packed_vectors'][2]=(rotation@np.array([100,100,0])+translation).tolist()
        profile['packed_vectors'][8:]=[[310,450,3]]*16
        world=lambda p:(rotation@np.asarray(p)+translation)*[1,-1,1]
        a,b=world([199,100,100]),world([201,101,100])
        v=(rotation@np.array([120,60,0]))*[1,-1,1]
        q,w,face=constrain(a,b,v,1/60,profile,lambda face,t:310)
        self.assertEqual(face,2)
        np.testing.assert_allclose(q,world([198.95,101,100]),atol=1e-10)
        np.testing.assert_allclose(w,(rotation@np.array([-3,60,0]))*[1,-1,1],atol=1e-10)

    def test_invalid_timestep_does_not_invent_motion(self):
        for dt in (0,-1,np.nan,np.inf):
            q,w,face=constrain([199,-100,100],[201,-100,100],[120,0,0],dt,self.profile,self.bed)
            self.assertEqual(face,0);np.testing.assert_array_equal(q,[201,-100,100])

    def test_observed_near_edge_step67_requires_inlet_response(self):
        # Original recorded world points. A centre-based float32 projection
        # rounded this exterior endpoint onto the face and skipped correction.
        profile={'packed_vectors':[
            [-.9299998355760436,.36755993501540923,0],[-.36755993501540923,-.9299998355760436,0],
            [-929.9998355760437,367.5599350154092,350],[24500,8100,800],
            [50,50,800/24],[490,162,24],[494,166,24],[24700,8300,800]]+
            [[409.8984774106752,647.81787109375,3.186234712600708]]*1304}
        a=np.array([-12961.0048828125,-3254.4404296875,446.7201232910156])
        b=np.array([-12961.1328125,-3254.29638671875,446.7057800292969])
        v=np.array([2.1885440349578857,4.428580284118652,.10762262344360352])
        p,w,face=constrain(a,b,v,1/60,profile,lambda face,t:409.8984774106752)
        self.assertEqual(face,2)
        inward=-np.asarray(profile['packed_vectors'][0])*[1,-1,1]
        packed=np.asarray(profile['packed_vectors']);origin=packed[2]*[1,-1,1]
        distance=packed[3,0]/2+np.dot(a-origin,inward)
        avg,end=relaxation(distance,200,647.81787109375-409.8984774106752,1/60)
        self.assertAlmostEqual(np.dot(p-a,inward),
            np.dot(b-a,inward)*avg+3.186234712600708/60*(1-avg),places=10)
        self.assertAlmostEqual(np.dot(w,inward),
            np.dot(v,inward)*end+3.186234712600708*(1-end),places=10)
        self.assertGreater(distance+np.dot(p-a,inward),0)
        # The legacy plane-only capture keeps its original reference semantics.
        old_p,old_v,old_face=constrain(a,b,v,1/60,profile,lambda face,t:409.8984774106752,relaxation_enabled=False)
        self.assertEqual(old_face,2)
        self.assertAlmostEqual(np.dot(old_p-a,inward),3.186234712600708/60,places=10)


if __name__=='__main__':unittest.main()
