#include "RaftSimCartesianWaterRegions.h"
#include "Dom/JsonObject.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "RaftSimWaterRuntimeAdapter.h"

bool FRaftSimCartesianWaterRegions::ConfigureAtWorldPosition(URaftSimWaterRuntimeAdapter* Water,
    const FString& ManifestPath, const FString& FlowBand, const FVector& PositionCm)
{
    if (!Water || !Water->HasCartesianWaterCoordinates() || PositionCm.ContainsNaN()) return false;
    FVector2D PositionM;
    FVector Tangent, Left;
    if (!Water->WorldToRiverCoordinates(PositionCm, PositionM, Tangent, Left)) return false;
    FString Text, Error;
    TSharedPtr<FJsonObject> Root;
    if (!FFileHelper::LoadFileToString(Text, *URaftSimWaterRuntimeAdapter::ResolveRuntimeDataPath(ManifestPath)) ||
        !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text), Root)) return false;
    FRaftSimCartesianWaterRegions Regions;
    if (!Regions.Load(Root, Error)) return false;
    FVector2D CenterM;
    const auto* Region = Regions.Select(PositionM, TEXT(""), &CenterM);
    return Region && Water->ConfigureMovingRiverWindowValidated(Region->FieldsDirectory,
        FlowBand, CenterM, Regions.GetExtentM(), Regions.GetRoughnessManning(), PositionM);
}

