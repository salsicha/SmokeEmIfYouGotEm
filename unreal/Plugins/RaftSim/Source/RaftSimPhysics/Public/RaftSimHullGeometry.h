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
        // A private, per-thread certificate for EXACT previously validated
        // data, never an asset pointer, hash, topology-only or rest-pose key.
        // Every byte of every original vertex/face/section is compared. Any
        // changed input takes the complete original validation below; invalid
        // snapshots are never remembered. Two keys cover Before/After poses.
        class FValidatedKey
        {
            bool bKnownValid=false;
            TArray<FVector> Vertices;
            TArray<FIntVector> Triangles;
            TArray<FRaftSimHullSection> Ranges;
        public:
            bool Matches(const FRaftSimHullGeometry& G) const
            {
                return bKnownValid && Vertices.Num()==G.VerticesM.Num() &&
                    Triangles.Num()==G.Faces.Num() && Ranges.Num()==G.Sections.Num() &&
                    FMemory::Memcmp(Vertices.GetData(),G.VerticesM.GetData(),SIZE_T(Vertices.Num())*sizeof(FVector))==0 &&
                    FMemory::Memcmp(Triangles.GetData(),G.Faces.GetData(),SIZE_T(Triangles.Num())*sizeof(FIntVector))==0 &&
                    FMemory::Memcmp(Ranges.GetData(),G.Sections.GetData(),SIZE_T(Ranges.Num())*sizeof(FRaftSimHullSection))==0;
            }
            void Remember(const FRaftSimHullGeometry& G)
            {
                Vertices=G.VerticesM;Triangles=G.Faces;Ranges=G.Sections;bKnownValid=true;
            }
        };
        static thread_local FValidatedKey Keys[2];
        static thread_local uint8 NextKey=0;
        for(const auto& Key:Keys)if(Key.Matches(*this))return true;
        for(const auto& V:VerticesM)if(V.ContainsNaN())return false;
        for(const auto& F:Faces)
            if(!VerticesM.IsValidIndex(F.X) || !VerticesM.IsValidIndex(F.Y) || !VerticesM.IsValidIndex(F.Z))return false;
        int64 Vertices=0,Triangles=0;
        for(const auto& S:Sections)
        {
            if(S.VertexStart!=Vertices || S.FaceStart!=Triangles || S.VertexCount<=0 || S.FaceCount<=0)return false;
            Vertices+=S.VertexCount;Triangles+=S.FaceCount;
        }
        if(Vertices!=VerticesM.Num() || Triangles!=Faces.Num())return false;
        Keys[NextKey].Remember(*this);NextKey^=1;
        return true;
    }
};
