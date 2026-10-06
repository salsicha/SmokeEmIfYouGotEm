#include "RaftSimAdjacentBankContour.h"
#include "RaftSimWaterShoreline.h"
#include "RaftSimShorelineCrestWeights.h"
#include "RaftSimCrestMidpointExpansion.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS
namespace
{
double MinimumQuadratic(double A,double B,double C)
{
    double Result=FMath::Min(C,A+B+C);
    if(A>0.)
    {
        const double T=-B/(2.*A);
        if(T>0. && T<1.)Result=FMath::Min(Result,(A*T+B)*T+C);
    }
    return Result;
}
double EdgeMinimumDepth(const RaftSimAdjacentBankContour::FCurve& C,FVector2D P,FVector2D Q)
{
    const double U=Q.X-P.X,V=Q.Y-P.Y;
    return MinimumQuadratic(-C.Delta*U*V,
        (C.H1-C.H0)*U-C.D0*V-C.Delta*(P.X*V+P.Y*U),
        C.H0+(C.H1-C.H0)*P.X-P.Y*(C.D0+C.Delta*P.X));
}
FVector2D Canonical(int32 Side,FVector2D P)
{
    switch(Side){case 0:return P;case 1:return FVector2D(P.Y,1.-P.X);
    case 2:return FVector2D(P.X,1.-P.Y);default:return FVector2D(P.Y,P.X);}
}
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimAdjacentBankTest,"RaftSim.M4.AdjacentBankContour",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimAdjacentBankTest::RunTest(const FString&)
{
    using namespace RaftSimAdjacentBankContour;
    using namespace RaftSimWaterShoreline;
    struct FCase{double B[4],H[4];FVector2D Probe;};
    // Canonical permutations of same-call v22/v23 raw-dry source cells.
    const FCase Cases[]={
        {{9.594528198242188,9.588058471679688,9.673553466796875,9.621139526367188},
         {.012181011028587818,.0226591844111681,0.,0.},{.6,.4340968379797414}},
        {{9.535598754882812,9.448638916015625,9.88519287109375,9.668182373046875},
         {.010308436118066311,.05996418744325638,0.,0.},{.15,.055713128173}},
        {{8.5440673828125,8.579727172851562,8.68426513671875,9.10076904296875},
         {.045327287167310715,.04456954076886177,0.,0.},{.25,.2315360917407}}
    };
    for(const auto& Case:Cases)for(int32 Side=0;Side<4;++Side)
    for(bool Compact:{false,true})for(double Sign:{-1.,1.})for(double Angle:{0.,.37})
    {
        double B[4],D[4];
        TArray<float> Bed,H;Bed.SetNum(4);H.SetNum(4);
        TArray<uint8> Wet,Available={1,1,1,1};Wet.SetNum(4);
        for(int32 I=0;I<4;++I)
        {
            const int32 J=Corner(Side,I);B[J]=Bed[J]=float(Case.B[I]);D[J]=H[J]=float(Case.H[I]);Wet[J]=I<2;
        }
        const auto C=Make(B,D,Side);
        const auto World=[&](FVector2D P,double Z){
            return FVector(-540300.+100.*(FMath::Cos(Angle)*P.X-FMath::Sin(Angle)*P.Y),
                Sign*(357400.+100.*(FMath::Sin(Angle)*P.X+FMath::Cos(Angle)*P.Y)),Z*100.);};
        const auto ToCanonical=[&](const FVector& P){
            const double X=(P.X+540300.)/100.,Y=(Sign*P.Y-357400.)/100.;
            return Canonical(Side,FVector2D(FMath::Cos(Angle)*X+FMath::Sin(Angle)*Y,
                -FMath::Sin(Angle)*X+FMath::Cos(Angle)*Y));};
        TArray<FProcMeshVertex> Source;Source.SetNum(4);
        TArray<float> Coarse,Shore;Coarse.SetNum(4);Shore.SetNum(4);
        for(int32 I=0;I<4;++I)
        {
            Source[I].Position=World(FVector2D(I%2,I/2),B[I]+D[I]);Source[I].Normal=FVector::UpVector;
            const double U=Canonical(Side,FVector2D(I%2,I/2)).X;
            Source[I].UV1=FVector2D(U,2.);Coarse[I]=1.+2.*U;Shore[I]=.2+.6*U;
        }
        const FVector Probe=World(Local(Side,Case.Probe),0.);FVector Hit;
        TArray<FProcMeshVertex> V;TArray<uint32> T;TArray<FCurvedBank> Banks;TArray<RaftSimWaterShoreline::FEdge> Edges;
        auto Input=Source;
        if(!TestTrue(TEXT("old captured pair builds"),RaftSimWaterShoreline::Build(2,2,MoveTemp(Input),
            Wet,Available,H,Bed,V,T,nullptr,nullptr,Compact,true,false)))return false;
        TestTrue(TEXT("old straight shoreline covers retained dry point"),
            Sample(FVector2D(Probe.X,Probe.Y),0,T.Num(),V,T,Hit));
        Input=Source;
        if(!TestTrue(TEXT("conservative pair builds"),RaftSimWaterShoreline::Build(2,2,MoveTemp(Input),
            Wet,Available,H,Bed,V,T,nullptr,&Edges,Compact,true,true,&Banks)))return false;
        if(!TestEqual(TEXT("one adjacent bank"),Banks.Num(),1))return false;
        TestEqual(TEXT("oriented pair classification"),Banks[0].PairSide,Side);
        TestFalse(TEXT("all retained dry probes excluded"),Sample(FVector2D(Probe.X,Probe.Y),0,T.Num(),V,T,Hit));
        FRaftSimShorelineCrestWeights Weights;Weights.Update(V.Num(),Coarse,Shore,Edges,Banks);
        for(int32 I=0;I<Banks[0].IntermediateCount();++I)
        {
            const auto& P=V[Banks[0].FirstNode+I];const double U=ToCanonical(P.Position).X;
            TestTrue(TEXT("height uses actual position, not node ordinal"),
                FMath::Abs(P.Position.Z-100.*((1.-U)*(Case.B[0]+Case.H[0])+U*(Case.B[1]+Case.H[1])))<1.e-7);
            TestTrue(TEXT("flow/crest/shore channels share actual position"),
                FMath::Abs(P.UV1.X-U)<1.e-9 &&
                FMath::Abs(Weights.Coarse[Banks[0].FirstNode+I]-(1.+2.*U))<1.e-6 &&
                FMath::Abs(Weights.Shore[Banks[0].FirstNode+I]-(.2+.6*U))<1.e-6);
        }
        for(int32 I=0;I<T.Num();I+=3)
        {
            const FVector A=V[T[I]].Position,Bv=V[T[I+1]].Position,Cv=V[T[I+2]].Position;
            TestTrue(TEXT("submitted triangle has clockwise winding"),FVector::CrossProduct(Bv-A,Cv-A).Z<0.);
            const FVector2D P[3]={ToCanonical(A),ToCanonical(Bv),ToCanonical(Cv)};
            // Bilinear depth has a saddle, never an interior strict minimum.
            // Certify every whole edge, hence every whole submitted triangle.
            for(int32 J=0;J<3;++J)TestTrue(TEXT("whole triangle stays on wet side"),
                EdgeMinimumDepth(C,P[J],P[(J+1)%3])>=-1.e-9);
            const FVector Q=.2*A+.3*Bv+.5*Cv;
            TestTrue(TEXT("actual triangles stay sampleable"),Sample(FVector2D(Q.X,Q.Y),0,T.Num(),V,T,Hit));
        }
    }

    FRandomStream Random(28092026);
    for(int32 Case=0;Case<256;++Case)
    {
        const double B0=Random.FRandRange(-20.,20.),B1=Random.FRandRange(-20.,20.);
        const double H0=Random.FRandRange(.001,1.),H1=Random.FRandRange(.001,1.);
        const double High=FMath::Max(B0+H0,B1+H1);
        const double B[4]={B0,B1,High+Random.FRandRange(.001,20.),High+Random.FRandRange(.001,20.)};
        const double H[4]={H0,H1,0.,0.};
        const auto C=Make(B,H,0);TArray<FVector2D> Interior;
        const double Across=Case%2 ? 100. : 700.;
        if(!TestTrue(TEXT("varied metric cells adapt"),RaftSimAdjacentBankContour::Build(C,Across,Interior)))return false;
        TArray<FVector2D> Points;Points.Add(FVector2D(0.,C.Value(0.)));Points.Append(Interior);Points.Add(FVector2D(1.,C.Value(1.)));
        for(int32 I=1;I<Points.Num();++I)
        {
            const auto P=Points[I-1],Q=Points[I];
            TestTrue(TEXT("whole segment conservative"),EdgeMinimumDepth(C,P,Q)>=-1.e-9);
            const double M=(Q.Y-P.Y)/(Q.X-P.X);
            double Error=FMath::Max(C.Value(P.X)-P.Y,C.Value(Q.X)-Q.Y);
            if(C.K*M>0. && C.Delta!=0.)
            {
                const double X=(FMath::Sqrt(C.K/M)-C.D0)/C.Delta;
                if(X>P.X && X<Q.X)Error=FMath::Max(Error,C.Value(X)-(P.Y+M*(X-P.X)));
            }
            TestTrue(TEXT("full interval width error <= 1mm"),
                Error*Across<=MaximumBoundaryWidthErrorCm+1.e-7);
        }
    }

    for(double Delta:{-1.e-10,0.,1.e-10})
    {
        const double B[4]={0.,0.,2.,2.+Delta},H[4]={.2,.3,0.,0.};
        const auto C=Make(B,H,0);TArray<FVector2D> Interior;
        TestTrue(TEXT("linear and near-linear limits remain representable"),RaftSimAdjacentBankContour::Build(C,100.,Interior));
        if(Delta==0.)TestEqual(TEXT("exact linear contour uses legacy chord"),Eligible(B,H),INDEX_NONE);
        TArray<FVector2D> Points;Points.Add(FVector2D(0.,C.Value(0.)));Points.Append(Interior);Points.Add(FVector2D(1.,C.Value(1.)));
        for(int32 I=1;I<Points.Num();++I)TestTrue(TEXT("near-linear whole segments remain conservative"),EdgeMinimumDepth(C,Points[I-1],Points[I])>=-1.e-12);
    }

    // Cache invalidation under changing segment count, fan sign, exact-dry
    // eligibility and low advancing fronts. Never discard positive films.
    FTopologyCache Cache;bool Rebuilt=false;TSet<int32> SeenCurveCounts;
    TArray<FProcMeshVertex> V;TArray<uint32> T;TArray<int32> Offsets;
    for(int32 Frame=0;Frame<32;++Frame)
    {
        TArray<float> Bed,H;for(int32 I=0;I<4;++I){Bed.Add(Cases[0].B[I]);H.Add(Cases[0].H[I]);}
        const TArray<uint8> Wet={1,1,0,0},Available={1,1,1,1};
        if(Frame>1)H[0]*=1.+.01*(Frame%7);
        if(Frame==12)H[2]=1.e-12f;
        if(Frame==14)Bed[2]=Bed[0]+H[0]-.001f;
        if(Frame>=20)
        {
            H[0]=(Frame%2 ? .1f : .2f)*(Bed[2]-Bed[0]);
            H[1]=(Frame%2 ? .2f : .1f)*(Bed[3]-Bed[1]);
        }
        TArray<FProcMeshVertex> Source;Source.SetNum(4);
        for(int32 I=0;I<4;++I){Source[I].Position=FVector(100.*(I%2),100.*(I/2),100.*(double(Bed[I])+H[I]));Source[I].Normal=FVector::UpVector;}
        auto Input=Source;
        if(!TestTrue(TEXT("changing pair cache"),Cache.Update(2,2,MoveTemp(Input),Wet,Available,H,Bed,V,T,Offsets,Rebuilt,true,true,true)))return false;
        TArray<FProcMeshVertex> Fresh;TArray<uint32> FT;TArray<int32> FO;
        if(!TestTrue(TEXT("fresh changing pair"),RaftSimWaterShoreline::Build(2,2,MoveTemp(Source),Wet,Available,H,Bed,Fresh,FT,&FO,nullptr,true,true,true)))return false;
        TestTrue(TEXT("cached membership/ordering/ownership matches fresh"),T==FT && Offsets==FO && V.Num()==Fresh.Num());
        for(uint32 I:T)TestTrue(TEXT("all submitted attributes match fresh"),
            FRaftSimCrestMidpointExpansion::EqualAttributes(V[I],Fresh[I]));
        if(Frame==1)TestFalse(TEXT("unchanged pair reuses topology"),Rebuilt);
        for(const auto& Bank:Cache.GetCurvedBanks())SeenCurveCounts.Add(Bank.IntermediateCount());
        if(Frame==12 || Frame==14)TestTrue(TEXT("films/low banks leave specialized branch"),
            Rebuilt && Cache.GetCurvedBanks().IsEmpty());
    }
    TestTrue(TEXT("cache exercised actual adaptive node-count changes"),SeenCurveCounts.Num()>1);
    return !HasAnyErrors();
}
#endif