bool FRaftSimCartesianWaterRegions::Load(const TSharedPtr<FJsonObject>& Root, FString& OutError)
{
    Regions.Reset();
    SourceContextCells = 1.;
    MinimumRaftInteriorMarginM = 0.;
    OutError = TEXT("Invalid Cartesian cooked-water streaming manifest");
    FString Schema;
    const TArray<TSharedPtr<FJsonValue>>* Extent = nullptr;
    const TArray<TSharedPtr<FJsonValue>>* Windows = nullptr;
    if (!Root.IsValid() || !Root->TryGetStringField(TEXT("schema"), Schema) ||
        Schema != TEXT("raftsim.cartesian_water_streaming.v1") ||
        !Root->TryGetArrayField(TEXT("live_window_extent_m"), Extent) || Extent->Num() != 2 ||
        !Root->TryGetNumberField(TEXT("grid_spacing_m"), GridSpacingM) ||
        !Root->TryGetNumberField(TEXT("advance_m"), AdvanceM) ||
        !Root->TryGetNumberField(TEXT("roughness_manning"), RoughnessManning) ||
        !Root->TryGetArrayField(TEXT("windows"), Windows) || Windows->IsEmpty()) return false;
    if (!(*Extent)[0].IsValid() || !(*Extent)[1].IsValid() ||
        !(*Extent)[0]->TryGetNumber(ExtentM.X) || !(*Extent)[1]->TryGetNumber(ExtentM.Y) ||
        ExtentM.ContainsNaN() || !FMath::IsFinite(GridSpacingM) || !FMath::IsFinite(AdvanceM) ||
        !FMath::IsFinite(RoughnessManning) || RoughnessManning <= 0. ||
        GridSpacingM <= 0. || ExtentM.GetMin() < 8.*GridSpacingM || AdvanceM <= 0. ||
        AdvanceM >= ExtentM.GetMin()*.5) return false;
    // A MUSCL crop needs two ghost layers plus one cell for outward crop
    // rounding. Legacy first-order sources keep their one-cell margin.
    if (Root->HasField(TEXT("source_context_cells")) &&
        (!Root->TryGetNumberField(TEXT("source_context_cells"), SourceContextCells) ||
         !FMath::IsFinite(SourceContextCells) || SourceContextCells < 3. ||
         SourceContextCells != FMath::FloorToDouble(SourceContextCells))) return false;
    const bool bHasRaftMargin = Root->HasField(TEXT("minimum_raft_interior_margin_m"));
    if (bHasRaftMargin && (!Root->TryGetNumberField(TEXT("minimum_raft_interior_margin_m"),MinimumRaftInteriorMarginM) ||
        !FMath::IsFinite(MinimumRaftInteriorMarginM) || MinimumRaftInteriorMarginM <= 0. ||
        MinimumRaftInteriorMarginM >= ExtentM.GetMin()*.5)) return false;
    TArray<FRegion> Candidate;
    TSet<FString> Ids, Directories;
    for (const auto& Value : *Windows)
    {
        const TSharedPtr<FJsonObject>* Object = nullptr;
        const TArray<TSharedPtr<FJsonValue>>* Bounds = nullptr;
        FString Manifest;
        FRegion Region;
        if (!Value.IsValid() || !Value->TryGetObject(Object) || !Object->IsValid() ||
            !(*Object)->TryGetStringField(TEXT("window_id"), Region.Id) || Region.Id.IsEmpty() ||
            !(*Object)->TryGetStringField(TEXT("cooked_fields_manifest"), Manifest) ||
            FPaths::GetCleanFilename(Manifest) != TEXT("manifest.json") ||
            !(*Object)->TryGetArrayField(TEXT("hydraulic_bounds_m"), Bounds) || Bounds->Num() != 4) return false;
        double Coordinates[4];
        for (int32 Index = 0; Index < 4; ++Index)
        {
            if (!(*Bounds)[Index].IsValid() || !(*Bounds)[Index]->TryGetNumber(Coordinates[Index]) ||
                !FMath::IsFinite(Coordinates[Index])) return false;
        }
        Region.BoundsM = FBox2D(FVector2D(Coordinates[0],Coordinates[1]), FVector2D(Coordinates[2],Coordinates[3]));
        const FVector2D Size = Region.BoundsM.Max - Region.BoundsM.Min;
        if (Size.X < ExtentM.X+2.*SourceContextCells*GridSpacingM ||
            Size.Y < ExtentM.Y+2.*SourceContextCells*GridSpacingM) return false;
        if ((*Object)->HasField(TEXT("valid_live_center_bounds_m")))
        {
            const TArray<TSharedPtr<FJsonValue>>* Centers = nullptr;
            if (!bHasRaftMargin || SourceContextCells < 3. ||
                !(*Object)->TryGetArrayField(TEXT("valid_live_center_bounds_m"),Centers)) return false;
            Region.bHasExplicitLiveCenters = true;
            const FVector2D Half = ExtentM*.5+FVector2D(SourceContextCells*GridSpacingM);
            for (const auto& Center : *Centers)
            {
                const TArray<TSharedPtr<FJsonValue>>* Values = nullptr;
                if (!Center.IsValid() || !Center->TryGetArray(Values) || Values->Num()!=4) return false;
                double C[4];
                for (int32 I=0;I<4;++I)
                    if (!(*Values)[I].IsValid() || !(*Values)[I]->TryGetNumber(C[I]) || !FMath::IsFinite(C[I])) return false;
                if (C[0]>C[2] || C[1]>C[3]) return false;
                const FBox2D Rectangle(FVector2D(C[0],C[1]),FVector2D(C[2],C[3]));
                if (!Region.BoundsM.IsInsideOrOn(Rectangle.Min-Half) ||
                    !Region.BoundsM.IsInsideOrOn(Rectangle.Max+Half)) return false;
                Region.LiveCenterBoundsM.Add(Rectangle);
            }
            // Empty means this source has no complete live crop. Retain its
            // identity, but never invent a usable center or shrink the window.
        }
        Region.FieldsDirectory = FPaths::GetPath(Manifest);
        if (Region.FieldsDirectory.IsEmpty() || Ids.Contains(Region.Id) || Directories.Contains(Region.FieldsDirectory)) return false;
        Ids.Add(Region.Id);
        Directories.Add(Region.FieldsDirectory);
        Candidate.Add(MoveTemp(Region));
    }
    Regions = MoveTemp(Candidate);
    OutError.Reset();
    return true;
}

