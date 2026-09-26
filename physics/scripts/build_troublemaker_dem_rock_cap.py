"""Recover an exposed-rock interpretation above the retained DEM, not bathymetry.

The source image/returns support a compact rock hypothesis outside the older
water-only selection. Original DEM and registered terrain stay immutable.
The optional vertical connection below that cap is explicitly inferred. Neither
closed geometry nor numeric sampling establishes playable integration.
"""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
from scipy.spatial import Delaunay
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'
PARENT = BASE/'full_reach/composite_terrain/troublemaker_registered_source.npz'
RETURNS = BASE/'troublemaker/classified_lidar_returns.npz'
PARENT_SHA = '8bdf1a586e7bd2536eaf25a982763efd9e5a558e7172fd7897b8ae0ecc8fe06b'
RETURNS_SHA = '7f0a5d903a3914c830916390820cbf99260d7cb2f2cf667c57f2a1faa1c47cfe'
ORIGIN = np.array([683805.1336302214, 4296673.447587562, 220.])
# Interpreted search window, NOT a surveyed rock outline. It follows the compact
# exposed patch in the original NAIP; original XYZ still determines each vertex.
REGION = [[-7.,14.],[-7.,23.],[-4.,25.],[0.,24.],[3.,21.],
          [3.,12.],[0.,9.],[-2.,11.],[-4.,13.]]


def select_lower_returns(xyz, classification, above_dem, polygon,
                         cell_m=.5, minimum_count=2, threshold_m=.3,
                         corroborate_single_returns=False):
    """One exact original return per supported bin, stable original-index ties.

    No water-mask prerequisite; no smoothing, averaging or raster relocation.
    Selection/rock classification and bin spacing are explicit inference.
    """
    xyz = np.asarray(xyz, dtype=float)
    classification, above_dem = np.asarray(classification), np.asarray(above_dem)
    if xyz.ndim != 2 or xyz.shape[1] != 3 or classification.shape != (len(xyz),) or above_dem.shape != (len(xyz),):
        raise ValueError('Matching XYZ, classification and DEM residuals required')
    if not np.isfinite(xyz).all() or not np.isfinite(above_dem).all():
        raise ValueError('Nonfinite source observations cannot enter this reconstruction')
    if not np.isfinite(cell_m) or cell_m <= 0 or minimum_count < 1 or int(minimum_count) != minimum_count:
        raise ValueError('Positive bin size and integer return count required')
    if not np.isfinite(threshold_m) or threshold_m < 0:
        raise ValueError('Nonnegative DEM-clearance threshold required')
    polygon = Polygon(polygon)
    if not polygon.is_valid or polygon.area <= 0:
        raise ValueError('Valid positive-area interpreted region required')
    from shapely import intersects_xy
    inside = intersects_xy(polygon, xyz[:,0], xyz[:,1])
    eligible = inside & np.isin(classification, [1,2,20]) & (above_dem > threshold_m)
    indices = np.flatnonzero(eligible)
    if not len(indices):
        return indices, np.empty(0, dtype=np.int64)
    bins = np.floor(xyz[indices,:2]/cell_m).astype(np.int64)
    _, cell_index = np.unique(bins, axis=0, return_inverse=True)
    counts = np.bincount(cell_index)
    order = np.lexsort((indices, xyz[indices,2], cell_index))
    groups = cell_index[order]
    first = np.r_[True, groups[1:] != groups[:-1]]
    chosen = indices[order[first]]
    support = counts[groups[first]]
    keep = support >= minimum_count
    if corroborate_single_returns:
        # Same non-recursive evidence rule as the earlier rock recovery: only
        # originally multi-return bins may corroborate a singleton, never a
        # newly accepted singleton or an interpolated surface.
        selected_bins = bins[order[first]]
        strong = {tuple(cell): xyz[index,2] for cell,index,valid in
                  zip(selected_bins,chosen,keep) if valid}
        for i in np.flatnonzero(support == 1):
            x,y = selected_bins[i]
            heights = [strong[(x+dx,y+dy)] for dx in (-1,0,1) for dy in (-1,0,1)
                       if (dx or dy) and (x+dx,y+dy) in strong]
            if len(heights) >= 2 and min(heights)-1 <= xyz[chosen[i],2] <= max(heights)+1:
                keep[i] = True
    return chosen[keep], support[keep]


