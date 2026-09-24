"""Current project structure, not historical screenshot/asset hash contracts."""
from pathlib import Path
import json
import re
import unittest

ROOT=Path(__file__).resolve().parents[2]
CATALOG=json.loads((ROOT/'unreal/Config/scene_catalog.json').read_text(encoding='utf-8'))
PLUGIN=ROOT/'unreal/Plugins/RaftSim/Source'


class ProjectLayoutTests(unittest.TestCase):
    def test_shipping_scenes_match_frontend_and_cook_list(self):
        shipping={item['map'] for item in CATALOG['shipping']}
        self.assertEqual(len(shipping),len(CATALOG['shipping']))
        self.assertEqual(sum(item['role']=='river' for item in CATALOG['shipping']),6)
        config=(ROOT/'unreal/Config/DefaultGame.ini').read_text()
        cooked=re.findall(r'^\+MapsToCook=\(FilePath="([^"]+)"\)',config,re.M)
        self.assertEqual(len(cooked),len(set(cooked)))
        self.assertEqual(set(cooked),shipping)
        frontend=(PLUGIN/'RaftSimUI/Private/RaftSimVerticalSliceFrontend.cpp').read_text()
        launches=set(re.findall(r'TEXT\("(/Game/RaftSim/Maps/[^"\n]+)"\)',frontend))
        components={item['map'] for item in CATALOG['shipping'] if item['role']=='rapid_component'}
        self.assertEqual(launches,shipping-{'/Game/RaftSim/Maps/L_RaftSimBoot'}-components)
        self.assertTrue(components.isdisjoint(launches))
        for item in CATALOG['shipping']:
            if item['role']=='rapid_component':
                self.assertIn(item['parent_map'],launches)

    def test_current_maps_exist(self):
        for item in CATALOG['shipping']:
            path=ROOT/'unreal/Content'/(item['map'].removeprefix('/Game/')+'.umap')
            self.assertTrue(path.is_file(),str(path))

    def test_retired_scene_not_recreated_or_cooked(self):
        bootstrap=(PLUGIN/'RaftSimEditor/Private/Commands/RaftSimEditorVerticalSliceBootstrap.cpp').read_text()
        for item in CATALOG['retired']:
            path=ROOT/'unreal/Content'/(item['map'].removeprefix('/Game/')+'.umap')
            self.assertFalse(path.exists())
            self.assertNotIn('TEXT("'+item['map'].rsplit('/',1)[-1]+'")',bootstrap)
        self.assertFalse((ROOT/'unreal/Scripts/bootstrap_troublemaker.py').exists())

    def test_development_scenes_are_explicitly_not_cooked(self):
        config=(ROOT/'unreal/Config/DefaultGame.ini').read_text()
        self.assertIn('+DirectoriesToNeverCook=(Path="/Game/RaftSim/Maps/Review")',config)
        shipping={item['map'] for item in CATALOG['shipping']}
        self.assertTrue(all(item['map'] not in shipping for item in CATALOG['development']))

    def test_review_water_is_excluded_without_removing_playable_vfx(self):
        config=(ROOT/'unreal/Config/DefaultGame.ini').read_text()
        self.assertIn('+DirectoriesToNeverCook=(Path="/Game/RaftSim/VFX/Water/LiquidBodyReview")',config)
        self.assertIn('+DirectoriesToAlwaysCook=(Path="/Game/RaftSim/VFX/Water")',config)
        self.assertNotIn('+DirectoriesToNeverCook=(Path="/Game/RaftSim/VFX/Water")',config)
        self.assertTrue(any((ROOT/'unreal/Content/RaftSim/VFX/Water/LiquidBodyReview').glob('*.uasset')))

    def test_live_map_tests_cover_current_six_rivers(self):
        source=(PLUGIN/'RaftSimAutomation/Private/Tests/RaftSimTroublemakerMapTest.cpp').read_text()
        block=source.split('const TCHAR* GRiverMapPaths[] = {',1)[1].split('};',1)[0]
        tested=set(re.findall(r'TEXT\("([^"]+)"\)',block))
        self.assertEqual(tested,{item['map'] for item in CATALOG['shipping'] if item['role']=='river'})
        enumeration=source.split('void FRaftSimRiverMapLoadsTest::GetTests',1)[1].split('bool FRaftSimRiverMapLoadsTest::RunTest',1)[0]
        self.assertNotIn('if (MapExists',enumeration)
        self.assertNotIn('bUsesLegacyStraightRiverCoordinates',source)

    def test_native_ci_cannot_succeed_with_no_tests(self):
        cmake=(ROOT/'physics/cpp/CMakeLists.txt').read_text()
        workflow=(ROOT/'.github/workflows/physics.yml').read_text()
        self.assertIn('include(CTest)',cmake)
        self.assertIn('add_test(NAME water_${fixture}',cmake)
        self.assertIn('--no-tests=error',workflow)

    def test_local_scratch_and_accidental_hooks_are_excluded(self):
        ignore=(ROOT/'.gitignore').read_text().splitlines()
        self.assertIn('/tmp/',ignore)
        self.assertIn('/dev/null/',ignore)
        self.assertFalse(any((ROOT/'dev/null').glob('*')))


if __name__=='__main__':unittest.main()
