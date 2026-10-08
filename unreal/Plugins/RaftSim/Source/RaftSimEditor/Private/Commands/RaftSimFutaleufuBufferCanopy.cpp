// Remove only source-identified hydraulic-buffer conflicts through FFoliageInfo.
// Editing HISM instances alone would leave stale editor foliage metadata.
#include "Editor.h"
#include "EngineUtils.h"
#include "InstancedFoliageActor.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "HAL/IConsoleManager.h"
#include "Materials/RaftSimLiquidDataset.h"

namespace RaftSimFutaleufuBufferCanopy
{
struct FTarget { FString Mesh;FTransform Transform;int32 Found=0; };
struct FRemoval { AInstancedFoliageActor* Actor;FFoliageInfo* Info;TArray<int32> Indices; };

static FString Key(const UFoliageType* Type,const FFoliageInstance& I)
{
    // Stable serialized metadata, excluding transient UObject pointers. Sorting
    // makes native swap-removal harmless while preserving duplicate counts.
    return FString::Printf(TEXT("%s|%.17g,%.17g,%.17g|%.17g,%.17g,%.17g|%.17g,%.17g,%.17g|%.9g,%.9g,%.9g|%.9g|%u|%d|%s"),
        *Type->GetPathName(),I.Location.X,I.Location.Y,I.Location.Z,I.Rotation.Pitch,I.Rotation.Yaw,I.Rotation.Roll,
        I.PreAlignRotation.Pitch,I.PreAlignRotation.Yaw,I.PreAlignRotation.Roll,
        I.DrawScale3D.X,I.DrawScale3D.Y,I.DrawScale3D.Z,I.ZOffset,I.Flags,I.BaseId,*I.ProceduralGuid.ToString());
}

static FString Digest(TArray<FString>& Rows)
{
    Rows.Sort();const FString Joined=FString::Join(Rows,TEXT("\n"));FTCHARToUTF8 Utf8(*Joined);
    uint8 Bytes[SHA256_DIGEST_LENGTH];SHA256(reinterpret_cast<const uint8*>(Utf8.Get()),Utf8.Length(),Bytes);
    return BytesToHex(Bytes,SHA256_DIGEST_LENGTH).ToLower();
}

static bool Run(const FString& Path,bool Apply,TSharedPtr<FJsonObject>& Result,FString& Error)
{
    const auto J=FRaftSimLiquidDataset::Read(Path);
    UWorld* World=GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
    if(!J || J->GetStringField(TEXT("schema"))!=TEXT("raftsim.futaleufu_buffer_canopy_update.v1") || !World ||
        World->GetPackage()->GetName()!=TEXT("/Game/RaftSim/Maps/Continuous/L_Futaleufu_ContinuousContextV1"))return false;
    TArray<FTarget> Targets;
    for(const auto& Value:J->GetArrayField(TEXT("remove")))
    {
        const auto Row=Value->AsObject();if(!Row)return false;
        const auto& P=Row->GetArrayField(TEXT("location_cm"));const auto& S=Row->GetArrayField(TEXT("scale_xyz"));
        if(P.Num()!=3 || S.Num()!=3)return false;
        FTarget T;T.Mesh=Row->GetStringField(TEXT("mesh_asset"));
        T.Transform=FTransform(FRotator(0,Row->GetNumberField(TEXT("yaw_deg")),0),
            FVector(P[0]->AsNumber(),P[1]->AsNumber(),P[2]->AsNumber()),FVector(S[0]->AsNumber(),S[1]->AsNumber(),S[2]->AsNumber()));
        if(T.Transform.ContainsNaN())return false;Targets.Add(MoveTemp(T));
    }
    if(Targets.Num()!=42)return false;
    TArray<FRemoval> Removals;TArray<FString> Expected;int32 Before=0,Groups=0;bool Valid=true;
    auto Inspect=[&](AInstancedFoliageActor* Actor,UFoliageType* Type,FFoliageInfo& Info,bool Find,TArray<FString>& Rows)->bool
    {
        auto* Static=Cast<UFoliageType_InstancedStaticMesh>(Type);auto* C=Info.GetComponent();
        if(!Static || !Static->GetStaticMesh() || !C || C->GetCollisionEnabled()!=ECollisionEnabled::NoCollision ||
            C->InstanceStartCullDistance!=45000 || C->InstanceEndCullDistance!=65000 ||
            C->GetInstanceCount()!=Info.Instances.Num())return false;
        FRemoval Removal{Actor,&Info,{}};
        for(int32 I=0;I<Info.Instances.Num();++I)
        {
            const FTransform Native=Info.Instances[I].GetInstanceWorldTransform();FTransform Render;
            if(Native.ContainsNaN() || !C->GetInstanceTransform(I,Render,true) ||
                !Native.GetLocation().Equals(Render.GetLocation(),1.) ||
                !Native.GetScale3D().Equals(Render.GetScale3D(),1.e-5) ||
                !Native.GetRotation().Equals(Render.GetRotation(),1.e-5))return false;
            bool Remove=false;
            for(auto& T:Targets)
                if(T.Mesh==Static->GetStaticMesh()->GetPathName() && Native.GetLocation().Equals(T.Transform.GetLocation(),1.))
                {
                    if(!Native.GetScale3D().Equals(T.Transform.GetScale3D(),1.e-5) ||
                        !Native.GetRotation().Equals(T.Transform.GetRotation(),1.e-5))return false;
                    if(!Find || Remove)return false;
                    ++T.Found;Removal.Indices.Add(I);Remove=true;
                }
            if(!Remove)Rows.Add(Key(Type,Info.Instances[I]));
        }
        if(Find){Before+=Info.Instances.Num();++Groups;if(!Removal.Indices.IsEmpty())Removals.Add(MoveTemp(Removal));}
        return true;
    };
    for(TActorIterator<AInstancedFoliageActor> It(World);It;++It)
    {
        if(!It->GetIsSpatiallyLoaded())return false;
        It->ForEachFoliageInfo([&](UFoliageType* Type,FFoliageInfo& Info)
            {Valid=Valid && Inspect(*It,Type,Info,Apply,Expected);return Valid;});
        if(!Valid)return false;
    }
    if(Expected.IsEmpty())return false;
    TSet<UPackage*> Packages;
    if(Apply)
    {
        for(const auto& T:Targets)if(T.Found!=1){Error=TEXT("Every exclusion must match exactly one native instance");return false;}
        for(auto& R:Removals)
        {
            R.Actor->Modify();Packages.Add(R.Actor->GetPackage());
            R.Info->RemoveInstances(R.Indices,true);R.Actor->MarkPackageDirty();
        }
        TArray<FString> Actual;
        for(TActorIterator<AInstancedFoliageActor> It(World);It;++It)
            It->ForEachFoliageInfo([&](UFoliageType* Type,FFoliageInfo& Info)
                {Valid=Valid && Inspect(*It,Type,Info,false,Actual);return Valid;});
        if(!Valid || Actual.Num()!=Before-42 || Digest(Actual)!=Digest(Expected))
        {Error=TEXT("Retained foliage metadata or render instances changed; no save permitted");return false;}
    }
    TArray<TSharedPtr<FJsonValue>> Names;
    for(auto* P:Packages)
    {
        if(!P->GetName().StartsWith(TEXT("/Game/__ExternalActors__/RaftSim/Maps/Continuous/L_Futaleufu_ContinuousContextV1/")))return false;
        Names.Add(MakeShared<FJsonValueString>(P->GetName()));
    }
    Result=MakeShared<FJsonObject>();Result->SetStringField(TEXT("request_sha256"),FRaftSimLiquidDataset::Hash(Path));
    Result->SetStringField(TEXT("retained_native_metadata_sha256"),Digest(Expected));
    Result->SetNumberField(TEXT("retained_loaded_instances"),Expected.Num());
    Result->SetNumberField(TEXT("removed_instances"),Apply ? 42 : 0);
    Result->SetBoolField(TEXT("all_exclusions_absent_after_operation"),true);
    Result->SetBoolField(TEXT("native_metadata_matches_render_instances"),true);
    Result->SetArrayField(TEXT("target_packages"),Names);return true;
}

static void Command(const TArray<FString>& Args)
{
    if(Args.Num()!=3 || (Args[1]!=TEXT("apply") && Args[1]!=TEXT("verify")))return;
    const FString Root=FPaths::ConvertRelativePathToFull(FPaths::ProjectDir()/TEXT(".."));
    for(int32 I:{0,2})if(!Args[I].StartsWith(TEXT("tmp/")) || Args[I].Contains(TEXT("..")))return;
    if(FPaths::FileExists(Root/Args[2]))return;
    TSharedPtr<FJsonObject> Result;FString Error=TEXT("Native foliage precondition failed");
    if(!Run(Root/Args[0],Args[1]==TEXT("apply"),Result,Error))
    {UE_LOG(LogTemp,Error,TEXT("Futaleufu buffer canopy: %s"),*Error);return;}
    FString Text;FJsonSerializer::Serialize(Result.ToSharedRef(),TJsonWriterFactory<>::Create(&Text));
    FFileHelper::SaveStringToFile(Text,*(Root/Args[2]));UE_LOG(LogTemp,Display,TEXT("Futaleufu buffer canopy: %s"),*Text);
}
static FAutoConsoleCommand Registration(TEXT("RaftSim.UpdateFutaleufuBufferCanopy"),
    TEXT("<request> <apply|verify> <fresh-receipt>; caller owns backup and targeted save"),FConsoleCommandWithArgsDelegate::CreateStatic(&Command));
}
