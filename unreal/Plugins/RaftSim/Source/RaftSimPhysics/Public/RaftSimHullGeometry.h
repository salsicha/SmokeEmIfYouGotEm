#pragma once
#include "CoreMinimal.h"

// Exact indexed surface, in rigid-body-local metres. No convexification,
// welding, sphere fitting or omitted material sections. Authored geometry is
// not a measured hull, and a surface snapshot is not itself a contact solver.
struct FRaftSimHullSection
{
    int32 VertexStart=0,VertexCount=0,FaceStart=0,FaceCount=0;
};

struct FRaftSimHullGeometry
{
    TArray<FVector> VerticesM;
    TArray<FIntVector> Faces;
    TArray<FRaftSimHullSection> Sections;

    bool IsValid() const
    {
        if(VerticesM.IsEmpty() || Faces.IsEmpty() || Sections.IsEmpty())return false;
        for(const auto& V:VerticesM)if(V.ContainsNaN())return false;
        for(const auto& F:Faces)
            if(!VerticesM.IsValidIndex(F.X) || !VerticesM.IsValidIndex(F.Y) || !VerticesM.IsValidIndex(F.Z))return false;
        int64 Vertices=0,Triangles=0;
        for(const auto& S:Sections)
        {
            if(S.VertexStart!=Vertices || S.FaceStart!=Triangles || S.VertexCount<=0 || S.FaceCount<=0)return false;
            Vertices+=S.VertexCount;Triangles+=S.FaceCount;
        }
        return Vertices==VerticesM.Num() && Triangles==Faces.Num();
    }
};