const FRaftSimCartesianWaterRegions::FRegion* FRaftSimCartesianWaterRegions::Select(
    FVector2D PositionM, const FString& ActiveDirectory, FVector2D* OutWindowCenterM,
    const FBox2D* RequiredSourceBoundsM) const
{
    if (PositionM.ContainsNaN()) return nullptr;
    const FVector2D FieldHalf=ExtentM*.5;
    FBox2D RequiredCenters(ForceInit);
    if(RequiredSourceBoundsM)
    {
        if(!RequiredSourceBoundsM->bIsValid || RequiredSourceBoundsM->Min.ContainsNaN() ||
            RequiredSourceBoundsM->Max.ContainsNaN())return nullptr;
        RequiredCenters=FBox2D(RequiredSourceBoundsM->Max-FieldHalf,RequiredSourceBoundsM->Min+FieldHalf);
        if(RequiredCenters.Min.X>RequiredCenters.Max.X || RequiredCenters.Min.Y>RequiredCenters.Max.Y)return nullptr;
    }
    const double ContextM = SourceContextCells*GridSpacingM;
    const FVector2D Half = ExtentM*.5 + FVector2D(ContextM,ContextM);
    const FRegion* Best = nullptr;
    double BestMargin = -1.;
    double BestShiftSquared = TNumericLimits<double>::Max();
    bool bBestActive = false;
    const auto Consider = [&](const FRegion& Region, FVector2D Center)
    {
        if (!CoversRaft(PositionM,Center) || !Region.BoundsM.IsInsideOrOn(Center-Half) ||
            !Region.BoundsM.IsInsideOrOn(Center+Half)) return;
        if(RequiredSourceBoundsM && !RequiredCenters.IsInsideOrOn(Center))return;
        const double Shift = FVector2D::DistSquared(PositionM,Center);
        const bool bActive = Region.FieldsDirectory==ActiveDirectory;
        const double Margin = FMath::Min((Center-Region.BoundsM.Min).GetMin(),
            (Region.BoundsM.Max-Center).GetMin());
        const bool bEqualShift = FMath::IsNearlyEqual(Shift,BestShiftSquared,1.e-9);
        if (Shift < BestShiftSquared-1.e-9 || (bEqualShift &&
            ((bActive && !bBestActive) || (bActive==bBestActive && Margin>BestMargin))))
        {
            Best=&Region; BestShiftSquared=Shift; BestMargin=Margin; bBestActive=bActive;
            if (OutWindowCenterM) *OutWindowCenterM=Center;
        }
    };
    for (const FRegion& Region : Regions)
    {
        if(RequiredSourceBoundsM)
        {
            const auto Cover=[&](const FBox2D& Rectangle)
            {
                const FVector2D Low=FVector2D::Max(Rectangle.Min,RequiredCenters.Min);
                const FVector2D High=FVector2D::Min(Rectangle.Max,RequiredCenters.Max);
                if(Low.X<=High.X && Low.Y<=High.Y)
                    Consider(Region,FVector2D(FMath::Clamp(PositionM.X,Low.X,High.X),FMath::Clamp(PositionM.Y,Low.Y,High.Y)));
            };
            if(Region.bHasExplicitLiveCenters)
                for(const FBox2D& Rectangle:Region.LiveCenterBoundsM)Cover(Rectangle);
            else Cover(FBox2D(Region.BoundsM.Min+Half,Region.BoundsM.Max-Half));
            continue;
        }
        if (Region.bHasExplicitLiveCenters)
        {
            for (const FBox2D& Rectangle : Region.LiveCenterBoundsM)
                Consider(Region,FVector2D(FMath::Clamp(PositionM.X,Rectangle.Min.X,Rectangle.Max.X),
                    FMath::Clamp(PositionM.Y,Rectangle.Min.Y,Rectangle.Max.Y)));
        }
        else Consider(Region,PositionM);
    }
    return Best; // Never choose a nearby but incomplete source as a fallback.
}

bool FRaftSimCartesianWaterRegions::CoversRaft(FVector2D PositionM,FVector2D WindowCenterM) const
{
    if (PositionM.ContainsNaN() || WindowCenterM.ContainsNaN()) return false;
    const FVector2D Difference=PositionM-WindowCenterM;
    return FMath::Abs(Difference.X)<=ExtentM.X*.5-MinimumRaftInteriorMarginM &&
        FMath::Abs(Difference.Y)<=ExtentM.Y*.5-MinimumRaftInteriorMarginM;
}

bool FRaftSimCartesianWaterRegions::NeedsRecentering(FVector2D PositionM, FVector2D PreviousCenterM) const
{
    const FVector2D Difference = PositionM-PreviousCenterM;
    return FMath::Max(FMath::Abs(Difference.X),FMath::Abs(Difference.Y)) >= AdvanceM;
}
