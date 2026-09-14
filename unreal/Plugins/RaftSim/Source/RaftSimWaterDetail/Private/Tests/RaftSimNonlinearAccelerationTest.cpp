#include "Misc/AutomationTest.h"
#include "RaftSimNonlinearAccelerationGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"
#include <limits>

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FNonlinearAccelerationTest,"RaftSim.WaterDetail.NonlinearAccelerationGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FNonlinearAccelerationTest::RunTest(const FString&)
{
    if(GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("Actual GPU required for nonlinear acceleration evidence"));return false; }
    bool Passed=true,InvalidDescriptorsRejected=true;TArray<FString> Records;FString Error;
    ENQUEUE_RENDER_COMMAND(RaftSimNonlinearAccelerationTest)([&](FRHICommandListImmediate& Cmd)
    {
        TMap<int32,TArray<uint8>> DirectRecords;
        for(int32 Mode=0;Mode<5;++Mode)
        for(int32 Case=0;Case<16;++Case)
        {
            const bool Distributed=Mode!=0,Fused=Mode==2 || Mode==4,Indirect=Mode>=3;
            if(!Distributed && (Case==9 || Case==10))continue;
            const FIntPoint Size=Case==9?FIntPoint(512,512):Case==10?FIntPoint(1,257):
                (Case==2 || Case==7)?FIntPoint(128,128):FIntPoint(17,13);
            const bool Periodic=Case==1 || Case==6 || Case==9,Zero=Case==3,BadGraph=Case==4,PhysicalSlope=Case>=5,BadSlope=Case==8;
            const bool MixedFraction=Case==11,ZeroFraction=Case==12,BadFraction=Case==13;
            const int32 N=Size.X*Size.Y;const double Dx=.5;
            const FVector2f Lengths(.4052787713439809f,.03916567310046354f);
            TArray<FVector2f> Geometry,Slopes;TArray<uint32> Pairs;TArray<FVector4f> Expected,RHS;
            TArray<float> Fractions;
            for(int32 Y=0;Y<Size.Y;++Y)for(int32 X=0;X<Size.X;++X)
            {
                float H=.9f+.2f*FMath::Sin(float(X)*.23f)+.1f*FMath::Cos(float(Y)*.31f);
                if(X==5 && Y==5)H=0;if(X==7 && Y==6)H=1e-20f;
                Geometry.Add(FVector2f(H,.1f*FMath::Sin(float(X)*.17f)*FMath::Cos(float(Y)*.13f)));
                Fractions.Add(ZeroFraction?0.f:MixedFraction?((X/4+Y/3)%3==0?0.f:(X/4+Y/3)%3==1?.35f:1.f):1.f);
                const double Root=FMath::Sqrt(double(H));
                Expected.Add(Zero?FVector4f(0,0,0,0):FVector4f(Root*.2*FMath::Sin(X*.2),Root*.3*FMath::Cos(Y*.19),
                    Root*.15*FMath::Cos(X*.11),Root*-.1*FMath::Sin(Y*.17)));
            }
            auto Neighbor=[&](int32 I,int32 Axis)
            { int32 X=I%Size.X,Y=I/Size.X;if(Axis==0)X=(X+1)%Size.X;else Y=(Y+1)%Size.Y;return Y*Size.X+X; };
            // Fixed sampled-bed derivative: independent of h and wet graph.
            for(int32 I=0;I<N;++I)
            {
                FVector2f Slope(0,0);
                for(int32 A=0;A<2;++A)
                {
                    const int32 Coord=A==0?I%Size.X:I/Size.X,Count=A==0?Size.X:Size.Y,Stride=A==0?1:Size.X;
                    const int32 L=Coord==0?(Periodic?I+(Count-1)*Stride:I):I-Stride;
                    const int32 R=Coord==Count-1?(Periodic?I-(Count-1)*Stride:I):I+Stride;
                    if(Count==1)continue;
                    const double Span=(!Periodic && (Coord==0 || Coord==Count-1))?Dx:2*Dx;
                    Slope[A]=float((double(Geometry[R].Y)-Geometry[L].Y)/Span);
                }
                Slopes.Add(Slope);
            }
            for(int32 I=0;I<N;++I)
            {
                uint32 Mask=0;for(int32 A=0;A<2;++A)
                {
                    const bool Boundary=A==0?I%Size.X==Size.X-1:I/Size.X==Size.Y-1;
                    if((A==0?Size.X:Size.Y)>1 && (Periodic || !Boundary) && Geometry[I].X>0 && Geometry[Neighbor(I,A)].X>0)Mask|=1u<<A;
                }
                Pairs.Add(Mask);
            }
            // Independent double-precision D/G implementation, using face
            // accumulation, not the shader's factored W coefficient stencil.
            auto Grad=[&](const TArray<double>& Scalar)
            {
                TArray<FVector2D> Out;Out.Init(FVector2D::ZeroVector,N);
                for(int32 I=0;I<N;++I)for(int32 A=0;A<2;++A)if(Pairs[I]&(1u<<A))
                {
                    const int32 J=Neighbor(I,A);const double Total=double(Geometry[I].X)+Geometry[J].X;
                    const double Delta=(Scalar[J]-Scalar[I])/Dx;
                    Out[I][A]+=Geometry[I].X/Total*Delta;Out[J][A]+=Geometry[J].X/Total*Delta;
                }
                return Out;
            };
            auto Div=[&](const TArray<FVector2D>& Vector)
            {
                TArray<double> Out;Out.Init(0.,N);
                for(int32 I=0;I<N;++I)for(int32 A=0;A<2;++A)if(Pairs[I]&(1u<<A))
                {
                    const int32 J=Neighbor(I,A);const double Total=double(Geometry[I].X)+Geometry[J].X;
                    const double Face=(Geometry[I].X*Vector[I][A]+Geometry[J].X*Vector[J][A])/Total/Dx;
                    Out[I]+=Face;Out[J]-=Face;
                }
                return Out;
            };
            TArray<double> Bed;for(const auto& G:Geometry)Bed.Add(G.Y);auto B=Grad(Bed);
            if(PhysicalSlope)for(int32 I=0;I<N;++I)B[I]=Geometry[I].X>0?FVector2D(Slopes[I].X,Slopes[I].Y):FVector2D::ZeroVector;
            auto Apply=[&](const TArray<FVector2D>& Value,double Length)
            {
                TArray<FVector2D> A;for(int32 I=0;I<N;++I)A.Add(Geometry[I].X>0?Value[I]/FMath::Sqrt(double(Geometry[I].X)):FVector2D::ZeroVector);
                const auto D=Div(A);TArray<double> W,HW;
                for(int32 I=0;I<N;++I)
                {
                    const double H32=Geometry[I].X*FMath::Sqrt(double(Geometry[I].X));
                    W.Add(Fractions[I]*(H32*D[I]-1.5*FVector2D::DotProduct(B[I],Value[I])));HW.Add(H32*W[I]);
                }
                const auto G=Grad(HW);TArray<FVector2D> Out;
                for(int32 I=0;I<N;++I)
                {
                    const double InvRoot=Geometry[I].X>0?1/FMath::Sqrt(double(Geometry[I].X)):0;
                    Out.Add(Value[I]+Length*(-InvRoot*G[I]-1.5*B[I]*W[I]+.75*Fractions[I]*B[I]*FVector2D::DotProduct(B[I],Value[I])));
                }
                return Out;
            };
            TArray<FVector2D> X0,X1;for(const auto& X:Expected){X0.Add({X.X,X.Y});X1.Add({X.Z,X.W});}
            // Either pole may be inactive from the beginning while the other
            // still needs iterations. Inactive reduction lanes must stay zero.
            if(Case==14 || Case==15)
            {
                for(int32 I=0;I<N;++I)
                {
                    if(Case==14){X0[I]=FVector2D::ZeroVector;Expected[I].X=Expected[I].Y=0;}
                    else {X1[I]=FVector2D::ZeroVector;Expected[I].Z=Expected[I].W=0;}
                }
            }
            const auto B0=Apply(X0,Lengths.X),B1=Apply(X1,Lengths.Y);
            for(int32 I=0;I<N;++I)RHS.Add(FVector4f(B0[I].X,B0[I].Y,B1[I].X,B1[I].Y));
            if(BadGraph)Pairs[Size.X-1]|=1u;
            if(BadSlope)Slopes[3].X=std::numeric_limits<float>::quiet_NaN();
            if(BadFraction)Fractions[3]=std::numeric_limits<float>::quiet_NaN();
            FRDGBuilder Graph(Cmd);
            auto G=CreateStructuredBuffer(Graph,TEXT("AccelerationTest.Geometry"),TConstArrayView<FVector2f>(Geometry));
            auto P=CreateStructuredBuffer(Graph,TEXT("AccelerationTest.Pairs"),TConstArrayView<uint32>(Pairs));
            auto R=CreateStructuredBuffer(Graph,TEXT("AccelerationTest.RHS"),TConstArrayView<FVector4f>(RHS));
            auto S=CreateStructuredBuffer(Graph,TEXT("AccelerationTest.PhysicalSlope"),TConstArrayView<FVector2f>(Slopes));
            auto F=CreateStructuredBuffer(Graph,TEXT("AccelerationTest.NonbreakingFraction"),TConstArrayView<float>(Fractions));
            FRDGBufferRef IterationArgs=nullptr;
            if(Indirect)
            {
                IterationArgs=Graph.CreateBuffer(FRDGBufferDesc::CreateIndirectDesc(4u,6u),TEXT("AccelerationTest.IndirectArgs"));
                const uint32 Arguments[]={uint32(FMath::DivideAndRoundUp(N,256)),1u,1u,1u,1u,1u};
                Graph.QueueBufferUpload(IterationArgs,Arguments,sizeof(Arguments));
            }
            if(Case==0)
            {
                InvalidDescriptorsRejected &= !RaftSimSolveNonlinearAccelerationGPU(Graph,G,P,R,Size,.5f,Lengths,Periodic,41,Error).Solution;
                InvalidDescriptorsRejected &= !RaftSimSolveNonlinearAccelerationGPU(Graph,G,P,R,Size,0,Lengths,Periodic,40,Error).Solution;
                InvalidDescriptorsRejected &= !RaftSimSolveNonlinearAccelerationGPU(Graph,R,P,R,Size,.5f,Lengths,Periodic,40,Error).Solution;
                InvalidDescriptorsRejected &= !RaftSimSolveNonlinearAccelerationGPU(Graph,G,P,R,Size,.5f,Lengths,Periodic,40,Error,R).Solution;
                InvalidDescriptorsRejected &= !RaftSimSolveNonlinearAccelerationGPU(Graph,G,P,R,Size,.5f,Lengths,Periodic,40,Error,S,true,R).Solution;
                for(int32 Fault=0;Fault<4;++Fault)
                {
                    auto Desc=FRDGBufferDesc::CreateIndirectDesc(Fault==1?8u:4u,Fault==0?5u:Fault==1?3u:6u);
                    if(Fault==2)Desc.Usage &= ~BUF_DrawIndirect;
                    auto BadArgs=Graph.CreateBuffer(Desc,TEXT("AccelerationTest.BadIndirectArgs"));
                    InvalidDescriptorsRejected &= !RaftSimSolveNonlinearAccelerationGPU(Graph,G,P,R,Size,.5f,Lengths,Periodic,40,Error,
                        S,Fault!=3,F,true,BadArgs).Solution && !Error.IsEmpty();
                }
            }
            auto Result=RaftSimSolveNonlinearAccelerationGPU(Graph,G,P,R,Size,.5f,Lengths,Periodic,40,Error,PhysicalSlope?S:nullptr,Distributed,
                (MixedFraction || ZeroFraction || BadFraction)?F:nullptr,Fused,IterationArgs);
            if(!Result.Solution || !Error.IsEmpty()){Passed=false;Graph.Execute();return;}
            // Actual GPU component intervals, not scene FPS. Inputs stay on
            // the GPU; timestamps bracket clear/prepare/two-pole solve only.
            // Extract diagnostics so RDG cannot cull the repeated work.
            FRenderQueryPoolRHIRef TimingPool;
            TArray<FRHIPooledRenderQuery> TimingQueries;
            TArray<TRefCountPtr<FRDGPooledBuffer>> TimingKeepAlive;
            if(Case==7 && !Fused && !Indirect && GSupportsTimestampRenderQueries)
            {
                constexpr int32 Samples=8;TimingPool=RHICreateRenderQueryPool(RQT_AbsoluteTime,Samples*2);
                TimingKeepAlive.SetNum(Samples);
                for(int32 I=0;I<Samples*2;++I)TimingQueries.Add(TimingPool->AllocateQuery());
                for(int32 I=0;I<Samples;++I)
                {
                    auto* Begin=TimingQueries[2*I].GetQuery();auto* End=TimingQueries[2*I+1].GetQuery();
                    Graph.AddPass(RDG_EVENT_NAME("AccelerationTest.TimestampBegin"),ERDGPassFlags::None,
                        [Begin](FRHICommandList& List){List.EndRenderQuery(Begin);});
                    auto Timed=RaftSimSolveNonlinearAccelerationGPU(Graph,G,P,R,Size,.5f,Lengths,false,40,Error,S,Distributed,nullptr,false);
                    if(!Timed.Diagnostics){Passed=false;Graph.Execute();return;}
                    Graph.QueueBufferExtraction(Timed.Diagnostics,&TimingKeepAlive[I]);
                    Graph.AddPass(RDG_EVENT_NAME("AccelerationTest.TimestampEnd"),ERDGPassFlags::None,
                        [End](FRHICommandList& List){List.EndRenderQuery(End);});
                }
            }
            FRHIGPUBufferReadback XRead(TEXT("AccelerationTest.X")),RRead(TEXT("AccelerationTest.TrueResidual")),DRead(TEXT("AccelerationTest.Diagnostics"));
            AddEnqueueCopyPass(Graph,&XRead,Result.Solution,N*16);AddEnqueueCopyPass(Graph,&RRead,Result.Residual,N*16);AddEnqueueCopyPass(Graph,&DRead,Result.Diagnostics,16);
            Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
            for(int32 I=0;I<TimingQueries.Num()/2;++I)
            {
                uint64 Begin=0,End=0;
                if(RHIGetRenderQueryResult(TimingQueries[2*I].GetQuery(),Begin,true) &&
                    RHIGetRenderQueryResult(TimingQueries[2*I+1].GetQuery(),End,true) && End>=Begin)
                    Records.Add(FString::Printf(TEXT("GPU component distributed=%d 128x128 physical-slope sample %d: %.6f ms (clear/prepare/two-pole solve, excludes upload/readback; not frame FPS)"),Distributed,I,(End-Begin)/1000.));
                else Records.Add(TEXT("GPU component timestamp unavailable; no timing claim"));
            }
            const auto* X=static_cast<const FVector4f*>(XRead.Lock(N*16));const auto* TrueR=static_cast<const FVector4f*>(RRead.Lock(N*16));
            const auto* Diagnostic=static_cast<const uint32*>(DRead.Lock(16));
            if(!X || !TrueR || !Diagnostic){Passed=false;return;}
            if(BadGraph || BadSlope || BadFraction)Passed &= Diagnostic[0]>0;
            else
            {
                double MaxError=0,MaxAccelerationError=0,Residual2=0,Norm2=0;
                Passed &= Diagnostic[0]==0 && Diagnostic[1]==0 && Diagnostic[2]<=40 && Diagnostic[3]<=40;
                if(Zero)Passed &= Diagnostic[2]==0 && Diagnostic[3]==0;
                if(ZeroFraction)Passed &= Diagnostic[2]<=1 && Diagnostic[3]<=1;
                if(Case==14)Passed &= Diagnostic[2]==0 && Diagnostic[3]>0;
                if(Case==15)Passed &= Diagnostic[3]==0 && Diagnostic[2]>0;
                for(int32 I=0;I<N;++I)for(int32 A=0;A<4;++A)
                {
                    const double E=FMath::Abs(double(X[I][A])-Expected[I][A]);MaxError=FMath::Max(MaxError,E);
                    if(Geometry[I].X>0)MaxAccelerationError=FMath::Max(MaxAccelerationError,E/FMath::Sqrt(double(Geometry[I].X)));
                    Passed &= FMath::IsFinite(X[I][A]) && FMath::IsFinite(TrueR[I][A]);
                    if((Case==14 && A<2) || (Case==15 && A>=2))Passed &= X[I][A]==0;
                    Residual2+=double(TrueR[I][A])*TrueR[I][A];Norm2+=double(RHS[I][A])*RHS[I][A];
                }
                const double Relative=Norm2>0?FMath::Sqrt(Residual2/Norm2):FMath::Sqrt(Residual2);
                Passed &= MaxAccelerationError<1e-4 && Relative<2e-5;
                Records.Add(FString::Printf(TEXT("distributed=%d fused=%d %dx%d periodic=%d zero=%d physical-slope=%d mixed-fraction=%d zero-fraction=%d: max solution error %.9g, acceleration error %.9g, true relative residual %.9g, iterations %u/%u"),
                    Distributed,Fused,Size.X,Size.Y,Periodic,Zero,PhysicalSlope,MixedFraction,ZeroFraction,MaxError,MaxAccelerationError,Relative,Diagnostic[2],Diagnostic[3]));
            }
            if(Distributed)
            {
                TArray<uint8> Record;Record.SetNumUninitialized(N*32+16);
                FMemory::Memcpy(Record.GetData(),X,N*16);FMemory::Memcpy(Record.GetData()+N*16,TrueR,N*16);
                FMemory::Memcpy(Record.GetData()+N*32,Diagnostic,16);
                const int32 Key=Case+(Fused?16:0);
                if(!Indirect)DirectRecords.Add(Key,MoveTemp(Record));
                else
                {
                    const auto* Direct=DirectRecords.Find(Key);const bool Exact=Direct && *Direct==Record;
                    Passed &= Exact;
                    Records.Add(FString::Printf(TEXT("acceleration indirect/direct fused%d case%d solution/residual/diagnostics exact%d"),Fused,Case,Exact));
                }
            }
            XRead.Unlock();RRead.Unlock();DRead.Unlock();
        }
    });
    FlushRenderingCommands();
    TestTrue(TEXT("invalid descriptors and iteration increase rejected"),InvalidDescriptorsRejected);
    TestTrue(TEXT("coupled two-pole GPU solve matches independent manufactured solutions including dry/thin/boundary cells"),Passed);
    for(const auto& Record:Records)AddInfo(Record);
    if(!Error.IsEmpty())AddError(Error);
    return !HasAnyErrors();
}
#endif
