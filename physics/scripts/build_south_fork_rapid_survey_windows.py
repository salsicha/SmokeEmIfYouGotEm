"""Build native-source half-metre search windows for every named South Fork rapid."""
from pathlib import Path
import json
import sys
import re

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tmp/south-fork-geospatial-deps'))
import rasterio
from rasterio.warp import transform_bounds
from shapely.geometry import box
from build_south_fork_survey_reconstruction import reconstruct_window,read_breaklines,validated_horizontal_crs

BASE=ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'


def main():
    atlas=json.loads((BASE/'sources/rapid_atlas/index.json').read_text())
    if atlas['failures']: raise ValueError('Incomplete reference atlas')
    tiles=json.loads((BASE/'sources/dem/full-reach-downloads.json').read_text())
    footprints=[]
    for tile in tiles:
        with rasterio.open(BASE/'sources/dem'/tile['file']) as src:
            bounds=transform_bounds(validated_horizontal_crs(src),'EPSG:32610',*src.bounds)
            footprints.append((tile,box(*bounds)))
    breaklines=read_breaklines()
    reports=[]
    for entry in atlas['entries']:
        slug=re.sub(r'[^a-z0-9]+','_',entry['rapid'].lower()).strip('_')
        metadata=json.loads((BASE/'sources/rapid_atlas'/slug/'export.json').read_text())
        e=metadata['extent']; region=box(e['xmin'],e['ymin'],e['xmax'],e['ymax'])
        selected=[tile for tile,footprint in footprints if footprint.intersects(region)]
        report=reconstruct_window('rapid_windows/'+slug,breaklines,selected,export_metadata=metadata,preselected=True)
        report['rapid_name']=entry['rapid']; report['rapid_identity_verified']=False
        report['status']='captured_search_window_requires_rapid_location_review'
        target=BASE/'rapid_windows'/slug/'manifest.json'
        target.write_text(json.dumps(report,indent=2),encoding='utf-8')
        reports.append({'rapid':entry['rapid'],'manifest':target.relative_to(ROOT).as_posix(),
            'valid_fraction':report['valid_fraction'],'rapid_identity_verified':False})
    (BASE/'rapid_windows/index.json').write_text(json.dumps({'windows':reports,'production_promoted':False},indent=2),encoding='utf-8')


if __name__=='__main__':main()
