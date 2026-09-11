#include "HAL/IConsoleManager.h"
#include "HAL/FileManager.h"
#include "Materials/Material.h"
#include "Materials/MaterialExpression.h"
#include "Materials/MaterialExpressionMaterialFunctionCall.h"
#include "Materials/MaterialFunction.h"
#include "Misc/FileHelper.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/UnrealType.h"
#include "RaftSimLiquidOptics.h"
#include "Materials/MaterialInstanceConstant.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "NiagaraEmitter.h"
#include "NiagaraEmitterHandle.h"
#include "NiagaraRendererProperties.h"
#include "AssetCompilingManager.h"
#include "ShaderCompiler.h"
#include "UObject/StrongObjectPtr.h"
#include "UObject/UObjectIterator.h"

namespace
{
// Read-only source-graph evidence. Never edits an engine template or saves an asset.
FAutoConsoleCommand InspectLiquidMaterial(TEXT("RaftSim.InspectLiquidMaterial"),
    TEXT("Export the liquid SDF source graph and dependent functions to a new JSON file: material-path output-path."),
    FConsoleCommandWithArgsDelegate::CreateLambda([](const TArray<FString>& Args)
    {
        if (Args.Num()!=2 || IFileManager::Get().FileExists(*Args[1])) return;
        auto* Material=LoadObject<UMaterial>(nullptr,*Args[0]);
        if (!Material) { UE_LOG(LogTemp,Error,TEXT("Liquid material inspection: missing material"));return; }
        auto Report=MakeShared<FJsonObject>();
        Report->SetStringField(TEXT("material"),Material->GetPathName());
        Report->SetNumberField(TEXT("blend_mode"),Material->BlendMode);
        Report->SetNumberField(TEXT("shading_models"),Material->GetShadingModels().GetShadingModelField());
        Report->SetBoolField(TEXT("tangent_space_normal"),Material->bTangentSpaceNormal);
        auto Outputs=MakeShared<FJsonObject>();
        for (int32 Property=0;Property<MP_MAX;++Property)
            if (const auto* Input=Material->GetExpressionInputForProperty(static_cast<EMaterialProperty>(Property)))
            {
                auto Output=MakeShared<FJsonObject>();
                Output->SetStringField(TEXT("expression"),Input->Expression ? Input->Expression->GetPathName() : TEXT("null"));
                Output->SetNumberField(TEXT("output_index"),Input->OutputIndex);
                Outputs->SetObjectField(UEnum::GetValueAsString(static_cast<EMaterialProperty>(Property)),Output);
            }
        Report->SetObjectField(TEXT("outputs"),Outputs);
        TArray<TSharedPtr<FJsonValue>> Nodes;
        TSet<UMaterialExpression*> Visited;
        TFunction<void(UMaterialExpression*)> Visit=[&](UMaterialExpression* Expression)
        {
            if (!Expression || Visited.Contains(Expression)) return;
            Visited.Add(Expression);
            auto Node=MakeShared<FJsonObject>();
            Node->SetStringField(TEXT("path"),Expression->GetPathName());
            Node->SetStringField(TEXT("class"),Expression->GetClass()->GetName());
            auto Properties=MakeShared<FJsonObject>();
            for (TFieldIterator<FProperty> It(Expression->GetClass());It;++It)
            {
                FString Value;
                It->ExportText_InContainer(0,Value,Expression,nullptr,Expression,PPF_None);
                Properties->SetStringField(It->GetName(),Value);
            }
            Node->SetObjectField(TEXT("properties"),Properties);
            Nodes.Add(MakeShared<FJsonValueObject>(Node));
            if (auto* Call=Cast<UMaterialExpressionMaterialFunctionCall>(Expression))
                if (Call->MaterialFunction)
                    if (auto* Function=Call->MaterialFunction->GetBaseFunction())
                        for (const auto& Child:Function->GetExpressionCollection().Expressions) Visit(Child.Get());
        };
        for (const auto& Expression:Material->GetExpressionCollection().Expressions) Visit(Expression.Get());
        Report->SetArrayField(TEXT("nodes"),Nodes);
        Report->SetBoolField(TEXT("read_only"),true);
        FString Json;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Json));
        if (!FFileHelper::SaveStringToFile(Json,*Args[1]))
        { UE_LOG(LogTemp,Error,TEXT("Liquid material inspection: export failed")); }
        else
        { UE_LOG(LogTemp,Display,TEXT("Liquid material inspection: %d nodes exported"),Nodes.Num()); }
    }));

