#include "HAL/IConsoleManager.h"
#include "HAL/FileManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "NiagaraSystemInstanceController.h"
#include "NiagaraDataInterfaceGrid3DCollection.h"
#include "NiagaraDataInterfaceRenderTargetVolume.h"
#include "RenderTargetPool.h"
#include "RenderingThread.h"
#include "RHICommandList.h"
#include "RHIGPUReadback.h"
#include "UObject/UObjectIterator.h"

namespace
{
FAutoConsoleCommandWithWorldAndArgs GridReadbackCommand(TEXT("RaftSim.LiquidGridReadback"),
    TEXT("Blocking diagnostic readback of actual live liquid grid textures; new output directory required."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World)
    {
        if (Args.Num()!=1 || FPaths::DirectoryExists(Args[0])) return;
        UNiagaraComponent* Component=nullptr;
        for (TObjectIterator<UNiagaraComponent> It;It;++It)
            if (It->GetWorld()==World && It->GetAsset() && It->GetAsset()->GetName().Contains(TEXT("_DrivenBoundary_")))
            { if (Component) { UE_LOG(LogTemp,Error,TEXT("Ambiguous liquid grid component"));return; }Component=*It; }
        if (!Component || !Component->GetSystemInstanceController()) return;
        const auto Id=Component->GetSystemInstanceController()->GetSystemInstanceID();
        FlushRenderingCommands();
        IFileManager::Get().MakeDirectory(*Args[0],true);
        auto Report=MakeShared<FJsonObject>();
        Report->SetStringField(TEXT("asset"),Component->GetAsset()->GetPathName());
        Report->SetBoolField(TEXT("blocking_gpu_readback"),true);
        Report->SetStringField(TEXT("encoding"),TEXT("per-grid encoding; X fastest then Y then Z; original float32 pressure, float16 RGBA for half-float sources"));
        bool PressureValid=false;
        const int32 PressureIterations=Component->GetVariableInt(TEXT("User.Pressure Iterations"),PressureValid);
        Report->SetBoolField(TEXT("pressure_iterations_valid"),PressureValid);
        Report->SetNumberField(TEXT("pressure_iterations"),PressureIterations);
        TArray<TSharedPtr<FJsonValue>> Grids;
        for (TObjectIterator<UNiagaraDataInterfaceGrid3DCollection> It;It;++It)
        {
            if (It->GetClass()!=UNiagaraDataInterfaceGrid3DCollection::StaticClass()) continue;
            const auto* const* Found=It->GetSystemInstancesToProxyData_GT().Find(Id);
            if (!Found || !*Found) continue;
            const auto* Data=*Found;
            // Disabled high-precision stages retain unallocated 3-cell DIs.
            // They are not solver grids and have no live GPU texture to read.
            if (Data->Vars.IsEmpty() || Data->NumCells.X<64 || Data->NumCells.Y<64) continue;
            auto G=MakeShared<FJsonObject>();
            G->SetStringField(TEXT("interface"),It->GetPathName());
            const auto IntVector=[](FIntVector V)
            { return TArray<TSharedPtr<FJsonValue>>{MakeShared<FJsonValueNumber>(V.X),MakeShared<FJsonValueNumber>(V.Y),MakeShared<FJsonValueNumber>(V.Z)}; };
            G->SetArrayField(TEXT("cells"),IntVector(Data->NumCells));
            G->SetArrayField(TEXT("tiles"),IntVector(Data->NumTiles));
            G->SetStringField(TEXT("interface_cell_size"),Data->CellSize.ToString());
            G->SetStringField(TEXT("interface_bbox_size"),Data->WorldBBoxSize.ToString());
            G->SetBoolField(TEXT("rgba_texture"),Data->UseRGBATexture);
            TArray<TSharedPtr<FJsonValue>> Attributes;
            for (int32 Index=0;Index<Data->Vars.Num();++Index)
            {
                auto A=MakeShared<FJsonObject>();A->SetStringField(TEXT("name"),Data->Vars[Index].GetName().ToString());
                A->SetStringField(TEXT("type"),Data->Vars[Index].GetType().GetName());
                A->SetNumberField(TEXT("offset"),Data->Offsets.IsValidIndex(Index)?Data->Offsets[Index]:-1);
                Attributes.Add(MakeShared<FJsonValueObject>(A));
            }
            G->SetArrayField(TEXT("attributes"),Attributes);
            auto* Proxy=static_cast<FNiagaraDataInterfaceProxyGrid3DCollectionProxy*>(It->GetProxy());
            TArray<FFloat16Color> Pixels;TArray<uint8> RawFloat;FIntVector Size=FIntVector::ZeroValue;int32 Format=PF_Unknown;
            ENQUEUE_RENDER_COMMAND(RaftSimReadLiquidGrid)([Proxy,Id,&Pixels,&RawFloat,&Size,&Format](FRHICommandListImmediate& RHICmdList)
            {
                auto* RT=Proxy->SystemInstancesToProxyData_RT.Find(Id);
                if (!RT || !RT->CurrentData || !RT->CurrentData->IsValid()) return;
                auto* Texture=RT->CurrentData->GetPooledTexture()->GetRHI();
                const auto& Desc=Texture->GetDesc();Size=FIntVector(Desc.Extent.X,Desc.Extent.Y,Desc.Depth);Format=Desc.Format;
                if (int64(Size.X)*Size.Y*Size.Z>8000000 ||
                    (Format!=PF_R16F && Format!=PF_R32_FLOAT && Format!=PF_FloatRGBA)) return;
                if (Format==PF_R32_FLOAT)
                {
                    // Pressure exceeds half-float range. Copy original float32
                    // bytes, one volume slice at a time, without conversion.
                    RawFloat.SetNumUninitialized(Size.X*Size.Y*Size.Z*sizeof(float));
                    RHICmdList.Transition(FRHITransitionInfo(Texture,ERHIAccess::Unknown,ERHIAccess::CopySrc));
                    for (int32 Z=0;Z<Size.Z;++Z)
                    {
                        FRHIGPUTextureReadback Readback(TEXT("RaftSimLiquidPressure"));
                        Readback.EnqueueCopy(RHICmdList,Texture,FIntVector(0,0,Z),0,FIntVector(Size.X,Size.Y,1));
                        RHICmdList.SubmitAndBlockUntilGPUIdle();
                        int32 Pitch=0;const auto* Source=static_cast<const uint8*>(Readback.Lock(Pitch));
                        if (!Source || Pitch<Size.X) { RawFloat.Empty();break; }
                        for (int32 Y=0;Y<Size.Y;++Y)
                            FMemory::Memcpy(RawFloat.GetData()+(Z*Size.Y+Y)*Size.X*sizeof(float),Source+Y*Pitch*sizeof(float),Size.X*sizeof(float));
                        Readback.Unlock();
                    }
                    RHICmdList.Transition(FRHITransitionInfo(Texture,ERHIAccess::CopySrc,ERHIAccess::SRVMask));
                }
                else RHICmdList.Read3DSurfaceFloatData(Texture,FIntRect(0,0,Size.X,Size.Y),FIntPoint(0,Size.Z),Pixels);
            });
            FlushRenderingCommands();
            G->SetArrayField(TEXT("texture_size"),IntVector(Size));G->SetNumberField(TEXT("pixel_format"),Format);
            G->SetNumberField(TEXT("pixel_count"),Format==PF_R32_FLOAT ? RawFloat.Num()/sizeof(float) : Pixels.Num());
            G->SetStringField(TEXT("encoding"),Format==PF_R32_FLOAT?TEXT("r32f"):TEXT("rgba16f"));
            const FString File=FString::Printf(TEXT("grid_%02d.%s"),Grids.Num(),Format==PF_R32_FLOAT?TEXT("r32f"):TEXT("rgba16f"));
            TArray<uint8> Bytes=MoveTemp(RawFloat);
            if (Bytes.IsEmpty()) Bytes.Append(reinterpret_cast<const uint8*>(Pixels.GetData()),Pixels.Num()*sizeof(FFloat16Color));
            const bool Saved=!Bytes.IsEmpty() && FFileHelper::SaveArrayToFile(Bytes,*(Args[0]/File));
            G->SetBoolField(TEXT("readback_saved"),Saved);G->SetStringField(TEXT("file"),File);
            Grids.Add(MakeShared<FJsonValueObject>(G));
        }
        Report->SetArrayField(TEXT("grids"),Grids);Report->SetNumberField(TEXT("grid_count"),Grids.Num());
        TArray<TSharedPtr<FJsonValue>> Volumes;
        for (TObjectIterator<UNiagaraDataInterfaceRenderTargetVolume> It;It;++It)
        {
            auto* Proxy=static_cast<FNiagaraDataInterfaceProxyRenderTargetVolumeProxy*>(It->GetProxy());
            TArray<FFloat16Color> Pixels;FIntVector Size=FIntVector::ZeroValue;int32 Format=PF_Unknown;
            ENQUEUE_RENDER_COMMAND(RaftSimReadLiquidVolume)([Proxy,Id,&Pixels,&Size,&Format](FRHICommandListImmediate& RHICmdList)
            {
                auto* Data=Proxy->SystemInstancesToProxyData_RT.Find(Id);
                if (!Data || !Data->RenderTarget.IsValid()) return;
                auto* Texture=Data->RenderTarget->GetRHI();
                const auto& Desc=Texture->GetDesc();Size=FIntVector(Desc.Extent.X,Desc.Extent.Y,Desc.Depth);Format=Desc.Format;
                if (int64(Size.X)*Size.Y*Size.Z>8000000 ||
                    (Format!=PF_R16F && Format!=PF_FloatRGBA)) return;
                RHICmdList.Read3DSurfaceFloatData(Texture,FIntRect(0,0,Size.X,Size.Y),FIntPoint(0,Size.Z),Pixels);
            });
            FlushRenderingCommands();
            if (Format==PF_Unknown) continue;
            auto V=MakeShared<FJsonObject>();V->SetStringField(TEXT("interface"),It->GetPathName());
            V->SetNumberField(TEXT("pixel_format"),Format);
            V->SetArrayField(TEXT("size"),{MakeShared<FJsonValueNumber>(Size.X),MakeShared<FJsonValueNumber>(Size.Y),MakeShared<FJsonValueNumber>(Size.Z)});
            V->SetBoolField(TEXT("override_format"),It->bOverrideFormat);
            V->SetNumberField(TEXT("configured_format"),It->OverrideRenderTargetFormat);
            V->SetNumberField(TEXT("filter"),It->OverrideRenderTargetFilter);
            const FString File=FString::Printf(TEXT("volume_%02d.rgba16f"),Volumes.Num());
            TArray<uint8> Bytes;Bytes.Append(reinterpret_cast<const uint8*>(Pixels.GetData()),Pixels.Num()*sizeof(FFloat16Color));
            V->SetBoolField(TEXT("readback_saved"),!Bytes.IsEmpty() && FFileHelper::SaveArrayToFile(Bytes,*(Args[0]/File)));
            V->SetStringField(TEXT("file"),File);Volumes.Add(MakeShared<FJsonValueObject>(V));
        }
        Report->SetArrayField(TEXT("render_target_volumes"),Volumes);
        FString Text;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Text));
        FFileHelper::SaveStringToFile(Text,*(Args[0]/TEXT("grids.json")));
        UE_LOG(LogTemp,Display,TEXT("Liquid grid readback exported %d interfaces"),Grids.Num());
    }));
}
