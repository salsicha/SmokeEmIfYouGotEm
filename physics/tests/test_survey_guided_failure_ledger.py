"""Retain pre-traversal engine failures; never turn absent reports into passes."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import summarize_south_fork_guided_review as ledger


class GuidedFailureLedgerTests(unittest.TestCase):
    def run_missing_report(self,state):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            review=root/'review'
            log=root/'unreal/Saved/Logs/Preflight.log'
            log.parent.mkdir(parents=True)
            log.write_text('Missing candidate guided route\n')
            index=review/'engine/index.json'
            index.parent.mkdir(parents=True)
            index.write_text(json.dumps({'tests':[{'fullTestPath':'RaftSim.Survey.SouthForkGuidedTraversal','state':state}]}))
            with patch.object(ledger,'ROOT',root),patch.object(ledger,'REVIEW',review),patch.object(ledger,'RUNS',(('preflight','Preflight','engine'),)):
                if state=='Fail':
                    ledger.main()
                    run=json.loads((review/'guided-review.json').read_text())['runs'][0]
                    self.assertFalse(run['meets_current_bounded_criteria'])
                    self.assertIsNone(run['metrics'])
                    self.assertEqual(run['engine_state'],'Fail')
                else:
                    with self.assertRaisesRegex(ValueError,'Missing completed report'):
                        ledger.main()
                    self.assertFalse((review/'guided-review.json').exists())

    def test_preflight_failure_retained(self):self.run_missing_report('Fail')
    def test_success_without_evidence_rejected(self):self.run_missing_report('Success')


if __name__=='__main__':unittest.main()