FAutoConsoleCommandWithWorldAndArgs InstallBaseScattering(TEXT("RaftSim.LiquidTerrainBaseScatteringReview"),
    TEXT("Unsaved base-scattering material on the transient outlet-stage candidate only."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World)
    {
        const bool Foam=Args.Num()==1 && Args[0]==TEXT("foam-world-frame");
        const bool WorldRay=Foam || (Args.Num()==1 && Args[0]==TEXT("world-frame"));
        const bool WorldNormal=WorldRay || (Args.Num()==1 && Args[0]==TEXT("world-normal"));
        if (!Args.IsEmpty() && !WorldNormal) return;
        for (TObjectIterator<UNiagaraComponent> It;It;++It)
        {
            auto* System=It->GetAsset();
            if (It->GetWorld()!=World || !System || System->GetOutermost()!=GetTransientPackage() ||
                !System->GetName().Contains(TEXT("_OutletStage_"))) continue;
            if (Foam && !System->GetName().Contains(TEXT("_Foam_"))) continue;
            TSet<UMaterialInstanceConstant*> Instances;
            for (const auto& Handle:System->GetEmitterHandles())
                // Spray has its own sprite material; only the primary emitter
                // owns the single SDF liquid surface whose optics we replace.
                if (Handle.GetIsEnabled() && Handle.GetName()==TEXT("Grid3D_FLIP_FluidControl_Emitter"))
                if (auto* Data=Handle.GetInstance().GetEmitterData())
                    for (auto* Renderer:Data->GetRenderers())
                        if (Renderer->GetIsEnabled())
                        {
                            TArray<UMaterialInterface*> Materials;Renderer->GetUsedMaterials(nullptr,Materials);
                            for (auto* Material:Materials)
                            {
                                auto* Instance=Cast<UMaterialInstanceConstant>(Material);
                                if (!Instance || Instance->GetOutermost()!=GetTransientPackage())
                                { UE_LOG(LogTemp,Error,TEXT("Refusing non-transient liquid material modification"));return; }
                                Instances.Add(Instance);
                            }
                        }
            if (Instances.Num()!=1)
            { UE_LOG(LogTemp,Error,TEXT("Expected one owned SDF material"));return; }
            auto* Instance=*Instances.CreateConstIterator();
            TStrongObjectPtr<UMaterial> Material(RaftSimCreateLiquidScatteringReview(Instance->GetMaterial()));
            if (!Material.IsValid())
            { UE_LOG(LogTemp,Error,TEXT("Unexpected liquid scattering source graph"));return; }
            if (WorldNormal && !RaftSimCorrectLiquidWorldNormal(Material.Get()))
            { UE_LOG(LogTemp,Error,TEXT("Unexpected grid-local normal source graph"));return; }
            if (WorldRay && !RaftSimCorrectLiquidRayFrame(Material.Get()))
            { UE_LOG(LogTemp,Error,TEXT("Unexpected local/world ray depth source graph"));return; }
            if (Foam && !RaftSimConnectLiquidFoamOptics(Material.Get()))
            { UE_LOG(LogTemp,Error,TEXT("Unexpected liquid surface foam source graph"));return; }
            TStrongObjectPtr<UMaterialInstanceConstant> Snapshot(NewObject<UMaterialInstanceConstant>(GetTransientPackage()));
            Snapshot->SetParentEditorOnly(Instance->GetMaterial(),false);
            Snapshot->CopyMaterialUniformParametersEditorOnly(Instance,false);
            Material->PostEditChange();
            Instance->SetParentEditorOnly(Material.Get());
            Instance->CopyMaterialUniformParametersEditorOnly(Snapshot.Get(),false);
            Instance->PostEditChange();
            FAssetCompilingManager::Get().FinishAllCompilation();
            if (GShaderCompilingManager) GShaderCompilingManager->FinishAllCompilation();
            It->MarkRenderStateDirty();
            UE_LOG(LogTemp,Display,TEXT("Advected foam surface optics=%d"),Foam);
            UE_LOG(LogTemp,Display,TEXT("Unsaved liquid base-scattering review installed; source tangent-space-normal=%d; world-normal-corrected=%d; world-ray-corrected=%d"),Material->bTangentSpaceNormal,WorldNormal,WorldRay);
            return;
        }
        UE_LOG(LogTemp,Error,TEXT("No transient outlet-stage candidate for optical review"));
    }));

