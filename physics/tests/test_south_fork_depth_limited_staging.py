"""Candidate-core guards supplement the shared triangle staging tests."""
from pathlib import Path
import importlib.util
import json
import tempfile
import unittest
from unittest.mock import patch

SCRIPT=Path(__file__).resolve().parents[2]/'unreal/Scripts/stage_south_fork_depth_limited_review.py'
spec=importlib.util.spec_from_file_location('depth_limited_staging',SCRIPT)
candidate=importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)
ARCHIVE='83f35ddf4e6ab28fc07999804e63d3ccfcd5d0d78d8f0775c96e909913910f03'
BINARY='1f010cbe7edce8eb579c2d9a040820a24d6ee6ac1615073e3afbf899cac9ba50'


class CandidateStagingTests(unittest.TestCase):
    def test_wrong_archive_rejected_before_staging(self):
        with patch.object(candidate.stage,'sha',return_value='wrong'), patch.object(candidate.stage,'main') as main:
            with self.assertRaisesRegex(ValueError,'archive'):
                candidate.main()
            main.assert_not_called()

    def exercise_fields(self,binary):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            manifest=root/candidate.stage.NEW_FIELDS/'manifest.json'
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({'review':{'source_solver_binary_sha256':binary}}))
            with patch.object(candidate.stage,'ROOT',root), patch.object(candidate.stage,'sha',return_value=ARCHIVE), patch.object(candidate.stage,'main') as main:
                if binary==BINARY:
                    candidate.main()
                    main.assert_called_once_with()
                else:
                    with self.assertRaisesRegex(ValueError,'numerical core'):
                        candidate.main()
                    main.assert_not_called()

    def test_matching_core_reaches_shared_guards(self):self.exercise_fields(BINARY)
    def test_other_core_rejected(self):self.exercise_fields('other')
    def test_missing_core_rejected(self):self.exercise_fields(None)


if __name__=='__main__':unittest.main()
