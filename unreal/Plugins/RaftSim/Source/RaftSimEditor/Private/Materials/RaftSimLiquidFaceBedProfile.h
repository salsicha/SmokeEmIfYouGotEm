#pragma once
#include "RaftSimLiquidRegionalState.h"
#include "RaftSimLiquidParticleExitGPU.h"
#include "Misc/FileHelper.h"
#include <cfloat>
THIRD_PARTY_INCLUDES_START
#include <openssl/sha.h>
THIRD_PARTY_INCLUDES_END

namespace RaftSimLiquidFaceBedProfile
{
inline bool Decode(const TSharedPtr<FJsonObject>& Json,const RaftSimLiquidRegionalState::FParent& Parent,
    const FString& MeshPath,const FString& BoundaryPath,const FString& ContactMeshHash,
    FRaftSimLiquidFaceBed& Out,FString& Error)
{
    Out={};Error=TEXT("Exact outlet bed must match current contact mesh, exterior source and physical frame");
    FString Schema,MeshHash,BoundaryHash;
    if(!Json || !Json->TryGetStringField(TEXT("schema"),Schema) || Schema!=TEXT("raftsim.physical_face_bed.v1") ||
        !Json->TryGetStringField(TEXT("source_mesh_sha256"),MeshHash) || MeshHash!=ContactMeshHash ||
        !Json->TryGetStringField(TEXT("source_boundary_sha256"),BoundaryHash)) return false;
    auto HashMatches=[](const FString& Path,const FString& Expected)
    {
        TArray<uint8> Bytes;uint8 Hash[SHA256_DIGEST_LENGTH];
        return Expected.Len()==64 && FFileHelper::LoadFileToArray(Bytes,*Path) &&
            SHA256(Bytes.GetData(),Bytes.Num(),Hash) && BytesToHex(Hash,SHA256_DIGEST_LENGTH).Equals(Expected,ESearchCase::IgnoreCase);
    };
    if(!HashMatches(MeshPath,MeshHash) || !HashMatches(BoundaryPath,BoundaryHash)) return false;
    auto Matches=[](const TArray<TSharedPtr<FJsonValue>>& A,TConstArrayView<double> Values,bool ComputedExtent=false)
    {
        if(A.Num()!=Values.Num()) return false;
        for(int32 I=0;I<A.Num();++I)
        {
            double V;
            // Extents are also computed as (metres/cell * 100) * cell count.
            // That order rounds the 800 cm vertical extent to 799.9999999999999.
            // Allow only double arithmetic roundoff, not a spatial tolerance.
            const double Roundoff=ComputedExtent?8*DBL_EPSILON*FMath::Max(1.,FMath::Abs(Values[I])):0.;
            if(!A[I]->TryGetNumber(V) || !FMath::IsFinite(V) || FMath::Abs(V-Values[I])>Roundoff) return false;
        }
        return true;
    };
    const TArray<TSharedPtr<FJsonValue>> *Axes,*Lower,*Extent,*Cells,*Faces;
    if(!Json->TryGetArrayField(TEXT("canonical_axes"),Axes) || Axes->Num()!=2 ||
        !Json->TryGetArrayField(TEXT("lower_station_lateral_m"),Lower) ||
        !Json->TryGetArrayField(TEXT("extent_cm"),Extent) || !Json->TryGetArrayField(TEXT("parent_cells"),Cells) ||
        !Json->TryGetArrayField(TEXT("faces"),Faces) || Faces->Num()!=4) return false;
    const FVector A[2]={Parent.Frame.AxisX,Parent.Frame.AxisY};
    for(int32 I=0;I<2;++I)
    {
        const TArray<TSharedPtr<FJsonValue>>* Row;const double Values[]={A[I].X,A[I].Y,A[I].Z};
        if(!(*Axes)[I]->TryGetArray(Row) || !Matches(*Row,Values)) return false;
    }
    const double L[]={Parent.Lower.X,Parent.Lower.Y};
    const double E[]={Parent.Cells.X*Parent.Spacing.X,Parent.Cells.Y*Parent.Spacing.Y,Parent.Cells.Z*Parent.Spacing.Z};
    const double C[]={double(Parent.Cells.X),double(Parent.Cells.Y),double(Parent.Cells.Z)};
    if(!Matches(*Lower,L) || !Matches(*Extent,E,true) || !Matches(*Cells,C)) return false;
    FRaftSimLiquidFaceBed Candidate;
    for(int32 Face=0;Face<4;++Face)
    {
        const TSharedPtr<FJsonObject>* Object;const TArray<TSharedPtr<FJsonValue>>* Knots;double Index;
        if(!(*Faces)[Face]->TryGetObject(Object) || !(*Object)->TryGetNumberField(TEXT("face"),Index) || Index!=Face ||
            !(*Object)->TryGetArrayField(TEXT("knots_cm"),Knots) || Knots->Num()<2 || Knots->Num()>4096) return false;
        Candidate.Offsets[Face]=Candidate.Knots.Num();Candidate.Counts[Face]=Knots->Num();
        for(const auto& Knot:*Knots)
        {
            const TArray<TSharedPtr<FJsonValue>>* Row;double T,Z;
            if(!Knot->TryGetArray(Row) || Row->Num()!=2 || !(*Row)[0]->TryGetNumber(T) || !(*Row)[1]->TryGetNumber(Z) ||
                !FMath::IsFinite(T) || !FMath::IsFinite(Z)) return false;
            const FVector2f K{float(T),float(Z)};
            if(K.ContainsNaN() || (Candidate.Knots.Num()>Candidate.Offsets[Face] && K.X<=Candidate.Knots.Last().X)) return false;
            Candidate.Knots.Add(K);
        }
        const int32 Tangent=Face<2?1:0;
        if(Candidate.Knots[Candidate.Offsets[Face]].X!=0 || Candidate.Knots.Last().X!=float(E[Tangent])) return false;
    }
    Out=MoveTemp(Candidate);Error.Reset();return true;
}
}
