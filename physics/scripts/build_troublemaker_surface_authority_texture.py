"""Encode surveyed/inferred surface classes as shader data, not painted terrain."""
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'tmp/south-fork-rock-return-xy-candidate-v2-20260907/registered_mesh_source.npz'
OUT=ROOT/'unreal/SourceArt/RaftSim/TroublemakerSurfaceAuthority'

def main():
    digest=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    manifest=json.loads(SOURCE.with_name('manifest.json').read_text())
    assert digest==manifest['mesh_sha256']
    with np.load(SOURCE) as d:
        authority=d['authority'];x=d['nominal_east_axis_m'];y=d['nominal_north_axis_m']
        dry=authority==1
        # Exclude the full adjacent cell ring at the inferred-water boundary.
        # Aerial whitewater must not be draped onto the model's submerged bed.
        interior=dry.copy()
        for dy,dx in ((-1,0),(1,0),(0,-1),(0,1)):
            interior &= np.roll(dry,(dy,dx),(0,1))
        interior[[0,-1],:]=False;interior[:,[0,-1]]=False
        rgb=np.zeros((*authority.shape,3),dtype=np.uint8)
        rgb[:,:,0]=interior*255
        # Green controls rock-like appearance, not measurement provenance.
        # Keep inferred flank support separately identifiable in blue.
        rgb[:,:,1]=np.isin(authority,[3,5])*255
        rgb[:,:,2]=(authority==5)*255
        OUT.mkdir(parents=True,exist_ok=True)
        path=OUT/'T_TroublemakerSurfaceAuthority.png'
        Image.fromarray(rgb).save(path)
        report={'source_mesh_sha256':digest,'texture_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'local_bounds_m':[float(x[0]-.25),float(y[-1]-.25),float(x[-1]+.25),float(y[0]+.25)],
            'origin_utm_m':manifest['origin_utm_m'],'world_y_sign':-1,
            'red':'dry DEM cells, one-cell water exclusion ring',
            'green':'interpreted rock-return or inferred flank support, not surveyed material classification',
            'blue':'inferred rock-flank cells only; never captured returns',
            'inferred_bed_receives_aerial_color':False,'geometry_modified':False}
        (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))

if __name__=='__main__':main()
