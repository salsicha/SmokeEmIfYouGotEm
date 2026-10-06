#pragma once
#include "RaftSimDetailPresentationFrame.h"
#include "RaftSimDetailWaterGPU.h"
#include "RHIGPUReadback.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Misc/FileHelper.h"

// Opt-in audit of the exact uploaded frame used by the simultaneous carrier
// contact audit. All inputs are retained until the GPU result is ready.
struct FRaftSimDetailFrameAudit
{
    FRHIGPUBufferReadback Readback{TEXT("RaftSimDetailFrameParity")};
    TSharedPtr<const FRaftSimDetailPresentationFrame,ESPMode::ThreadSafe> Frame;
    TArray<FVector4f> Queries;
    FString Path;
    bool Start(FRHICommandListImmediate& Cmd,FRHITexture* Texture,FString& Error)
    {
        const auto M=Frame->Pixels[Frame->Size.X*Frame->Size.Y];
        for (int32 Y=-1;Y<=Frame->Size.Y;Y+=2) for (int32 X=-1;X<=Frame->Size.X;X+=2)
            Queries.Add(FVector4f(M.X+(X+.25f)*M.Z,M.Y+(Y+.75f)*M.Z,0,0));
        Queries.Add(FVector4f(M.X+(Frame->Size.X-1)*M.Z,M.Y+(Frame->Size.Y-1)*M.Z,0,0));
        return RaftSimValidateRegisteredDetailSamplingGPU(Cmd,Texture,Queries,&Readback,Error);
    }
    bool Poll()
    {
        if (!Readback.IsReady()) return false;
        const auto* Values=static_cast<const FVector4f*>(Readback.Lock(Queries.Num()*sizeof(FVector4f)));
        if (!Values) return false;
        double MaxError=0,MaxHeight=0;bool Finite=true;
        for (int32 I=0;I<Queries.Num();++I)
        {
            const auto CPU=Frame->SampleField(FVector2f(Queries[I].X,Queries[I].Y));
            for (int32 C=0;C<4;++C)
            { Finite &= FMath::IsFinite(Values[I][C]);MaxError=FMath::Max(MaxError,double(FMath::Abs(Values[I][C]-CPU[C]))); }
            MaxHeight=FMath::Max(MaxHeight,double(FMath::Abs(CPU.X)*100.f));
        }
        Readback.Unlock();
        auto Report=MakeShared<FJsonObject>();
        Report->SetStringField(TEXT("scope"),TEXT("Actual presented detail texture after upload versus the immutable CPU contact payload, using the same GPU sampling helper as the material. Match sequence with carrier-contact audit. Excludes full render-frame latency, traversal and visual acceptance."));
        Report->SetNumberField(TEXT("detail_frame_sequence"),Frame->Sequence);
        Report->SetNumberField(TEXT("sample_elapsed_seconds"),Frame->ElapsedSeconds);
        Report->SetNumberField(TEXT("simulation_seconds"),Frame->SimulationSeconds);
        Report->SetNumberField(TEXT("queries"),Queries.Num());
        Report->SetNumberField(TEXT("maximum_rgba_error"),MaxError);
        Report->SetNumberField(TEXT("maximum_sampled_detail_height_cm"),MaxHeight);
        Report->SetBoolField(TEXT("passed"),Finite && MaxError<1.e-6);
        FString Json; auto Writer=TJsonWriterFactory<>::Create(&Json);FJsonSerializer::Serialize(Report,Writer);
        FFileHelper::SaveStringToFile(Json,*Path);return true;
    }
};
