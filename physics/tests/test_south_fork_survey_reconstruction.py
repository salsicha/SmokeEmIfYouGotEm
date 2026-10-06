"""Geographic and unit regressions independent of visual acceptance claims."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tmp/south-fork-geospatial-deps'))
sys.path.insert(0,str(ROOT/'physics/src'))
from pyproj import CRS
from shapely.geometry import LineString
import numpy as np
import rasterio

spec = importlib.util.spec_from_file_location('survey_reconstruction', ROOT / 'physics/scripts/build_south_fork_survey_reconstruction.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
axis_spec = importlib.util.spec_from_file_location('survey_axis', ROOT / 'physics/scripts/align_south_fork_survey_axis.py')
axis = importlib.util.module_from_spec(axis_spec)
axis_spec.loader.exec_module(axis)
BASE = ROOT / 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'


class SurveyReconstructionTests(unittest.TestCase):
    def test_continuation_requires_unchanged_grid_bed_axes_and_constant_forcing(self):
        import runpy
        validate=runpy.run_path(str(ROOT/'physics/scripts/cook_troublemaker_survey_hydraulics.py'))['validate_continuation_layout']
        fine=SimpleNamespace(grid='grid',bed=np.zeros((2,2)))
        parent=SimpleNamespace(**vars(fine),boundaries=())
        registration={'geometry_sha256':'g','downstream_unit':[-.9299998355760436,.36755993501540923]}
        validate(fine,parent,registration,'g')
        for change in ({'grid':'different'},{'bed':np.ones((2,2))},
                       {'boundaries':(SimpleNamespace(hydrograph=[(0,1)]),)}):
            with self.subTest(change=str(change)):
                with self.assertRaises(ValueError):validate(fine,SimpleNamespace(**{**vars(parent),**change}),registration,'g')
        for change in ({'geometry_sha256':'other'},{'downstream_unit':[1,0]}):
            with self.subTest(change=change):
                with self.assertRaises(ValueError):validate(fine,parent,{**registration,**change},'g')

    def test_refinement_inherits_forcing_without_resampling_boundary_stage(self):
        import runpy
        from raftsim.scenario2_5d import BoundaryCondition2_5D
        inherit=runpy.run_path(str(ROOT/'physics/scripts/cook_troublemaker_survey_hydraulics.py'))['refinement_boundaries']
        metadata=SimpleNamespace(provenance={'target_discharge_m3s':45.3})
        fine=SimpleNamespace(metadata=metadata,fixed_dt=.1,roughness=.035,
            boundaries=(BoundaryCondition2_5D('west','inflow',stage=10.001),))
        parent=SimpleNamespace(fixed_dt=.1,roughness=.035,
            boundaries=(BoundaryCondition2_5D('west','inflow',stage=10.),))
        registration=dict(boundary_mode='mixed',cfl=.2,solver_binary_sha256='same',target_discharge_m3s=45.3)
        kwargs=dict(boundary_mode='mixed',cfl=.2,solver_sha='same')
        self.assertIs(inherit(fine,parent,registration,**kwargs),parent.boundaries)
        self.assertEqual(fine.boundaries[0].stage,10.001)
        for key,value in (('boundary_mode','different'),('cfl',.38),
                          ('solver_binary_sha256','changed'),('target_discharge_m3s',60.),
                          ('bed_sampling','render_triangles')):
            with self.subTest(key=key):
                with self.assertRaises(ValueError):inherit(fine,parent,dict(registration,**{key:value}),**kwargs)
        for key,value in (('fixed_dt',.2),('roughness',.04)):
            with self.subTest(key=key):
                with self.assertRaises(ValueError):inherit(fine,SimpleNamespace(**{**vars(parent),key:value}),registration,**kwargs)

    def test_hydraulic_refinement_preserves_physical_boundary(self):
        import runpy
        make_grid=runpy.run_path(str(ROOT/'physics/scripts/cook_troublemaker_survey_hydraulics.py'))['physical_grid']
        coarse=make_grid(1.)
        fine=make_grid(.5)
        for attr,size,count in [('origin_x','dx','nx'),('origin_y','dy','ny')]:
            self.assertEqual(getattr(coarse,attr)-getattr(coarse,size)/2,
                getattr(fine,attr)-getattr(fine,size)/2)
            self.assertEqual(getattr(coarse,count)*getattr(coarse,size),getattr(fine,count)*getattr(fine,size))
        for invalid in (0,-1,float('nan'),.3,2):
            with self.assertRaises(ValueError):make_grid(invalid)

    def test_mixed_regime_inlet_is_explicit_and_requires_discharge(self):
        from raftsim.dual_solver import CppSolverRunConfig
        self.assertFalse(CppSolverRunConfig(executable=Path('unused')).experimental_west_supercritical_stage)
        with self.assertRaises(ValueError):
            CppSolverRunConfig(executable=Path('unused'),experimental_west_supercritical_stage=True)
        config=CppSolverRunConfig(executable=Path('unused'),solver_mode='finite_volume',
            disable_fixture_calibrations=True,experimental_west_discharge_m3s=45.3,
            experimental_west_supercritical_stage=True)
        self.assertTrue(config.experimental_west_supercritical_stage)

    def test_candidate_does_not_excavate_captured_dry_ground(self):
        folder=BASE/'troublemaker/geometry_candidate'
        data=np.load(folder/'engine_mesh_source.npz')
        measured=data['authority']==1
        self.assertTrue(np.array_equal(data['z_m'][measured],data['source_surface_m'][measured]))
        self.assertTrue(np.isfinite(data['z_m']).all())
        self.assertTrue(np.any(data['authority']==3))
        manifest=json.loads((folder/'manifest.json').read_text())
        self.assertFalse(manifest['production_promoted'])
        self.assertEqual(manifest['random_rocks_added'],0)

    def test_axis_cannot_cross_a_dry_gap_or_diagonal_corner(self):
        wet = np.eye(3,dtype=bool)
        self.assertFalse(axis.wet_segment((0,0),(2,2),wet))
        with self.assertRaises(ValueError):
            axis.channel_path(wet,np.ones((3,3)),np.zeros((3,3)),(0,0),(2,2))

    def test_axis_routes_around_land_without_modifying_it(self):
        wet = np.ones((9,9),dtype=bool)
        wet[2:7,4]=False
        original=wet.copy()
        path,_=axis.channel_path(wet,np.ones(wet.shape),np.zeros(wet.shape),(4,0),(4,8))
        simplified=axis.simplify_inside_water(path,wet)
        self.assertTrue(np.array_equal(wet,original))
        self.assertTrue(all(axis.wet_segment(a,b,wet) for a,b in zip(simplified[:-1],simplified[1:])))

    def test_full_aligned_axis_stays_inside_captured_water(self):
        data=json.loads((BASE/'survey_constrained_route_candidate.geojson').read_text())
        feature=data['features'][0]
        points=np.array([module.TO_METRIC.transform(*p) for p in feature['geometry']['coordinates']])
        with rasterio.open(BASE/'full_reach/unknown_submerged_bed_mask.tif') as ds:
            wet=ds.read(1)==1
            col,row=(~ds.transform)*(points[:,0],points[:,1])
            cells=np.column_stack([row-.5,col-.5])
        self.assertTrue(all(axis.wet_segment(a,b,wet) for a,b in zip(cells[:-1],cells[1:])))
        self.assertTrue(33000<LineString(points).length<34500)
        self.assertFalse(feature['properties']['production_promoted'])

    def test_survey_foot_is_not_international_foot_or_metre(self):
        self.assertAlmostEqual(module.FT_US_TO_M, 0.3048006096012192, places=15)
        self.assertAlmostEqual(1000 * module.FT_US_TO_M, 304.8006096012192, places=10)

    def test_compound_crs_has_vertical_component_removed(self):
        src = SimpleNamespace(crs=CRS.from_user_input('EPSG:6418+6360'), units=('US survey foot',))
        result = CRS.from_wkt(module.validated_horizontal_crs(src))
        self.assertFalse(result.is_compound)
        self.assertEqual(result.to_epsg(), 6418)

    def test_wrong_units_rejected(self):
        with self.assertRaises(ValueError):
            module.validated_horizontal_crs(SimpleNamespace(crs=CRS.from_epsg(6418), units=('metre',)))

    def test_wrong_vertical_datum_rejected(self):
        with self.assertRaises(ValueError):
            module.validated_horizontal_crs(SimpleNamespace(crs=CRS.from_user_input('EPSG:6418+5703'), units=('US survey foot',)))

    def test_image_pixel_mapping_uses_returned_extent(self):
        meta = {'width':100, 'height':50, 'extent': {'xmin':10,'xmax':210,'ymin':30,'ymax':130,'spatialReference':{'wkid':32610}}}
        self.assertEqual(module.pixel_to_metric({'pixel_xy':[0,0]}, meta), (10,130))
        self.assertEqual(module.pixel_to_metric({'pixel_xy':[100,50]}, meta), (210,30))
        with self.assertRaises(ValueError):
            module.pixel_to_metric({'pixel_xy':[-1,0]}, meta)

    def test_corrected_route_and_old_origin_cannot_be_confused(self):
        features = json.loads((BASE/'corrected_route_candidate.geojson').read_text())['features']
        route = next(f for f in features if f['geometry']['type']=='LineString')
        line = LineString([module.TO_METRIC.transform(*p) for p in route['geometry']['coordinates']])
        bridge = next(f for f in features if f.get('id')=='chili_bar_bridge_channel_crossing')['properties']['metric_xy']
        module.validate_origin(line, bridge)
        self.assertTrue(33000 < line.length < 34500)
        old = module.TO_METRIC.transform(-120.7199431,38.7786168)
        with self.assertRaises(ValueError):
            module.validate_origin(LineString([old,*line.coords]), bridge)
        self.assertFalse(route['properties']['production_promoted'])

    def test_full_reach_has_no_missing_corridor_elevation(self):
        manifest = json.loads((BASE/'full_reach/manifest.json').read_text())
        self.assertEqual(manifest['source_tile_count'],82)
        self.assertEqual(manifest['corridor_valid_fraction'],1)
        self.assertFalse(manifest['bathymetry_known'])
        self.assertFalse(manifest['measured_dry_terrain_modified'])
        with rasterio.open(BASE/'full_reach/captured_surface_navd88_m.tif') as ds:
            surface = ds.read(1)
        with rasterio.open(BASE/'full_reach/unknown_submerged_bed_mask.tif') as ds:
            mask = ds.read(1)
        self.assertTrue(np.isfinite(surface[mask!=255]).all())
        self.assertEqual(set(np.unique(mask)),{0,1,255})
        self.assertTrue(np.isnan(surface[mask==255]).all())


if __name__ == '__main__':
    unittest.main()
