import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from build_catalog_map_contract import ROOT
from continuous_collision_probes import owners, sha, write_chunks
from export_colorado_continuous_runtime import registered_queries


class ChunkedCollisionProbes(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT/'tmp')
        self.addCleanup(self.temp.cleanup); self.out = Path(self.temp.name)/'probes'
        self.grid = dict(nx=270, ny=7, dx=2., dy=2., origin_x=0., origin_y=-6.)
        self.mapping = dict(schema='raftsim.curved_river_coordinate_map.v1',
            world_y_sign=-1, horizontal_origin_epsg6404_m=[242600., 650500.], vertical_datum_m=310.,
            points=[[float(s), float(s)-252., 0., 0., 1.] for s in range(0, 540, 2)])
        self.terrain = dict(horizontal_origin_epsg6404_m=[242600., 650500.], vertical_datum_m=310.,
            chunks=[dict(chunk=[x,y],world_northwest_xy_cm=[x*25200.,-(y+1)*25200.])
                for x in range(-2,3) for y in (-1,0)])
        rng = np.random.default_rng(71)
        self.bed = rng.uniform(320.,330.,(7,270)).astype('<f4')
        self.wet = (rng.random((7,270))>.2).astype('u1')

    def write(self, **kwargs):
        return write_chunks(self.out,ROOT,self.mapping,self.terrain,self.grid,self.bed,self.wet,**kwargs)

    def test_exact_legacy_values_order_and_hashes_across_blocks(self):
        _, queries = registered_queries(self.mapping,self.terrain,self.grid)
        rows, cols = np.nonzero(self.wet)
        xy = queries[rows,cols] - self.mapping['horizontal_origin_epsg6404_m']
        legacy = np.column_stack((xy[:,0]*100,-xy[:,1]*100,(self.bed[rows,cols]-310.)*100))
        indices = {tuple(c['chunk']):i for i,c in enumerate(self.terrain['chunks'])}
        assignment = owners(legacy,indices)
        for block in (1,31,262144):
            self.out = Path(self.temp.name)/str(block)
            receipt,files = self.write(block_cells=block)
            self.assertEqual(receipt['count'],int(self.wet.sum()))
            for c in receipt['chunks']:
                path = ROOT/c['file']
                self.assertEqual(files[c['file']],sha(path)); self.assertEqual(c['sha256'],sha(path))
                actual = np.fromfile(path,dtype='<f8').reshape(-1,3)
                np.testing.assert_array_equal(actual,legacy[assignment==indices[tuple(c['chunk'])]])
                self.assertEqual(len(actual),c['count'])

    def test_native_boundary_tiebreak_and_missing_primary(self):
        points = np.array([[0,0,1],[25200,-25200,2],[-25200,25200,3]],dtype=float)
        self.assertEqual(owners(points,{(0,0):0,(1,1):1,(-1,-1):2}).tolist(),[0,1,2])
        self.assertEqual(owners(points[:1],{(-1,-1):7}).tolist(),[7])
        with self.assertRaisesRegex(ValueError,'no source terrain'): owners(points,{})
        with self.assertRaisesRegex(ValueError,'finite'): owners([[0,0,float('nan')]],{})

    def test_reject_bad_shape_mask_duplicate_chunk_and_existing_output(self):
        self.wet[0,0]=2
        with self.assertRaisesRegex(ValueError,'Nonbinary'):self.write()
        self.wet[0,0]=1
        with self.assertRaises(FileExistsError):self.write()
        self.out=Path(self.temp.name)/'duplicate'
        self.terrain['chunks'].append(self.terrain['chunks'][0])
        with self.assertRaisesRegex(ValueError,'duplicate'):self.write()

    def test_disk_reserve_and_no_wet_cells(self):
        with patch('continuous_collision_probes.shutil.disk_usage') as disk:
            disk.return_value.free=40*1024**3
            with self.assertRaisesRegex(ValueError,'reserve'):self.write()
        self.assertFalse(self.out.exists())
        self.wet[:]=0
        with self.assertRaisesRegex(ValueError,'No cooked wet'):self.write()


if __name__=='__main__':unittest.main()
