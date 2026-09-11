import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import audit_liquid_current_surface_foam as auditor


class FoamAuditDurationTest(unittest.TestCase):
    def run_audit(self,steps,age):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'capture';path.mkdir()
            (path/'capture.json').write_text(json.dumps(dict(simulation_steps=steps,complete=True,error=None)))
            path.with_suffix('.log').write_text('')
            snapshots=[dict(verified=True,clock=[age,1/60,0,1]),dict(verified=True,clock=[age,0,0,0])]
            with patch.object(auditor,'snapshot',side_effect=snapshots) as mock:
                result=auditor.audit(path)
            return result,mock.call_args_list

    def test_long_run_uses_matching_independent_grid(self):
        result,calls=self.run_audit(3600,60)
        self.assertEqual(calls[0].args[1].name,'terrain_3600_grids')
        self.assertTrue(result['transport_verified'])

    def test_short_snapshot_does_not_verify_long_run(self):
        result,_=self.run_audit(3600,12)
        self.assertFalse(result['simulation_age_matches_requested'])
        self.assertFalse(result['transport_verified'])

    def test_unbounded_or_noninteger_count_rejected(self):
        for steps in (0,600,3601,720.5):
            with self.assertRaises(ValueError):self.run_audit(steps,steps/60)


if __name__=='__main__':unittest.main()
