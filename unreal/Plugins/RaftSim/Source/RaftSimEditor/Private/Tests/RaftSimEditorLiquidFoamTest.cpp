#include "Misc/AutomationTest.h"
#include "RaftSimLiquidFoamGPU.h"
#include "RenderGraphBuilder.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidCurrentFoamGPURegression,
    "RaftSim.Editor.LiquidFixtureCurrentFoamGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLiquidCurrentFoamGPURegression::RunTest(const FString&)
{
    if (GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("Actual GPU required for surface foam"));return false; }
    constexpr int32 R=12,V=6,Count=R*R*R;
    for (int32 Case=0;Case<17;++Case)
    {
        TArray<FFloat16Color> Current,History,Flow,Boundary,Actual;
        Current.Init(FFloat16Color(FLinearColor(0,.75,10,.25)),Count);History=Current;
        if (Case==4 || (Case>=9 && Case<=11) || Case==13 || Case>=15)
            for (int32 I=0;I<Count;++I)
                Current[I].R=FFloat16(float(10*((Case==11?I%R:I/(R*R))-5)));
        if (Case==8) for (auto& P:Current) P.R=FFloat16(50.f);
        Flow.Init(FFloat16Color(FLinearColor(0,0,0,0)),V*V*V);Boundary=Flow;
        for (int32 I=0;I<Count;++I) History[I].G=FFloat16(Case==3?.5f:I%R==4?1.f:0.f);
        for (int32 I=0;I<V*V*V;++I)
        {
            if (Case==0) Flow[I].R=FFloat16(50.f);
            if (Case==4) Flow[I].G=FFloat16(float(200+40*(I%V)));
            if (Case==5) Boundary[I].A=FFloat16(1.f);
            const float X=(I%V+.5f)*20-60,Z=(I/(V*V)+.5f)*20-60,Y=((I/V)%V+.5f)*20-60;
            if (Case==9) Flow[I]=FFloat16Color(FLinearColor(-3*Y,400+3*X,0,0));
            if (Case==10 || Case>=15) Flow[I]=FFloat16Color(FLinearColor(-2*X,400,2*Z,0));
            if (Case==11) Flow[I]=FFloat16Color(FLinearColor(2*X,400,-2*Z,0));
            if (Case==12) Flow[I].G=FFloat16(float(200+40*(I%V)));
            if (Case==13 || Case==14) Flow[I]=FFloat16Color(FLinearColor(
                300+230*FMath::Sin(I*.73f),400+310*FMath::Cos(I*.37f),180*FMath::Sin(I*.91f),0));
        }
        if (Case==4 || Case>=9) for (auto& P:History) P.G=FFloat16(0.f);
        if (Case==14) for(int32 I=0;I<Count;++I) History[I].G=FFloat16(float((I*37)%101)/100.f);
        const FVector4f ClockValue(10,Case==1||Case==2?0.f:Case==6?.5f:.1f,Case==2?1.f:0.f,1);
        uint32 Status[4]={0,0,0,0};FString Error;bool Success=false;
        TArray<FVector4f> ActualAudit;ActualAudit.SetNum(Count);
        ENQUEUE_RENDER_COMMAND(RaftSimFoamAnalyticTest)([&](FRHICommandListImmediate& Cmd)
        {
            auto Upload=[&](const TCHAR* Name,int32 Size,const TArray<FFloat16Color>& Pixels)
            {
                auto T=Cmd.CreateTexture(FRHITextureCreateDesc::Create3D(Name,Size,Size,Size,PF_FloatRGBA)
                    .SetFlags(TexCreate_ShaderResource).SetInitialState(ERHIAccess::CopyDest));
                Cmd.UpdateTexture3D(T,0,FUpdateTextureRegion3D(0,0,0,0,0,0,Size,Size,Size),Size*sizeof(FFloat16Color),Size*Size*sizeof(FFloat16Color),reinterpret_cast<const uint8*>(Pixels.GetData()));
                Cmd.Transition(FRHITransitionInfo(T,ERHIAccess::CopyDest,ERHIAccess::SRVMask));return T;
            };
            auto C=Upload(TEXT("FoamTestCurrent"),R,Current),H=Upload(TEXT("FoamTestHistory"),R,History);
            auto F=Upload(TEXT("FoamTestFlow"),V,Flow),B=Upload(TEXT("FoamTestBoundary"),V,Boundary);
            FRDGBuilder Graph(Cmd);
            auto Register=[&](FTextureRHIRef Texture,const TCHAR* Name){return Graph.RegisterExternalTexture(CreateRenderTarget(Texture,Name));};
            auto Clock=CreateStructuredBuffer(Graph,TEXT("FoamTestClock"),TConstArrayView<FVector4f>(&ClockValue,1));
            auto DiagnosticDesc=FRDGBufferDesc::CreateStructuredDesc(sizeof(uint32),4);DiagnosticDesc.Usage|=BUF_SourceCopy;
            auto Diagnostics=Graph.CreateBuffer(DiagnosticDesc,TEXT("FoamTestDiagnostics"));
            AddClearUAVPass(Graph,Graph.CreateUAV(Diagnostics),0);
            auto Result=RaftSimLiquidFoamGPU(Graph,Register(C,TEXT("FoamTestC")),Case==7?nullptr:Register(H,TEXT("FoamTestH")),
                Register(F,TEXT("FoamTestF")),Register(B,TEXT("FoamTestB")),Clock,0,FVector3f(Case==8?200.f:120.f),
                Case==15?FVector2f(1000,20):Case==16?FVector2f(20,1000):FVector2f(1000,1000),Case==4||Case>=9?1.f:0.f,
                Case==3||Case==4||Case>=9?.25f:0.f,Diagnostics,Error);
            if (!Result.Surface) return;
            TRefCountPtr<IPooledRenderTarget> Output;
            Graph.QueueTextureExtraction(Result.Surface,&Output);
            FRHIGPUBufferReadback StatusRead(TEXT("FoamTestStatus"));AddEnqueueCopyPass(Graph,&StatusRead,Diagnostics,sizeof(Status));
            FRHIGPUBufferReadback AuditRead(TEXT("FoamTestAudit"));
            AddEnqueueCopyPass(Graph,&AuditRead,Result.Audit,Count*sizeof(FVector4f));
            Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
            FMemory::Memcpy(Status,StatusRead.Lock(sizeof(Status)),sizeof(Status));StatusRead.Unlock();
            FMemory::Memcpy(ActualAudit.GetData(),AuditRead.Lock(Count*sizeof(FVector4f)),Count*sizeof(FVector4f));AuditRead.Unlock();
            Cmd.Read3DSurfaceFloatData(Output->GetRHI(),FIntRect(0,0,R,R),FIntPoint(0,R),Actual);Success=true;
        });
        FlushRenderingCommands();
        if (!TestTrue(TEXT("Foam dispatched on real GPU"),Success)) { AddError(Error);return false; }
        if (Case==6)
        {
            TestTrue(TEXT("Invalid simulation delta diagnosed"),Status[2]>0);
            TestFalse(TEXT("Invalid delta does not produce accepted finite foam"),FMath::IsFinite(Actual[0].G.GetFloat()));
            continue;
        }
        TestTrue(TEXT("Valid foam diagnostics zero"),(Status[0]|Status[1]|Status[2]|Status[3])==0);
        bool Metadata=true,Finite=true;float MaxError=0;
        for (int32 I=0;I<Count;++I)
        {
            Metadata &= Actual[I].R==Current[I].R && Actual[I].B==Current[I].B && Actual[I].A==Current[I].A;
            const float Value=Actual[I].G.GetFloat();Finite &= FMath::IsFinite(Value) && Value>=0 && Value<=1;
            float Expected=0;
            if (Case==0) Expected=I%R==4 || I%R==5?.5f:0.f;
            if (Case==1) Expected=History[I].G.GetFloat();
            if (Case==3) Expected=FFloat16(.5f*FMath::Exp(-.025f)).GetFloat();
            if (Case!=4 && Case<9) MaxError=FMath::Max(MaxError,FMath::Abs(Value-Expected));
        }
        TestTrue(TEXT("Single surface distance and clock unchanged"),Metadata);
        TestTrue(TEXT("Finite bounded foam"),Finite);
        TestTrue(TEXT("Advection/pause/reset/decay/solid/initialization analytic result"),MaxError<=1e-6f);
        if (Case==4)
        {
            const float Expected=FFloat16((.28f/.53f)*(1-FMath::Exp(-.053f))).GetFloat();
            TestEqual(TEXT("Shear source uses current SDF surface"),Actual[5+R*(5+R*5)].G.GetFloat(),Expected,1e-5f);
        }
        if (Case==9 || Case==12)
            TestEqual(TEXT("Rigid rotation or degenerate SDF produces no source"),Actual[5+R*(5+R*5)].G.GetFloat(),0.f);
        if (Case==10 || Case==11)
        {
            const float Expected=FFloat16((.6f/.85f)*(1-FMath::Exp(-.085f))).GetFloat();
            TestEqual(TEXT("Tangential compression invariant under surface rotation"),Actual[5+R*(5+R*5)].G.GetFloat(),Expected,1e-5f);
        }
        if (Case>=15)
        {
            // Independent physical half-extents: source fades at the narrow
            // side only, not an incorrectly inferred square. Uniform affine
            // compression gives a known source before the rectangular taper.
            const float Rate=.6f*(15.f/40.f);
            const float Expected=FFloat16((Rate/(Rate+.25f))*(1-FMath::Exp(-(Rate+.25f)*.1f))).GetFloat();
            TestEqual(TEXT("Rectangle center uses nearest physical side"),Actual[5+R*(5+R*5)].G.GetFloat(),Expected,1e-5f);
            const int32 Narrow=Case==15?5+R*(8+R*5):8+R*(5+R*5);
            const int32 Wide=Case==15?8+R*(5+R*5):5+R*(8+R*5);
            TestEqual(TEXT("Outside narrow physical side has no source"),Actual[Narrow].G.GetFloat(),0.f);
            TestEqual(TEXT("Long side retains source at same distance"),Actual[Wide].G.GetFloat(),Expected,1e-5f);
            continue;
        }
        if (Case>=13)
        {
            // Independent double-precision interpolation of the uploaded half
            // texels. Non-affine velocities expose filtering precision lost
            // by tests that only use exactly representable uniform gradients.
            auto Sample=[&](FVector Unit)
            {
                const FVector Q=Unit*V-FVector(.5);
                const FIntVector Low(FMath::FloorToInt(Q.X),FMath::FloorToInt(Q.Y),FMath::FloorToInt(Q.Z));
                const FVector T=Q-FVector(Low);FVector Result=FVector::ZeroVector;
                for (int32 Z=0;Z<2;++Z) for (int32 Y=0;Y<2;++Y) for (int32 X=0;X<2;++X)
                {
                    const int32 Index=FMath::Clamp(Low.X+X,0,V-1)+V*(FMath::Clamp(Low.Y+Y,0,V-1)+V*FMath::Clamp(Low.Z+Z,0,V-1));
                    const auto& F=Flow[Index];
                    Result+=FVector(F.R.GetFloat(),F.G.GetFloat(),F.B.GetFloat())*
                        ((X?T.X:1-T.X)*(Y?T.Y:1-T.Y)*(Z?T.Z:1-T.Z));
                }
                return Result;
            };
            if(Case==14)
            {
                double MaxHistoryError=0;int32 Advected=0;
                for(int32 Z=2;Z<R-2;++Z) for(int32 Y=2;Y<R-2;++Y) for(int32 X=2;X<R-2;++X)
                {
                    const int32 I=X+R*(Y+R*Z);const FVector Unit=(FVector(X,Y,Z)+FVector(.5))/R;
                    const FVector Mid=Unit-Sample(Unit)*(.5*double(ClockValue.Y)/120);
                    const FVector Back=Unit-Sample(Mid)*(double(ClockValue.Y)/120);
                    double Expected=0;
                    if(Back.GetMin()>0 && Back.GetMax()<1)
                    {
                        const FVector Q=Back*R-FVector(.5);
                        const FIntVector Low(FMath::FloorToInt(Q.X),FMath::FloorToInt(Q.Y),FMath::FloorToInt(Q.Z));
                        const FVector T=Q-FVector(Low);
                        for(int32 K=0;K<2;++K) for(int32 J=0;J<2;++J) for(int32 A=0;A<2;++A)
                        {
                            const int32 N=FMath::Clamp(Low.X+A,0,R-1)+R*(FMath::Clamp(Low.Y+J,0,R-1)+R*FMath::Clamp(Low.Z+K,0,R-1));
                            Expected+=History[N].G.GetFloat()*(A?T.X:1-T.X)*(J?T.Y:1-T.Y)*(K?T.Z:1-T.Z);
                        }
                        ++Advected;
                    }
                    MaxHistoryError=FMath::Max(MaxHistoryError,FMath::Abs(Expected-ActualAudit[I].Y));
                    TestEqual(TEXT("Transport-only degenerate surface has no foam source"),ActualAudit[I].X,0.f);
                }
                TestTrue(TEXT("High-contrast history exercises fractional backtraces"),Advected>20);
                TestTrue(TEXT("RK2 history interpolation preserves fractional precision"),MaxHistoryError<=.00001);
                continue;
            }
            double MaxRateError=0;int32 SourceCount=0;
            for (int32 Z=2;Z<R-2;++Z) for (int32 Y=2;Y<R-2;++Y) for (int32 X=2;X<R-2;++X)
            {
                const int32 I=X+R*(Y+R*Z);const FVector Unit=(FVector(X,Y,Z)+FVector(.5))/R;
                const FVector DX=(Sample(Unit+FVector(1./V,0,0))-Sample(Unit-FVector(1./V,0,0)))/40.;
                const FVector DY=(Sample(Unit+FVector(0,1./V,0))-Sample(Unit-FVector(0,1./V,0)))/40.;
                const FVector DZ=(Sample(Unit+FVector(0,0,1./V))-Sample(Unit-FVector(0,0,1./V)))/40.;
                const double Curl=FVector(DY.Z-DZ.Y,DZ.X-DX.Z,DX.Y-DY.X).Length();
                const double Strain=FMath::Sqrt(2*(DX.X*DX.X+DY.Y*DY.Y+DZ.Z*DZ.Z)+
                    FMath::Square(DX.Y+DY.X)+FMath::Square(DX.Z+DZ.X)+FMath::Square(DY.Z+DZ.Y));
                const double Compression=FMath::Max(-(DX.X+DY.Y),0.);
                const double Band=FMath::Clamp(1-FMath::Abs(double(Current[I].R.GetFloat()))/20.,0.,1.);
                const double Speed=FMath::Clamp((Sample(Unit).Length()-50)/150,0.,1.);
                const double Expected=FMath::Min(8.,Band*Speed*(FMath::Max(FMath::Min(Curl,Strain)-1.2,0.)*.35+
                    FMath::Max(Compression-.8,0.)*.5));
                SourceCount+=Expected>0;MaxRateError=FMath::Max(MaxRateError,FMath::Abs(Expected-ActualAudit[I].X));
            }
            TestTrue(TEXT("Non-affine half-texel fixture exercises active sources"),SourceCount>20);
            TestTrue(TEXT("Source interpolation retains precision before differentiation"),MaxRateError<=.00001);
        }
    }
    return true;
}