def cap_triangles(xyz, polygon, maximum_edge_m=1.):
    """Locally inferred adjacency only; gaps/concave boundaries are not filled."""
    xyz = np.asarray(xyz, dtype=float)
    region = Polygon(polygon)
    if xyz.ndim != 2 or xyz.shape[1] != 3 or len(xyz) < 3 or not np.isfinite(xyz).all():
        raise ValueError('At least three finite source points required')
    if not region.is_valid or region.area <= 0 or not np.isfinite(maximum_edge_m) or maximum_edge_m <= 0:
        raise ValueError('Valid region and positive edge bound required')
    if len(np.unique(xyz[:,:2],axis=0)) != len(xyz):
        raise ValueError('Ambiguous duplicate XY in candidate')
    faces = Delaunay(xyz[:,:2]).simplices.copy()
    points = xyz[faces,:2]
    lengths = np.linalg.norm(points-np.roll(points,1,axis=1),axis=2)
    keep = lengths.max(axis=1) <= maximum_edge_m
    keep &= np.array([region.covers(Polygon(p)) for p in points])
    faces = faces[keep]
    if not len(faces):
        raise ValueError('No supported local cap faces')
    p,q,r = xyz[faces[:,0],:2],xyz[faces[:,1],:2],xyz[faces[:,2],:2]
    area2 = (q[:,0]-p[:,0])*(r[:,1]-p[:,1])-(q[:,1]-p[:,1])*(r[:,0]-p[:,0])
    if np.any(area2 == 0):
        raise ValueError('Degenerate source triangle')
    # Upward normals in east/north/up coordinates, independent of Qhull order.
    flip = area2 < 0
    faces[flip] = faces[flip][:,[0,2,1]]
    return faces


def refine_source_coverage(pool_xyz, seed_indices, polygon, maximum_edge_m=1.):
    """Insert discarded ORIGINAL points into overlong supported triangles.

    Sampling bins must not create holes where captured data exists. No
    synthetic points, no edge-bound relaxation, no filling true source gaps.
    """
    pool_xyz = np.asarray(pool_xyz,float)
    chosen = np.unique(np.asarray(seed_indices,dtype=np.int64))
    if pool_xyz.ndim != 2 or pool_xyz.shape[1] != 3 or not np.isfinite(pool_xyz).all():
        raise ValueError('Finite original source pool required')
    if len(chosen)<3 or chosen.min()<0 or chosen.max()>=len(pool_xyz):
        raise ValueError('Valid original seed indices required')
    if len(np.unique(pool_xyz[:,:2],axis=0)) != len(pool_xyz):
        raise ValueError('Source pool must resolve duplicate XY explicitly')
    region = Polygon(polygon)
    if not region.is_valid or region.area <= 0 or not np.isfinite(maximum_edge_m) or maximum_edge_m <= 0:
        raise ValueError('Valid region and edge bound required')
    for _ in range(len(pool_xyz)):
        faces=Delaunay(pool_xyz[chosen,:2]).simplices
        p=pool_xyz[chosen[faces],:2]
        long=np.linalg.norm(p-np.roll(p,1,axis=1),axis=2).max(axis=1)>maximum_edge_m
        remaining=np.setdiff1d(np.arange(len(pool_xyz)),chosen)
        additions=[]
        for triangle in p[long]:
            if not region.covers(Polygon(triangle)):continue
            a,b,c=triangle;u=b-a;v=c-a;det=u[0]*v[1]-u[1]*v[0]
            d=pool_xyz[remaining,:2]-a
            beta=(d[:,0]*v[1]-d[:,1]*v[0])/det
            gamma=(u[0]*d[:,1]-u[1]*d[:,0])/det
            ids=remaining[(beta>=0)&(gamma>=0)&(beta+gamma<=1)]
            if not len(ids):continue
            distance=np.sum((pool_xyz[ids,:2]-triangle.mean(axis=0))**2,axis=1)
            additions.append(ids[np.lexsort((ids,pool_xyz[ids,2],distance))[0]])
        if not additions:return chosen
        chosen=np.union1d(chosen,additions)
    raise ValueError('Original-point refinement did not terminate')


