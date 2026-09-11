#include "RaftSimLiquidGridAllocation.h"
#include "HAL/IConsoleManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"
#include "NiagaraComponent.h"
#include "NiagaraSystemInstanceController.h"
#include "NiagaraDataInterfaceGrid3DCollection.h"
#include "NiagaraDataInterfaceRenderTargetVolume.h"
#include "RenderTargetPool.h"
#include "RenderingThread.h"
#include "RHICommandList.h"
#include "Materials/MaterialInterface.h"
#include "UObject/UObjectIterator.h"

namespace
{
UNiagaraComponent* AllocationComponent(UWorld* World,bool Installed)
{
    UNiagaraComponent* Found=nullptr;
    for (TObjectIterator<UNiagaraComponent> It;It;++It)
        if (It->GetWorld()==World && It->GetAsset() &&
            (Installed?It->GetAsset()->GetName().StartsWith(TEXT("SouthForkLiquidAllocationReview")):
                It->GetAsset()->GetName()==TEXT("NS_SouthForkLiquidTerrainReview")))
        { if (Found) return nullptr;Found=*It; }
    return Found;
}

FAutoConsoleCommandWithWorldAndArgs Install(TEXT("RaftSim.LiquidAllocationReview"),
    TEXT("Unsaved, zero-inlet grid-allocation diagnostic: NX NY NZ extentXcm extentYcm extentZcm."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World)
    {
        if (Args.Num()!=6) return;
        FIntVector Cells;FVector3f Extent;
        for (int32 A=0;A<3;++A)
            if (!LexTryParseString(Cells[A],*Args[A]) || !LexTryParseString(Extent[A],*Args[A+3])) return;
        auto* Component=AllocationComponent(World,false);
        if (!Component || !Component->GetComponentScale().Equals(FVector::OneVector,.00001)) return;
        auto* Candidate=DuplicateObject<UNiagaraSystem>(Component->GetAsset(),GetTransientPackage(),
            MakeUniqueObjectName(GetTransientPackage(),UNiagaraSystem::StaticClass(),TEXT("SouthForkLiquidAllocationReview")));
        FString Error;
        if (!RaftSimInstallLiquidGridAllocation(Candidate,Cells,Extent,Error))
        { UE_LOG(LogTemp,Error,TEXT("Explicit grid allocation failed: %s"),*Error);return; }
        auto& Store=Candidate->GetExposedParameters();
        Store.SetParameterValue<float>(0,FNiagaraVariable(FNiagaraTypeDefinition::GetFloatDef(),TEXT("User.Inlet Particle Rate")));
        const FNiagaraVariable Request(FNiagaraTypeDefinition::GetVec3Def(),TEXT("User.RaftSim Allocation Cells"));
        Store.AddParameter(Request);Store.SetParameterValue<FVector3f>(FVector3f(Cells),Request);
        Candidate->RequestCompile(true);Candidate->WaitForCompilationComplete(false,false);Candidate->WaitForCompilationComplete(true,false);
        if (!Candidate->IsReadyToRun()) { UE_LOG(LogTemp,Error,TEXT("Allocation candidate not ready"));return; }
        for (const auto& Handle:Candidate->GetEmitterHandles())
            if (Handle.GetIsEnabled()) if (const auto* Data=Handle.GetInstance().GetEmitterData())
            {
                TArray<UNiagaraScript*> Scripts;Data->GetScripts(Scripts,false);
                for (const auto* Script:Scripts)
                    if (Script->GetUsage()==ENiagaraScriptUsage::ParticleGPUComputeScript && !Script->DidScriptCompilationSucceed(true))
                    { UE_LOG(LogTemp,Error,TEXT("Allocation GPU shader compilation failed"));return; }
            }
        Component->SetAsset(Candidate);
        UE_LOG(LogTemp,Display,TEXT("Independent allocation installed %s / %s cm; zero inlet, no physics acceptance or saved assets"),*Cells.ToString(),*Extent.ToString());
    }));

