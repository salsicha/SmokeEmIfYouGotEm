import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from diagnose_liquid_projection_packet import load_field,analyze


class ProjectionPacketTest(unittest.TestCase):
    def test_native_half_vector_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);data=np.arange(96,dtype='<f2').reshape(2,3,4,4)
            data.tofile(root/'field.bin')
            r={'field':'field.bin','field_format':'rgba16f','cells':[4,3,2]}
            np.testing.assert_array_equal(load_field(root,r,'field',4),data)

    def test_incomplete_and_nonfinite_scalar_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);r={'field':'field.bin','field_format':'r32f','cells':[2,2,2]}
            for data in (np.ones(7,dtype='<f4'),np.full(8,np.nan,dtype='<f4')):
                data.tofile(root/'field.bin')
                with self.assertRaises(ValueError):load_field(root,r,'field',1)

    def test_wrong_format_and_escape_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for path,fmt in (('field.bin','rgba16f'),('../outside.bin','r32f')):
                with self.assertRaises(ValueError):
                    load_field(root,{'field':path,'field_format':fmt,'cells':[2,2,2]},'field',1)


if __name__=='__main__':unittest.main()