def sample_cap(xyz, triangles, points):
    """Exact triangle heights; unsupported XY stays NaN, never zero/clamped."""
    xyz, points = np.asarray(xyz, float), np.asarray(points, float)
    triangles = np.asarray(triangles)
    if xyz.ndim != 2 or xyz.shape[1] != 3 or points.ndim != 2 or points.shape[1] != 2:
        raise ValueError('XYZ vertices and XY queries required')
    if not np.isfinite(xyz).all() or not np.isfinite(points).all():
        raise ValueError('Finite coordinates required')
    if triangles.ndim != 2 or triangles.shape[1] != 3 or not np.issubdtype(triangles.dtype,np.integer):
        raise ValueError('Integer triangles required')
    if triangles.size and (triangles.min() < 0 or triangles.max() >= len(xyz)):
        raise ValueError('Triangle outside source vertices')
    result = np.full(len(points), np.nan)
    for ids in triangles:
        a,b,c = xyz[ids]
        u,v = b[:2]-a[:2],c[:2]-a[:2]
        det = u[0]*v[1]-u[1]*v[0]
        if det <= 0:
            raise ValueError('Degenerate or reversed cap face')
        delta = points-a[:2]
        beta = (delta[:,0]*v[1]-delta[:,1]*v[0])/det
        gamma = (u[0]*delta[:,1]-u[1]*delta[:,0])/det
        inside = (beta >= -1e-10)&(gamma >= -1e-10)&(beta+gamma <= 1+1e-10)
        height = a[2]+beta[inside]*(b[2]-a[2])+gamma[inside]*(c[2]-a[2])
        # Shared edges agree; max is the terrain-solid union if caps overlap.
        result[inside] = np.fmax(result[inside],height)
    return result


def close_cap_below_retained_terrain(xyz, faces, floor_m):
    """Closed candidate rock solid; measured roof XYZ remains exact.

    Vertical perimeter faces are an INFERRED flank hypothesis. The bottom
    belongs inside the retained terrain and never defines exposed bathymetry.
    The physical union must use both solids, not replace the DEM by this cap.
    """
    xyz,faces=np.asarray(xyz,float),np.asarray(faces)
    if xyz.ndim!=2 or xyz.shape[1]!=3 or not np.isfinite(xyz).all() or not np.isfinite(floor_m):
        raise ValueError('Finite cap geometry and internal closure elevation required')
    if faces.ndim!=2 or faces.shape[1]!=3 or not np.issubdtype(faces.dtype,np.integer):
        raise ValueError('Integer cap faces required')
    if not len(faces) or faces.min()<0 or faces.max()>=len(xyz) or floor_m>=xyz[:,2].min():
        raise ValueError('Closure must be below every cap vertex')
    normal=np.cross(xyz[faces[:,1]]-xyz[faces[:,0]],xyz[faces[:,2]]-xyz[faces[:,0]])
    if np.any(normal[:,2]<=0):raise ValueError('Cap roof must have upward winding')
    directed=np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]])
    _,first,count=np.unique(np.sort(directed,axis=1),axis=0,return_index=True,return_counts=True)
    if np.any(count>2):raise ValueError('Nonmanifold cap')
    boundary=directed[first[count==1]]
    bottom=xyz.copy();bottom[:,2]=floor_m;n=len(xyz)
    a,b=boundary[:,0],boundary[:,1]
    walls=np.concatenate([np.column_stack([a,a+n,b+n]),np.column_stack([a,b+n,b])])
    closed=np.concatenate([faces,faces[:,[0,2,1]]+n,walls])
    vertices=np.concatenate([xyz,bottom])
    edges=np.concatenate([closed[:,[0,1]],closed[:,[1,2]],closed[:,[2,0]]])
    unique,counts=np.unique(np.sort(edges,axis=1),axis=0,return_counts=True)
    if np.any(counts!=2):raise ValueError('Candidate solid has open or nonmanifold edges')
    # Every undirected edge appears once in each direction.
    if not np.array_equal(np.unique(edges,axis=0),np.unique(edges[:,::-1],axis=0)):
        raise ValueError('Inconsistent solid winding')
    relative=vertices-np.array([xyz[0,0],xyz[0,1],floor_m])
    signed=float(np.einsum('ij,ij->i',relative[closed[:,0]],
        np.cross(relative[closed[:,1]],relative[closed[:,2]])).sum()/6)
    exact=float(np.sum(normal[:,2]/2*(xyz[faces,2].mean(axis=1)-floor_m)))
    if signed<=0 or not np.isclose(signed,exact,rtol=1e-12,atol=1e-10):
        raise ValueError('Closed solid does not preserve the cap volume')
    # 0 roof between original returns, 1 internal bottom, 2 inferred flanks.
    kinds=np.r_[np.zeros(len(faces),np.uint8),np.ones(len(faces),np.uint8),np.full(len(walls),2,np.uint8)]
    return vertices,closed,kinds,dict(volume_m3=signed,maximum_volume_error_m3=abs(signed-exact),
        manifold_edge_count=len(unique),inferred_vertical_wall_triangles=len(walls))


