"""Never audit a historical solve with a subsequently replaced executable."""
from pathlib import Path
import hashlib
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'physics/scripts'))
import verify_south_fork_survey_flux as flux


class FluxIdentityTests(unittest.TestCase):
    def test_relative_and_absolute_binary_paths_keep_exact_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            executable=root/'solver.exe'
            executable.write_bytes(b'original fixture binary')
            expected=hashlib.sha256(executable.read_bytes()).hexdigest()
            (root/'registration.json').write_text(json.dumps({'solver_binary_sha256':expected}))
            with patch.object(flux,'ROOT',root):
                for path in ('solver.exe',str(executable)):
                    with self.subTest(path=path):
                        self.assertEqual(flux.verified_solver_sha(root,{'command':[path]}),expected)
                executable.write_bytes(b'replaced fixture binary')
                with self.assertRaisesRegex(ValueError,'differs from the completed cook'):
                    flux.verified_solver_sha(root,{'command':['solver.exe']})

    def test_missing_binary_does_not_silently_choose_default(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'registration.json').write_text(json.dumps({'solver_binary_sha256':'unused'}))
            with patch.object(flux,'ROOT',root),self.assertRaises(FileNotFoundError):
                flux.verified_solver_sha(root,{'command':['missing.exe']})


if __name__=='__main__':unittest.main()
