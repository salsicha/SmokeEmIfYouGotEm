#include "HAL/IConsoleManager.h"
#include "HAL/FileManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"
#include "Engine/VolumeTexture.h"
#include "Engine/TextureRenderTargetVolume.h"
#include "RaftSimLiquidRedistanceGPU.h"
#include "RaftSimLiquidDensityGPU.h"
#include "RenderGraphBuilder.h"
#include "RenderGraphUtils.h"
#include "RHIGPUReadback.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "RenderingThread.h"
#include "RHICommandList.h"
#include "TextureResource.h"
#include "UObject/StrongObjectPtr.h"
#include "UObject/UObjectIterator.h"

namespace
{
FAutoConsoleCommand DensityReview(TEXT("RaftSim.LiquidDensityGPUReview"),
    TEXT("GPU reconstruct captured particle field: input-dir unused-output-dir. Diagnostic only."),
    FConsoleCommandWithArgsDelegate::CreateLambda([](const TArray<FString>& Args)
    {
        if (Args.Num()!=2) return;
        const FString Root=FPaths::ConvertRelativePathToFull(FPaths::ProjectDir()/TEXT("../docs/reconstruction-review-2026-09-07"));
        const FString Source=FPaths::ConvertRelativePathToFull(Args[0]),Output=FPaths::ConvertRelativePathToFull(Args[1]);
        if (!FPaths::IsUnderDirectory(Source,Root) || !FPaths::IsUnderDirectory(Output,Root) ||
            IFileManager::Get().DirectoryExists(*Output) || IFileManager::Get().FileExists(*Output)) return;
        FString Text;TSharedPtr<FJsonObject> Manifest;
        if (!FFileHelper::LoadFileToString(Text,*(Source/TEXT("report.json"))) ||
            !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Manifest) || !Manifest.IsValid()) return;
        const int32 Count=Manifest->GetIntegerField(TEXT("count"));
        if (Count<1 || Count>262144) return;
        const auto& Min=Manifest->GetArrayField(TEXT("minimum_m"));const auto& Ext=Manifest->GetArrayField(TEXT("extent_m"));
        const auto& Size=Manifest->GetArrayField(TEXT("grid_cells"));
        if (Min.Num()!=3 || Ext.Num()!=3 || Size.Num()!=3) return;
        const FVector3f Minimum(Min[0]->AsNumber(),Min[1]->AsNumber(),Min[2]->AsNumber());
        const FVector3f Extent(Ext[0]->AsNumber(),Ext[1]->AsNumber(),Ext[2]->AsNumber());
        const FIntVector Cells(Size[0]->AsNumber(),Size[1]->AsNumber(),Size[2]->AsNumber());
        const float Radius=Manifest->GetNumberField(TEXT("radius_m")),Footprint=Manifest->GetNumberField(TEXT("footprint_m"));
        TArray<uint8> Input;
        if (!FFileHelper::LoadFileToArray(Input,*(Source/TEXT("positions.rgba32f"))) || Input.Num()!=Count*sizeof(FVector4f)) return;
        const auto* Points=reinterpret_cast<const FVector4f*>(Input.GetData());
        for (int32 I=0;I<Count;++I) if (Points[I].ContainsNaN()) return;
        TArray<uint8> Kernels,Density,Status,ScalarReadback;
        FString Error;bool Success=false;double GPUMilliseconds=-1;
        ENQUEUE_RENDER_COMMAND(RaftSimParticleDensityReview)([&](FRHICommandListImmediate& Cmd)
        {
            FRDGBuilder Graph(Cmd);
            auto Positions=CreateStructuredBuffer(Graph,TEXT("LiquidDensity.CapturedPositions"),TConstArrayView<FVector4f>(Points,Count));
            const auto Result=RaftSimLiquidDensityGPU(Graph,Positions,Count,nullptr,0,Minimum,Extent,Cells,Radius,Footprint,Error);
            if (!Result.Scalar) return;
            FRHIGPUBufferReadback KernelRead(TEXT("LiquidDensity.KernelReadback")),DensityRead(TEXT("LiquidDensity.DensityReadback")),StatusRead(TEXT("LiquidDensity.StatusReadback"));
            const uint32 KernelBytes=Count*3*sizeof(FVector4f),DensityBytes=Cells.X*Cells.Y*Cells.Z*sizeof(uint32);
            AddEnqueueCopyPass(Graph,&KernelRead,Result.KernelRows,KernelBytes);
            AddEnqueueCopyPass(Graph,&DensityRead,Result.DensityFixed,DensityBytes);
            AddEnqueueCopyPass(Graph,&StatusRead,Result.Diagnostics,4*sizeof(uint32));
            TRefCountPtr<IPooledRenderTarget> ScalarTexture;
            Graph.QueueTextureExtraction(Result.Scalar,&ScalarTexture);
            FRenderQueryPoolRHIRef Pool;FRHIPooledRenderQuery Begin,End;
            if (GSupportsTimestampRenderQueries)
            { Pool=RHICreateRenderQueryPool(RQT_AbsoluteTime,2);Begin=Pool->AllocateQuery();End=Pool->AllocateQuery();Cmd.EndRenderQuery(Begin.GetQuery()); }
            Graph.Execute();
            if (Pool) Cmd.EndRenderQuery(End.GetQuery());
            Cmd.SubmitAndBlockUntilGPUIdle();
            if (Pool)
            {
                uint64 A=0,B=0;
                if (RHIGetRenderQueryResult(Begin.GetQuery(),A,true) && RHIGetRenderQueryResult(End.GetQuery(),B,true) && B>=A) GPUMilliseconds=(B-A)/1000.;
            }
            auto Copy=[&](FRHIGPUBufferReadback& Read,uint32 Bytes,TArray<uint8>& Destination)
            { const auto* Data=static_cast<const uint8*>(Read.Lock(Bytes));if (Data) Destination.Append(Data,Bytes);Read.Unlock(); };
            Copy(KernelRead,KernelBytes,Kernels);Copy(DensityRead,DensityBytes,Density);Copy(StatusRead,4*sizeof(uint32),Status);
            // Read3DSurfaceFloatData converts R32f into half floats. Preserve
            // original R32f bytes here; the parity gate must not test lossy IO.
            auto* ScalarRHI=ScalarTexture->GetRHI();ScalarReadback.SetNumUninitialized(DensityBytes);
            Cmd.Transition(FRHITransitionInfo(ScalarRHI,ERHIAccess::Unknown,ERHIAccess::CopySrc));
            for (int32 Z=0;Z<Cells.Z;++Z)
            {
                FRHIGPUTextureReadback Slice(TEXT("LiquidDensity.ScalarSlice"));
                Slice.EnqueueCopy(Cmd,ScalarRHI,FIntVector(0,0,Z),0,FIntVector(Cells.X,Cells.Y,1));
                Cmd.SubmitAndBlockUntilGPUIdle();int32 Pitch=0;
                const auto* Bytes=static_cast<const uint8*>(Slice.Lock(Pitch));
                if (!Bytes || Pitch<Cells.X) { ScalarReadback.Empty();if (Bytes) Slice.Unlock();break; }
                for (int32 Y=0;Y<Cells.Y;++Y)
                    FMemory::Memcpy(ScalarReadback.GetData()+(Z*Cells.Y+Y)*Cells.X*sizeof(float),Bytes+Y*Pitch*sizeof(float),Cells.X*sizeof(float));
                Slice.Unlock();
            }
            Cmd.Transition(FRHITransitionInfo(ScalarRHI,ERHIAccess::CopySrc,ERHIAccess::SRVMask));
            Success=Kernels.Num()==KernelBytes && Density.Num()==DensityBytes && Status.Num()==16 && ScalarReadback.Num()==DensityBytes;
        });
        FlushRenderingCommands();
        if (!Success) { UE_LOG(LogTemp,Error,TEXT("Particle density review failed: %s"),*Error);return; }
        if (!IFileManager::Get().MakeDirectory(*Output,true)) return;
        if (!FFileHelper::SaveArrayToFile(Input,*(Output/TEXT("positions.rgba32f"))) ||
            !FFileHelper::SaveArrayToFile(Kernels,*(Output/TEXT("kernels.rgba32f"))) ||
            !FFileHelper::SaveArrayToFile(Density,*(Output/TEXT("density.u32")))) return;
        if (!FFileHelper::SaveArrayToFile(ScalarReadback,*(Output/TEXT("scalar_readback.r32f")))) return;
        auto Report=MakeShared<FJsonObject>();Report->SetStringField(TEXT("source_directory"),Source);
        Report->SetNumberField(TEXT("particle_count"),Count);Report->SetNumberField(TEXT("fixed_point_scale"),1048576);
        TArray<TSharedPtr<FJsonValue>> Values;
        for (int32 I=0;I<4;++I) Values.Add(MakeShared<FJsonValueNumber>(reinterpret_cast<const uint32*>(Status.GetData())[I]));
        Report->SetArrayField(TEXT("diagnostics"),Values);
        Report->SetNumberField(TEXT("gpu_dispatch_and_diagnostic_copy_ms"),GPUMilliseconds);
        Report->SetBoolField(TEXT("live_particle_source_connected"),false);
        Report->SetBoolField(TEXT("physical_or_visual_acceptance"),false);
        FString Json;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Json));
        FFileHelper::SaveStringToFile(Json,*(Output/TEXT("report.json")));
        UE_LOG(LogTemp,Display,TEXT("GPU particle covariance/density reconstructed %d captured particles; not live integration"),Count);
    }));