def sample_terrain_union(parent_sampler, cap_xyz, cap_triangles, points):
    """Same vertical terrain-solid union for hydraulic/ground-height queries."""
    points=np.asarray(points,float)
    roof=sample_cap(cap_xyz,cap_triangles,points)
    base=parent_sampler.sample(points[:,0],points[:,1])
    if not np.isfinite(base).all():raise ValueError('Retained terrain support is missing')
    return np.fmax(base,roof)


def native_collision_probes(vertices,faces,solid_vertices,solid_faces,face_kind,source_sha):
    """Exact source positions in the same reflected frame as the physical actor."""
    probes=[]
    for kind,points in [('original_roof_vertex',vertices),('roof_triangle_centroid',vertices[faces].mean(axis=1))]:
        for point in points:
            probes.append(dict(kind=kind,world_position_cm=(point*[100,-100,100]).tolist(),
                outward_normal=[0.,0.,1.],ray_half_length_cm=100.))
    # Keep the original vertical probes, including tangent boundary rays.
    # Also approach EVERY original vertex through its solid's interior cone:
    # float32 rounding can put an extremal source XY just outside the imported
    # footprint, making a vertical edge ray miss despite sub-millimetre XYZ.
    # No point is shifted, no vertex omitted and no hit tolerance enlarged.
    for index,point in enumerate(vertices):
        incident=faces[np.any(faces==index,axis=1)]
        if not len(incident):raise ValueError('Unsupported original roof vertex')
        triangle=vertices[incident[0]]
        interior=triangle.mean(axis=0)
        interior[2]=min(interior[2],point[2])-1.
        normal=point-interior;normal/=np.linalg.norm(normal)
        probes.append(dict(kind='original_vertex_interior_cone',
            world_position_cm=(point*[100,-100,100]).tolist(),
            outward_normal=(normal*[1,-1,1]).tolist(),ray_half_length_cm=100.))
    walls=solid_faces[np.asarray(face_kind)==2]
    for triangle in solid_vertices[walls]:
        normal=np.cross(triangle[1]-triangle[0],triangle[2]-triangle[0]);normal/=np.linalg.norm(normal)
        probes.append(dict(kind='inferred_wall_centroid',world_position_cm=(triangle.mean(axis=0)*[100,-100,100]).tolist(),
            outward_normal=(normal*[1,-1,1]).tolist(),ray_half_length_cm=1.))
    return dict(source_cap_sha256=source_sha,probes=probes)