FAutoConsoleCommandWithWorldAndArgs Report(TEXT("RaftSim.LiquidAllocationReport"),
    TEXT("Record actual native grid and GPU texture allocations in a new JSON file."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World)
    {
        if (Args.Num()!=1 || FPaths::FileExists(Args[0])) return;
        auto* Component=AllocationComponent(World,true);
        if (!Component || !Component->GetSystemInstanceController()) return;
        const auto Id=Component->GetSystemInstanceController()->GetSystemInstanceID();
        const auto& Store=Component->GetAsset()->GetExposedParameters();
        const auto C=Store.GetParameterValue<FVector3f>(FNiagaraVariable(FNiagaraTypeDefinition::GetVec3Def(),TEXT("User.RaftSim Allocation Cells")));
        const FIntVector Expected(int32(C.X),int32(C.Y),int32(C.Z));
        const auto ExpectedExtent=Store.GetParameterValue<FVector3f>(FNiagaraVariable(FNiagaraTypeDefinition::GetVec3Def(),TEXT("User.World Grid Extents")));
        const auto Vector=[](FIntVector V) { return TArray<TSharedPtr<FJsonValue>>{
            MakeShared<FJsonValueNumber>(V.X),MakeShared<FJsonValueNumber>(V.Y),MakeShared<FJsonValueNumber>(V.Z)}; };
        FlushRenderingCommands();
        auto Json=MakeShared<FJsonObject>();TArray<TSharedPtr<FJsonValue>> Grids,Volumes;
        int32 SolverCount=0,RenderCount=0;bool Consistent=true;
        for (TObjectIterator<UNiagaraDataInterfaceGrid3DCollection> It;It;++It)
        {
            if (It->GetClass()!=UNiagaraDataInterfaceGrid3DCollection::StaticClass()) continue;
            const auto* const* Found=It->GetSystemInstancesToProxyData_GT().Find(Id);
            if (!Found || !*Found || (*Found)->Vars.IsEmpty()) continue;
            auto* Proxy=static_cast<FNiagaraDataInterfaceProxyGrid3DCollectionProxy*>(It->GetProxy());
            FIntVector Cells=FIntVector::ZeroValue,TextureSize=FIntVector::ZeroValue;
            ENQUEUE_RENDER_COMMAND(RaftSimAllocationSize)([&](FRHICommandListImmediate&)
            {
                auto* Data=Proxy->SystemInstancesToProxyData_RT.Find(Id);
                if (!Data || !Data->CurrentData || !Data->CurrentData->IsValid()) return;
                Cells=Data->NumCells;const auto& D=Data->CurrentData->GetPooledTexture()->GetRHI()->GetDesc();
                TextureSize=FIntVector(D.Extent.X,D.Extent.Y,D.Depth);
            });
            FlushRenderingCommands();
            if (TextureSize==FIntVector::ZeroValue) continue;
            auto G=MakeShared<FJsonObject>();G->SetStringField(TEXT("interface"),It->GetPathName());
            G->SetArrayField(TEXT("game_thread_cells"),Vector((*Found)->NumCells));G->SetArrayField(TEXT("render_thread_cells"),Vector(Cells));
            G->SetArrayField(TEXT("actual_texture_size"),Vector(TextureSize));
            G->SetStringField(TEXT("cell_size_cm"),(*Found)->CellSize.ToString());
            G->SetStringField(TEXT("world_bbox_cm"),(*Found)->WorldBBoxSize.ToString());
            Consistent &= Cells==(*Found)->NumCells && (Cells==Expected || Cells==Expected*2);
            SolverCount+=Cells==Expected;RenderCount+=Cells==Expected*2;Grids.Add(MakeShared<FJsonValueObject>(G));
        }
        int32 RenderTargets=0;
        for (TObjectIterator<UNiagaraDataInterfaceRenderTargetVolume> It;It;++It)
        {
            auto* Proxy=static_cast<FNiagaraDataInterfaceProxyRenderTargetVolumeProxy*>(It->GetProxy());
            FIntVector Size=FIntVector::ZeroValue;
            ENQUEUE_RENDER_COMMAND(RaftSimAllocationVolume)([&](FRHICommandListImmediate&)
            {
                auto* Data=Proxy->SystemInstancesToProxyData_RT.Find(Id);
                if (!Data || !Data->RenderTarget.IsValid()) return;
                const auto& D=Data->RenderTarget->GetRHI()->GetDesc();Size=FIntVector(D.Extent.X,D.Extent.Y,D.Depth);
            });
            FlushRenderingCommands();
            if (Size==FIntVector::ZeroValue) continue;
            auto V=MakeShared<FJsonObject>();V->SetStringField(TEXT("interface"),It->GetPathName());V->SetArrayField(TEXT("actual_texture_size"),Vector(Size));
            Volumes.Add(MakeShared<FJsonValueObject>(V));Consistent &= Size==Expected*2;RenderTargets+=Size==Expected*2;
        }
        Json->SetArrayField(TEXT("expected_cells"),Vector(Expected));Json->SetArrayField(TEXT("grids"),Grids);Json->SetArrayField(TEXT("volumes"),Volumes);
        Json->SetNumberField(TEXT("solver_grid_count"),SolverCount);Json->SetNumberField(TEXT("render_grid_count"),RenderCount);Json->SetNumberField(TEXT("render_target_count"),RenderTargets);
        // Grid DI bbox defaults are not the fluid's physical transform. Check
        // the actual SDF renderer binding as well as allocated texture sizes.
        TArray<UMaterialInterface*> Materials;Component->GetUsedMaterials(Materials);
        TSet<UMaterialInterface*> Seen;int32 BoundSurfaces=0;bool FrameValid=true;
        auto Bindings=MakeShared<FJsonObject>();
        for (auto* Material:Materials)
        {
            if (!Material || Seen.Contains(Material)) continue;Seen.Add(Material);
            FLinearColor Extent;
            if (!Material->GetVectorParameterValue(FMaterialParameterInfo(TEXT("WorldGridExtents")),Extent)) continue;
            ++BoundSurfaces;Bindings->SetStringField(TEXT("WorldGridExtents"),Extent.ToString());
            FrameValid &= FVector3f(Extent.R,Extent.G,Extent.B).Equals(ExpectedExtent,.001f);
            for (int32 Axis=0;Axis<4;++Axis)
            {
                const FName Name(*FString::Printf(TEXT("LocalToWorld%d"),Axis));FLinearColor Row;
                if (!Material->GetVectorParameterValue(FMaterialParameterInfo(Name),Row)) { FrameValid=false;continue; }
                const FVector Actual(Row.R,Row.G,Row.B);
                const FVector ExpectedRow=Axis<3?Component->GetComponentTransform().GetUnitAxis(EAxis::Type(Axis+1)):
                    Component->GetComponentLocation()+Component->GetUpVector()*(ExpectedExtent.Z*.5);
                FrameValid &= Actual.Equals(ExpectedRow,.001);
                Bindings->SetStringField(Name.ToString(),Row.ToString());
            }
        }
        Json->SetObjectField(TEXT("actual_material_bindings"),Bindings);
        Json->SetBoolField(TEXT("physical_frame_verified"),FrameValid && BoundSurfaces==1);
        Json->SetBoolField(TEXT("allocation_verified"),Consistent && SolverCount>=3 && RenderTargets>=1 && FrameValid && BoundSurfaces==1);
        Json->SetBoolField(TEXT("physical_visual_or_performance_acceptance"),false);
        FString Text;FJsonSerializer::Serialize(Json,TJsonWriterFactory<>::Create(&Text));FFileHelper::SaveStringToFile(Text,*Args[0]);
    }));
}
