#include "Misc/AutomationTest.h"
#include "../RaftSimTotalDepthSourceGPU.h"
#include "RaftSimTotalDepthTransportGPU.h"
#include "RHIGPUReadback.h"
#include <limits>

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTotalDepthSourceTest,"RaftSim.WaterDetail.LiveTotalDepthSourceGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FTotalDepthSourceTest::RunTest(const FString&)
{
    TArray<FVector4f> HUV,Geometry;
    TArray<float> FaceVelocity;for(int32 I=0;I<512;++I)FaceVelocity.Add((I-256)*.125f);
    for(int32 Y=-1;Y<=65;++Y)for(int32 X=-1;X<=65;++X)
    {
        float H=Y==0?1e-30f:Y==1?.005f:X%2==0?2.f:10.f;
        HUV.Add(FVector4f(H,X%2==0?1.f:3.f,-2,0));
        // Rounded surface==bed must not erase independently stored depth;
        // bWet=0 in the geometry's fourth component must not mask it either.
        Geometry.Add(FVector4f(1000000.f,1000000.f,H,0));
    }
    FString Error;auto Source=FRaftSimTotalDepthSource::Build(HUV,Geometry,FaceVelocity,FVector2f(123,-456),7.25,1,Error);
    if(!TestTrue(TEXT("paired unmasked live source builds"),Source.IsValid())){AddError(Error);return false;}
    TestEqual(TEXT("tiny positive depth survives a rounded zero surface-bed difference"),Source->State[0].X,1e-30f);
    TestEqual(TEXT("sub1cm presentation-dry depth is retained"),Source->State[2*128].X,.005f);
    TestEqual(TEXT("depth interpolation"),Source->State[4*128+1].X,6.f);
    TestEqual(TEXT("interpolate hu, not interpolated h times interpolated velocity"),Source->State[4*128+1].Y,16.f);
    TestEqual(TEXT("signed transverse momentum interpolation"),Source->State[4*128+1].Z,-12.f);
    TestEqual(TEXT("source observation time is explicit"),Source->SampleSeconds,7.25);
    TestEqual(TEXT("all exterior centres supplied"),Source->ExteriorState.Num(),512);
    TestEqual(TEXT("independent face velocity is not inferred from ghost momentum"),Source->FaceNormalVelocity[0],-32.f);
    TestEqual(TEXT("west face lies halfway between interior and ghost centres"),FRaftSimTotalDepthSource::ExteriorFace(0),FVector2f(-.5f,0));
    TestEqual(TEXT("east face coordinate"),FRaftSimTotalDepthSource::ExteriorFace(255),FVector2f(127.5f,127));
    TestEqual(TEXT("south face coordinate"),FRaftSimTotalDepthSource::ExteriorFace(256),FVector2f(0,-.5f));
    TestEqual(TEXT("north face coordinate"),FRaftSimTotalDepthSource::ExteriorFace(511),FVector2f(127,127.5f));
    {auto BadSource=*Source;BadSource.FaceNormalVelocity.Pop();TestFalse(TEXT("missing face trace refused"),BadSource.Validate(Error));}
    {auto BadSource=*Source;BadSource.FaceNormalVelocity.Last()=std::numeric_limits<float>::infinity();TestFalse(TEXT("invalid face trace refused"),BadSource.Validate(Error));}
    TestEqual(TEXT("west ghost interpolates exterior depth instead of clamping interior"),Source->ExteriorState[4].X,6.f);
    TestEqual(TEXT("west ghost interpolates momentum, not velocity"),Source->ExteriorState[4].Y,16.f);
    TestEqual(TEXT("west ghost transverse momentum stays signed"),Source->ExteriorState[4].Z,-12.f);
    TestEqual(TEXT("east ghost is the actual outside node"),Source->ExteriorState[128+4].X,2.f);
    {auto BadSource=*Source;BadSource.ExteriorState.Pop();TestFalse(TEXT("missing exterior cell refused"),BadSource.Validate(Error));}
    {auto BadSource=*Source;BadSource.ExteriorBed.Last()=std::numeric_limits<float>::infinity();TestFalse(TEXT("invalid exterior bed refused"),BadSource.Validate(Error));}
    Error.Reset();
    auto Refuse=[&](TArray<FVector4f> Flow,TArray<FVector4f> G)
    {FString E;return !FRaftSimTotalDepthSource::Build(Flow,G,FaceVelocity,FVector2f::ZeroVector,0,1,E) && !E.IsEmpty();};
    auto Bad=HUV;Bad[0].X=-1;TestTrue(TEXT("negative source depth rejected"),Refuse(Bad,Geometry));
    Bad=HUV;Bad[0].Y=std::numeric_limits<float>::infinity();TestTrue(TEXT("nonfinite velocity rejected"),Refuse(Bad,Geometry));
    auto BadG=Geometry;BadG[0].Z=0;TestTrue(TEXT("unpaired depth/geometry rejected"),Refuse(HUV,BadG));
    BadG=Geometry;BadG[0].Y=std::numeric_limits<float>::quiet_NaN();TestTrue(TEXT("invalid carrier rejected"),Refuse(HUV,BadG));
    Bad=HUV;Bad.Pop();TestTrue(TEXT("mismatched sample count rejected"),Refuse(Bad,Geometry));
    {FString E;TestFalse(TEXT("missing source revision rejected"),FRaftSimTotalDepthSource::Build(HUV,Geometry,FaceVelocity,FVector2f::ZeroVector,0,0,E).IsValid());}
    if(GUsingNullRHI){AddError(TEXT("Actual GPU required for source upload proof"));return false;}
    bool Passed=true;
    ENQUEUE_RENDER_COMMAND(TotalDepthSourceVerification)([&](FRHICommandListImmediate& Cmd)
    {
        FRaftSimTotalDepthSourceGPU Owner;
        Passed &= Owner.Upload(Cmd,Source,Error);auto FirstState=Owner.State;
        auto FirstExterior=Owner.ExteriorState;
        Passed &= Owner.Upload(Cmd,Source,Error) && Owner.Uploads==1 && Owner.State==FirstState && Owner.ExteriorState==FirstExterior;
        auto SameRevision=FRaftSimTotalDepthSource::Build(HUV,Geometry,FaceVelocity,FVector2f(999,999),8,1,Error);
        Passed &= !Owner.Upload(Cmd,SameRevision,Error) && Owner.Source==Source && Owner.State==FirstState && Owner.ExteriorState==FirstExterior;
        auto Next=FRaftSimTotalDepthSource::Build(HUV,Geometry,FaceVelocity,FVector2f(127,-448),8.5,2,Error);
        Passed &= Owner.Upload(Cmd,Next,Error) && Owner.Source==Next && Owner.Uploads==2;
        Passed &= !Owner.HasTemporalBracket(); // Crop moved: old faces cannot be paired.
        auto LaterVelocity=FaceVelocity;for(auto& U:LaterVelocity)U+=.25f;
        auto Later=FRaftSimTotalDepthSource::Build(HUV,Geometry,LaterVelocity,Next->OriginMeters,9,3,Error);
        Passed &= Owner.Upload(Cmd,Later,Error) && Owner.HasTemporalBracket() && Owner.PreviousSource==Next;
        Next=Later;
        Passed &= Source->OriginMeters==FVector2f(123,-456) && Source->SampleSeconds==7.25;
        FRDGBuilder Graph(Cmd);FRHIGPUBufferReadback SR(TEXT("LiveSource.StateRead")),BR(TEXT("LiveSource.BedRead")),RR(TEXT("LiveSource.ReferenceRead")),
            ESR(TEXT("LiveSource.ExteriorStateRead")),EBR(TEXT("LiveSource.ExteriorBedRead")),DR(TEXT("LiveSource.TransportDiagnostics")),
            FVR(TEXT("LiveSource.FaceRead")),TTR(TEXT("LiveSource.TemporalTrace")),TDR(TEXT("LiveSource.TemporalDiagnostics"));
        AddEnqueueCopyPass(Graph,&SR,Graph.RegisterExternalBuffer(Owner.State),128*128*16);
        AddEnqueueCopyPass(Graph,&BR,Graph.RegisterExternalBuffer(Owner.Bed),128*128*4);
        AddEnqueueCopyPass(Graph,&RR,Graph.RegisterExternalBuffer(Owner.Reference),128*128*8);
        AddEnqueueCopyPass(Graph,&ESR,Graph.RegisterExternalBuffer(Owner.ExteriorState),512*16);
        AddEnqueueCopyPass(Graph,&EBR,Graph.RegisterExternalBuffer(Owner.ExteriorBed),512*4);
        AddEnqueueCopyPass(Graph,&FVR,Graph.RegisterExternalBuffer(Owner.FaceNormalVelocity),512*4);
        TArray<FVector4f> Clock={FVector4f(8,.75f,0,0)},Info={FVector4f(0,.0625f,0,0)};
        const auto Temporal=Owner.SampleBoundary(Graph,CreateStructuredBuffer(Graph,TEXT("LiveSource.TestClock"),Clock),
            CreateStructuredBuffer(Graph,TEXT("LiveSource.TestInfo"),Info),Error);
        if(!Temporal.Diagnostics){Passed=false;Graph.Execute();return;}
        AddEnqueueCopyPass(Graph,&TTR,Temporal.Input.FaceVelocity,512*8);AddEnqueueCopyPass(Graph,&TDR,Temporal.Diagnostics,16);
        // Exercise the real immutable source uploader's outputs directly, not
        // separately re-uploaded fixture copies, as exterior transport inputs.
        const auto Transport=RaftSimTotalDepthTransportGPU(Graph,Graph.RegisterExternalBuffer(Owner.State),
            Graph.RegisterExternalBuffer(Owner.Bed),Next->Size,Next->CellMeters,false,true,Error,
            Graph.RegisterExternalBuffer(Owner.ExteriorState),Graph.RegisterExternalBuffer(Owner.ExteriorBed));
        if(!Transport.Diagnostics){Passed=false;Graph.Execute();return;}
        AddEnqueueCopyPass(Graph,&DR,Transport.Diagnostics,16);
        Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
        const void* S=SR.Lock(128*128*16);const void* B=BR.Lock(128*128*4);const void* R=RR.Lock(128*128*8);
        const void* ES=ESR.Lock(512*16);const void* EB=EBR.Lock(512*4);const auto* D=static_cast<const uint32*>(DR.Lock(16));
        const void* FV=FVR.Lock(512*4);const auto* TT=static_cast<const FVector2f*>(TTR.Lock(512*8));const auto* TD=static_cast<const uint32*>(TDR.Lock(16));
        if(!S || !B || !R || !ES || !EB || !D || !FV || !TT || !TD){Passed=false;return;}
        Passed &= FMemory::Memcmp(S,Next->State.GetData(),128*128*16)==0 &&
            FMemory::Memcmp(B,Next->Bed.GetData(),128*128*4)==0 && FMemory::Memcmp(R,Next->Reference.GetData(),128*128*8)==0 &&
            FMemory::Memcmp(ES,Next->ExteriorState.GetData(),512*16)==0 && FMemory::Memcmp(EB,Next->ExteriorBed.GetData(),512*4)==0 &&
            FMemory::Memcmp(FV,Next->FaceNormalVelocity.GetData(),512*4)==0 && D[0]==0 && D[1]==0;
        Passed &= (TD[0]|TD[1]|TD[2]|TD[3])==0;
        for(int32 I=0;I<512;++I)Passed &= TT[I].X==FaceVelocity[I]+.15625f && TT[I].Y==.5f;
        SR.Unlock();BR.Unlock();RR.Unlock();ESR.Unlock();EBR.Unlock();DR.Unlock();FVR.Unlock();TTR.Unlock();TDR.Unlock();
        auto DuplicateTime=FRaftSimTotalDepthSource::Build(HUV,Geometry,LaterVelocity,Next->OriginMeters,9,4,Error);
        Passed &= Owner.Upload(Cmd,DuplicateTime,Error) && !Owner.HasTemporalBracket();
    });
    FlushRenderingCommands();TestTrue(TEXT("normal source uploader preserves all represented state/bed/reference bits, deduplicates and rejects stale revisions"),Passed);
    if(!Error.IsEmpty())AddError(Error);
    return !HasAnyErrors();
}
#endif
