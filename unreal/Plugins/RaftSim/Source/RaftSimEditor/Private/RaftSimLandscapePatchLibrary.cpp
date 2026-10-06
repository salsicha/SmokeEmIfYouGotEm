#include "RaftSimLandscapePatchLibrary.h"
#include "LandscapeProxy.h"
#include "LandscapeInfo.h"
#include "LandscapeSubsystem.h"
#include "LandscapeEditTypes.h"
#include "Engine/World.h"
#include "LandscapeEdit.h"
#include "LandscapeEditorModule.h"
#include "LandscapeEditorUtils.h"
#include "LandscapeFileFormatInterface.h"
#include "Modules/ModuleManager.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"

FString URaftSimLandscapePatchLibrary::ApplyHeightfieldPatch(ALandscapeProxy* Landscape,
    const FString& BeforePng,const FString& AfterPng)
{
    auto Report=MakeShared<FJsonObject>();Report->SetBoolField(TEXT("applied"),false);
    const auto Done=[&](const TCHAR* Reason)
    {
        Report->SetStringField(TEXT("reason"),Reason);FString Text;
        FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Text));return Text;
    };
    if(!Landscape || !Landscape->GetWorld() || Landscape->GetWorld()->IsGameWorld())return Done(TEXT("editor_landscape_required"));
    auto* Info=Landscape->GetLandscapeInfo();int32 X0=0,Y0=0,X1=0,Y1=0;
    if(!Info || !Info->GetLandscapeExtent(X0,Y0,X1,Y1))return Done(TEXT("landscape_extent_unavailable"));
    const int32 Width=X1-X0+1,Height=Y1-Y0+1;
    auto& Module=FModuleManager::LoadModuleChecked<ILandscapeEditorModule>(TEXT("LandscapeEditor"));
    const auto* Format=Module.GetHeightmapFormatByExtension(TEXT(".png"));
    if(!Format)return Done(TEXT("png_importer_unavailable"));
    const FLandscapeFileResolution Size(Width,Height);
    if(!Format->Validate(*BeforePng).PossibleResolutions.Contains(Size) ||
       !Format->Validate(*AfterPng).PossibleResolutions.Contains(Size))return Done(TEXT("heightfield_dimensions_differ"));
    const auto Before=Format->Import(*BeforePng,Size),After=Format->Import(*AfterPng,Size);
    if(Before.ResultCode==ELandscapeImportResult::Error || After.ResultCode==ELandscapeImportResult::Error ||
       Before.Data.Num()!=Width*Height || After.Data.Num()!=Before.Data.Num())return Done(TEXT("heightfield_import_failed"));
    TArray<int32> Changes;
    for(int32 I=0;I<Before.Data.Num();++I)if(Before.Data[I]!=After.Data[I])Changes.Add(I);
    Report->SetNumberField(TEXT("changed_pixels"),Changes.Num());
    if(Changes.IsEmpty() || Changes.Num()>4096)return Done(TEXT("not_a_small_patch"));
    TArray<uint16> Current;Current.SetNumZeroed(Width*Height);
    {
        FLandscapeEditDataInterface Edit(Info);
        Edit.GetHeightDataFast(X0,Y0,X1,Y1,Current.GetData(),Width);
    }
    for(int32 I:Changes)if(Current[I]!=Before.Data[I])return Done(TEXT("live_terrain_differs_from_before_source"));
    for(int32 I:Changes)Current[I]=After.Data[I];
    Landscape->Modify();
    if(!LandscapeEditorUtils::SetHeightmapData(Landscape,Current))return Done(TEXT("heightmap_update_failed"));
    Landscape->RecreateComponentsState();
    Landscape->PostEditChange();
    Landscape->RecreateCollisionComponents();
    if(Landscape->IsNaniteEnabled())
    {
        auto* Subsystem=Landscape->GetWorld()->GetSubsystem<ULandscapeSubsystem>();
        if(!Subsystem)return Done(TEXT("landscape_subsystem_missing_not_saved"));
        TArray<ALandscapeProxy*> OnlyThisLandscape={Landscape};
        // Public build API waits for export/build/finalization internally.
        // Keep the user's Nanite settings and rebuild only the patched proxy.
        Subsystem->BuildNanite(UE::Landscape::EBuildFlags::ForceRebuild,OnlyThisLandscape);
        if(!Landscape->IsNaniteMeshUpToDate())return Done(TEXT("nanite_rebuild_incomplete_not_saved"));
    }
    TArray<uint16> Verified;Verified.SetNumZeroed(Current.Num());
    {
        FLandscapeEditDataInterface Edit(Info);
        Edit.GetHeightDataFast(X0,Y0,X1,Y1,Verified.GetData(),Width);
    }
    if(Verified!=Current)return Done(TEXT("heightmap_readback_mismatch_not_saved"));
    Report->SetBoolField(TEXT("applied"),true);
    Report->SetBoolField(TEXT("collision_rebuilt"),true);
    Report->SetBoolField(TEXT("nanite_enabled"),Landscape->IsNaniteEnabled());
    Report->SetStringField(TEXT("landscape"),Landscape->GetPathName());
    return Done(TEXT("exact_height_readback_verified_unsaved"));
}
