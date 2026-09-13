"""Find complete, fixed-size live crops without inventing exterior water state."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach"


def sha(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source,"sha256").hexdigest()


def rectangles(mask):
    """Merge equal horizontal runs vertically, returning exclusive index bounds."""
    result, active = [], {}
    for y,row in enumerate(mask):
        edges = np.diff(np.r_[False,row,False].astype(np.int8))
        runs = list(zip(np.flatnonzero(edges==1),np.flatnonzero(edges==-1)))
        next_active = {}
        for a,b in runs:
            key = (int(a),int(b))
            start = active.pop(key,y)
            next_active[key] = start
        result.extend((a,start,b,y) for (a,b),start in active.items())
        active = next_active
    result.extend((a,start,b,len(mask)) for (a,b),start in active.items())
    return result


def main():
    import rasterio
    from scipy.spatial import cKDTree
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audit",type=Path)
    parser.add_argument("output",type=Path)
    args = parser.parse_args()
    assert not args.output.exists()
    audit = json.loads(args.audit.read_text())
    source_path = BASE / "hydraulic_regions_context/manifest.json"
    route_path = BASE / "playable_route/coordinate_map.json"
    assert sha(source_path)==audit["source_manifest_sha256"]
    source = json.loads(source_path.read_text())
    assert sha(route_path)==source["coordinate_map_sha256"]
    route = json.loads(route_path.read_text())
    datum_xy = np.asarray(route["origin_utm_m"])
    windows, masks, all_rects, rect_owners = [], [], [], []
    centers = np.asarray([r["center_utm_m"] for r in source["regions"]])
    x,y = np.meshgrid(np.arange(115,206),np.arange(115,206))
    for owner,(record,checked) in enumerate(zip(source["regions"],audit["regions"])):
        assert record["name"]==checked["name"]
        path=ROOT/record["geometry_file"]
        assert sha(path)==record["geometry_sha256"]==checked["source_geometry_sha256"]
        with np.load(path,allow_pickle=False) as packet:
            wet=packet["captured_water_mask"].astype(bool)
        modeled=np.zeros(wet.shape,dtype=bool)
        for entry in checked["intersections"]:
            y0,y1,x0,x1=entry["packet_slice"]
            modeled[y0:y1,x0:x1]=True
        unknown=wet & ~modeled
        assert int(unknown.sum())==checked["unmodeled_captured_wet_cells"]
        integral=np.pad(unknown.astype(np.int32).cumsum(0).cumsum(1),((1,0),(1,0)))
        count=integral[y+115,x+115]-integral[y-114,x+115]-integral[y+115,x-114]+integral[y-114,x-114]
        safe=count==0
        masks.append(safe)
        # Four safe integer corners prove every continuous center in a unit
        # square: outward-rounded crop+ghost cells are the corners' union.
        quads=safe[:-1,:-1]&safe[1:,:-1]&safe[:-1,1:]&safe[1:,1:]
        covered=np.zeros(safe.shape,dtype=bool)
        for dy in (0,1):
            for dx in (0,1): covered[dy:dy+90,dx:dx+90] |= quads
        bounds=list(rectangles(quads))
        # Keep any genuinely admissible degenerate rows/points too; do not
        # silently discard an integer center just because it has no quad.
        for row in range(91):
            for a,_,b,_ in rectangles((safe & ~covered)[row:row+1]):
                bounds.append((a,row,b-1,row))
        origin=centers[owner]-160
        world_bounds=[(np.asarray(b)+np.tile(origin+115,2)).tolist() for b in bounds]
        local_bounds=[(np.asarray(b)-np.tile(datum_xy,2)).tolist() for b in world_bounds]
        windows.append(dict(window_id=record["name"],valid_live_center_bounds_m=local_bounds,
                            safe_integer_centers=int(safe.sum()),center_rectangle_count=len(bounds)))
        all_rects.extend(world_bounds)
        rect_owners.extend([owner]*len(bounds))
    all_rects=np.asarray(all_rects)
    with rasterio.open(BASE/"unknown_submerged_bed_mask.tif") as dataset:
        rows,columns=np.nonzero(dataset.read(1)==1)
        water=np.column_stack((dataset.transform.c+(columns+.5)*2.,dataset.transform.f-(rows+.5)*2.))
    _,nearest=cKDTree(centers).query(water,p=np.inf)
    available=np.zeros(len(water),dtype=bool)
    for owner,mask in enumerate(masks):
        indexes=np.flatnonzero(nearest==owner)
        if not len(indexes): continue
        positions=water[indexes]-(centers[owner]-45)
        assert np.array_equal(positions,np.rint(positions))
        positions=positions.astype(int)
        assert positions.min()>=0 and positions.max()<=90
        available[indexes]=mask[positions[:,1],positions[:,0]]
    bad=np.flatnonzero(~available)
    assert len(bad)==audit["original_water_domain_crop_ghost_failures"]
    shifted=[]
    for index in bad:
        position=water[index]
        candidates=np.maximum(all_rects[:,:2],np.minimum(position,all_rects[:,2:]))
        squared=np.square(candidates-position).sum(axis=1)
        chosen=int(np.argmin(squared))
        center=candidates[chosen]
        margin=112.-float(np.max(np.abs(center-position)))
        shifted.append(dict(position_utm_m=position.tolist(),center_utm_m=center.tolist(),
                            window_id=windows[rect_owners[chosen]]["window_id"],
                            shift_m=float(np.sqrt(squared[chosen])),raft_interior_margin_m=margin))
    minimum_margin=min(r["raft_interior_margin_m"] for r in shifted) if shifted else 112.
    result=dict(schema="raftsim.cartesian_live_center_coverage.v1",source_manifest_sha256=sha(source_path),
                coverage_audit_sha256=sha(args.audit),route_sha256=sha(route_path),
                live_window_extent_m=[224.,224.],source_context_cells=3,ghost_layers=2,
                windows=windows,original_water_probes=len(water),unchanged_centers=int(available.sum()),
                shifted_centers=len(shifted),minimum_raft_interior_margin_m=minimum_margin,
                maximum_center_shift_m=max((r["shift_m"] for r in shifted),default=0.),
                rectangle_count=len(all_rects),unusable_source_windows=sum(not w["center_rectangle_count"] for w in windows),
                all_original_probes_have_complete_crop_and_8m_raft_margin=minimum_margin>=8.,
                settling_accepted=False,normal_map_integrated=False,shifted_probe_records=shifted)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in ("windows","shifted_probe_records")},indent=2))


if __name__=="__main__":
    main()
