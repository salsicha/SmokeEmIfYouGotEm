#pragma once
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "Serialization/JsonSerializer.h"
#include "NiagaraSystem.h"
#include "NiagaraDataInterfaceArrayFloat.h"
#include "UObject/UnrealType.h"

// Two explicit review packages, never arbitrary paths or a saved-asset rewrite.
namespace RaftSimLiquidWindowProfile
{
inline bool Centered() { return FParse::Param(FCommandLine::Get(),TEXT("RaftSimLiquidControlCentered")); }
inline bool Geographic() { return FParse::Param(FCommandLine::Get(),TEXT("RaftSimLiquidGeographicReview")); }
inline FVector GeographicTranslation=FVector::ZeroVector;
// Source tables remain immutable in their documented ENU presentation frame.
// Niagara uses a positive-scale, proper rotation; reflect source vectors and
// query coordinates explicitly, since a reflection cannot be a quaternion.
inline bool InitializeGeographicFrame()
{
    if (!Geographic()) return true;
    if (!Centered()) return false;
    FString Text;TSharedPtr<FJsonObject> Geometry;
    const FString Path=FPaths::ProjectDir()/TEXT("../tmp/south-fork-liquid-control-centered-20260909/geometry/manifest.json");
    if (!FFileHelper::LoadFileToString(Text,*Path) ||
        !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Geometry) || !Geometry.IsValid() ||
        !Geometry->GetBoolField(TEXT("coordinate_rebase_only"))) return false;
    const auto& Offset=Geometry->GetArrayField(TEXT("parent_frame_offset_east_north_m"));
    if (Offset.Num()!=2 || !FMath::IsFinite(Offset[0]->AsNumber()) || !FMath::IsFinite(Offset[1]->AsNumber())) return false;
    GeographicTranslation=FVector(100*Offset[0]->AsNumber(),-100*Offset[1]->AsNumber(),0);
    return true;
}
inline FVector PresentVector(FVector V) { if (Geographic()) V.Y=-V.Y;return V; }
inline FVector PresentPosition(FVector P) { return PresentVector(P)+(Geographic()?GeographicTranslation:FVector::ZeroVector); }
inline FString SourcePositionHlsl(const TCHAR* P)
{
    if (!Geographic()) return P;
    return FString::Printf(TEXT("float3((%s).x-(%.9f),-((%s).y-(%.9f)),(%s).z)"),
        P,GeographicTranslation.X,P,GeographicTranslation.Y,P);
}
inline FString PresentPositionHlsl(const TCHAR* P)
{
    if (!Geographic()) return P;
    return FString::Printf(TEXT("float3((%s).x+(%.9f),-(%s).y+(%.9f),(%s).z)"),
        P,GeographicTranslation.X,P,GeographicTranslation.Y,P);
}
inline FString Directory()
{
    return FPaths::ProjectDir()/TEXT("SourceArt/RaftSim")/
        (Centered()?TEXT("SouthForkLiquidControlCentered20260909"):TEXT("SouthForkLiquidWindow20260908"));
}
inline bool Read(const TCHAR* Name,TSharedPtr<FJsonObject>& Json)
{
    FString Text;
    return FFileHelper::LoadFileToString(Text,*(Directory()/Name)) &&
        FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Json) && Json.IsValid();
}
inline bool InstallRecenteredSources(UNiagaraSystem* System)
{
    if (!InitializeGeographicFrame()) return false;
    if (!Centered()) return true;
    if (!System || System->GetOutermost()!=GetTransientPackage()) return false;
    TSharedPtr<FJsonObject> Profile,Window;
    if (!Read(TEXT("native_source_profile.json"),Profile) || !Read(TEXT("manifest.json"),Window) ||
        Profile->GetStringField(TEXT("schema"))!=TEXT("raftsim.native_face_liquid_source.v1") ||
        Profile->GetStringField(TEXT("source_geometry_sha256"))!=Window->GetStringField(TEXT("source_geometry_sha256")) ||
        Profile->GetStringField(TEXT("solid_sha256"))!=Window->GetStringField(TEXT("solid_sha256"))) return false;
    const auto& Positions=Profile->GetArrayField(TEXT("positions_world_offset_cm"));
    const auto& Velocities=Profile->GetArrayField(TEXT("velocities_world_cm_per_s"));
    const auto& Weights=Profile->GetArrayField(TEXT("weights_m3_per_s"));
    const float Rate=Profile->GetNumberField(TEXT("requested_spawn_particles_per_second"));
    if (Positions.IsEmpty() || Positions.Num()!=Velocities.Num() || Positions.Num()!=Weights.Num() ||
        !FMath::IsFinite(Rate) || Rate<=0 || Rate>100000) return false;
    double WeightSum=0;
    for (int32 I=0;I<Positions.Num();++I)
    {
        const auto& P=Positions[I]->AsArray();const auto& V=Velocities[I]->AsArray();
        const double Weight=Weights[I]->AsNumber();
        if (P.Num()!=3 || V.Num()!=3 || !FMath::IsFinite(Weight) || Weight<=0) return false;
        for (int32 Axis=0;Axis<3;++Axis)
            if (!FMath::IsFinite(P[Axis]->AsNumber()) || !FMath::IsFinite(V[Axis]->AsNumber())) return false;
        WeightSum+=Weight;
    }
    if (!FMath::IsNearlyEqual(WeightSum,Profile->GetNumberField(TEXT("total_inflow_m3_per_s")),1e-8)) return false;
    auto& Store=System->GetExposedParameters();
    const auto SetArray=[&](const TCHAR* Name,const TArray<TSharedPtr<FJsonValue>>& Rows)
    {
        auto* Array=NewObject<UNiagaraDataInterfaceArrayFloat3>(System);
        for (const auto& Row:Rows)
        {
            const auto& V=Row->AsArray();const FVector P=PresentVector(FVector(V[0]->AsNumber(),V[1]->AsNumber(),V[2]->AsNumber()));
            Array->FloatData.Add(P);Array->InternalFloatData.Add(FVector3f(P));
        }
        FNiagaraVariable Variable(FNiagaraTypeDefinition(Array->GetClass()),Name);
        Store.AddParameter(Variable);Store.SetDataInterface(Array,Variable);
    };
    SetArray(TEXT("User.River Source Positions"),Positions);SetArray(TEXT("User.River Source Velocities"),Velocities);
    auto* Class=LoadClass<UNiagaraDataInterface>(nullptr,TEXT("/Script/Niagara.NiagaraDataInterfaceArrayDistributionInt"));
    if (!Class) return false;
    auto* Distribution=NewObject<UNiagaraDataInterface>(System,Class);
    auto* ArrayProperty=FindFProperty<FArrayProperty>(Class,TEXT("ArrayData"));
    auto* Entry=ArrayProperty?CastField<FStructProperty>(ArrayProperty->Inner):nullptr;
    auto* Value=Entry?FindFProperty<FIntProperty>(Entry->Struct,TEXT("Value")):nullptr;
    auto* Weight=Entry?FindFProperty<FFloatProperty>(Entry->Struct,TEXT("Weight")):nullptr;
    if (!Value || !Weight) return false;
    FScriptArrayHelper Entries(ArrayProperty,ArrayProperty->ContainerPtrToValuePtr<void>(Distribution));
    Entries.Resize(Weights.Num());
    for (int32 I=0;I<Weights.Num();++I)
    {
        Value->SetPropertyValue_InContainer(Entries.GetRawPtr(I),I);
        Weight->SetPropertyValue_InContainer(Entries.GetRawPtr(I),float(Weights[I]->AsNumber()));
    }
    FPropertyChangedEvent Changed(ArrayProperty);Distribution->PostEditChangeProperty(Changed);
    FNiagaraVariable Variable(FNiagaraTypeDefinition(Class),TEXT("User.River Source Distribution"));
    Store.AddParameter(Variable);Store.SetDataInterface(Distribution,Variable);
    Store.SetParameterValue<float>(Rate,FNiagaraVariable(FNiagaraTypeDefinition::GetFloatDef(),TEXT("User.Inlet Particle Rate")));
    UE_LOG(LogTemp,Display,TEXT("Control-centred sources installed: points=%d nominal_Q=%.9f rate=%.6f; unsaved"),Positions.Num(),WeightSum,Rate);
    return true;
}
}
