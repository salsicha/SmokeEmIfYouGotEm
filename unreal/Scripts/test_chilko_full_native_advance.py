import unittest
from unittest.mock import patch
from advance_chilko_full_native import ROOT,CELLS,STEPS,INTERVAL,require_qualification,validate_execution,scratch_requirement,native_output_path


class FullNativeAdvance(unittest.TestCase):
    def test_only_successful_full_domain_qualification(self):
        completion=dict(exit_code=0,full_domain_cells=CELLS,actual_native_steps=0,
            initial_fields_and_grid_verified=True,inputs_unchanged=True,frame_bytes=328668959)
        require_qualification(completion)
        for key,value in (('exit_code',1),('full_domain_cells',500),('actual_native_steps',1),
                          ('initial_fields_and_grid_verified',False),('inputs_unchanged',False),('frame_bytes',0)):
            with self.subTest(key=key),self.assertRaises(ValueError):require_qualification({**completion,key:value})

    def test_full_schedule_must_be_observed_not_just_requested(self):
        log='scenario_id=chilko\nsolver=raftsim_water_cpp_v1\nsteps=200\nframes=11\nvalidation_passed=true\n'
        validate_execution(log,'chilko')
        for text in (log.replace('steps=200','steps=20'),log.replace('frames=11','frames=3'),
                     log.replace('validation_passed=true','validation_passed=false'),log+'steps=200\n',
                     log.replace('scenario_id=chilko','scenario_id=window')):
            with self.assertRaises(ValueError):validate_execution(text,'chilko')

    def test_storage_keeps_every_frame_and_existing_reserve(self):
        self.assertEqual((CELLS,STEPS,INTERVAL),(6566864,200,20))
        self.assertEqual(scratch_requirement(100),40*1024**3+22*100+3*CELLS*15*8)

    def test_native_output_stays_in_project_despite_system_temp(self):
        with patch.dict('os.environ',{'TEMP':'C:/temp','TMP':'C:/temp','SystemDrive':'C:'}):
            self.assertEqual(native_output_path(ROOT/'tmp/test-job'),(ROOT/'tmp/test-job/native').resolve())
        with self.assertRaises(ValueError):native_output_path(ROOT/'outside-tmp')

    def test_system_drive_project_is_refused(self):
        with patch.dict('os.environ',{'SystemDrive':ROOT.drive}),self.assertRaises(ValueError):
            native_output_path(ROOT/'tmp/test-job')


if __name__=='__main__':unittest.main()
