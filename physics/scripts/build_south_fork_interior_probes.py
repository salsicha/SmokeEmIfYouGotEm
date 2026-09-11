"""Prepare off-vertex probes to distinguish bilinear bed from the render mesh."""
from pathlib import Path
import sys
import json
import hashlib
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tmp/south-fork-geospatial-deps'))
sys.path.insert(0,str(ROOT/'physics/src'))
import numpy as np
from raftsim.scenario2_5d import read_scenario2_5d_package
from south_fork_mesh_sampling import sample_mesh_raster


def main():
    folder=ROOT/'tmp/south-fork-survey-hydraulics'
    probes=[];metrics=[]
    for label in ('1m-mixed-inlet-enclosed-rock-gaps-continuation-20260907',
                  '0.5m-mixed-inlet-enclosed-rock-gaps-settling-20260907'):
        work=folder/label
        registration=json.loads((work/'registration.json').read_text())
        scenario=read_scenario2_5d_package(next((work/'scenario').glob('*/scenario.json')))
        source=ROOT/'tmp/south-fork-rock-gap-candidate-20260907/shared_render_collision_hydraulic_bed_navd88_m.tif'
        if hashlib.sha256(source.read_bytes()).hexdigest()!=registration['geometry_sha256']:
            raise ValueError('Geometry identity changed')
        x,y=scenario.grid.meshgrid()
        origin=np.asarray(registration['origin_utm_m'])
        tangent=np.asarray(registration['downstream_unit']);left=np.asarray(registration['left_unit'])
        east=origin[0]+x*tangent[0]+y*left[0]
        north=origin[1]+x*tangent[1]+y*left[1]
        mesh=sample_mesh_raster(source,east,north)-registration['vertical_origin_navd88_m']
        delta=mesh-scenario.bed
        wet=scenario.initial_state.depth>.1
        eligible=np.flatnonzero(wet&(abs(x)<50))
        selected=eligible[np.argsort(-abs(delta.ravel()[eligible]))[:8]]
        for index in selected:
            r,c=np.unravel_index(index,scenario.grid.shape)
            probes.append({'label':label,'row_col':[int(r),int(c)],
                'position_cm':[float((east[r,c]-origin[0])*100),float((north[r,c]-origin[1])*100)],
                'triangle_height_cm':float(mesh[r,c]*100),'bilinear_height_cm':float(scenario.bed[r,c]*100),
                'difference_cm':float(delta[r,c]*100)})
        metrics.append({'grid_m':scenario.grid.dx,'wet_cell_count':int(wet.sum()),
            'absolute_height_difference_p50_p95_max_m':np.percentile(abs(delta[wet]),[50,95,100]).tolist(),
            'wet_cells_differing_more_than_10cm':int(np.sum(wet&(abs(delta)>.1)))})
    output=ROOT/'docs/reconstruction-review-2026-09-07/interior-mesh-probes.json'
    with output.open('x',encoding='utf-8') as handle:
        json.dump({'scope':__doc__,'source_geometry_sha256':registration['geometry_sha256'],
            'metrics':metrics,'probes':probes,'production_promoted':False},handle,indent=2)
    print(json.dumps(metrics,indent=2))


if __name__=='__main__':main()
