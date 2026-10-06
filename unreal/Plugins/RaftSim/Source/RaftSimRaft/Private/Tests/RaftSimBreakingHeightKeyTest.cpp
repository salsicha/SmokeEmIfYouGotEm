#include "RaftSimBreakingHeightKey.h"
#include "RaftSimIndexedBreakingProfile.h"
#include "RaftSimShorelineCrests.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimBreakingHeightKeyTest,"RaftSim.M4.BreakingHeightKey",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimBreakingHeightKeyTest::RunTest(const FString&)
{
    using FSite=URaftSimWaterRuntimeAdapter::FSupportBreakingSite;
    FSite S;S.RiverCoordinatesMeters=FVector2D(0,0);S.FlowDirection=FVector2D(1,0);
    S.PhysicalCrestHeightMeters=.5f;S.PhysicalCrestLengthMeters=2.f;
    S.Intensity=.2f;S.SpillingFraction=0.f;S.bLocalEnvelopeCap=true;
    const TArray<FSite> Original={S};
    const auto Key=[](const TArray<FSite>& Sites){return RaftSimBreakingHeightKey::Build(Sites,.22f,1.f,1.f,-1.f);};
    const auto Base=Key(Original);
    auto Changed=Original;Changed[0].Intensity=.9f;Changed[0].SpillingFraction=1.f;
    TestTrue(TEXT("physical optical changes retain height identity"),Base==Key(Changed));
    const FRaftSimIndexedBreakingProfile A(Original,.22f,1.f),B(Changed,.22f,1.f);
    bool FoamChanges=false;
    for(int32 X=-28;X<=56;++X)for(int32 Y=-8;Y<=8;++Y)
    {
        const FVector2D P(X*.5,Y*.5);float FA=0,FB=0;
        const float HA=URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(P,Original,.22f,1.f,&FA);
        const float HB=URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(P,Changed,.22f,1.f,&FB);
        TestEqual(TEXT("independent full height unchanged while foam is refreshed"),HA,HB);
        TestEqual(TEXT("indexed height unchanged"),A.SampleWithEmptyTileSkip(P,nullptr,true,false),B.SampleWithEmptyTileSkip(P,nullptr,true,false));
        FoamChanges|=FA!=FB;
    }
    TestTrue(TEXT("foam source actually changes; not frozen to preserve geometry"),FoamChanges);
    for(int32 Field=0;Field<7;++Field)
    {
        Changed=Original;
        switch(Field)
        {
        case 0:Changed[0].RiverCoordinatesMeters.X+=.1;break;
        case 1:Changed[0].RiverCoordinatesMeters.Y+=.1;break;
        case 2:Changed[0].PhysicalCrestHeightMeters+=.1f;break;
        case 3:Changed[0].PhysicalCrestLengthMeters+=.1f;break;
        case 4:Changed[0].FlowDirection.X-=.1;break;
        case 5:Changed[0].FlowDirection.Y+=.1;break;
        case 6:Changed[0].bLocalEnvelopeCap=false;break;
        }
        TestTrue(TEXT("every physical height input invalidates"),Base!=Key(Changed));
    }
    for(int32 Field=0;Field<4;++Field)
    {
        float Globals[4]={.22f,1.f,1.f,-1.f};Globals[Field]+=.125f;
        TestTrue(TEXT("global height inputs invalidate"),Base!=RaftSimBreakingHeightKey::Build(Original,Globals[0],Globals[1],Globals[2],Globals[3]));
    }
    auto Legacy=Original;Legacy[0].PhysicalCrestHeightMeters=-1.f;
    auto LegacyChanged=Legacy;LegacyChanged[0].Intensity=.9f;
    TestTrue(TEXT("legacy intensity still invalidates"),Key(Legacy)!=Key(LegacyChanged));
    TestTrue(TEXT("legacy intensity really affects height"),
        URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(FVector2D::ZeroVector,Legacy,.22f,1.f)!=
        URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(FVector2D::ZeroVector,LegacyChanged,.22f,1.f));
    LegacyChanged=Legacy;LegacyChanged[0].SpillingFraction=1.f;
    TestTrue(TEXT("legacy foam is not a height input"),Key(Legacy)==Key(LegacyChanged));
    TestTrue(TEXT("physical/legacy transition invalidates"),Base!=Key(Legacy));
    TArray<FSite> Mixed={Original[0],Legacy[0]},Reversed={Legacy[0],Original[0]};
    TestTrue(TEXT("site order retained"),Key(Mixed)!=Key(Reversed));
    TestTrue(TEXT("site removal retained"),Key(Mixed)!=Base);
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimBreakingHeightCacheTest,"RaftSim.M4.BreakingHeightCache",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimBreakingHeightCacheTest::RunTest(const FString&)
{
    using FSite=URaftSimWaterRuntimeAdapter::FSupportBreakingSite;
    FSite S;S.RiverCoordinatesMeters=FVector2D(0,0);S.FlowDirection=FVector2D(1,0);
    S.PhysicalCrestHeightMeters=.5f;S.PhysicalCrestLengthMeters=2.f;S.bLocalEnvelopeCap=true;
    TArray<FSite> Sites={S};
    TArray<FProcMeshVertex> Source;TArray<uint32> Root;TArray<int32> Offsets;
    constexpr int32 N=5;Source.SetNum(N*N);
    for(int32 Y=0;Y<N;++Y)for(int32 X=0;X<N;++X)
    {
        auto& V=Source[Y*N+X];V.Position=FVector((X-2)*100.,(Y-2)*100.,100.);
        V.Normal=FVector::UpVector;V.Color=FColor::White;
        if(X<N-1 && Y<N-1){Offsets.Add(Root.Num());const uint32 I=Y*N+X;Root.Append({I,I+1,I+N,I+1,I+N+1,I+N});}
    }
    Offsets.Add(Root.Num());
    FRaftSimShorelineCrests Cached,Fresh;TArray<float> Coarse,Shore;Coarse.Init(0,Source.Num());Shore.Init(1,Source.Num());
    FRaftSimShorelineCrestInput Input;Input.BlendAlpha=.37f;
    TAtomic<int32> Queries{0};
    for(int32 Frame=0;Frame<12;++Frame)
    {
        Sites[0].Intensity=float(Frame)/12;Sites[0].SpillingFraction=float(Frame%3)*.5f;
        if(Frame==6)Sites[0].PhysicalCrestHeightMeters+=.125f;
        Input.ProfileKey=RaftSimBreakingHeightKey::Build(Sites,.22f,1.f,1.f,1.f);
        Input.HeightAtWorldXYCm=[&,Records=Sites](const FVector2D& P)
        {++Queries;return 100.f*URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(P*.01,Records,.22f,1.f);};
        for(int32 I=0;I<Source.Num();++I)
        {
            Coarse[I]=Input.HeightAtWorldXYCm(FVector2D(Source[I].Position.X,Source[I].Position.Y));
            Source[I].Position.Z=100+Coarse[I];Source[I].UV3.X=Frame*.1f;Source[I].Color.R=uint8(Frame*10);
        }
        Queries.Store(0);
        TArray<FProcMeshVertex> A,B;TArray<uint32> AT,BT;TArray<int32> AO,BO;
        if(!Cached.Update(Source,Root,Offsets,Coarse,Shore,Input,A,AT,AO))return false;
        if(Frame!=0 && Frame!=6)TestEqual(TEXT("optical-only frame makes no height queries"),Queries.Load(),0);
        TestEqual(TEXT("only initial and actual amplitude changes rebuild"),Cached.GetBuildCount(),uint64(Frame<6?1:2));
        auto Forced=Input;Forced.ProfileKey.Add(Frame); // SAME history, forced current profile every frame.
        if(!Fresh.Update(Source,Root,Offsets,Coarse,Shore,Forced,B,BT,BO))return false;
        TestTrue(TEXT("all target corrections remain exact"),Cached.GetTargetCorrectionsCm()==Fresh.GetTargetCorrectionsCm());
        bool Equal=AT==BT && AO==BO && A.Num()==B.Num();
        for(int32 I=0;Equal && I<A.Num();++I)
        {
            const auto& V=A[I];const auto& W=B[I];
            Equal=V.Position==W.Position && V.Normal==W.Normal && V.Color==W.Color && V.UV0==W.UV0 &&
                V.UV1==W.UV1 && V.UV2==W.UV2 && V.UV3==W.UV3 && V.Tangent.TangentX==W.Tangent.TangentX &&
                V.Tangent.bFlipTangentY==W.Tangent.bFlipTangentY;
        }
        TestTrue(TEXT("rendered attributes, topology and temporal history equal forced rebuild"),Equal);
    }
    return !HasAnyErrors();
}
#endif
