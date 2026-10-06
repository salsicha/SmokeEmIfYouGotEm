import unittest
from extract_colorado_bed_windows import crop_bounds,selected_windows


class SourceCrop(unittest.TestCase):
    def test_registered_integer_bounds_and_explicit_margin(self):
        self.assertEqual(crop_bounds([100.2,200.8,300.1,400.3]),(20,120,381,481))
        self.assertEqual(crop_bounds([100.2,200.8,300.1,400.3],250),(-150,-50,551,651))

    def test_unbounded_or_invalid_source_refused(self):
        for margin in (0,19,401,float('nan'),25.5):
            with self.assertRaises(ValueError):crop_bounds([0,0,100,100],margin)
        for bounds in ([0,0,10000,10000],[1,0,0,1],[0,0,float('nan'),1]):
            with self.assertRaises(ValueError):crop_bounds(bounds)

    def test_selection_cannot_silently_omit_unknown_entry(self):
        index=dict(windows=[dict(name='Granite'),dict(name='Unkar')])
        self.assertEqual(selected_windows(index,['Unkar']),[dict(name='Unkar')])
        with self.assertRaises(ValueError):selected_windows(index,['Unkar','Unknown'])


if __name__=='__main__':unittest.main()
