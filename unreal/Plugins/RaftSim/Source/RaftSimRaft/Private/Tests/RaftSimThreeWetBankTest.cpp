#include "RaftSimThreeWetBankContour.h"
#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "HAL/PlatformTime.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimThreeWetBankTest,"RaftSim.M4.ThreeWetBankEnvelope",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimThreeWetBankTest::RunTest(const FString&)
{
    using namespace RaftSimThreeWetBankContour;
    struct FCase{double B[4],H[4];};
    const FCase Cases[]={
        {{8.711944580078125,8.45587158203125,8.534469604492188,8.397781372070312},
         {0.,double(.061720576137304306f),double(.17600621283054352f),double(.16925844550132751f)}},
        {{9.9083251953125,7.7048187255859375,7.243682861328125,7.27630615234375},
         {0.,double(.2190435528755188f),double(.5688362717628479f),double(.492604672908783f)}},
        {{2.,0.,0.,0.},{0.,1.,1.,1.}},
        {{2.,0.,0.,0.},{0.,1.e-8,1.,1.}}
    };
    TArray<TSharedPtr<FJsonValue>> ExportCases;
    for(int32 K=0;K<UE_ARRAY_COUNT(Cases);++K)
    {
        FCurve C;
        if(!TestTrue(TEXT("original high-bank inputs accepted"),C.Init(Cases[K].B,Cases[K].H)))return false;
        {
            const FScopedIEEE Scope;FStats Stats;
            for(int32 Axis:{0,1})
            {
                const FPoint Q=IdealEdgeRoot(C,Axis);
                TestTrue(TEXT("repeated canonical endpoint is analytically zero"),Certificate(C,Q,Q,Q,true,Stats) && Certificate(C,Q,Q,Q,false,Stats));
                const FPoint Rounded=EdgeRoot(C,Axis);
                TestTrue(TEXT("stored endpoint is on the wet side"),C.Value(Rounded).Lo>0. && Certificate(C,Rounded,Rounded,Rounded,true,Stats));
                TestFalse(TEXT("wet-rounded endpoint is not labelled dry"),Certificate(C,Rounded,Rounded,Rounded,false,Stats));
            }
            const FPoint Wet(FVector2D(1.,1.));
            TestFalse(TEXT("positive wet corner cannot certify dry"),Certificate(C,Wet,Wet,Wet,false,Stats));
            const FPoint Dry(FVector2D(.001,.001));
            TestFalse(TEXT("genuinely dry corner neighborhood cannot certify wet"),Certificate(C,Dry,Dry,Dry,true,Stats));
        }
        FResult R;const uint32 ControlBefore=VectorGetControlRegister();
        const double Start=FPlatformTime::Seconds();
        const bool Built=Build(C,.001,R);const double Ms=(FPlatformTime::Seconds()-Start)*1000.;
        AddInfo(FString::Printf(TEXT("ThreeWet case=%d built=%d segments=%d initial=%d coefficient_tests=%d construction_ms=%.6f; not game FPS"),
            K,int32(Built),R.Boundary.Num()-1,R.Stats.InitialSegments,R.Stats.CoefficientTests,Ms));
        TestEqual(TEXT("floating point control restored"),VectorGetControlRegister(),ControlBefore);
        if(!TestTrue(TEXT("complete native envelope proved"),Built))return false;
        TestEqual(TEXT("polygon fully triangulated"),R.Triangles.Num(),R.Polygon.Num()-2);
        TestTrue(TEXT("canonical crossings retained"),R.Boundary[0].XY.Y==0. && R.Boundary.Last().XY.X==0.);
        const auto PointArray=[](const TArray<FPoint>& Points)
        {
            TArray<TSharedPtr<FJsonValue>> Values;
            for(const auto& P:Points)
            {
                // Decimal strings with17 significant digits roundtrip binary64
                // without depending on the engine JSON number printer.
                TArray<TSharedPtr<FJsonValue>> XY;
                XY.Add(MakeShared<FJsonValueString>(FString::Printf(TEXT("%.17g"),P.XY.X)));
                XY.Add(MakeShared<FJsonValueString>(FString::Printf(TEXT("%.17g"),P.XY.Y)));
                Values.Add(MakeShared<FJsonValueArray>(XY));
            }
            return Values;
        };
        auto Item=MakeShared<FJsonObject>();Item->SetNumberField(TEXT("case"),K);
        Item->SetNumberField(TEXT("construction_ms"),Ms);Item->SetNumberField(TEXT("coefficient_tests"),R.Stats.CoefficientTests);
        Item->SetNumberField(TEXT("root_solves"),R.Stats.RootSolves);
        if(K==0)
        {
            TArray<double> CachedTimes,RepeatedTimes;int32 RepeatedRoots=0;
            // Same-binary A/B/B/A; concurrent source work excludes GAME FPS
            // acceptance, but exact work-count/output comparisons remain valid.
            for(int32 Repeat=0;Repeat<4;++Repeat)for(bool CacheRoots:{true,false,false,true})
            {
                FResult Trial;const double Begin=FPlatformTime::Seconds();
                const bool Good=Build(C,.001,Trial,CacheRoots);const double Time=(FPlatformTime::Seconds()-Begin)*1000.;
                if(!TestTrue(TEXT("both root policies certify"),Good))return false;
                TestTrue(TEXT("root reuse preserves exact triangle indices"),Trial.Triangles==R.Triangles);
                if(!TestEqual(TEXT("root reuse preserves node count"),Trial.Polygon.Num(),R.Polygon.Num()))return false;
                for(int32 I=0;I<R.Polygon.Num();++I)
                    TestTrue(TEXT("root reuse preserves every binary64 node and bound"),
                        Trial.Polygon[I].XY==R.Polygon[I].XY && SamePoint(Trial.Polygon[I],R.Polygon[I]));
                if(CacheRoots)CachedTimes.Add(Time);else{RepeatedTimes.Add(Time);RepeatedRoots=Trial.Stats.RootSolves;}
            }
            TestTrue(TEXT("actual root solves reduced"),R.Stats.RootSolves<RepeatedRoots);
            CachedTimes.Sort();RepeatedTimes.Sort();
            Item->SetNumberField(TEXT("repeated_root_solves"),RepeatedRoots);
            Item->SetNumberField(TEXT("cached_median_ms"),(CachedTimes[3]+CachedTimes[4])*.5);
            Item->SetNumberField(TEXT("repeated_median_ms"),(RepeatedTimes[3]+RepeatedTimes[4])*.5);
            AddInfo(FString::Printf(TEXT("ThreeWet same-binary ABBA cached_roots=%d repeated_roots=%d cached_median_ms=%.6f repeated_median_ms=%.6f; not isolated game FPS"),
                R.Stats.RootSolves,RepeatedRoots,(CachedTimes[3]+CachedTimes[4])*.5,(RepeatedTimes[3]+RepeatedTimes[4])*.5));
        }
        TArray<TSharedPtr<FJsonValue>> Beds,Depths,Triangles;
        for(int32 I=0;I<4;++I)
        {
            Beds.Add(MakeShared<FJsonValueString>(FString::Printf(TEXT("%.17g"),Cases[K].B[I])));
            Depths.Add(MakeShared<FJsonValueString>(FString::Printf(TEXT("%.17g"),Cases[K].H[I])));
        }
        for(const auto& T:R.Triangles)
        {
            TArray<TSharedPtr<FJsonValue>> Ids;
            for(int32 I:{T.X,T.Y,T.Z})Ids.Add(MakeShared<FJsonValueNumber>(I));
            Triangles.Add(MakeShared<FJsonValueArray>(Ids));
        }
        Item->SetArrayField(TEXT("bed"),Beds);Item->SetArrayField(TEXT("depth"),Depths);
        Item->SetArrayField(TEXT("boundary"),PointArray(R.Boundary));Item->SetArrayField(TEXT("inner"),PointArray(R.InnerBoundary));
        Item->SetArrayField(TEXT("polygon"),PointArray(R.Polygon));Item->SetArrayField(TEXT("triangles"),Triangles);
        ExportCases.Add(MakeShared<FJsonValueObject>(Item));
    }
    {
        FCurve C;TestTrue(TEXT("validation fixture"),C.Init(Cases[0].B,Cases[0].H));FResult R;
        TestFalse(TEXT("zero geometric width rejected"),Build(C,0.,R));
        TestFalse(TEXT("nonfinite geometric width rejected"),Build(C,std::numeric_limits<double>::infinity(),R));
        double H[4];for(int32 I=0;I<4;++I)H[I]=Cases[0].H[I];H[0]=1.e-12;
        TestFalse(TEXT("positive dry-corner film not discarded"),C.Init(Cases[0].B,H));
        TestFalse(TEXT("failed reinitialization cannot reuse previous curve"),Build(C,.001,R));
        FCurve Uninitialized;TestFalse(TEXT("uninitialized curve rejected"),Build(Uninitialized,.001,R));
    }
    FString Path;
    if(FParse::Value(FCommandLine::Get(),TEXT("RaftSimThreeWetExport="),Path))
    {
        auto Root=MakeShared<FJsonObject>();Root->SetArrayField(TEXT("cases"),ExportCases);
        Root->SetBoolField(TEXT("normal_renderer_integrated"),false);Root->SetBoolField(TEXT("gameplay_accepted"),false);
        FString Text;auto Writer=TJsonWriterFactory<>::Create(&Text);
        TestTrue(TEXT("native proof export serializes"),FJsonSerializer::Serialize(Root,Writer));
        TestTrue(TEXT("native proof export saved"),FFileHelper::SaveStringToFile(Text,*Path));
    }
    return !HasAnyErrors();
}
#endif
