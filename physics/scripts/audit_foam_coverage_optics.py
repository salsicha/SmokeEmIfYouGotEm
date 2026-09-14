"""Audit optical breakup on the actual authored lace; not foam mass/realism."""
import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
TEXTURE=ROOT/'unreal/SourceArt/RaftSim/Water/T_RaftSim_SouthForkWater_FoamLace.png'
HELPER=ROOT/'unreal/Plugins/RaftSim/Shaders/Private/RaftSimFoamCoverage.ush'


def smoothstep(a,b,x):
    t=np.clip((x-a)/(b-a),0,1)
    return t*t*(3-2*t)


def breakup(coverage,lace,mean):
    return coverage+min(coverage/mean,(1-coverage)/(1-mean))*(lace-mean)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    assert not args.report.exists()
    sha=hashlib.sha256(TEXTURE.read_bytes()).hexdigest()
    assert sha=='5aeea75dc41b0441314064494ba440f85a80f3b5bd4726e77918ca7eab0d9576'
    image=np.asarray(Image.open(TEXTURE),dtype=np.float64)/255.
    assert image.shape==(1024,1024)
    source=HELPER.read_text()
    mean=float(re.search(r'MeanLace = ([0-9.]+);',source)[1])
    assert abs(mean-float(image.mean()))<1e-12
    levels=[]
    while True:
        cases=[]
        for p in (0,.01,.05,.12,.25,.5,.75,.95,.999999,1):
            new=breakup(p,image,mean)
            # Frozen prior material with minimum anti-alias width. The actual
            # old pixel result also depends on derivatives; this is not a GPU
            # image measurement or a claim about every projected pixel.
            amount=min(-np.log(max(1-p,1e-6))/3.,1)
            dense=smoothstep(.12,.65,amount)
            threshold=.8*(1-dense)+.12*dense
            old=(1-np.exp(-3*amount))*(.1+.9*smoothstep(threshold-.04,threshold+.04,image))
            cases.append(dict(input_coverage=p,new_mean=float(new.mean()),
                old_mean_minimum_aa=float(old.mean()),new_min=float(new.min()),new_max=float(new.max())))
            assert new.min()>=-1e-12 and new.max()<=1+1e-12
            assert abs(float(new.mean())-p)<1e-12
        levels.append(dict(size=list(image.shape),mean=float(image.mean()),cases=cases))
        if image.shape==(1,1):break
        image=image.reshape(image.shape[0]//2,2,image.shape[1]//2,2).mean(axis=(1,3))
    args.report.write_text(json.dumps(dict(passed=True,source_sha256=sha,
        helper_sha256=hashlib.sha256(HELPER.read_bytes()).hexdigest(),levels=levels,
        scope='Uncompressed linear authored texture and exact box mips. Shared helper tested separately on GPU. Runtime compression/warped spatial correlations can change local means. No fluid-mass, physical or visual acceptance.',
        visual_accepted=False),indent=2)+'\n')
    print(json.dumps(dict(passed=True,mip_levels=len(levels),source_mean=mean,
        coverage_12_percent=levels[0]['cases'][3])))


if __name__=='__main__':main()