def run(output):
    from south_fork_registered_mesh import RegisteredMeshSampler
    output = Path(output).resolve()
    if not output.is_relative_to(ROOT/'tmp') or output.exists():
        raise ValueError('A fresh project tmp directory is required for this unpromoted cap')
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    if sha(PARENT) != PARENT_SHA or sha(RETURNS) != RETURNS_SHA:
        raise ValueError('Original source identity changed')
    with np.load(PARENT,allow_pickle=False) as mesh:
        sampler = RegisteredMeshSampler(mesh)
        internal_floor=float(mesh['z_m'].min())-1.
    with np.load(RETURNS,allow_pickle=False) as data:
        xyz = np.column_stack([data[k] for k in ('utm_easting_m','utm_northing_m','navd88_m')])-ORIGIN
        classification = data['classification']
        residual = data['height_above_flattened_surface_m']
        # The archive has unsupported DEM samples elsewhere. Filter those
        # explicitly before the strict constructor, retaining original IDs.
        valid = np.isfinite(xyz).all(axis=1)&np.isfinite(residual)
        source_ids = np.flatnonzero(valid)
        selected, support = select_lower_returns(xyz[valid],classification[valid],residual[valid],REGION,
            corroborate_single_returns=True)
        selected = source_ids[selected]
        seed_count=len(selected)
        bins=np.zeros((len(xyz),2),np.int64)
        bins[valid]=np.floor(xyz[valid,:2]/0.5).astype(np.int64)
        support_by_bin={tuple(bins[i]):int(count) for i,count in zip(selected,support)}
        from shapely import intersects_xy
        eligible=valid&np.isin(classification,[1,2,20])&(residual>.3)&intersects_xy(Polygon(REGION),xyz[:,0],xyz[:,1])
        pool=np.array([i for i in np.flatnonzero(eligible) if tuple(bins[i]) in support_by_bin],dtype=np.int64)
        # Duplicate horizontal observations remain in the original archive;
        # this height-field interpretation explicitly selects their lowest Z.
        order=np.lexsort((pool,xyz[pool,2],xyz[pool,1],xyz[pool,0]))
        pool=pool[order]
        first=np.r_[True,np.any(xyz[pool[1:],:2]!=xyz[pool[:-1],:2],axis=1)]
        pool=np.sort(pool[first])
        seed_lookup={int(i):j for j,i in enumerate(pool)}
        if any(int(i) not in seed_lookup for i in selected):
            raise ValueError('Duplicate-XY rule conflicts with a retained original seed')
        refined=refine_source_coverage(xyz[pool],[seed_lookup[int(i)] for i in selected],REGION)
        selected=pool[refined]
        support=np.array([support_by_bin[tuple(bins[i])] for i in selected],dtype=np.int64)
        refined_count=len(selected)-seed_count
        vertices = xyz[selected]
        faces = cap_triangles(vertices,REGION)
        used = np.unique(faces)
        mapping = np.full(len(vertices),-1,dtype=np.int64);mapping[used] = np.arange(len(used))
        faces = mapping[faces];vertices=vertices[used];selected=selected[used];support=support[used]
        original_xyz = np.column_stack([data[k][selected] for k in ('utm_easting_m','utm_northing_m','navd88_m')])
        if not np.array_equal(vertices+ORIGIN,original_xyz):
            raise ValueError('Original captured XYZ was not retained exactly')
        parent_heights = sampler.sample(vertices[:,0],vertices[:,1])
        centroid = vertices[faces].mean(axis=1)
        sampled = sample_cap(vertices,faces,centroid[:,:2])
        if not np.allclose(sampled,centroid[:,2],rtol=0,atol=1e-8):
            raise ValueError('Cap triangles do not reproduce their source geometry')
        edges=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1)
        unique,counts=np.unique(edges,axis=0,return_counts=True)
        if np.any(counts > 2):raise ValueError('Nonmanifold candidate edges')
        boundary = unique[counts == 1]
        areas = np.cross(vertices[faces[:,1]]-vertices[faces[:,0]],vertices[faces[:,2]]-vertices[faces[:,0]])[:,2]/2
        boundary_xyz = vertices[np.unique(boundary)]
        boundary_gap = boundary_xyz[:,2]-sampler.sample(boundary_xyz[:,0],boundary_xyz[:,1])
        solid_vertices,solid_faces,face_kind,solid_report=close_cap_below_retained_terrain(vertices,faces,internal_floor)
        nearby=np.all((xyz[:,:2]>=vertices[:,:2].min(axis=0))&(xyz[:,:2]<=vertices[:,:2].max(axis=0)),axis=1)
        observations={}
        for name,classes in [('classified_ground',[2,20]),('unclassified',[1])]:
            ix=np.flatnonzero(nearby&np.isin(classification,classes))
            heights=sample_cap(vertices,faces,xyz[ix,:2]);inside=np.isfinite(heights)
            differences=heights[inside]-xyz[ix[inside],2]
            observations[name]=dict(original_return_count_inside_cap=int(inside.sum()),
                cap_minus_original_height_min_median_max_m=np.percentile(differences,[0,50,100]).tolist() if len(differences) else None,
                absence_of_classified_ground_is_not_verification=True)
        output.mkdir()
        cap_path = output/'original_return_rock_cap.npz'
        np.savez_compressed(cap_path,vertices_m=vertices,triangles=faces,
            original_return_index=selected,original_classification=classification[selected],
            bin_support_count=support,original_height_above_dem_m=residual[selected],
            retained_parent_height_m=parent_heights,boundary_edges=boundary,
            solid_vertices_m=solid_vertices,solid_triangles=solid_faces,solid_face_kind=face_kind)
        report=dict(schema='raftsim.original_return_rock_cap.v1',
            status='unpromoted_source_roof_with_inferred_vertical_flanks_shared_runtime_validation_required',
            source_mesh_path=PARENT.relative_to(ROOT).as_posix(),source_mesh_sha256=PARENT_SHA,
            original_returns_path=RETURNS.relative_to(ROOT).as_posix(),original_returns_sha256=RETURNS_SHA,
            original_sources_unchanged=sha(PARENT)==PARENT_SHA and sha(RETURNS)==RETURNS_SHA,
            source_naip_sha256=sha(BASE/'sources/troublemaker_naip.png'),
            source_naip_export_sha256=sha(BASE/'sources/troublemaker_naip_export.json'),
            cap_path=cap_path.relative_to(ROOT).as_posix(),cap_sha256=sha(cap_path),
            origin_utm_and_vertical_datum_m=ORIGIN.tolist(),
            interpreted_search_polygon_m=REGION,registration_uncertainty_m=3.,
            selection=dict(bin_size_prior_m=.5,minimum_original_returns_per_bin=2,
                singleton_exception='At least two ORIGINAL multi-return neighbouring bins; selected height within their range plus/minus 1 m; non-recursive.',
                coverage_refinement='Insert additional original returns from supported bins inside overlong faces; never enlarge the edge bound or synthesize points.',
                minimum_height_above_dem_m=.3,maximum_triangle_edge_prior_m=1.,water_mask_required=False),
            original_seed_count=seed_count,original_pool_count=len(pool),additional_original_points_for_coverage=refined_count,
            vertex_count=len(vertices),triangle_count=len(faces),projected_area_m2=float(areas.sum()),
            boundary_edge_count=len(boundary),boundary_height_gap_range_m=[float(boundary_gap.min()),float(boundary_gap.max())],
            selected_classification_counts={str(int(c)):int(np.sum(classification[selected]==c)) for c in np.unique(classification[selected])},
            selected_returns_outside_old_water_mask=int(np.sum(~data['within_survey_water'][selected])),
            corroborated_single_return_vertices=int(np.sum(support==1)),
            vertex_height_above_retained_parent_range_m=[float((vertices[:,2]-parent_heights).min()),float((vertices[:,2]-parent_heights).max())],
            maximum_triangle_centroid_error_m=float(np.max(abs(sampled-centroid[:,2]))),
            original_observation_comparison=observations,
            inferred_solid=dict(internal_floor_m=internal_floor,
                floor_rule='One metre below the minimum of the ENTIRE retained parent mesh; interior closure only, not bathymetry.',
                boundary_rule='Vertical connection at the source-supported cap perimeter; explicitly inferred, not a measured rock outline.',
                vertex_count=len(solid_vertices),triangle_count=len(solid_faces),**solid_report),
            source_xyz_retained_exactly=True,rock_classification='Interpreted from imagery and local return continuity; class 1 remains unclassified, NOT certified ground.',
            faces_measured=False,boundary_reconstructed=True,closed_solid_geometry_verified=True,engine_collision_verified=False,
            hydraulic_recooked=False,game_integrated=False,production_promoted=False,
            limitations='No bathymetry, camera calibration or measured rock outline. Vertical flanks are a candidate hypothesis, not measured sides. Use the union with the retained parent for render/collision/hydraulics; never install a visual-only prop or silently replace the DEM.')
        (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
        (output/'native-probes.json').write_text(json.dumps(native_collision_probes(vertices,faces,
            solid_vertices,solid_faces,face_kind,report['cap_sha256']),indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    print(json.dumps(run(parser.parse_args().output),indent=2))
