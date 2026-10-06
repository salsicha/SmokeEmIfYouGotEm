#pragma once
#include "RaftSimLiquidRegionalBoundary.h"
#include "RaftSimLiquidParticleExitGPU.h"

// A read-only parent FACE TABLE, never a whole-domain grid allocation. It must
// be validated together with every bounded physical owner before use. Querying
// the parent faces avoids inventing reservoirs at a region cut, including an
// exterior halo corner whose tangent lies in the neighboring region.
namespace RaftSimLiquidParentExterior
{
class FProfile
{
    struct FOwner
    {
        FIntPoint First;
        FIntVector Cells,Compute;
        FVector Origin,AxisX,AxisY,Extent;
    };
    TArray<FVector3f> Values;
    TMap<int32,FOwner> Owners;
    FIntPoint ParentCells=FIntPoint::ZeroValue;
    FVector3f ExitLower=FVector3f::ZeroVector,ExitAxisX=FVector3f::ZeroVector,ExitAxisY=FVector3f::ZeroVector;
    FVector2f ExitSpacing=FVector2f::ZeroVector;
    float ExitHeight=0;
    FRaftSimLiquidFaceBed ExactBed;
public:
    void SetExactBed(FRaftSimLiquidFaceBed Bed) { ExactBed=MoveTemp(Bed); }
    const TArray<FVector3f>& Packed() const { return Values; }
    // Upload the exact float32 frame also bound to routing/exit shaders. Do not
    // reconstruct the lower corner from a separately rounded centre on the GPU.
    TArray<FVector3f> PhysicalFrame() const { return {ExitLower,ExitAxisX,ExitAxisY}; }
    FRaftSimLiquidParticleExitPlan ExitPlan(FRDGBuilder& Graph,const FRaftSimLiquidParticleRoutePlan& Routing,FString& Error) const
    {
        Error=TEXT("Particle exit policy must match the validated physical parent, not a local region");
        if(Values.IsEmpty() || Routing.ParentCells!=ParentCells || Routing.Owners!=uint32(Owners.Num()) ||
            Routing.LowerWorldCm!=ExitLower || Routing.AxisX!=ExitAxisX || Routing.AxisY!=ExitAxisY || Routing.SpacingCm!=ExitSpacing)
            return {};
        return RaftSimBuildLiquidParticleExitPlan(Graph,Routing,ExitHeight,
            TConstArrayView<FVector3f>(Values.GetData()+8,2*(ParentCells.X+ParentCells.Y)),Error,ExactBed.Knots.IsEmpty()?nullptr:&ExactBed);
    }
    bool Matches(const RaftSimLiquidRegionalState::FState& R) const
    {
        const auto* O=Owners.Find(R.Id);
        return O && O->First==R.FirstCell && O->Cells==R.Cells && O->Compute==R.ComputationalCells &&
            O->Origin==R.Frame.Origin && O->AxisX==R.Frame.AxisX && O->AxisY==R.Frame.AxisY && O->Extent==R.Extent;
    }
    static bool Build(const RaftSimLiquidRegionalState::FParent& Parent,
        const TArray<RaftSimLiquidRegionalState::FState>& Regions,const TSharedPtr<FJsonObject>& Json,
        FProfile& Out,FString& Error)
    {
        Out={};TArray<RaftSimLiquidRegionalBoundary::FRegion> Boundaries;
        if (!RaftSimLiquidRegionalBoundary::Build(Parent,Regions,Json,Boundaries,Error)) return false;
        // The existing builder verified schema, exact parent metric/frame,
        // complete physical ownership and every scalar/vector exterior row.
        FProfile Candidate;
        using RaftSimLiquidRegionalState::FCanonicalFrame;
        Candidate.ParentCells=FIntPoint(Parent.Cells.X,Parent.Cells.Y);
        Candidate.ExitLower=FVector3f(FCanonicalFrame::WorldPosition(Parent.Frame.AxisX*(Parent.Lower.X*100)+
            Parent.Frame.AxisY*(Parent.Lower.Y*100)+FVector(0,0,Parent.Frame.Origin.Z)));
        Candidate.ExitAxisX=FVector3f(FCanonicalFrame::WorldVector(Parent.Frame.AxisX));
        Candidate.ExitAxisY=FVector3f(FCanonicalFrame::WorldVector(Parent.Frame.AxisY));
        Candidate.ExitSpacing=FVector2f(Parent.Spacing.X,Parent.Spacing.Y);
        Candidate.ExitHeight=float(Parent.Cells.Z*Parent.Spacing.Z);
        for (const auto& Value:Json->GetArrayField(TEXT("packed_vectors")))
        {
            const auto& R=Value->AsArray();
            Candidate.Values.Emplace(float(R[0]->AsNumber()),float(R[1]->AsNumber()),float(R[2]->AsNumber()));
        }
        Candidate.Values[3].Z=-Candidate.Values[3].Z; // shared v3 query ABI only
        const int32 VectorStart=8+2*(Parent.Cells.X+Parent.Cells.Y);
        for (int32 I=VectorStart;I<Candidate.Values.Num();++I)
            for (int32 A=0;A<3;++A) if (FMath::Abs(Candidate.Values[I][A])>65504.f)
            { Error=TEXT("Exterior velocity exceeds finite native RGBA16F range");return false; }
        for (const auto& R:Regions)
            Candidate.Owners.Add(R.Id,{R.FirstCell,R.Cells,R.ComputationalCells,R.Frame.Origin,R.Frame.AxisX,R.Frame.AxisY,R.Extent});
        Out=MoveTemp(Candidate);Error.Reset();return true;
    }
};
}
