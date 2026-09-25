from prepare_troublemaker_mixed_union import candidate_solid_metadata


def test_new_closure_replaces_parent_statistics_without_mutating_parent():
    old={'inferred_solid':{'internal_floor_m':2.9,'volume_m3':2087.,
                           'manifold_edge_count':9606}}
    receipt={'closure':{'volume_m3':2086.,'manifold_edge_count':9642,
                        'maximum_volume_error_m3':0.,'inferred_vertical_wall_triangles':496}}
    result=candidate_solid_metadata(old,receipt)
    assert result==dict(internal_floor_m=2.9,**receipt['closure'])
    assert old['inferred_solid']['manifold_edge_count']==9606
