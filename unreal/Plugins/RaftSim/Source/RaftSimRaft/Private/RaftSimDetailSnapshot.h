#pragma once
#include "CoreMinimal.h"
#include "RHIGPUReadback.h"
#include "RHICommandList.h"
#include "HAL/FileManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"

// Explicit diagnostic only. No waits, physics feedback, state changes or
// readback allocation in ordinary play. Raw arrays are row-major float4.
struct FRaftSimDetailSnapshot
{
    FRHIGPUBufferReadback StateReadback{TEXT("RaftSimDetailSnapshotState")};
    FRHIGPUTextureReadback SurfaceReadback{TEXT("RaftSimDetailSnapshotSurface")};
    TArray<FVector4f> Flow,MeanGeometry;
    FString Prefix;
    double Elapsed=0,SimulationSeconds=0,MeanSampleElapsed=0;
    FVector Center,Downstream,Left;
    FIntPoint Size=FIntPoint(128,128);
    float CellMeters=0.5f;
    FVector2f OriginMeters=FVector2f(-32,-32);

    bool Poll()
    {
        if (!StateReadback.IsReady() || !SurfaceReadback.IsReady())return false;
        TArray<FVector4f> State,Surface;
        State.SetNumUninitialized(Size.X*Size.Y);Surface.SetNumUninitialized(Size.X*Size.Y);
        const void* StateData=StateReadback.Lock(State.Num()*sizeof(FVector4f));
        FMemory::Memcpy(State.GetData(),StateData,State.Num()*sizeof(FVector4f));
        StateReadback.Unlock();
        int32 Pitch=0;
        const auto* SurfaceData=static_cast<const FVector4f*>(SurfaceReadback.Lock(Pitch));
        for (int32 Y=0;Y<Size.Y;++Y)
            FMemory::Memcpy(Surface.GetData()+Y*Size.X,SurfaceData+Y*Pitch,Size.X*sizeof(FVector4f));
        SurfaceReadback.Unlock();
        IFileManager::Get().MakeDirectory(*FPaths::GetPath(Prefix),true);
        const auto Save=[&](const TCHAR* Suffix,const TArray<FVector4f>& Data)
        {
            TUniquePtr<FArchive> File(IFileManager::Get().CreateFileWriter(*(Prefix+Suffix)));
            if (!File)return false;
            File->Serialize(const_cast<FVector4f*>(Data.GetData()),Data.Num()*sizeof(FVector4f));
            const bool bOk=!File->IsError();return File->Close() && bOk;
        };
        const bool bArrays=MeanGeometry.Num()==Flow.Num() && Save(TEXT(".mean_geometry.f32"),MeanGeometry) &&
            Save(TEXT(".flow.f32"),Flow) && Save(TEXT(".state.f32"),State) && Save(TEXT(".surface.f32"),Surface);
        const FString Metadata=FString::Printf(TEXT("{\"schema\":\"raftsim.detail.snapshot.v1\",\"shape\":[%d,%d,4],\"dtype\":\"little-endian float32\",\"elapsed_s\":%.9f,\"simulation_s\":%.9f,\"cell_m\":%.9f,\"origin_m\":[%.9f,%.9f],\"center_world_cm\":[%.9f,%.9f,%.9f],\"downstream_world\":[%.9f,%.9f,%.9f],\"left_world\":[%.9f,%.9f,%.9f],\"arrays_complete\":%s,\"performance_qualification\":false}"),
            Size.Y,Size.X,Elapsed,SimulationSeconds,CellMeters,OriginMeters.X,OriginMeters.Y,Center.X,Center.Y,Center.Z,Downstream.X,Downstream.Y,Downstream.Z,
            Left.X,Left.Y,Left.Z,bArrays ? TEXT("true") : TEXT("false"));
        // Additional source record is from the SAME sampled field/upload as
        // Flow, not queried again after asynchronous state readback. The two
        // heights share the river vertical datum; raw depth is not wet-masked.
        FString PairedMetadata=Metadata.Replace(TEXT("raftsim.detail.snapshot.v1"),TEXT("raftsim.detail.snapshot.v2"));
        PairedMetadata.RemoveAt(PairedMetadata.Len()-1);
        PairedMetadata+=FString::Printf(TEXT(",\"mean_sample_elapsed_s\":%.9f,\"mean_geometry_channels\":[\"bed_m\",\"sampled_surface_m\",\"unmasked_depth_m\",\"wet_fraction\"],\"height_datum\":\"river_vertical_datum\",\"mean_geometry_resampling\":\"same bilinear 65-to-128 source grid as flow; wet masking applies only to flow\"}"),MeanSampleElapsed);
        const bool bMetadata=FFileHelper::SaveStringToFile(PairedMetadata,*(Prefix+TEXT(".json")));
        if (bArrays && bMetadata)
        { UE_LOG(LogTemp,Display,TEXT("Detail snapshot saved: %s elapsed=%.3f simulation=%.3f; diagnostic readback, not performance qualification"),*Prefix,Elapsed,SimulationSeconds); }
        else { UE_LOG(LogTemp,Error,TEXT("Detail snapshot save failed: %s"),*Prefix); }
        return true;
    }
};
