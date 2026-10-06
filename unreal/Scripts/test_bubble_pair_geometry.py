"""Connected pair mesh, seam and gas-volume checks at actual trajectory poses."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_bubble_pair_lab import geometry

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--migration',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
args=p.parse_args(sys.argv[sys.argv.index('--')+1:])
if args.output.exists():
    raise FileExistsError(args.output)
data=json.loads(args.migration.read_text())
volume=data['equilibrium']['model']['nominal_gas_volume_m3']
rows=[]
for index in (0,5,11):
    distance=data['frames'][index]['distance_m']
    estimates=[]
    for edges,rings in ((32,96),(64,192)):
        verts,faces,films,gas=geometry(data['equilibrium'],distance,edges,rings)
        errors=np.asarray(gas)/volume-1
        assert abs(gas[0]/gas[1]-1)<1e-10
        # The only x=0 water vertices are the common exterior seam: no
        # buried dielectric partition is allowed between the two cavities.
        xyz=np.array(verts)
        assert not any(all(abs(xyz[i,0])<1e-13 for i in face) for face in faces)
        estimates.append(dict(edge_steps=edges,rings=rings,relative_gas_volume_errors=errors.tolist(),
                              vertices=len(verts),faces=len(faces)))
    assert max(abs(e) for e in estimates[0]['relative_gas_volume_errors'])<.003
    assert max(abs(e) for e in estimates[1]['relative_gas_volume_errors'])<max(abs(e) for e in estimates[0]['relative_gas_volume_errors'])
    rows.append(dict(frame=index+1,checks=estimates))
report=dict(frames=rows,accepted=False,scope='Closed connected geometry, no interior water partition and gas-volume refinement; superposition is not exact coupled 3D equilibrium.')
args.output.write_text(json.dumps(report,indent=2))
print('PAIR_GEOMETRY_TESTS',json.dumps(report),flush=True)
