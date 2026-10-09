import copy
import unittest
from qualify_chilko_full_native import FLAGS, validate_inputs, validate_execution


class FullNativeQualification(unittest.TestCase):
    def fixtures(self):
        return (dict(exit_code=0,inputs_unchanged=True,full_route_inputs=True),
            dict(full_route_hydraulic_inputs=True,full_route_chart=True,
                 complete_source_route_length_m=55723.04503105954,stations=25552,lateral_cells=257),
            dict(grid=dict(nx=25552,ny=257,dx=2.,dy=2.),fixed_dt=.05,feature_count=0,
                 metadata=dict(river_id='chilko_river_bc',scenario_id='chilko_full_corridor_inputs_v11_reference1m')))

    def test_complete_domain_only(self):
        values=self.fixtures();validate_inputs(*values)
        for target,key,value in ((0,'inputs_unchanged',False),(0,'exit_code',1),
            (1,'full_route_chart',False),(1,'stations',200),(1,'complete_source_route_length_m',1200.),
            (2,'feature_count',3),(2,'fixed_dt',.1)):
            bad=copy.deepcopy(values);bad[target][key]=value
            with self.assertRaises(ValueError):validate_inputs(*bad)
        for key,value in (('nx',200),('ny',20),('dx',4.)):
            bad=copy.deepcopy(values);bad[2]['grid'][key]=value
            with self.assertRaises(ValueError):validate_inputs(*bad)

    def test_output_cannot_escape_job(self):
        for name in ('../outside','a/b','','C:/outside'):
            values=self.fixtures();values[2]['metadata']['scenario_id']=name
            with self.assertRaises(ValueError):validate_inputs(*values)

    def test_lossless_unforced_native_settings(self):
        self.assertIn('--stream-output',FLAGS)
        self.assertIn('--disable-fixture-calibrations',FLAGS)
        self.assertIn('--no-preserve-initial-mass',FLAGS)
        for key,value in (('--feature-strength-scale','0'),('--spatial-order','2'),('--cfl','0.2'),
                          ('--roughness-scale','1'),('--bed-slope-source-scale','1')):
            self.assertEqual(FLAGS[FLAGS.index(key)+1],value)

    def test_observed_execution_must_be_one_initial_frame(self):
        log='scenario_id=chilko\nsolver=raftsim_water_cpp_v1\nsteps=0\nframes=1\nvalidation_passed=true\n'
        validate_execution(log,'chilko')
        for key,value in (('scenario_id','other'),('solver','other'),('steps','1'),
                          ('frames','2'),('validation_passed','false')):
            lines=log.splitlines()
            for variant in ('\n'.join(line for line in lines if not line.startswith(key+'=')),
                            log+'\n'+next(line for line in lines if line.startswith(key+'=')),
                            '\n'.join(key+'='+value if line.startswith(key+'=') else line for line in lines)):
                with self.subTest(key=key), self.assertRaises(ValueError):validate_execution(variant,'chilko')


if __name__=='__main__':unittest.main()
