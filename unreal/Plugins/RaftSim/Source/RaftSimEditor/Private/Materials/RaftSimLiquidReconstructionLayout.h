#pragma once
#include "CoreMinimal.h"

// Metric geometry shared by reconstruction, foam, runtime DI checks and
// diagnostic readback. Two-cell XY solver halo and 2x render refinement are
// explicit contracts, not inferred from a square max-axis resolution.
struct FRaftSimLiquidReconstructionLayout
{
    FIntVector Solver=FIntVector(68,68,24),Render=FIntVector(136,136,48);
    FVector3f ExtentCm=FVector3f(2231.25f,2231.25f,800.f);
    FVector2f PhysicalHalfCm=FVector2f(1050.f,1050.f);
    FVector3f MinimumMeters() const { return FVector3f(-ExtentCm.X/200.f,-ExtentCm.Y/200.f,0); }
    FVector3f ExtentMeters() const { return ExtentCm/100.f; }
    FVector3f RenderSpacingCm() const { return ExtentCm/FVector3f(Render); }
    bool Configure(FVector3f Counts,FVector3f Extent,FString& Error)
    {
        if (Counts.ContainsNaN() || Extent.ContainsNaN() || Counts.GetMin()<4 || Counts.GetMax()>4096 || Extent.GetMin()<=0 ||
            Counts.X!=FMath::FloorToFloat(Counts.X) || Counts.Y!=FMath::FloorToFloat(Counts.Y) || Counts.Z!=FMath::FloorToFloat(Counts.Z))
        { Error=TEXT("Finite integer reconstruction dimensions and positive metric extent required");return false; }
        const FIntVector C(int32(Counts.X),int32(Counts.Y),int32(Counts.Z));
        if (C.X<6 || C.Y<6 || C.X%2 || int64(C.X)*C.Y*C.Z*8>2000000)
        { Error=TEXT("Bounded reconstruction requires physical cells plus XY halo and even X");return false; }
        Solver=C;Render=C*2;ExtentCm=Extent;
        PhysicalHalfCm=FVector2f(Extent.X*(C.X-4)/C.X*.5f,Extent.Y*(C.Y-4)/C.Y*.5f);
        Error.Reset();return true;
    }
};
