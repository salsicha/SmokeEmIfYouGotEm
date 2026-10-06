#include "Misc/AutomationTest.h"
#include "RaftSimLiquidInterfaceHighOrderGPU.h"
#include "RaftSimLiquidHaloGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidHighOrderRegionsTest,"RaftSim.Editor.LiquidInterfaceHighOrderRegionsGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLiquidHighOrderRegionsTest::RunTest(const FString&)
{
    if(GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM6)
    { AddError(TEXT("Actual SM6 GPU required for interface owner-cut test"));return false; }
    // 44 x 6 physical XY cells, split into four owners of 22 x 3. Same exterior,
    // solid field, velocity, timestep and 24-step floating point persistence.
    const FIntVector WholeSize(48,10,10),LocalSize(26,7,10);
    const FVector3f Cell(70,120,60);const float Dt=.5f;
    TArray<float> Results[5];TArray<uint32> Counters;FString Error;bool Ran=false,Rejected=false;
    ENQUEUE_RENDER_COMMAND(RaftSimHighOrderOwnerCut)([&](FRHICommandListImmediate& Cmd)
    {
        FRDGBuilder Graph(Cmd);
        auto Input=[&](FIntVector Size,FIntPoint Offset,const TCHAR* Name,bool Native=false)
        {
            const int Count=Size.X*Size.Y*Size.Z;
            TArray<float> Phi;TArray<FVector4f> Flow;TArray<uint32> Solid;
            TArray<FFloat16Color> Boundary;
            Phi.SetNumUninitialized(Count);Flow.SetNumUninitialized(Count);Solid.Init(0,Count);
            Boundary.SetNumUninitialized(Count);
            for(int Z=0;Z<Size.Z;++Z) for(int Y=0;Y<Size.Y;++Y) for(int X=0;X<Size.X;++X)
            {
                const int I=(Z*Size.Y+Y)*Size.X+X;const float GX=float(X+Offset.X),GY=float(Y+Offset.Y);
                const float Crest=70.f*FMath::Exp(-FMath::Square((GX-20.4f)/1.8f));
                Phi[I]=(Z-4.3f)*Cell.Z-Crest*(.8f+.2f*FMath::Cos((GY-4.5f)*.6f));
                Flow[I]=FVector4f(30,5,-3,0);
                // Partial obstacle crossing the owner cut, but off the crest
                // centerline. A split must preserve solid fallback too.
                Solid[I]=(GX>=23 && GX<=25 && GY==2 && Z<=3)?1u:0u;
                const float Phase=Solid[I]?((Z%2)?3.f:1.f):((Z%2)?2.f:0.f);
                Boundary[I]=FFloat16Color(FLinearColor(17,-9,2,Phase));
            }
            auto Upload=[&](EPixelFormat Format,const void* Data,int Stride)
            {
                auto Texture=Cmd.CreateTexture(FRHITextureCreateDesc::Create3D(Name,Size.X,Size.Y,Size.Z,Format)
                    .SetFlags(TexCreate_ShaderResource|TexCreate_UAV).SetInitialState(ERHIAccess::CopyDest));
                Cmd.UpdateTexture3D(Texture,0,FUpdateTextureRegion3D(0,0,0,0,0,0,Size.X,Size.Y,Size.Z),
                    Size.X*Stride,Size.X*Size.Y*Stride,static_cast<const uint8*>(Data));
                Cmd.Transition(FRHITransitionInfo(Texture,ERHIAccess::CopyDest,ERHIAccess::SRVCompute));
                return Graph.RegisterExternalTexture(CreateRenderTarget(Texture,Name));
            };
            return FRaftSimLiquidInterfaceHighOrderRegion{Upload(PF_R32_FLOAT,Phi.GetData(),4),
                Upload(PF_A32B32G32R32F,Flow.GetData(),16),Native?Upload(PF_FloatRGBA,Boundary.GetData(),8):Upload(PF_R32_UINT,Solid.GetData(),4)};
        };
        auto Whole=Input(WholeSize,FIntPoint(0),TEXT("HighOrderRegions.Whole"));
        TArray<FRaftSimLiquidInterfaceHighOrderRegion> Regions;
        TArray<FIntVector> Sizes;TArray<FRaftSimLiquidHaloColumn> Columns;
        for(int Owner=0;Owner<4;++Owner)
        {
            const FIntPoint Offset((Owner%2)*22,(Owner/2)*3);
            Regions.Add(Input(LocalSize,Offset,TEXT("HighOrderRegions.Owner"),true));Sizes.Add(LocalSize);
            for(int Y=0;Y<LocalSize.Y;++Y) for(int X=0;X<LocalSize.X;++X)
            {
                const int GX=X+Offset.X,GY=Y+Offset.Y;
                if(GX<2 || GX>=46 || GY<2 || GY>=8) continue;
                const int SourceOwner=int(GX>=24)+2*int(GY>=5);
                if(SourceOwner==Owner) continue;
                Columns.Add({SourceOwner,Owner,FIntPoint(GX-(SourceOwner%2)*22,GY-(SourceOwner/2)*3),FIntPoint(X,Y)});
            }
        }
        const auto Halo=RaftSimBuildLiquidHaloPlan(Graph,Sizes,Columns,Error);
        if(!Halo.Columns) { Graph.Execute();return; }
        FString Invalid;auto Aliased=Regions;Aliased[1]=Regions[0];
        Rejected=RaftSimAdvectLiquidInterfaceHighOrderRegions(Graph,{},Regions,Cell,Dt,Invalid).IsEmpty() &&
            RaftSimAdvectLiquidInterfaceHighOrderRegions(Graph,Halo,Aliased,Cell,Dt,Invalid).IsEmpty();
        FRaftSimLiquidInterfaceHighOrderStep WholeStep;TArray<FRaftSimLiquidInterfaceHighOrderStep> Split;
        for(int Iteration=0;Iteration<24;++Iteration)
        {
            WholeStep=RaftSimAdvectLiquidInterfaceHighOrder(Graph,Whole.Source,Whole.Velocity,Whole.Solid,
                Cell,Dt,FIntVector(2),WholeSize-FIntVector(2),Error,true);
            Split=RaftSimAdvectLiquidInterfaceHighOrderRegions(Graph,Halo,Regions,Cell,Dt,Error,true);
            if(!WholeStep.Scalar || Split.Num()!=4) { Graph.Execute();return; }
            Whole.Source=WholeStep.Scalar;
            for(int I=0;I<4;++I) Regions[I].Source=Split[I].Scalar;
        }
        TRefCountPtr<IPooledRenderTarget> Retained[5];
        const FRaftSimLiquidInterfaceHighOrderStep Final[5]={WholeStep,Split[0],Split[1],Split[2],Split[3]};
        FRHIGPUBufferReadback C0(TEXT("HighOrderRegions.WholeCounters")),C1(TEXT("HighOrderRegions.LeftCounters")),C2(TEXT("HighOrderRegions.RightCounters"));
        FRHIGPUBufferReadback C3(TEXT("HighOrderRegions.UpperLeftCounters")),C4(TEXT("HighOrderRegions.UpperRightCounters"));
        FRHIGPUBufferReadback* Readbacks[5]={&C0,&C1,&C2,&C3,&C4};
        for(int I=0;I<5;++I)
        {
            Graph.QueueTextureExtraction(Final[I].Scalar,&Retained[I]);
            AddEnqueueCopyPass(Graph,Readbacks[I],Final[I].Diagnostics,32);
        }
        Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();Counters.SetNumUninitialized(40);
        for(int I=0;I<5;++I)
        {
            const auto* Values=Readbacks[I]->Lock(32);
            if(!Values) { Error=TEXT("Missing owner-cut diagnostics");return; }
            FMemory::Memcpy(Counters.GetData()+I*8,Values,32);Readbacks[I]->Unlock();
            const auto Size=I==0?WholeSize:LocalSize;Results[I].SetNumUninitialized(Size.X*Size.Y*Size.Z);
            Cmd.Transition(FRHITransitionInfo(Retained[I]->GetRHI(),ERHIAccess::Unknown,ERHIAccess::CopySrc));
            for(int Z=0;Z<Size.Z;++Z)
            {
                FRHIGPUTextureReadback Readback(TEXT("HighOrderRegions.Scalar"));
                Readback.EnqueueCopy(Cmd,Retained[I]->GetRHI(),FIntVector(0,0,Z),0,FIntVector(Size.X,Size.Y,1));Cmd.SubmitAndBlockUntilGPUIdle();
                int Pitch=0;const auto* Pixels=static_cast<const float*>(Readback.Lock(Pitch));
                if(!Pixels || Pitch<Size.X) { Error=TEXT("Incomplete owner-cut readback");return; }
                for(int Y=0;Y<Size.Y;++Y) FMemory::Memcpy(Results[I].GetData()+(Z*Size.Y+Y)*Size.X,Pixels+Y*Pitch,Size.X*4);
                Readback.Unlock();
            }
        }
        Ran=true;
    });
    FlushRenderingCommands();if(!Ran) { AddError(Error);return false; }
    TestTrue(TEXT("Invalid plan and aliased owners rejected"),Rejected);
    for(int I=0;I<5;++I) for(int D:{1,2,6,7}) TestEqual(TEXT("No trace/nonfinite failure"),Counters[I*8+D],0u);
    for(int D:{0,3,5}) TestEqual(TEXT("Owner split preserves updated/high-order/fallback counts"),Counters[D],Counters[8+D]+Counters[16+D]+Counters[24+D]+Counters[32+D]);
    double Maximum=0;int Compared=0;
    for(int Owner=0;Owner<4;++Owner) for(int Z=0;Z<10;++Z) for(int Y=0;Y<7;++Y) for(int X=0;X<26;++X)
    {
        const int GX=X+22*(Owner%2),GY=Y+3*(Owner/2);const float Actual=Results[Owner+1][(Z*7+Y)*26+X];
        const float Expected=Results[0][(Z*10+GY)*48+GX];const double Delta=FMath::Abs(double(Actual)-Expected);
        if(!FMath::IsFinite(Actual) || Delta>.02)
        { AddError(FString::Printf(TEXT("24-step owner seam mismatch owner%d xyz%d,%d,%d: %g versus %g, error%gcm"),Owner,X,Y,Z,Actual,Expected,Delta));return false; }
        Maximum=FMath::Max(Maximum,Delta);++Compared;
    }
    AddInfo(FString::Printf(TEXT("24-step four-owner/whole GPU transport: %d samples including XY corner halos, maximum error %.9gcm. Not native particle coupling or visual acceptance."),Compared,Maximum));
    return true;
}
