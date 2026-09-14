#pragma once
#include "RaftSimTotalDepthSourceGPU.h"
#include "RHIGPUReadback.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"

// Opt-in, asynchronous observation audit. Uses the actual live source owner's
// uploaded buffers, but does NOT drive gameplay PDE evolution or claim a wave test.
struct FRaftSimTemporalBoundaryAudit
{
    FRHIGPUBufferReadback StateRead{TEXT("LiveTemporal.State")},BedRead{TEXT("LiveTemporal.Bed")},
        TraceRead{TEXT("LiveTemporal.Trace")},DiagRead{TEXT("LiveTemporal.Diagnostics")};
    TSharedPtr<const FRaftSimTotalDepthSource,ESPMode::ThreadSafe> A,B;
    FString Path;FVector4f Clock=FVector4f(0,0,0,0);float StageDt=0;
    bool Start(FRHICommandListImmediate& Cmd,const FRaftSimTotalDepthSourceGPU& Owner,const FString& Output,FString& Error)
    {
        if(!Owner.HasTemporalBracket() || FPaths::FileExists(Output) || FPaths::FileExists(Output+TEXT(".inputs.json")))
        {Error=TEXT("Live temporal audit requires a valid bracket and a fresh output path");return false;}
        A=Owner.PreviousSource;B=Owner.Source;Path=Output;
        const double Span=B->SampleSeconds-A->SampleSeconds,T=A->SampleSeconds+.25*Span;
        Clock=FVector4f(float(T),float(T-double(float(T))),0,0);StageDt=float(.25*Span);
        FRDGBuilder Graph(Cmd);TArray<FVector4f> P={Clock},Info={FVector4f(0,StageDt,0,0)};
        const auto R=Owner.SampleBoundary(Graph,CreateStructuredBuffer(Graph,TEXT("LiveTemporal.Clock"),P),
            CreateStructuredBuffer(Graph,TEXT("LiveTemporal.Info"),Info),Error);
        if(!R.Diagnostics){Graph.Execute();return false;}
        AddEnqueueCopyPass(Graph,&StateRead,R.Input.ExteriorState,512*16);AddEnqueueCopyPass(Graph,&BedRead,R.Input.ExteriorBed,512*4);
        AddEnqueueCopyPass(Graph,&TraceRead,R.Input.FaceVelocity,512*8);AddEnqueueCopyPass(Graph,&DiagRead,R.Diagnostics,16);
        Graph.Execute();return true;
    }
    bool Poll()
    {
        if(!StateRead.IsReady() || !BedRead.IsReady() || !TraceRead.IsReady() || !DiagRead.IsReady())return false;
        const auto* S=static_cast<const FVector4f*>(StateRead.Lock(512*16));const auto* Z=static_cast<const float*>(BedRead.Lock(512*4));
        const auto* T=static_cast<const FVector2f*>(TraceRead.Lock(512*8));const auto* D=static_cast<const uint32*>(DiagRead.Lock(16));
        if(!S || !Z || !T || !D)return false;
        const double Span=B->SampleSeconds-A->SampleSeconds;
        const double Time=double(Clock.X)+Clock.Y+StageDt,Alpha=(Time-A->SampleSeconds)/Span;
        bool Finite=true,BedExact=true;double MaxStateError=0,MaxTraceError=0,MaxNormalizedError=0,MaxObservedStateChange=0,MaxObservedFaceChange=0;
        for(int32 I=0;I<512;++I)
        {
            BedExact &= Z[I]==A->ExteriorBed[I];
            for(int32 K=0;K<4;++K)
            {
                const double Expected=(1-Alpha)*double(A->ExteriorState[I][K])+Alpha*double(B->ExteriorState[I][K]);
                const double Difference=FMath::Abs(double(S[I][K])-Expected);Finite &= FMath::IsFinite(S[I][K]);
                MaxStateError=FMath::Max(MaxStateError,Difference);MaxNormalizedError=FMath::Max(MaxNormalizedError,Difference/FMath::Max(1.,FMath::Abs(Expected)));
                MaxObservedStateChange=FMath::Max(MaxObservedStateChange,FMath::Abs(double(B->ExteriorState[I][K])-A->ExteriorState[I][K]));
            }
            const double Expected[2]={(1-Alpha)*A->FaceNormalVelocity[I]+Alpha*B->FaceNormalVelocity[I],
                (double(B->FaceNormalVelocity[I])-A->FaceNormalVelocity[I])/Span};
            for(int32 K=0;K<2;++K)
            {
                const double Difference=FMath::Abs(double(T[I][K])-Expected[K]);Finite &= FMath::IsFinite(T[I][K]);
                MaxTraceError=FMath::Max(MaxTraceError,Difference);MaxNormalizedError=FMath::Max(MaxNormalizedError,Difference/FMath::Max(1.,FMath::Abs(Expected[K])));
            }
            MaxObservedFaceChange=FMath::Max(MaxObservedFaceChange,FMath::Abs(double(B->FaceNormalVelocity[I])-A->FaceNormalVelocity[I]));
        }
        bool Passed=Finite && BedExact && (D[0]|D[1]|D[2]|D[3])==0 && MaxNormalizedError<1e-6 && Alpha>=0 && Alpha<=1;
        auto Report=MakeShared<FJsonObject>();
        Report->SetStringField(TEXT("schema"),TEXT("raftsim.live_temporal_boundary_audit.v1"));
        Report->SetStringField(TEXT("scope"),TEXT("Actual live owner GPU endpoint buffers versus double CPU interpolation at an explicit compensated stage clock. No PDE evolution, radiation, visual, or performance acceptance."));
        Report->SetBoolField(TEXT("passed"),Passed);Report->SetNumberField(TEXT("faces"),512);
        Report->SetNumberField(TEXT("first_revision"),A->Revision);Report->SetNumberField(TEXT("second_revision"),B->Revision);
        Report->SetNumberField(TEXT("first_native_seconds"),A->SampleSeconds);Report->SetNumberField(TEXT("second_native_seconds"),B->SampleSeconds);
        Report->SetNumberField(TEXT("sample_stage_seconds"),Time);Report->SetNumberField(TEXT("stage_dt_seconds"),StageDt);
        Report->SetNumberField(TEXT("maximum_state_error"),MaxStateError);Report->SetNumberField(TEXT("maximum_trace_error"),MaxTraceError);
        Report->SetNumberField(TEXT("maximum_normalized_error"),MaxNormalizedError);Report->SetBoolField(TEXT("bed_exact"),BedExact);
        Report->SetNumberField(TEXT("maximum_observed_state_change"),MaxObservedStateChange);Report->SetNumberField(TEXT("maximum_observed_face_velocity_change"),MaxObservedFaceChange);
        Report->SetNumberField(TEXT("time_errors"),D[0]);Report->SetNumberField(TEXT("state_errors"),D[1]);
        Report->SetNumberField(TEXT("bed_errors"),D[2]);Report->SetNumberField(TEXT("face_errors"),D[3]);
        StateRead.Unlock();BedRead.Unlock();TraceRead.Unlock();DiagRead.Unlock();
        auto Inputs=MakeShared<FJsonObject>();Inputs->SetStringField(TEXT("schema"),TEXT("raftsim.live_temporal_boundary_inputs.v1"));
        Inputs->SetStringField(TEXT("scope"),TEXT("Immutable actual live source observations; interpolated raster data, not a new survey or evolved GPU state. Packed h/hu/hv/foam in world field axes; boundary faces west/east/south/north."));
        const auto Encode=[&](const FRaftSimTotalDepthSource& Source)
        {
            auto O=MakeShared<FJsonObject>();O->SetNumberField(TEXT("revision"),Source.Revision);O->SetNumberField(TEXT("native_seconds"),Source.SampleSeconds);
            O->SetNumberField(TEXT("nx"),Source.Size.X);O->SetNumberField(TEXT("ny"),Source.Size.Y);O->SetNumberField(TEXT("cell_meters"),Source.CellMeters);
            O->SetNumberField(TEXT("origin_x"),Source.OriginMeters.X);O->SetNumberField(TEXT("origin_y"),Source.OriginMeters.Y);
            const auto Scalars=[](const TArray<float>& Values)
            {TArray<TSharedPtr<FJsonValue>> R;R.Reserve(Values.Num());for(float V:Values)R.Add(MakeShared<FJsonValueNumber>(V));return R;};
            const auto Vectors=[](const TArray<FVector4f>& Values)
            {TArray<TSharedPtr<FJsonValue>> R;R.Reserve(4*Values.Num());for(const auto& V:Values)for(int32 K=0;K<4;++K)R.Add(MakeShared<FJsonValueNumber>(V[K]));return R;};
            O->SetArrayField(TEXT("state"),Vectors(Source.State));O->SetArrayField(TEXT("bed"),Scalars(Source.Bed));
            O->SetArrayField(TEXT("exterior_state"),Vectors(Source.ExteriorState));O->SetArrayField(TEXT("exterior_bed"),Scalars(Source.ExteriorBed));
            O->SetArrayField(TEXT("face_normal_velocity"),Scalars(Source.FaceNormalVelocity));
            if(!Source.PressureStencilState.IsEmpty())
            {
                O->SetNumberField(TEXT("pressure_stencil_width"),3);
                O->SetArrayField(TEXT("pressure_stencil_state"),Vectors(Source.PressureStencilState));
                O->SetArrayField(TEXT("pressure_stencil_bed"),Scalars(Source.PressureStencilBed));
            }
            return O;
        };
        Inputs->SetObjectField(TEXT("first"),Encode(*A));Inputs->SetObjectField(TEXT("second"),Encode(*B));
        const FString InputPath=Path+TEXT(".inputs.json");FString InputJson;auto InputWriter=TJsonWriterFactory<>::Create(&InputJson);
        FJsonSerializer::Serialize(Inputs,InputWriter);Passed &= FFileHelper::SaveStringToFile(InputJson,*InputPath);
        Report->SetStringField(TEXT("input_observations"),InputPath);Report->SetBoolField(TEXT("passed"),Passed);
        FString Json;auto Writer=TJsonWriterFactory<>::Create(&Json);FJsonSerializer::Serialize(Report,Writer);
        if(!FFileHelper::SaveStringToFile(Json,*Path) || !Passed)
        {UE_LOG(LogTemp,Error,TEXT("Live temporal boundary audit failed: %s"),*Path);}
        else
        {UE_LOG(LogTemp,Display,TEXT("Live temporal boundary audit passed512 faces: normalized_error=%.9g native_bracket=[%.9f,%.9f]"),MaxNormalizedError,A->SampleSeconds,B->SampleSeconds);}
        return true;
    }
};
