#include "RaftSimSharedBankCrossing.h"
#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSharedBankCrossingTest,"RaftSim.M4.SharedBankCrossing",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimSharedBankCrossingTest::RunTest(const FString&)
{
    using namespace RaftSimSharedBankCrossing;
    struct FDonor{double WetBed,DryBed,H;};
    const FDonor Donors[]={
        {8.45587158203125,8.711944580078125,double(.061720576137304306f)},
        {8.5344696044921875,8.711944580078125,double(.17600621283054352f)},
        {7.7048187255859375,9.9083251953125,double(.2190435528755188f)},
        {0.,2.,1.e-8}, {0.,2.,1.}, {0.,2.,1.999999}
    };
    TArray<TSharedPtr<FJsonValue>> Cases;int32 Passed=0;
    for(double Origin:{0.,-543000.,361100.,1000000.})for(double Direction:{-1.,1.})for(const auto& Donor:Donors)
    {
        const double W=Origin,D=W+Direction*100.;FResult R;
        const uint32 Control=VectorGetControlRegister();
        const bool Good=Build(W,D,Donor.WetBed,Donor.DryBed,Donor.H,.1,R);
        TestEqual(TEXT("caller floating point control preserved"),VectorGetControlRegister(),Control);
        if(!TestTrue(TEXT("one millimetre bound at representative coordinate scales"),Good))return false;
        TestTrue(TEXT("GPU float cast does not change certified coordinate"),double(float(R.Position))==R.Position);
        TestTrue(TEXT("transport fraction stays on the original edge"),R.WetToDryFraction>=0. && R.WetToDryFraction<=1.);
        // Opposite cell ordering still supplies the same semantic W,D; no
        // cell-local complement/reversal or independent rounding is allowed.
        const double ReversedEndpoints[]={D,W};FResult Neighbor;
        if(!TestTrue(TEXT("opposite cell can use canonical wet/dry identity"),Build(ReversedEndpoints[1],ReversedEndpoints[0],
            Donor.WetBed,Donor.DryBed,Donor.H,.1,Neighbor)))return false;
        TestTrue(TEXT("neighboring canonical nodes and attributes agree bit exactly"),
            R.Position==Neighbor.Position && R.WetToDryFraction==Neighbor.WetToDryFraction);
        auto Item=MakeShared<FJsonObject>();
        const auto Number=[&](const TCHAR* Key,double V){Item->SetStringField(Key,FString::Printf(TEXT("%.17g"),V));};
        Number(TEXT("wet_position_cm"),W);Number(TEXT("dry_position_cm"),D);
        Number(TEXT("wet_bed_m"),Donor.WetBed);Number(TEXT("dry_bed_m"),Donor.DryBed);Number(TEXT("depth_m"),Donor.H);
        Number(TEXT("position_cm"),R.Position);Number(TEXT("fraction"),R.WetToDryFraction);
        Number(TEXT("retreat_bound_cm"),R.MaximumRetreatCm);Number(TEXT("width_cm"),.1);
        Cases.Add(MakeShared<FJsonValueObject>(Item));++Passed;
    }
    FResult R;
    TestFalse(TEXT("submillimetre unrepresentable crossing fails closed"),Build(10000000.,10000100.,0.,2.,.333333333,.1,R));
    TestTrue(TEXT("failed call clears previous successful output"),R.Position==0. && R.WetToDryFraction==0. && R.MaximumRetreatCm==0.);
    TestFalse(TEXT("non-binary32 source coordinate rejected"),Build(.1,100.,0.,2.,1.,.1,R));
    TestFalse(TEXT("zero depth is not made into a wet donor"),Build(0.,100.,0.,2.,0.,.1,R));
    TestFalse(TEXT("advancing front not given an invented bed crossing"),Build(0.,100.,0.,.5,1.,.1,R));
    TestFalse(TEXT("zero width rejected"),Build(0.,100.,0.,2.,1.,0.,R));
    TestFalse(TEXT("nonfinite input rejected"),Build(0.,100.,0.,2.,std::numeric_limits<double>::quiet_NaN(),.1,R));
    TestEqual(TEXT("all coordinate scales, directions and captured/thin donors tested"),Passed,48);
    FString Path;
    if(FParse::Value(FCommandLine::Get(),TEXT("RaftSimSharedBankExport="),Path))
    {
        auto Root=MakeShared<FJsonObject>();Root->SetArrayField(TEXT("cases"),Cases);
        Root->SetBoolField(TEXT("normal_renderer_integrated"),false);Root->SetBoolField(TEXT("gameplay_accepted"),false);
        FString Text;auto Writer=TJsonWriterFactory<>::Create(&Text);
        TestTrue(TEXT("coordinate proof export serializes"),FJsonSerializer::Serialize(Root,Writer));
        TestTrue(TEXT("coordinate proof export saved"),FFileHelper::SaveStringToFile(Text,*Path));
    }
    return !HasAnyErrors();
}
#endif
