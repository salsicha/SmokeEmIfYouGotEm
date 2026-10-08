import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
from shapely.geometry import box
from build_chilko_corridor_profile import build,main
from chilko_corridor_bed import carve_mapped_water

class ProfileResolutionTests(unittest.TestCase):
    def test_cli_forwards_requested_and_default_station_spacing(self):
        arguments=['--terrain','terrain','--route','route','--planform','polygon','--out','out']
        for extra,expected in (([],4.),(['--station-spacing-m','1'],1.)):
            with patch('build_chilko_corridor_profile.build',return_value=dict(rejected_source_sections=[])) as builder,patch('builtins.print'):
                main(arguments+extra)
                self.assertEqual(builder.call_args.kwargs['step'],expected)

    def test_native_spacing_resolves_short_drop_without_reclassifying_a_rock(self):
        station=np.arange(9.)
        heights=np.array([1000.,1000.,1000.,999.5,999.,999.,999.,999.,999.])
        def sample(xy):
            return np.interp(xy[...,0],station,heights),np.ones(xy.shape[:-1],np.uint8)
        terrain=SimpleNamespace(conditioned=True,folder=Path('terrain'),
            manifest=dict(route_sha256='fixture',source_kind={1:'synthetic native terrain'}),sample=sample)
        profiles=[]
        with tempfile.TemporaryDirectory() as tmp, \
                patch('build_chilko_corridor_profile.CorridorTerrain',return_value=terrain), \
                patch('build_chilko_corridor_profile.compatible_capture_route',return_value=True), \
                patch('build_chilko_corridor_profile.load_planform',return_value=box(-1,-10,9,10)), \
                patch('build_chilko_corridor_profile.route_xy',return_value=np.array([[0.,0.],[8.,0.]])), \
                patch('build_chilko_corridor_profile.route_planform_policy',return_value={}), \
                patch('build_chilko_corridor_profile.sha',return_value='fixture'),patch('builtins.print'):
            for step in (4.,1.):
                out=Path(tmp)/str(step)
                receipt=build(Path('terrain'),Path('route'),Path('polygon'),out,step=step)
                self.assertEqual(receipt['station_spacing_m'],step)
                with np.load(out/'profile.npz') as z:
                    profiles.append(np.interp(2.,z['station_m'],z['raw_reference_m']))
            self.assertEqual(profiles,[999.5,1000.])
            for reference,expected in zip(profiles,([False,False],[True,False])):
                _,owned=carve_mapped_water([1000.,1000.5],[1,1],[True,True],
                    [1000.,1000.],[4.,4.],[10.,10.],[1.,1.],ownership_reference=[reference,reference])
                np.testing.assert_array_equal(owned,expected)

if __name__=='__main__':unittest.main()
