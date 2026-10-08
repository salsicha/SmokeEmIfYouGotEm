#pragma once
#include "CoreMinimal.h"
#include "Dom/JsonObject.h"
#include "RaftSimCartesianWaterRegions.h"

// Import-time initialization only. This does not approve a river's hydraulic
// state or bypass its integration profile. Use the same geographic selector
// as normal play; downstream progress is never a Cartesian X coordinate.
namespace RaftSimContinuousRuntimeWindow
{
struct FBinding
{
    FVector2D CenterM = FVector2D::ZeroVector;
    FVector2D ExtentM = FVector2D::ZeroVector;
    double AdvanceM = 0.;
};

inline bool Resolve(bool bCartesian, const TSharedPtr<FJsonObject>& Streaming,
    FVector2D HydraulicLaunchM, double StartStationM, double LateralExtentM,
    const FString& InitialFieldsDirectory, FBinding& Out, FString& Error)
{
    Out = FBinding{};
    FString Schema;
    if (!Streaming || !Streaming->TryGetStringField(TEXT("schema"),Schema) ||
        HydraulicLaunchM.ContainsNaN() || !FMath::IsFinite(StartStationM) ||
        !FMath::IsFinite(LateralExtentM) || LateralExtentM<=0. || InitialFieldsDirectory.IsEmpty())
    { Error=TEXT("Invalid continuous runtime window inputs"); return false; }
    if (!bCartesian)
    {
        if(Schema!=TEXT("raftsim.south_fork.moving_water_streaming.v1"))
        { Error=TEXT("Curved water requires curved streaming"); return false; }
        // Preserve the established station/lateral configuration.
        Out.CenterM=FVector2D(StartStationM,0.);
        Out.ExtentM=FVector2D(480.,LateralExtentM); Out.AdvanceM=80.;
        return true;
    }
    FRaftSimCartesianWaterRegions Regions;
    if(!Regions.Load(Streaming,Error))return false;
    FVector2D Center;
    const auto* Region=Regions.Select(HydraulicLaunchM,InitialFieldsDirectory,&Center);
    if(!Region || Region->FieldsDirectory!=InitialFieldsDirectory)
    { Error=TEXT("Declared initial water source does not cover the geographic launch"); return false; }
    if(Regions.GetExtentM().Y!=LateralExtentM)
    { Error=TEXT("Declared lateral extent differs from the native streaming crop"); return false; }
    Out.CenterM=Center; Out.ExtentM=Regions.GetExtentM();
    Out.AdvanceM=Streaming->GetNumberField(TEXT("advance_m"));
    return true;
}
}
