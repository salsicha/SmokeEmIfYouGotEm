#pragma once
#include "RaftSimRaftMesh.h"
#include "RaftSimImmutableRestMesh.h"

// Exact-input memoization only. Every original vertex/face remains in the
// returned snapshot; source edits, condition and D4 changes invalidate it.
namespace RaftSimHullPrepareCache
{
using FRestOwner=TSharedPtr<const RaftSimRaftMesh::FImmutableProductionRestMesh>;
// Independently owned destinations; counts and EVERY byte are checked before
// eliding a deep assignment. No shape key, pointer, revision or tolerance is
// a substitute. This does not change input-cache or validity semantics.
struct FCopyCounts {int32 Assigned=0,Retained=0;};
template<class Element>
inline bool SameBytes(const TArray<Element>& A,const TArray<Element>& B)
{
    return A.Num()==B.Num() && (A.IsEmpty() ||
        FMemory::Memcmp(A.GetData(),B.GetData(),SIZE_T(A.Num())*sizeof(Element))==0);
}
template<class Element>
inline void CopyArrayIfChanged(const TArray<Element>& Source,TArray<Element>& Destination,FCopyCounts& Counts)
{
    if(SameBytes(Source,Destination)){++Counts.Retained;return;}
    Destination=Source;++Counts.Assigned;
}
inline void CopyPreparedIfChanged(const TArray<RaftSimRaftMesh::FMeshData>& Source,
    TArray<RaftSimRaftMesh::FMeshData>& Destination,FCopyCounts& Counts)
{
    if(Destination.Num()!=Source.Num())Destination.SetNum(Source.Num());
    for(int32 I=0;I<Source.Num();++I)
    {
        const auto& A=Source[I];auto& B=Destination[I];
        CopyArrayIfChanged(A.Vertices,B.Vertices,Counts);
        CopyArrayIfChanged(A.Triangles,B.Triangles,Counts);
        CopyArrayIfChanged(A.Normals,B.Normals,Counts);
        CopyArrayIfChanged(A.UVs,B.UVs,Counts);
        CopyArrayIfChanged(A.Tangents,B.Tangents,Counts);
    }
}
inline void CopyHullIfChanged(const FRaftSimHullGeometry& Source,
    FRaftSimHullGeometry& Destination,FCopyCounts& Counts)
{
    CopyArrayIfChanged(Source.VerticesM,Destination.VerticesM,Counts);
    CopyArrayIfChanged(Source.Faces,Destination.Faces,Counts);
    CopyArrayIfChanged(Source.Sections,Destination.Sections,Counts);
}
struct FCache
{
    bool bValid=false;float Radius=0.;FTransform Transform;
    RaftSimRaftMesh::FRaftSimRaftVisualCondition Condition;
    TArray<FRaftSimFlexVisualSegmentState> Segments;
    TArray<RaftSimRaftMesh::FMeshData> Prepared;
    FRaftSimHullGeometry Hull;
private:
    // Only Remember can replace the stored key or its finite-value proof.
    // Byte identity with a finite key implies the original exact equality;
    // byte differences still take the original comparisons (including +/-0).
    TArray<RaftSimRaftMesh::FMeshData> Rest;
    FRestOwner RestOwner;
    bool bFiniteRest=false;
    template<class Element>
    bool SameArray(const TArray<Element>& A,const TArray<Element>& B) const
    {
        if(A.Num()!=B.Num())return false;
        if(bFiniteRest && (A.IsEmpty() ||
            FMemory::Memcmp(A.GetData(),B.GetData(),SIZE_T(A.Num())*sizeof(Element))==0))return true;
        return A==B;
    }
    bool InputsMatch(float R,
        const TArray<FRaftSimFlexVisualSegmentState>& Input,
        const RaftSimRaftMesh::FRaftSimRaftVisualCondition& C,const FTransform& T) const
    {
        if(!bValid || R!=Radius || C.PressureFraction!=Condition.PressureFraction ||
            C.Integrity!=Condition.Integrity || C.CreaseAmplitudeM!=Condition.CreaseAmplitudeM ||
            T.GetTranslation()!=Transform.GetTranslation() || T.GetRotation()!=Transform.GetRotation() ||
            T.GetScale3D()!=Transform.GetScale3D() || Input.Num()!=Segments.Num())return false;
        for(int32 I=0;I<Input.Num();++I)
        {
            const auto& A=Input[I];const auto& B=Segments[I];
            if(A.SegmentId!=B.SegmentId || A.LocalPositionM!=B.LocalPositionM || A.ContactNormalLocal!=B.ContactNormalLocal ||
                A.CompressionM!=B.CompressionM || A.FreeboardLossM!=B.FreeboardLossM || A.IndentationM!=B.IndentationM ||
                A.bWrapping!=B.bWrapping || A.bPinned!=B.bPinned || A.bRecovering!=B.bRecovering)return false;
        }
        return true;
    }
public:
    bool HasSealedRestKey(const FRestOwner& Source) const
    {
        // A mutable-array address or revision is never accepted here. Only
        // the privately owned const import with the original finite proof.
        return bValid && bFiniteRest && Source.IsValid() && Source==RestOwner;
    }
    bool Matches(const FRestOwner& Source,float R,
        const TArray<FRaftSimFlexVisualSegmentState>& Input,
        const RaftSimRaftMesh::FRaftSimRaftVisualCondition& C,const FTransform& T,
        bool bReferenceRestKey=false) const
    {
        if(!Source)return false;
        if(!bReferenceRestKey && HasSealedRestKey(Source))return InputsMatch(R,Input,C,T);
        return Matches(Source->GetSections(),R,Input,C,T);
    }
    bool Matches(const TArray<RaftSimRaftMesh::FMeshData>& Source,float R,
        const TArray<FRaftSimFlexVisualSegmentState>& Input,
        const RaftSimRaftMesh::FRaftSimRaftVisualCondition& C,const FTransform& T) const
    {
        if(!InputsMatch(R,Input,C,T) || Source.Num()!=Rest.Num())return false;
        for(int32 I=0;I<Source.Num();++I)
        {
            const auto& A=Source[I];const auto& B=Rest[I];
            if(!SameArray(A.Vertices,B.Vertices) || A.Triangles!=B.Triangles ||
                !SameArray(A.Normals,B.Normals) || !SameArray(A.UVs,B.UVs) || A.Tangents.Num()!=B.Tangents.Num())return false;
            if(bFiniteRest && (A.Tangents.IsEmpty() || FMemory::Memcmp(A.Tangents.GetData(),B.Tangents.GetData(),
                SIZE_T(A.Tangents.Num())*sizeof(FProcMeshTangent))==0))continue;
            for(int32 J=0;J<A.Tangents.Num();++J)
                if(A.Tangents[J].TangentX!=B.Tangents[J].TangentX || A.Tangents[J].bFlipTangentY!=B.Tangents[J].bFlipTangentY)return false;
        }
        return true;
    }
    void Remember(const TArray<RaftSimRaftMesh::FMeshData>& Source,float R,
        const TArray<FRaftSimFlexVisualSegmentState>& Input,
        const RaftSimRaftMesh::FRaftSimRaftVisualCondition& C,const FTransform& T,
        const TArray<RaftSimRaftMesh::FMeshData>& Output,const FRaftSimHullGeometry& H)
    {
        RestOwner.Reset();
        Rest=Source;Radius=R;Segments=Input;Condition=C;Transform=T;Prepared=Output;Hull=H;bValid=H.IsValid();
        bFiniteRest=true;
        for(const auto& Section:Rest)
        {
            for(const auto& V:Section.Vertices)bFiniteRest &= !V.ContainsNaN();
            for(const auto& N:Section.Normals)bFiniteRest &= !N.ContainsNaN();
            for(const auto& UV:Section.UVs)bFiniteRest &= !UV.ContainsNaN();
            for(const auto& Tangent:Section.Tangents)bFiniteRest &= !Tangent.TangentX.ContainsNaN();
        }
    }
    void Remember(const FRestOwner& Source,float R,
        const TArray<FRaftSimFlexVisualSegmentState>& Input,
        const RaftSimRaftMesh::FRaftSimRaftVisualCondition& C,const FTransform& T,
        const TArray<RaftSimRaftMesh::FMeshData>& Output,const FRaftSimHullGeometry& H)
    {
        if(!Source){bValid=false;RestOwner.Reset();return;}
        if(Source==RestOwner)
        {
            // Rest already holds this immutable owner's sections and their
            // finiteness proof; only the per-pose key and outputs change.
            Radius=R;Segments=Input;Condition=C;Transform=T;Prepared=Output;Hull=H;bValid=H.IsValid();
            return;
        }
        Remember(Source->GetSections(),R,Input,C,T,Output,H);
        RestOwner=Source;
    }
};
}
