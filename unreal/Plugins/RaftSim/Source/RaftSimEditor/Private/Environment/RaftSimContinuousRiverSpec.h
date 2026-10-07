#pragma once

#include "CoreMinimal.h"
#include "Dom/JsonObject.h"
#include "RaftSimOarRig.h"

// Explicit integration identity, not a default inferred from an arbitrary map
// name. Adding a river requires its own asset/frame review before import.
namespace RaftSimContinuousRiver
{
struct FSpec
{
    FString RiverId;
    FString MapStem;
    FString PreviewId;
    FString RigName;
    ERaftSimRaftRig Rig = ERaftSimRaftRig::Auto;
    FString CRS;
    FString VerticalReference;
    FString AssetFolder;
    FString WaterStem;
    FString DetailStem;
    bool bChilko = false;
};

inline bool Resolve(const TSharedPtr<FJsonObject>& J, FSpec& Out, FString& Error)
{
    Out = FSpec{};
    FString Schema, River;
    if (!J || !J->TryGetStringField(TEXT("schema"), Schema)) return false;
    const bool Legacy = Schema == TEXT("raftsim.catalog_map_import.v1") ||
        Schema == TEXT("raftsim.colorado_continuous_map_import.v1") ||
        Schema == TEXT("raftsim.colorado_continuous_landscape.v1");
    if (!Legacy && Schema != TEXT("raftsim.continuous_map_import.v1") &&
        Schema != TEXT("raftsim.continuous_landscape.v1"))
    { Error=TEXT("Unsupported continuous river contract"); return false; }
    if (Legacy)
    {
        if (J->HasField(TEXT("river_id")) &&
            (!J->TryGetStringField(TEXT("river_id"), River) || River != TEXT("colorado_river_grand_canyon_rowing")))
        { Error=TEXT("Legacy Colorado contract cannot describe another river"); return false; }
        River=TEXT("colorado_river_grand_canyon_rowing");
    }
    else if (!J->TryGetStringField(TEXT("river_id"), River))
    { Error=TEXT("Continuous river identity is required"); return false; }
    if (River == TEXT("colorado_river_grand_canyon_rowing"))
        Out = {River,TEXT("Colorado"),TEXT("colorado_river"),TEXT("ColoradoOarRig"),
            ERaftSimRaftRig::ColoradoOarRig,TEXT("EPSG:6404"),TEXT("NAD83(2011) ellipsoid"),
            TEXT("ColoradoRun"),TEXT("ColoradoHance"),TEXT("ColoradoRiver"),false};
    else if (River == TEXT("chilko_river_bc"))
        Out = {River,TEXT("Chilko"),TEXT("chilko_river_lava_canyon"),TEXT("PaddleCrew"),
            ERaftSimRaftRig::PaddleCrew,TEXT("EPSG:3157"),TEXT("CGVD2013 (EPSG:6647)"),
            TEXT("ChilkoRun"),TEXT("ChilkoLavaCanyon"),TEXT("Chilko"),true};
    else { Error=TEXT("No reviewed continuous integration profile for river"); return false; }
    FString Rig;
    if (J->HasField(TEXT("rig")) && (!J->TryGetStringField(TEXT("rig"), Rig) || Rig != Out.RigName))
    { Error=TEXT("Raft rig disagrees with the river integration profile"); return false; }
    return true;
}

inline bool Dressing(const TSharedPtr<FJsonObject>& J,const FSpec& Spec,FString& Error)
{
    FString Schema;double Clearance=0,Slope=0,Start=0,End=0;
    const TArray<TSharedPtr<FJsonValue>>* Meshes=nullptr;
    if(!J || !J->TryGetStringField(TEXT("schema"),Schema) ||
        Schema!=(Spec.bChilko ? TEXT("raftsim.chilko_continuous_dressing.v1") : TEXT("raftsim.colorado_continuous_dressing.v1")) ||
        !J->TryGetNumberField(TEXT("minimum_water_clearance_m"),Clearance) || !FMath::IsFinite(Clearance) || Clearance<12. ||
        !J->TryGetNumberField(TEXT("maximum_slope_degrees"),Slope) || !FMath::IsFinite(Slope) || Slope>30. || Slope<0. ||
        !J->TryGetNumberField(TEXT("cull_start_cm"),Start) || Start!=45000. ||
        !J->TryGetNumberField(TEXT("cull_end_cm"),End) || End!=65000. ||
        !J->TryGetArrayField(TEXT("meshes"),Meshes) || !Meshes || Meshes->Num()!=4)
    {Error=TEXT("Invalid river vegetation contract");return false;}
    if(Spec.bChilko)
    {
        FString River;
        if(!J->TryGetStringField(TEXT("river_id"),River) || River!=Spec.RiverId)return false;
    }
    const TCHAR* Colorado[]={TEXT("SM_RaftSim_Hance_DesertShrub_A_OpaqueV2"),TEXT("SM_RaftSim_Hance_DesertShrub_B_OpaqueV2"),
        TEXT("SM_RaftSim_Hance_DryGroundCover_A_OpaqueV2"),TEXT("SM_RaftSim_Hance_DryGroundCover_B_OpaqueV2")};
    const TCHAR* Chilko[]={TEXT("SM_RaftSim_Temperate_ConiferTree_A_OpaqueV1"),TEXT("SM_RaftSim_Temperate_ConiferTree_B_OpaqueV1"),
        TEXT("SM_RaftSim_Temperate_RiparianShrub_A_OpaqueV1"),TEXT("SM_RaftSim_Temperate_RiparianShrub_B_OpaqueV1")};
    const FString Root=Spec.bChilko ? TEXT("/Game/RaftSim/Environment/TemperateRivers/Vegetation/Meshes/") :
        TEXT("/Game/RaftSim/Environment/ColoradoRun/Vegetation/Meshes/");
    for(int32 I=0;I<4;++I)
    {
        const FString Name=Spec.bChilko ? Chilko[I] : Colorado[I];FString Asset;
        if(!(*Meshes)[I]->TryGetString(Asset) || Asset!=Root+Name+TEXT(".")+Name)
        {Error=TEXT("Vegetation mesh does not match river profile");return false;}
    }
    return true;
}

inline bool Frame(const TSharedPtr<FJsonObject>& J, const FSpec& Spec,
    FVector2D& Origin, double& Datum, FString& Error)
{
    if (!J) return false;
    const TArray<TSharedPtr<FJsonValue>>* Values=nullptr;
    const bool Legacy=J->HasField(TEXT("horizontal_origin_epsg6404_m"));
    FString CRS, Vertical;
    if (Legacy)
    {
        if (Spec.CRS != TEXT("EPSG:6404") || J->HasField(TEXT("horizontal_origin_m")))
        { Error=TEXT("Ambiguous or incorrect legacy geographic origin"); return false; }
        if (J->HasField(TEXT("horizontal_crs")) &&
            (!J->TryGetStringField(TEXT("horizontal_crs"),CRS) || CRS != Spec.CRS)) return false;
    }
    else if (!J->TryGetStringField(TEXT("horizontal_crs"),CRS) || CRS != Spec.CRS ||
        !J->TryGetStringField(TEXT("vertical_reference"),Vertical) || Vertical != Spec.VerticalReference)
    { Error=TEXT("Unverified horizontal or vertical reference for river"); return false; }
    double X=0,Y=0;
    if (!J->TryGetArrayField(Legacy ? TEXT("horizontal_origin_epsg6404_m") : TEXT("horizontal_origin_m"),Values) ||
        !Values || Values->Num()!=2 || !(*Values)[0]->TryGetNumber(X) || !(*Values)[1]->TryGetNumber(Y) ||
        !J->TryGetNumberField(TEXT("vertical_datum_m"),Datum) ||
        !FMath::IsFinite(X) || !FMath::IsFinite(Y) || !FMath::IsFinite(Datum))
    { Error=TEXT("Invalid geographic origin or local vertical offset"); return false; }
    Origin=FVector2D(X,Y);
    return true;
}
}
