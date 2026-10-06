"""Authoring regression; saved graph behavior is tested in the engine installer."""
from pathlib import Path
import unittest

class HydraulicNormalAuthorTest(unittest.TestCase):
    def test_registered_wrapper_survives_optical_refresh(self):
        root=Path(__file__).resolve().parents[2]
        src=(root/'unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/RaftSimEditorCurrentWaterMaterial.cpp').read_text()
        self.assertIn('RiverLabel == TEXT("SouthFork") && Candidate->Desc == TEXT("SouthForkMovingDetailNormalV1")',src)
        self.assertIn('Base->Input.Expression != Detail',src)
        self.assertIn('Normal.Connect(0, RegisteredDetailNormal)',src)
        self.assertIn('else Material->GetEditorOnlyData()->Normal.Connect(0, Detail)',src)
        self.assertIn('Duplicate South Fork hydraulic normal composition; refusing refresh.',src)
        self.assertIn('Unrecognized South Fork hydraulic normal inputs; refusing refresh.',src)

if __name__=='__main__':unittest.main()
