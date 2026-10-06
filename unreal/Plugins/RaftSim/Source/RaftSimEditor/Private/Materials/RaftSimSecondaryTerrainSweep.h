#pragma once
#include "RaftSimLiquidWindowProfile.h"

// Read-only swept contact with the same packed heightfield triangles used by
// primary water. Secondary visual particles expire on impact; primary mass is
// untouched. Clip the full segment against each triangle's XY half-spaces,
// then solve its linear vertical clearance. No fixed temporal sampling gaps.
inline FString RaftSimSecondaryTerrainSweepHlsl()
{
    FString Code=TEXT(R"HLSL(
// RiverSecondaryExactTerrainSweep: continuous triangle contact, secondary only.
float3 origin=RiverUnitToWorld[3].xyz+0.5*(RiverUnitToWorld[0].xyz+RiverUnitToWorld[1].xyz);
float3 oldOffset=Position-origin,newOffset=OutPosition-origin;
float3 oldLocal=float3(dot(oldOffset,normalize(RiverUnitToWorld[0].xyz)),dot(oldOffset,normalize(RiverUnitToWorld[1].xyz)),dot(oldOffset,normalize(RiverUnitToWorld[2].xyz)));
float3 newLocal=float3(dot(newOffset,normalize(RiverUnitToWorld[0].xyz)),dot(newOffset,normalize(RiverUnitToWorld[1].xyz)),dot(newOffset,normalize(RiverUnitToWorld[2].xyz)));
if(any(abs(oldLocal.xy)>0.5*RiverPhysicalExtents.xy) || any(abs(newLocal.xy)>0.5*RiverPhysicalExtents.xy) ||
   oldLocal.z<0 || newLocal.z<0 || oldLocal.z>RiverPhysicalExtents.z || newLocal.z>RiverPhysicalExtents.z) OutAlive=false;
if(OutAlive)
{
    float3 meta,dims;Terrain.Get(0,meta);Terrain.Get(1,dims);
    int cols=(int)abs(dims.y),rows=(int)abs(dims.z);
    float3 pageOffset=0;if(dims.z<0) Terrain.Get(2,pageOffset);
    int header=dims.z<0?3:2;
    float2 xyMin=min(Position.xy,OutPosition.xy),xyMax=max(Position.xy,OutPosition.xy);
    int c0=max(0,(int)floor((xyMin.x-meta.x)/meta.z)-(int)pageOffset.x-1);
    int c1=min(cols-1,(int)floor((xyMax.x-meta.x)/meta.z)-(int)pageOffset.x+1);
    int r0=max(0,(int)floor((meta.y-xyMax.y)/dims.x)-(int)pageOffset.y-1);
    int r1=min(rows-1,(int)floor((meta.y-xyMin.y)/dims.x)-(int)pageOffset.y+1);
    bool coveredEnd=false,terrainHit=false;
    // A very large step is invalid for this bounded visual integrator; fail
    // closed instead of silently truncating a swept-contact search.
    if(c1<c0 || r1<r0 || (c1-c0+1)*(r1-r0+1)>256) OutAlive=false;
    else for(int r=r0;r<=r1 && !terrainHit;++r)
    for(int c=c0;c<=c1 && !terrainHit;++c)
    for(int side=0;side<2 && !terrainHit;++side)
    {
        int base=header+((r*cols+c)*2+side)*3;
        float3 a,b,d;Terrain.Get(base,a);Terrain.Get(base+1,b);Terrain.Get(base+2,d);
        float3 ab=b-a,ad=d-a;float det=ab.x*ad.y-ab.y*ad.x;
        if(abs(det)<0.000001) continue;
        float2 p=Position.xy-a.xy,q=OutPosition.xy-a.xy;
        if(dims.y<0)
        {
            // Subtract the nominal origin before the small vertex offset;
            // never reconstruct large absolute float32 rock vertices.
            float2 quadOrigin=float2(meta.x+(c+(int)pageOffset.x)*meta.z,meta.y-(r+(int)pageOffset.y)*dims.x);
            p=(Position.xy-quadOrigin)-a.xy;q=(OutPosition.xy-quadOrigin)-a.xy;
        }
        float2 uv0=float2(p.x*ad.y-p.y*ad.x,ab.x*p.y-ab.y*p.x)/det;
        float2 uv1=float2(q.x*ad.y-q.y*ad.x,ab.x*q.y-ab.y*q.x)/det;
        float3 b0=float3(uv0,1-uv0.x-uv0.y),b1=float3(uv1,1-uv1.x-uv1.y);
        coveredEnd=coveredEnd || all(b1>=-0.00001);
        float enter=0,leave=1;
        [unroll] for(int edge=0;edge<3;++edge)
        {
            float slope=b1[edge]-b0[edge];
            if(abs(slope)<0.0000001) { if(b0[edge]<-0.00001) leave=-1; }
            else if(slope>0) enter=max(enter,(-0.00001-b0[edge])/slope);
            else leave=min(leave,(-0.00001-b0[edge])/slope);
        }
        if(enter<=leave)
        {
            float clearance0=Position.z-(a.z+uv0.x*ab.z+uv0.y*ad.z);
            float clearance1=OutPosition.z-(a.z+uv1.x*ab.z+uv1.y*ad.z);
            // Clearance is linear within this exact triangle. Its minimum
            // over the clipped interval occurs at one of the two endpoints.
            float lo=lerp(clearance0,clearance1,enter),hi=lerp(clearance0,clearance1,leave);
            terrainHit=min(lo,hi)<=0.1;
        }
    }
    if(terrainHit || !coveredEnd) OutAlive=false;
}
)HLSL");
    if (RaftSimLiquidWindowProfile::Geographic())
    {
        // Only terrain-table lookup uses canonical source coordinates. Domain
        // clipping and particle integration retain the actual Niagara frame.
        const FString Declarations=TEXT("float3 contactStart=")+
            RaftSimLiquidWindowProfile::SourcePositionHlsl(TEXT("Position"))+TEXT("; float3 contactEnd=")+
            RaftSimLiquidWindowProfile::SourcePositionHlsl(TEXT("OutPosition"))+TEXT(";\n");
        Code.ReplaceInline(TEXT("float3 meta,dims;Terrain.Get"),*(Declarations+TEXT("float3 meta,dims;Terrain.Get")));
        Code.ReplaceInline(TEXT("min(Position.xy,OutPosition.xy),xyMax=max(Position.xy,OutPosition.xy)"),
            TEXT("min(contactStart.xy,contactEnd.xy),xyMax=max(contactStart.xy,contactEnd.xy)"));
        Code.ReplaceInline(TEXT("p=Position.xy-a.xy,q=OutPosition.xy-a.xy"),TEXT("p=contactStart.xy-a.xy,q=contactEnd.xy-a.xy"));
        Code.ReplaceInline(TEXT("(Position.xy-quadOrigin)"),TEXT("(contactStart.xy-quadOrigin)"));
        Code.ReplaceInline(TEXT("(OutPosition.xy-quadOrigin)"),TEXT("(contactEnd.xy-quadOrigin)"));
        Code.ReplaceInline(TEXT("clearance0=Position.z-"),TEXT("clearance0=contactStart.z-"));
        Code.ReplaceInline(TEXT("clearance1=OutPosition.z-"),TEXT("clearance1=contactEnd.z-"));
    }
    return Code;
}
