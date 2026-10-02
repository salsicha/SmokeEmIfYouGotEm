#pragma once
#include "RaftSimRaftMesh.h"

// Exact-input memoization only. Every original vertex/face remains in the
// returned snapshot; source edits, condition and D4 changes invalidate it.
namespace RaftSimHullPrepareCache
{
struct FCache
{
    bool bValid=false;float Radius=0.;FTransform Transform;
    RaftSimRaftMesh::FRaftSimRaftVisualCondition Condition;
    TArray<FRaftSimFlexVisualSegmentState> Segments;
    TArray<RaftSimRaftMesh::FMeshData> Rest,Prepared;
    FRaftSimHullGeometry Hull;
    bool Matches(const TArray<RaftSimRaftMesh::FMeshData>& Source,float R,
        const TArray<FRaftSimFlexVisualSegmentState>& Input,
        const RaftSimRaftMesh::FRaftSimRaftVisualCondition& C,const FTransform& T) const
    {
        if(!bValid || R!=Radius || C.PressureFraction!=Condition.PressureFraction ||
            C.Integrity!=Condition.Integrity || C.CreaseAmplitudeM!=Condition.CreaseAmplitudeM ||
            T.GetTranslation()!=Transform.GetTranslation() || T.GetRotation()!=Transform.GetRotation() ||
            T.GetScale3D()!=Transform.GetScale3D() || Input.Num()!=Segments.Num() || Source.Num()!=Rest.Num())return false;
        for(int32 I=0;I<Input.Num();++I)
        {
            const auto& A=Input[I];const auto& B=Segments[I];
            if(A.SegmentId!=B.SegmentId || A.LocalPositionM!=B.LocalPositionM || A.ContactNormalLocal!=B.ContactNormalLocal ||
                A.CompressionM!=B.CompressionM || A.FreeboardLossM!=B.FreeboardLossM || A.IndentationM!=B.IndentationM ||
                A.bWrapping!=B.bWrapping || A.bPinned!=B.bPinned || A.bRecovering!=B.bRecovering)return false;
        }
        for(int32 I=0;I<Source.Num();++I)
        {
            const auto& A=Source[I];const auto& B=Rest[I];
            if(A.Vertices!=B.Vertices || A.Triangles!=B.Triangles || A.Normals!=B.Normals || A.UVs!=B.UVs || A.Tangents.Num()!=B.Tangents.Num())return false;
            for(int32 J=0;J<A.Tangents.Num();++J)
                if(A.Tangents[J].TangentX!=B.Tangents[J].TangentX || A.Tangents[J].bFlipTangentY!=B.Tangents[J].bFlipTangentY)return false;
        }
        return true;
    }
    void Remember(const TArray<RaftSimRaftMesh::FMeshData>& Source,float R,
        const TArray<FRaftSimFlexVisualSegmentState>& Input,
        const RaftSimRaftMesh::FRaftSimRaftVisualCondition& C,const FTransform& T,
        const TArray<RaftSimRaftMesh::FMeshData>& Output,const FRaftSimHullGeometry& H)
    {Rest=Source;Radius=R;Segments=Input;Condition=C;Transform=T;Prepared=Output;Hull=H;bValid=H.IsValid();}
};
}
