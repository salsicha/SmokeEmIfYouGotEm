import pytest
import shapely
from futaleufu_planform import parse_water,mapped_span


def geom(xy):return [dict(lon=x,lat=y) for x,y in xy]
def member(ref,role,xy):return dict(type='way',ref=ref,role=role,geometry=geom(xy))
def way(ref,xy):return dict(type='way',id=ref,tags=dict(natural='water',water='river'),geometry=geom(xy))
def relation(members):return dict(type='relation',id=10,tags=dict(type='multipolygon',natural='water',water='river'),members=members)


def test_relation_preserves_island_even_when_outer_way_is_also_tagged_water():
    outer=[(0,0),(10,0),(10,10),(0,10),(0,0)]
    inner=[(4,4),(6,4),(6,6),(4,6),(4,4)]
    result=parse_water(dict(elements=[relation([member(1,'outer',outer),member(2,'inner',inner)]),way(1,outer)]))
    assert len(result)==1
    p=result[0][2]
    assert p.area==96 and not p.covers(shapely.Point(5,5)) and p.covers(shapely.Point(1,1))


def test_split_outer_ways_join_exactly_without_snapping():
    m=[member(1,'outer',[(0,0),(10,0),(10,10)]),member(2,'outer',[(10,10),(0,10),(0,0)])]
    assert parse_water(dict(elements=[relation(m)]))[0][2].area==100
    m[1]['geometry'][0]['lon']=10.001
    with pytest.raises(ValueError,match='incomplete'):parse_water(dict(elements=[relation(m)]))


@pytest.mark.parametrize('xy', [[(0,0),(1,0),(1,1)],[(0,0),(1,1),(0,1),(1,0),(0,0)]])
def test_open_and_self_intersecting_water_are_not_repaired(xy):
    with pytest.raises(ValueError):parse_water(dict(elements=[way(1,xy)]))


def test_outside_inner_ring_is_refused():
    m=[member(1,'outer',[(0,0),(2,0),(2,2),(0,2),(0,0)]),
       member(2,'inner',[(4,4),(5,4),(5,5),(4,5),(4,4)])]
    with pytest.raises(ValueError,match='outside'):parse_water(dict(elements=[relation(m)]))


def test_unrelated_lake_and_waterway_relation_are_ignored():
    lake=way(1,[(0,0),(10,0),(10,10),(0,10),(0,0)]);lake['tags']['water']='lake'
    valid=way(2,[(20,20),(21,20),(21,21),(20,21),(20,20)])
    result=parse_water(dict(elements=[lake,valid,dict(type='relation',id=3,tags=dict(type='waterway'))]))
    assert len(result)==1 and result[0][1]==2


def test_cross_section_does_not_bridge_an_island_or_side_channel():
    p=shapely.union_all([shapely.box(-100,-5,-60,5),shapely.box(-20,-5,30,5)])
    assert mapped_span(p,[0,0],[1,0])==(-20,30)
    assert mapped_span(p,[-40,0],[1,0]) is None


def test_mapping_cannot_be_clamped_to_the_sampling_extent():
    with pytest.raises(ValueError,match='clamped'):
        mapped_span(shapely.box(-500,-10,500,10),[0,0],[1,0])