FAutoConsoleCommandWithWorldAndArgs ScatteringControl(TEXT("RaftSim.LiquidTerrainScatteringControl"),
    TEXT("Unsaved optical controls: scattering coefficient multiplier (0..0.1 per cm), roughness (0..1)."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World)
    {
        float Strength=0,Roughness=0;
        if (Args.Num()!=2 || !LexTryParseString(Strength,*Args[0]) || !LexTryParseString(Roughness,*Args[1]) ||
            !FMath::IsFinite(Strength) || !FMath::IsFinite(Roughness) || Strength<0 || Strength>.1f || Roughness<0 || Roughness>1) return;
        for (TObjectIterator<UNiagaraComponent> It;It;++It)
            if (It->GetWorld()==World && It->GetAsset() && It->GetAsset()->GetName().Contains(TEXT("_OutletStage_")))
            {
                TArray<UMaterialInterface*> Materials;It->GetUsedMaterials(Materials);
                for (auto* Material:Materials)
                    if (auto* Dynamic=Cast<UMaterialInstanceDynamic>(Material))
                    {
                        if (!Dynamic->GetMaterial()->GetName().StartsWith(TEXT("M_RaftSimLiquidBaseScatteringReview"))) continue;
                        FLinearColor Scattering;
                        if (!Dynamic->GetVectorParameterValue(FMaterialParameterInfo(TEXT("Scattering")),Scattering)) continue;
                        Scattering.A=Strength;
                        Dynamic->SetVectorParameterValue(TEXT("Scattering"),Scattering);
                        Dynamic->SetScalarParameterValue(TEXT("River Roughness"),Roughness);
                    }
            }
    }));

FAutoConsoleCommandWithWorldAndArgs ExtinctionControl(TEXT("RaftSim.LiquidTerrainExtinctionControl"),
    TEXT("Transient optical comparison only: absorption RGB and scattering RGB (0..0.1 /cm), roughness (0..1)."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World)
    {
        if (Args.Num()!=7) return;
        float Values[7];
        for (int32 I=0;I<7;++I)
            if (!LexTryParseString(Values[I],*Args[I]) || !FMath::IsFinite(Values[I]) ||
                Values[I]<0 || Values[I]>(I==6 ? 1.f : .1f)) return;
        int32 Applied=0;
        for (TObjectIterator<UNiagaraComponent> It;It;++It)
            if (It->GetWorld()==World && It->GetAsset() &&
                It->GetAsset()->GetOutermost()==GetTransientPackage() &&
                It->GetAsset()->GetName().Contains(TEXT("_OutletStage_")))
            {
                TArray<UMaterialInterface*> Materials;It->GetUsedMaterials(Materials);
                for (auto* Material:Materials)
                    if (auto* Dynamic=Cast<UMaterialInstanceDynamic>(Material))
                    {
                        if (!Dynamic->GetMaterial()->GetName().StartsWith(TEXT("M_RaftSimLiquidBaseScatteringReview"))) continue;
                        // The source graph multiplies RGB by A. Unit A exposes
                        // explicit per-channel coefficients, not display colors.
                        Dynamic->SetVectorParameterValue(TEXT("Absorption"),FLinearColor(Values[0],Values[1],Values[2],1.f));
                        Dynamic->SetVectorParameterValue(TEXT("Scattering"),FLinearColor(Values[3],Values[4],Values[5],1.f));
                        Dynamic->SetScalarParameterValue(TEXT("River Roughness"),Values[6]);
                        ++Applied;
                    }
            }
        if (Applied==0) UE_LOG(LogTemp,Error,TEXT("No transient liquid material for extinction comparison"));
    }));

FAutoConsoleCommandWithWorldAndArgs FoamControl(TEXT("RaftSim.LiquidTerrainFoamControl"),
    TEXT("Unsaved foam strength control (0..8) on the transient foam candidate only."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World)
    {
        float Strength=0;
        if (Args.Num()!=1 || !LexTryParseString(Strength,*Args[0]) || !FMath::IsFinite(Strength) || Strength<0 || Strength>8) return;
        for (TObjectIterator<UNiagaraComponent> It;It;++It)
            if (It->GetWorld()==World && It->GetAsset() && It->GetAsset()->GetOutermost()==GetTransientPackage() && It->GetAsset()->GetName().Contains(TEXT("_Foam_")))
            {
                TArray<UMaterialInterface*> Materials;It->GetUsedMaterials(Materials);
                for (auto* Material:Materials)
                    if (auto* Dynamic=Cast<UMaterialInstanceDynamic>(Material))
                    {
                        Dynamic->SetScalarParameterValue(TEXT("River Foam Strength"),Strength);
                        float Applied=0,Tolerance=0,Voxel=0;
                        Dynamic->GetScalarParameterValue(FMaterialParameterInfo(TEXT("River Foam Strength")),Applied);
                        Dynamic->GetScalarParameterValue(FMaterialParameterInfo(TEXT("Tolerance")),Tolerance);
                        Dynamic->GetScalarParameterValue(FMaterialParameterInfo(TEXT("Voxel Size")),Voxel);
                        UE_LOG(LogTemp,Display,TEXT("Liquid foam optical control applied=%g inherited_tolerance=%g voxel_cm=%g material=%s"),Applied,Tolerance,Voxel,*Dynamic->GetPathName());
                    }
            }
    }));
}
