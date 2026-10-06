import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import finish_pinball_reference_install as install


class FinalizeTests(unittest.TestCase):
    def fixture(self, root):
        river=root/'physics/data/real_world/pacuare_river_costa_rica'
        river.mkdir(parents=True)
        tmp=root/'tmp';tmp.mkdir()
        mapfile=root/'unreal/Content/RaftSim/Maps/L_UpperHuacas.umap'
        mapfile.parent.mkdir(parents=True);mapfile.write_bytes(b'prepared map')
        live=river/'bed.npy';live.write_bytes(b'before')
        staged=tmp/'bed.npy';staged.write_bytes(b'after')
        report=dict(status='map_saved_runtime_pending',patch=dict(applied=True,collision_rebuilt=True),
                    final_receipt='tmp/finished.json',map_sha256_after=install.sha(mapfile),
                    paired_runtime_files={live.relative_to(root).as_posix():dict(
                        before=install.sha(live),after=install.sha(staged),staged='tmp/bed.npy')})
        pending=tmp/'install.pending.json';pending.write_text(json.dumps(report))
        return river,live,staged,pending

    def test_atomic_replacement_and_resume(self):
        for already_done in (False,True):
            with self.subTest(already_done=already_done), tempfile.TemporaryDirectory(prefix='raftsim-install-test-') as directory:
                root=Path(directory);river,live,staged,pending=self.fixture(root)
                if already_done:live.write_bytes(staged.read_bytes())
                with patch.object(install,'ROOT',root),patch.object(install,'RIVER',river),patch.object(install.subprocess,'check_output',return_value='"other.exe","1"\n'):
                    final=install.finish(pending)
                self.assertEqual(live.read_bytes(),b'after')
                self.assertEqual(json.loads(final.read_text())['status'],'paired_install_complete')
                self.assertTrue(pending.exists())

    def test_loaded_editor_refuses_before_any_write(self):
        with tempfile.TemporaryDirectory(prefix='raftsim-install-test-') as directory:
            root=Path(directory);river,live,_,pending=self.fixture(root)
            with patch.object(install,'ROOT',root),patch.object(install,'RIVER',river),patch.object(install.subprocess,'check_output',return_value='"UnrealEditor-Cmd.exe","123"\n'):
                with self.assertRaisesRegex(AssertionError,'must exit'):install.finish(pending)
            self.assertEqual(live.read_bytes(),b'before')

    def test_overlapping_user_edit_is_preserved(self):
        with tempfile.TemporaryDirectory(prefix='raftsim-install-test-') as directory:
            root=Path(directory);river,live,_,pending=self.fixture(root)
            live.write_bytes(b'user change')
            with patch.object(install,'ROOT',root),patch.object(install,'RIVER',river),patch.object(install.subprocess,'check_output',return_value=''):
                with self.assertRaisesRegex(AssertionError,'changed'):install.finish(pending)
            self.assertEqual(live.read_bytes(),b'user change')
            self.assertFalse((root/'tmp/finished.json').exists())


if __name__=='__main__':unittest.main()
