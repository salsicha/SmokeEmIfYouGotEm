import unittest
from verify_futaleufu_expanded_native_domain import physical_ports, physical_scenario


class NativeRepairTests(unittest.TestCase):
    def test_only_nonphysical_metadata_is_excluded(self):
        self.assertEqual(physical_scenario({'metadata':{'description':'before'},'roughness':.045}),
            physical_scenario({'metadata':{'description':'after'},'roughness':.045}))
        self.assertNotEqual(physical_scenario({'roughness':.045}),physical_scenario({'roughness':.04}))

    def test_port_identity_survives_tile_reindexing(self):
        a=dict(tile_indices=[[1,2]],boundary_probes=[dict(tile_index=0,edge='west',role='upstream',branch='rio_azul')])
        b=dict(tile_indices=[[0,0],[1,2]],boundary_probes=[dict(tile_index=1,edge='west',role='upstream',branch='rio_azul')])
        self.assertEqual(physical_ports(a),physical_ports(b))
        b['boundary_probes'][0]['edge']='east'
        self.assertNotEqual(physical_ports(a),physical_ports(b))

    def test_duplicate_physical_ports_refuse(self):
        row=dict(tile_index=0,edge='west',role='upstream',branch='rio_azul')
        with self.assertRaises(ValueError):physical_ports(dict(tile_indices=[[1,2]],boundary_probes=[row,row]))
