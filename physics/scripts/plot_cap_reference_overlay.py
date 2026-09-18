"""Plot unchanged source-image pixels with the retained cap and player-view hits.

Reference interpretation only. Neither image color nor a class-1 return is a
rock/vegetation classification; 2019/2022 dates and 3m registration remain limits.
"""
import argparse
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np

from build_troublemaker_dem_rock_cap import BASE, ORIGIN, ROOT
from south_fork_rock_union import sha


def run(output):
    if output.exists():
        raise ValueError('Fresh output required')
    manifest=json.loads((ROOT/'tmp/troublemaker-source-connected-landward-v1-20260915/manifest.json').read_text())
    image_path=BASE/'sources/troublemaker_naip.png'
    metadata_path=BASE/'sources/troublemaker_naip_export.json'
    cap_path=ROOT/manifest['cap_path']
    rays_path=ROOT/'tmp/constriction-downstream-source-rays-v1-20260918.json'
    rays=json.loads(rays_path.read_text())
    expected=((image_path,manifest['source_naip_sha256']),
        (metadata_path,manifest['source_naip_export_sha256']),
        (cap_path,manifest['cap_sha256']),
        (cap_path,rays['source_identities']['cap']['sha256']),
        (ROOT/rays['view_path'],rays['view_sha256']))
    if not rays['all_probes_match'] or any(sha(path)!=digest for path,digest in expected):
        raise ValueError('Source image/cap/native-view identity changed')
    with np.load(cap_path,allow_pickle=False) as data:
        xyz=data['vertices_m'];edges=data['boundary_edges']
    metadata=json.loads(metadata_path.read_text())['extent']
    if metadata['spatialReference']['wkid']!=32610:
        raise ValueError('Expected metric UTM frame')
    extent=[metadata['xmin']-ORIGIN[0],metadata['xmax']-ORIGIN[0],metadata['ymin']-ORIGIN[1],metadata['ymax']-ORIGIN[1]]
    hits=np.array([r['source_hit']['local_hit_m'] for r in rays['probes'] if r['source_hit']['source']=='cap'])
    fig,axes=plt.subplots(1,2,figsize=(13,9),layout='constrained')
    axes[0].imshow(plt.imread(image_path),extent=extent,interpolation='nearest')
    axes[0].add_collection(LineCollection(xyz[edges,:2],colors='magenta',linewidths=.6))
    axes[0].scatter(*hits[:,:2].T,s=25,c='cyan',marker='x')
    axes[0].set_title('2022 NAIP original pixels + interpreted cap boundary\ncyan: actual downstream source-ray hits; 3m registration uncertainty')
    artist=axes[1].scatter(*xyz[:,:2].T,c=xyz[:,2],s=10,cmap='terrain',vmin=6,vmax=12)
    axes[1].add_collection(LineCollection(xyz[edges,:2],colors='black',linewidths=.6))
    axes[1].scatter(*hits[:,:2].T,s=25,c='red',marker='x')
    axes[1].set_title('2019 original selected return elevations\nNAVD88 minus 220m; class1 remains unclassified')
    fig.colorbar(artist,ax=axes[1],label='Relative elevation (m)')
    for axis in axes:
        axis.set(xlim=(-28,8),ylim=(7,38),xlabel='Local east (m)',ylabel='Local north (m)')
        axis.set_aspect('equal');axis.grid(alpha=.2)
    fig.savefig(output,dpi=140)
    plt.close(fig)


if __name__=='__main__':
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    run(parser.parse_args().output)