// Frozen, offline-generated geometry comparison only. Does not change SimRT,
// particle positions, simulation stages, saved materials or production assets.
FAutoConsoleCommandWithWorldAndArgs SurfaceSnapshot(TEXT("RaftSim.LiquidSurfaceSnapshotReview"),
    TEXT("Bind verified offline distance snapshot to one frozen transient liquid material: source-dir new-report-dir."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World)
    {
        if (Args.Num()!=2) return;
        const FString Root=FPaths::ConvertRelativePathToFull(FPaths::ProjectDir()/TEXT("../docs/reconstruction-review-2026-09-07"));
        const FString Source=FPaths::ConvertRelativePathToFull(Args[0]);
        const FString Output=FPaths::ConvertRelativePathToFull(Args[1]);
        if (!FPaths::IsUnderDirectory(Source,Root) || !FPaths::IsUnderDirectory(Output,Root) ||
            IFileManager::Get().DirectoryExists(*Output) || IFileManager::Get().FileExists(*Output))
        { UE_LOG(LogTemp,Error,TEXT("Surface snapshot requires scoped source and unused output directory"));return; }
        FString Text;TSharedPtr<FJsonObject> Manifest;
        if (!FFileHelper::LoadFileToString(Text,*(Source/TEXT("report.json"))) ||
            !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Manifest) || !Manifest.IsValid()) return;
        const TArray<TSharedPtr<FJsonValue>> *Cells=nullptr,*Minimum=nullptr,*Extents=nullptr;
        if (!Manifest->TryGetArrayField(TEXT("grid_cells"),Cells) || Cells->Num()!=3 ||
            !Manifest->TryGetArrayField(TEXT("minimum_m"),Minimum) || Minimum->Num()!=3 ||
            !Manifest->TryGetArrayField(TEXT("extent_m"),Extents) || Extents->Num()!=3) return;
        const int32 ExpectedCells[]={136,136,48};const double ExpectedMin[]={-11.15625,-11.15625,0};
        const double ExpectedExtent[]={22.3125,22.3125,8};
        for (int32 Axis=0;Axis<3;++Axis)
            if ((*Cells)[Axis]->AsNumber()!=ExpectedCells[Axis] ||
                !FMath::IsNearlyEqual((*Minimum)[Axis]->AsNumber(),ExpectedMin[Axis],1.e-8) ||
                !FMath::IsNearlyEqual((*Extents)[Axis]->AsNumber(),ExpectedExtent[Axis],1.e-8)) return;
        FString Kind;
        if (!Manifest->TryGetStringField(TEXT("distance_reference"),Kind) ||
            (Kind!=TEXT("nearest piecewise-linear tetrahedron isosurface triangle, truncated narrow band") &&
             Kind!=TEXT("captured renderer SDF, unchanged red channel") &&
             Kind!=TEXT("upwind Eikonal narrow band with gradient-corrected subcell seeds"))) return;
        const bool GPUReconstruction=Kind==TEXT("upwind Eikonal narrow band with gradient-corrected subcell seeds");
        TArray<uint8> Bytes;
        constexpr int32 Count=136*136*48;
        if (!FFileHelper::LoadFileToArray(Bytes,*(Source/TEXT("surface.rgba16f"))) ||
            Bytes.Num()!=Count*sizeof(FFloat16Color)) return;
        const auto* Values=reinterpret_cast<const FFloat16Color*>(Bytes.GetData());
        bool Positive=false,Negative=false;
        for (int32 I=0;I<Count;++I)
        {
            const FLinearColor Value=Values[I].GetFloats();
            if (!FMath::IsFinite(Value.R) || FMath::Abs(Value.R)>50.01f || Value.G!=0 || Value.B!=0 || Value.A!=0)
            { UE_LOG(LogTemp,Error,TEXT("Surface snapshot must be finite metric distance with empty foam channel"));return; }
            Positive|=Value.R>0;Negative|=Value.R<0;
        }
        if (!Positive || !Negative) return;
        TSet<UMaterialInstanceDynamic*> Materials;int32 Components=0;
        for (TObjectIterator<UNiagaraComponent> It;It;++It)
        {
            auto* System=It->GetAsset();
            if (It->GetWorld()!=World || !System || System->GetOutermost()!=GetTransientPackage() ||
                !System->GetName().Contains(TEXT("_Foam_"))) continue;
            if (It->IsComponentTickEnabled())
            { UE_LOG(LogTemp,Error,TEXT("Surface snapshot refuses a ticking simulation"));return; }
            ++Components;
            TArray<UMaterialInterface*> Used;It->GetUsedMaterials(Used);
            for (auto* Material:Used)
                if (auto* Dynamic=Cast<UMaterialInstanceDynamic>(Material)) Materials.Add(Dynamic);
        }
        if (Components!=1 || Materials.Num()!=1) return;
        auto* Material=*Materials.CreateConstIterator();
        UTexture* Previous=nullptr;FLinearColor GridExtents;
        if (!Material->GetTextureParameterValue(FMaterialParameterInfo(TEXT("VolumeTex")),Previous) || !Previous ||
            !Material->GetVectorParameterValue(FMaterialParameterInfo(TEXT("WorldGridExtents")),GridExtents) ||
            !FMath::IsNearlyEqual(GridExtents.R,2231.25f) || !FMath::IsNearlyEqual(GridExtents.G,2231.25f) ||
            !FMath::IsNearlyEqual(GridExtents.B,800.f)) return;
        TStrongObjectPtr<UTexture> Texture;
        TStrongObjectPtr<UVolumeTexture> ScalarSource;
        if (GPUReconstruction)
        {
            TArray<uint8> Scalars;
            if (!FFileHelper::LoadFileToArray(Scalars,*(Source/TEXT("input_phi.r32f"))) || Scalars.Num()!=Count*sizeof(float)) return;
            const auto* InputValues=reinterpret_cast<const float*>(Scalars.GetData());
            for (int32 I=0;I<Count;++I) if (!FMath::IsFinite(InputValues[I])) return;
            ScalarSource.Reset(UVolumeTexture::CreateTransient(136,136,48,PF_R32_FLOAT));
            if (!ScalarSource.IsValid()) return;
            ScalarSource->SRGB=false;ScalarSource->NeverStream=true;
            auto& Mip=ScalarSource->GetPlatformData()->Mips[0];
            void* Data=Mip.BulkData.Lock(LOCK_READ_WRITE);FMemory::Memcpy(Data,Scalars.GetData(),Scalars.Num());Mip.BulkData.Unlock();
            ScalarSource->UpdateResource();
            auto* Target=NewObject<UTextureRenderTargetVolume>(GetTransientPackage(),
                MakeUniqueObjectName(GetTransientPackage(),UTextureRenderTargetVolume::StaticClass(),TEXT("T_RaftSimOfflineSurfaceSnapshot_GPU")));
            Target->bSupportsUAV=true;Target->bForceLinearGamma=true;Target->Filter=TF_Bilinear;
            Target->Init(136,136,48,PF_FloatRGBA);Target->UpdateResourceImmediate(true);
            Texture.Reset(Target);
        }
        else
        {
            auto* Volume=UVolumeTexture::CreateTransient(136,136,48,PF_FloatRGBA,
                MakeUniqueObjectName(GetTransientPackage(),UVolumeTexture::StaticClass(),TEXT("T_RaftSimOfflineSurfaceSnapshot")));
            if (!Volume) return;
            Texture.Reset(Volume);
            Volume->SRGB=false;Volume->Filter=TF_Bilinear;Volume->AddressMode=TA_Clamp;Volume->NeverStream=true;
            auto& Mip=Volume->GetPlatformData()->Mips[0];
            void* Data=Mip.BulkData.Lock(LOCK_READ_WRITE);
            FMemory::Memcpy(Data,Bytes.GetData(),Bytes.Num());Mip.BulkData.Unlock();
            Volume->UpdateResource();
        }
        FlushRenderingCommands();
        TArray<FFloat16Color> Readback;
        auto* Resource=Texture->GetResource();
        auto* InputResource=ScalarSource.IsValid()?ScalarSource->GetResource():nullptr;
        bool ComputeSuccess=!GPUReconstruction;FString ComputeError;TArray<double> GPUTimesMs;
        const double ComputeStart=FPlatformTime::Seconds();
        ENQUEUE_RENDER_COMMAND(RaftSimVerifyOfflineSurface)([Resource,InputResource,&Readback,&ComputeSuccess,&ComputeError,&GPUTimesMs](FRHICommandListImmediate& RHICmdList)
        {
            if (InputResource)
            {
                ComputeSuccess=RaftSimLiquidRedistanceGPU(RHICmdList,InputResource->TextureRHI,Resource->TextureRHI,
                    FIntVector(136,136,48),FVector3f(2231.25f/136,2231.25f/136,800.f/48),50.f,12,ComputeError);
                if (!ComputeSuccess) return;
                if (GSupportsTimestampRenderQueries)
                {
                    // The dispatch above warms shaders/resources. These are
                    // component GPU intervals, excluding texture upload and
                    // readback, not full-scene or packaged-build frame times.
                    constexpr int32 Samples=8;
                    auto Pool=RHICreateRenderQueryPool(RQT_AbsoluteTime,Samples*2);
                    TArray<FRHIPooledRenderQuery> Queries;
                    for (int32 I=0;I<Samples*2;++I) Queries.Add(Pool->AllocateQuery());
                    for (int32 I=0;I<Samples;++I)
                    {
                        RHICmdList.EndRenderQuery(Queries[2*I].GetQuery());
                        ComputeSuccess=RaftSimLiquidRedistanceGPU(RHICmdList,InputResource->TextureRHI,Resource->TextureRHI,
                            FIntVector(136,136,48),FVector3f(2231.25f/136,2231.25f/136,800.f/48),50.f,12,ComputeError);
                        RHICmdList.EndRenderQuery(Queries[2*I+1].GetQuery());
                        if (!ComputeSuccess) return;
                    }
                    RHICmdList.ImmediateFlush(EImmediateFlushType::FlushRHIThread);
                    for (int32 I=0;I<Samples;++I)
                    {
                        uint64 Begin=0,End=0;
                        if (!RHIGetRenderQueryResult(Queries[2*I].GetQuery(),Begin,true) ||
                            !RHIGetRenderQueryResult(Queries[2*I+1].GetQuery(),End,true) || End<Begin)
                        { GPUTimesMs.Empty();break; }
                        GPUTimesMs.Add((End-Begin)/1000.0);
                    }
                }
            }
            RHICmdList.Read3DSurfaceFloatData(Resource->TextureRHI,FIntRect(0,0,136,136),FIntPoint(0,48),Readback);
        });
        FlushRenderingCommands();
        const double ComputeAndReadbackMs=(FPlatformTime::Seconds()-ComputeStart)*1000;
        if (!ComputeSuccess || Readback.Num()!=Count)
        { UE_LOG(LogTemp,Error,TEXT("GPU redistance failed: %s"),*ComputeError);return; }
        const bool Exact=Readback.Num()==Count && FMemory::Memcmp(Readback.GetData(),Bytes.GetData(),Bytes.Num())==0;
        double MaxErrorCm=0,ErrorSquared=0;bool ValidSign=true,Finite=true;
        for (int32 I=0;I<Count;++I)
        {
            const float Actual=Readback[I].R.GetFloat(),Expected=Values[I].R.GetFloat();
            const double Difference=FMath::Abs(Actual-Expected);
            Finite &= FMath::IsFinite(Actual);ValidSign &= (Actual<0)==(Expected<0);
            MaxErrorCm=FMath::Max(MaxErrorCm,Difference);ErrorSquared+=Difference*Difference;
        }
        const bool MatchesCPU=GPUReconstruction && Finite && ValidSign && MaxErrorCm<=0.1;
        if ((!GPUReconstruction && !Exact) || (GPUReconstruction && !MatchesCPU))
        { UE_LOG(LogTemp,Error,TEXT("Surface verification failed: max CPU difference%gcm, sign=%d, finite=%d"),MaxErrorCm,ValidSign,Finite);return; }
        Material->SetTextureParameterValue(TEXT("VolumeTex"),Texture.Get());
        Material->SetScalarParameterValue(TEXT("River Foam Strength"),0.f);
        UTexture* Bound=nullptr;Material->GetTextureParameterValue(FMaterialParameterInfo(TEXT("VolumeTex")),Bound);
        if (Bound!=Texture.Get()) return;
        if (!IFileManager::Get().MakeDirectory(*Output,true)) return;
        auto Report=MakeShared<FJsonObject>();
        Report->SetStringField(TEXT("source_directory"),Source);
        Report->SetStringField(TEXT("previous_texture"),Previous->GetPathName());
        Report->SetStringField(TEXT("bound_texture"),Texture->GetPathName());
        Report->SetStringField(TEXT("material"),Material->GetPathName());
        Report->SetBoolField(TEXT("gpu_upload_readback_exact"),Exact);
        Report->SetBoolField(TEXT("gpu_reconstruction_executed"),GPUReconstruction);
        Report->SetBoolField(TEXT("gpu_reconstruction_matches_cpu"),MatchesCPU);
        Report->SetBoolField(TEXT("gpu_result_verified"),GPUReconstruction?MatchesCPU:Exact);
        Report->SetNumberField(TEXT("gpu_cpu_max_error_cm"),MaxErrorCm);
        Report->SetNumberField(TEXT("gpu_cpu_rms_error_cm"),FMath::Sqrt(ErrorSquared/Count));
        Report->SetNumberField(TEXT("compute_and_blocking_readback_wall_ms_not_gpu_timing"),ComputeAndReadbackMs);
        TArray<TSharedPtr<FJsonValue>> TimingValues;
        for (double Value:GPUTimesMs) TimingValues.Add(MakeShared<FJsonValueNumber>(Value));
        Report->SetArrayField(TEXT("gpu_component_timestamp_ms"),TimingValues);
        Report->SetBoolField(TEXT("gpu_timestamps_available"),GPUTimesMs.Num()==8);
        Report->SetBoolField(TEXT("full_scene_performance_measured"),false);
        Report->SetBoolField(TEXT("live_simulation_input_connected"),false);
        Report->SetBoolField(TEXT("material_binding_verified"),Bound==Texture.Get());
        Report->SetBoolField(TEXT("simulation_frozen"),true);
        Report->SetBoolField(TEXT("offline_geometry_not_live_animation"),true);
        Report->SetBoolField(TEXT("physical_or_visual_acceptance"),false);
        Report->SetNumberField(TEXT("voxel_count"),Count);
        Report->SetNumberField(TEXT("pixel_format"),Resource->TextureRHI->GetDesc().Format);
        TArray<uint8> ActualBytes;ActualBytes.Append(reinterpret_cast<const uint8*>(Readback.GetData()),Readback.Num()*sizeof(FFloat16Color));
        if (!FFileHelper::SaveArrayToFile(ActualBytes,*(Output/TEXT("gpu_surface.rgba16f")))) return;
        FString Json;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Json));
        if (!FFileHelper::SaveStringToFile(Json,*(Output/TEXT("binding.json")))) return;
        UE_LOG(LogTemp,Display,TEXT("Frozen offline surface bound; %d RGBA16f voxels verified on GPU; not live simulation"),Count);
    }));
}
