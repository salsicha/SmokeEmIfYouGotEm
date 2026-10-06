#pragma once
#include "CoreMinimal.h"
#include "RaftSimLiquidWindowProfile.h"

// Shared by particle contact and pressure classification. Terrain is a Niagara
// float3 array containing two metadata vectors followed by six vertices/quad.
// Outputs are distance (SIGNED VERTICAL clearance, not Euclidean SDF), closest,
// upward normal, zero wallVelocity, valid and encoded. Only this static,
// registered heightfield is supported; there is no claim of overhang support.
inline FString RaftSimRegisteredTerrainQueryHlsl(const TCHAR* Position,bool CanonicalWorld=false)
{
    // Regional source pages use parent ENU directly. Their world frame is an
    // explicit Y reflection, never the legacy window's mutable translation.
    const FString SourcePosition=CanonicalWorld ?
        FString::Printf(TEXT("float3((%s).x,-(%s).y,(%s).z)"),Position,Position,Position) :
        RaftSimLiquidWindowProfile::SourcePositionHlsl(Position);
    FString Code=FString::Printf(TEXT("{ float3 queryP=%s;\n"),*SourcePosition)+TEXT(
        "distance=1000000; closest=queryP; normal=float3(0,0,1); wallVelocity=0; valid=false; encoded=1000000;\n"
        "float3 meta, dims; Terrain.Get(0,meta); Terrain.Get(1,dims);\n"
        "int cols=(int)abs(dims.y), rows=(int)abs(dims.z);\n"
        "float3 pageOffset=0; if(dims.z<0) Terrain.Get(2,pageOffset);\n"
        "int header=dims.z<0?3:2;\n"
        "int c0=(int)floor((queryP.x-meta.x)/meta.z)-(int)pageOffset.x, r0=(int)floor((meta.y-queryP.y)/dims.x)-(int)pageOffset.y;\n"
        "for(int ri=0;ri<3 && !valid;++ri) { int r=r0+(ri==0?0:ri==1?-1:1);\n"
        " for(int ci=0;ci<3 && !valid;++ci) { int c=c0+(ci==0?0:ci==1?-1:1);\n"
        "  if(r<0 || r>=rows || c<0 || c>=cols) continue;\n"
        "  for(int side=0;side<2 && !valid;++side) {\n"
        "   int base=header+((r*cols+c)*2+side)*3; float3 a,b,d;\n"
        "   Terrain.Get(base,a); Terrain.Get(base+1,b); Terrain.Get(base+2,d);\n"
        "   float2 queryXY=queryP.xy;\n"
        "   if(dims.y<0) queryXY-=float2(meta.x+(c+(int)pageOffset.x)*meta.z,meta.y-(r+(int)pageOffset.y)*dims.x);\n"
        "   float3 ab=b-a, ad=d-a; float2 ap=queryXY-a.xy;\n"
        "   float det=ab.x*ad.y-ab.y*ad.x; if(abs(det)<0.000001) continue;\n"
        "   float u=(ap.x*ad.y-ap.y*ad.x)/det, v=(ab.x*ap.y-ab.y*ap.x)/det;\n"
        "   if(u>=-0.00001 && v>=-0.00001 && u+v<=1.00001) {\n"
        "    float bed=a.z+u*ab.z+v*ad.z; closest=float3(queryP.xy,bed); distance=queryP.z-bed;\n"
        "    normal=normalize(cross(ab,ad)); if(normal.z<0) normal=-normal; valid=true;\n"
        "   }\n"
        "  }\n"
        " }\n"
        "}\n"
        "}\n");
    if (CanonicalWorld)
        Code+=TEXT("closest.y=-closest.y; normal.y=-normal.y;\n");
    else if (RaftSimLiquidWindowProfile::Geographic())
        Code+=TEXT("closest=")+RaftSimLiquidWindowProfile::PresentPositionHlsl(TEXT("closest"))+TEXT("; normal.y=-normal.y;\n");
    return Code;
}
