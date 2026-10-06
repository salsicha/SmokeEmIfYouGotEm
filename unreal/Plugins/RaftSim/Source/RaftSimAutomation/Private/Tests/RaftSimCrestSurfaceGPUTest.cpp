#include "Misc/AutomationTest.h"
#include "RaftSimDetailWaterGPU.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimWaterFlowFrame.h"
#include "RHICommandList.h"
#include "RHIGPUReadback.h"
#include "RenderingThread.h"
#include "HAL/PlatformProcess.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrestSurfaceGPUTest,
    "RaftSim.WaterDetail.SharedFineCrestGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)
bool FRaftSimCrestSurfaceGPUTest::RunTest(const FString&)
{
    if (GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("Real SM5+ GPU required"));return false; }
    double MaxHeightError=0,MaxSlopeError=0,MaxRecovered=0,MaxVertexChange=0;
    int32 Verified=0;
    // Independent oracle is the existing CPU raft-support function. Include
    // local/global overlap caps, changed site records (previous-frame shape),
    // a zero-site atlas, both triangle halves and an organic shore taper.
    for (int32 Fixture=0;Fixture<6;++Fixture)
    {
        const FIntPoint Size(9,7);const int32 Count=Size.X*Size.Y,AtlasHeight=Size.Y*4+2;
        const float Spacing=1.5f,Scale=0.83f;
        const FVector2D Origin(-5.7,-4.4);
        TArray<URaftSimWaterRuntimeAdapter::FSupportBreakingSite> Sites;
        if (Fixture!=3)
        {
            auto& A=Sites.AddDefaulted_GetRef();A.RiverCoordinatesMeters=FVector2D(0.17+0.3*Fixture,0.13);
            A.PhysicalCrestHeightMeters=0.75f;A.PhysicalCrestLengthMeters=2;A.bLocalEnvelopeCap=Fixture!=1;
            auto& B=Sites.AddDefaulted_GetRef();B.RiverCoordinatesMeters=FVector2D(1.13,1.9);
            B.PhysicalCrestHeightMeters=0.43f;B.PhysicalCrestLengthMeters=3.2f;B.bLocalEnvelopeCap=Fixture!=1;
            const float Angle=Fixture==2 ? .713f : (Fixture==4 ? float(PI) : (Fixture==5 ? float(-PI/2) : 0.f));
            Sites[0].FlowDirection=RaftSimWaterFlowFrame::FromAngle(Angle);
            Sites[1].FlowDirection=RaftSimWaterFlowFrame::FromAngle(Fixture>=4 ? Angle-.47f : Angle);
        }
        const auto Height=[&](FVector2D P)
        { return double(URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(P,Sites,0.22f,Spacing)); };
        TArray<FVector4f> Data;Data.SetNumZeroed(Size.X*AtlasHeight);
        for (int32 Y=0;Y<Size.Y;++Y)for (int32 X=0;X<Size.X;++X)
        {
            const int32 I=Y*Size.X+X;
            const float Shore=FMath::SmoothStep(0.0f,3.0f,float(Y));
            const float Crest=Height(Origin+FVector2D(X,Y)*Spacing)*Shore*Scale*100;
            // Rotated/sheared world XY in cm verifies the inverse Jacobian.
            Data[I]=FVector4f(1000+120*X-70*Y,-700+90*X+110*Y,800+3*X-2*Y+Crest,Crest);
            Data[Count+I]=FVector4f(0,0,1,Shore);
        }
        Data[Count*4]=FVector4f(Origin.X,Origin.Y,Spacing,Sites.Num());
        Data[Count*4+Size.X]=FVector4f(Scale,0,0,0);
        for (int32 I=0;I<Sites.Num();++I)
        {
            const auto& S=Sites[I];
            Data[Count*4+I+1]=FVector4f(S.RiverCoordinatesMeters.X,S.RiverCoordinatesMeters.Y,S.PhysicalCrestHeightMeters,S.PhysicalCrestLengthMeters);
            Data[Count*4+Size.X+I+1]=FVector4f(1,0.5f,S.bLocalEnvelopeCap ? 1 : 0,
                FMath::Atan2(S.FlowDirection.Y,S.FlowDirection.X));
        }
        const auto Sample=[&](FVector2D P,int32 Band)
        {
            const int32 X=FMath::Clamp(FMath::FloorToInt(P.X),0,Size.X-2),Y=FMath::Clamp(FMath::FloorToInt(P.Y),0,Size.Y-2);
            const double U=P.X-X,V=P.Y-Y;const int32 I=Band*Count+Y*Size.X+X;
            const auto A=FVector4d(Data[I]),B=FVector4d(Data[I+1]),C=FVector4d(Data[I+Size.X]),D=FVector4d(Data[I+Size.X+1]);
            return U+V<=1 ? A+(B-A)*U+(C-A)*V : D+(C-D)*(1-U)+(B-D)*(1-V);
        };
        const auto Correction=[&](FVector2D P)
        { return Height(Origin+P*Spacing)*Sample(P,1).W*Scale*100-Sample(P,0).W; };
        TArray<FVector4f> Queries,Actual;
        for (int32 Y=0;Y<Size.Y;++Y)for (int32 X=0;X<Size.X;++X)Queries.Add(FVector4f(X,Y,0,0));
        const int32 VertexQueries=Queries.Num();
        for (int32 Y=0;Y+1<Size.Y;++Y)for (int32 X=0;X+1<Size.X;++X)
            for (const FVector2D Offset:{FVector2D(0.23,0.31),FVector2D(0.72,0.63)})
            { for (int32 Band=0;Band<3;++Band)Queries.Add(FVector4f(X+Offset.X,Y+Offset.Y,Band,0)); }
        auto Readback=MakeShared<FRHIGPUBufferReadback,ESPMode::ThreadSafe>(TEXT("RaftSimCrestTest"));
        FTextureRHIRef Texture;bool bSampled=false;FString Error;
        ENQUEUE_RENDER_COMMAND(RaftSimCrestTest)([&](FRHICommandListImmediate& Cmd)
        {
            const auto Desc=FRHITextureCreateDesc::Create2D(TEXT("CrestAtlasTest"),Size.X,AtlasHeight,PF_A32B32G32R32F)
                .SetFlags(ETextureCreateFlags::ShaderResource).SetInitialState(ERHIAccess::CopyDest);
            Texture=Cmd.CreateTexture(Desc);
            Cmd.UpdateTexture2D(Texture,0,FUpdateTextureRegion2D(0,0,0,0,Size.X,AtlasHeight),Size.X*sizeof(FVector4f),reinterpret_cast<const uint8*>(Data.GetData()));
            Cmd.Transition(FRHITransitionInfo(Texture,ERHIAccess::CopyDest,ERHIAccess::SRVMask));
            bSampled=RaftSimValidateMacroSamplingGPU(Cmd,Texture,Size,Queries,&Readback.Get(),Error,true);
        });
        FlushRenderingCommands();
        if (!TestTrue(TEXT("extended crest atlas dispatched"),bSampled)) { AddError(Error);return false; }
        const double Deadline=FPlatformTime::Seconds()+10;
        while (!Readback->IsReady() && FPlatformTime::Seconds()<Deadline)FPlatformProcess::Sleep(0.01f);
        if (!Readback->IsReady()) { AddError(TEXT("Crest GPU timeout"));return false; }
        ENQUEUE_RENDER_COMMAND(RaftSimCrestRead)([&](FRHICommandListImmediate&)
        {
            const void* Ptr=Readback->Lock(Queries.Num()*sizeof(FVector4f));Actual.SetNumUninitialized(Queries.Num());
            FMemory::Memcpy(Actual.GetData(),Ptr,Actual.Num()*sizeof(FVector4f));Readback->Unlock();Texture.SafeRelease();
        });
        FlushRenderingCommands();
        for (int32 I=0;I<Queries.Num();++I)
        {
            const FVector2D P(Queries[I].X,Queries[I].Y);const auto Coarse=Sample(P,0);
            for (int32 K=0;K<4;++K)if (!FMath::IsFinite(Actual[I][K])) { AddError(TEXT("Nonfinite crest result"));return false; }
            if (Queries[I].Z==0)
            {
                const double Expected=Coarse.Z+Correction(P);
                MaxHeightError=FMath::Max(MaxHeightError,FMath::Abs(Actual[I].Z-Expected));
                MaxRecovered=FMath::Max(MaxRecovered,FMath::Abs(Correction(P)));
                if (I<VertexQueries)MaxVertexChange=FMath::Max(MaxVertexChange,FMath::Abs(Actual[I].Z-Coarse.Z));
                TestTrue(TEXT("world XY unchanged"),FMath::Abs(Actual[I].X-Coarse.X)<0.001 && FMath::Abs(Actual[I].Y-Coarse.Y)<0.001);
            }
            else
            {
                // Central difference of CPU support oracle, away from triangle
                // edges. Height calculation is float; 0.002 grid units balances
                // roundoff and truncation without hiding a normal mismatch.
                const double E=0.002;
                const auto NormalHeight=[&](FVector2D Q)
                { return Correction(Q)+(Queries[I].Z==2 ? Sample(Q,0).W : 0); };
                const double GX=(NormalHeight(P+FVector2D(E,0))-NormalHeight(P-FVector2D(E,0)))/(2*E);
                const double GY=(NormalHeight(P+FVector2D(0,E))-NormalHeight(P-FVector2D(0,E)))/(2*E);
                const double SX=(110*GX-90*GY)/19500, SY=(70*GX+120*GY)/19500;
                MaxSlopeError=FMath::Max(MaxSlopeError,FMath::Max(FMath::Abs(Actual[I].Y-SX),FMath::Abs(Actual[I].Z-SY)));
            }
            ++Verified;
        }
    }
    TestTrue(TEXT("GPU shared crest matches continuous CPU support within 0.01mm"),MaxHeightError<0.001);
    TestTrue(TEXT("world slopes match independent differentiated CPU profile"),MaxSlopeError<0.001);
    TestTrue(TEXT("coarse vertices not double displaced"),MaxVertexChange<0.001);
    TestTrue(TEXT("fixture actually recovers subgrid crest, not a passthrough"),MaxRecovered>10);
    AddInfo(FString::Printf(TEXT("Shared fine crest: %d queries; height error %.9g cm, slope error %.9g, coarse vertex change %.9g cm, recovered %.9g cm"),
        Verified,MaxHeightError,MaxSlopeError,MaxVertexChange,MaxRecovered));
    return true;
}
#endif
