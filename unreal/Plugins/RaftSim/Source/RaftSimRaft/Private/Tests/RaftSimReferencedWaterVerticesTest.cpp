#include "RaftSimReferencedWaterVertices.h"
#include "RaftSimShorelineCrests.h"
#include "RaftSimWaterShoreline.h"
#include "Misc/AutomationTest.h"
#include "RaftSimShorelineMeshComponent.h"
#include "Engine/World.h"
#include "Misc/ScopeExit.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "RenderingThread.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimReferencedWaterVerticesTest,
    "RaftSim.M4.ReferencedWaterVertices",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimReferencedWaterVerticesTest::RunTest(const FString&)
{
    int64 Compared=0;
    for(double Sign:{-1.,1.})
    {
        FRaftSimReferencedWaterVertices Compact;
        FRaftSimShorelineCrests Reference,Candidate;
        for(int32 Frame=0;Frame<20;++Frame)
        {
            constexpr int32 Nx=17,Ny=13,N=Nx*Ny;
            TArray<FProcMeshVertex> Source;Source.SetNum(N);
            TArray<uint8> Wet,Available;Wet.SetNum(N);Available.Init(1,N);
            TArray<float> Depth,Bed,Coarse,Shore;
            Depth.SetNum(N);Bed.Init(0,N);Coarse.SetNum(N);Shore.SetNum(N);
            const float Amplitude=25.f+float(Frame/2);
            const auto Height=[Amplitude,Sign](const FVector2D& P)
            {const double X=P.X*.01-8.,Y=P.Y*.01*Sign-6.;return float(Amplitude*FMath::Exp(-X*X*.4-Y*Y*.25));};
            for(int32 Y=0;Y<Ny;++Y)for(int32 X=0;X<Nx;++X)
            {
                const int32 I=Y*Nx+X;
                Wet[I]=Frame!=15 && (Frame==7 || (X>=3+Frame/5 && X<=11 && (Frame<10 || I!=109)));
                Depth[I]=Wet[I] ? 1.f+float(Frame%3)*.01f : 0.f;
                Bed[I]=Wet[I] ? 0.f : 2.f;
                auto& V=Source[I];V.Position=FVector(X*100.+(Frame/4)*.03125,Y*100.*Sign,100.+Frame*.125);
                V.Normal=FVector::UpVector;V.Tangent=FProcMeshTangent(FVector::ForwardVector,true);
                V.Color=FColor((I+Frame)%255,31,77,255);
                V.UV0=FVector2D(X,Y);V.UV1=FVector2D(-2,3);V.UV2=FVector2D(.2,.4);V.UV3=FVector2D(1,Frame*.25);
                Shore[I]=.5f+float(I%3)*.1f;Coarse[I]=Height(FVector2D(V.Position.X,V.Position.Y))*Shore[I];
                V.Position.Z+=Coarse[I];
            }
            TArray<FProcMeshVertex> Base;
            TArray<uint32> Triangles;TArray<int32> Offsets;TArray<RaftSimWaterShoreline::FEdge> Edges;
            if(!TestTrue(TEXT("shore clipping succeeds"),RaftSimWaterShoreline::Build(Nx,Ny,MoveTemp(Source),
                Wet,Available,Depth,Bed,Base,Triangles,&Offsets,&Edges,true,true)))return false;
            Coarse.SetNumZeroed(Base.Num());Shore.SetNumZeroed(Base.Num());
            for(const auto& E:Edges){Coarse[E.Node]=Coarse[E.WetVertex];Shore[E.Node]=Shore[E.WetVertex];}
            if(!TestTrue(TEXT("referenced source builds"),Compact.Update(Base,Triangles,Coarse,Shore)))return false;
            for(int32 I=1;I<Compact.Sources.Num();++I)
                TestTrue(TEXT("source order strictly preserved"),Compact.Sources[I]>Compact.Sources[I-1]);
            FRaftSimShorelineCrestInput Input;Input.HeightAtWorldXYCm=Height;
            Input.ProfileKey={Amplitude};Input.BlendAlpha=Frame%4==0 ? 0.f : Frame%4==1 ? 1.f : .37f;
            Input.DetailWindowCm=FBox2D(FVector2D(500,Sign>0?400:-800),FVector2D(1000,Sign>0?800:-400));
            Input.DetailSpanCm=50;
            TArray<FProcMeshVertex> A,B;TArray<uint32> AT,BT;TArray<int32> AO,BO;
            if(!TestTrue(TEXT("reference crest history advances"),Reference.Update(Base,Triangles,Offsets,Coarse,Shore,Input,A,AT,AO)) ||
                !TestTrue(TEXT("compact crest history advances"),Candidate.Update(Compact.Vertices,Compact.Indices,Offsets,
                    Compact.Coarse,Compact.Shore,Input,B,BT,BO)))return false;
            bool Exact=AT.Num()==BT.Num() && AO==BO;
            for(int32 I=0;Exact && I<AT.Num();++I)
            {
                Exact=FRaftSimCrestMidpointExpansion::EqualAttributes(A[AT[I]],B[BT[I]]) &&
                    Reference.GetRenderedCorrectionsCm()[AT[I]]==Candidate.GetRenderedCorrectionsCm()[BT[I]] &&
                    Reference.GetTargetCorrectionsCm()[AT[I]]==Candidate.GetTargetCorrectionsCm()[BT[I]];
                ++Compared;
            }
            TestTrue(TEXT("all ordered triangle attributes and evolving corrections remain exact"),Exact);
            if(Frame==15)TestEqual(TEXT("empty draw retains only an anchor"),Compact.Vertices.Num(),1);
            const auto Before=Compact.Sources;
            auto Bad=Triangles;Bad.Append({uint32(Base.Num()),0,0});
            TestFalse(TEXT("invalid reference rejected without cache mutation"),Compact.Update(Base,Bad,Coarse,Shore));
            TestTrue(TEXT("invalid update preserves previous mapping"),Before==Compact.Sources);
        }
    }
    AddInfo(FString::Printf(TEXT("40 evolving clipped histories, both Y signs, %lld ordered triangle attributes compared"),Compared));
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimReferencedWaterComponentTest,
    "RaftSim.M4.ReferencedWaterComponent",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimReferencedWaterComponentTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Editor,false);
    if(!World)return false;
    ON_SCOPE_EXIT {World->DestroyWorld(false);World->RemoveFromRoot();FlushRenderingCommands();};
    auto* Actor=World->SpawnActor<AActor>();
    auto* Mesh=NewObject<URaftSimShorelineMeshComponent>(Actor);
    Actor->SetRootComponent(Mesh);Mesh->RegisterComponent();
    constexpr int32 N=9;
    const bool Compact=FParse::Param(FCommandLine::Get(),TEXT("RaftSimCompactCrestSource"));
    for(int32 Frame=0;Frame<4;++Frame)
    {
        TArray<FProcMeshVertex> Source;Source.SetNum(N*N);
        TArray<uint8> Wet,Available;Wet.Init(0,N*N);Available.Init(1,N*N);
        TArray<float> Depth,Bed,Coarse,Shore;
        Depth.Init(0,N*N);Bed.Init(2,N*N);Coarse.Init(0,N*N);Shore.Init(1,N*N);
        for(int32 Y=0;Y<N;++Y)for(int32 X=0;X<N;++X)
        {
            const int32 I=Y*N+X;
            auto& V=Source[I];V.Position=FVector(X*100.,Y*100.,100.+Frame);
            V.UV3=FVector2D(I,Frame);V.Normal=FVector::UpVector;
            Wet[I]=Frame<3 && X>=2+Frame && X<=6;
            if(Wet[I]){Depth[I]=1;Bed[I]=0;}
        }
        FRaftSimShorelineCrestInput Input;
        Input.SourceCrestCm=Coarse;Input.SourceShoreWeight=Shore;
        Input.HeightAtWorldXYCm=[](const FVector2D&){return 0.f;};Input.ProfileKey={0.};
        auto Copy=Source;
        if(!TestTrue(TEXT("component publishes changing clipped source"),Mesh->SetClippedWaterMesh(
            N,N,MoveTemp(Copy),Wet,Available,Depth,Bed,&Input)))return false;
        TestEqual(TEXT("mapping describes selected publication, not audit scratch"),Mesh->HasCompactCrestSource(),Compact);
        int32 OriginalAnchors=0;
        for(int32 Anchor=0;Anchor<Mesh->GetCrestSourceVertexCount();++Anchor)
        {
            const int32 Original=Mesh->GetCrestSourceOriginalIndex(Anchor);
            if(Original>=N*N)continue;
            ++OriginalAnchors;
            TestTrue(TEXT("source diagnostic mapping preserves position and transport"),
                Mesh->GetWaterVertices()[Anchor].Position==Source[Original].Position &&
                Mesh->GetWaterVertices()[Anchor].UV3==Source[Original].UV3);
        }
        TestTrue(TEXT("source anchors remain auditable, without treating absent anchors as measured"),
            OriginalAnchors>0 && (Compact ? OriginalAnchors<N*N : OriginalAnchors==N*N));
        World->SendAllEndOfFrameUpdates();FlushRenderingCommands();
        TestNotNull(TEXT("compact or reference publication retains native rendering proxy"),Mesh->GetSceneProxy());
    }
    return !HasAnyErrors();
}
#endif
