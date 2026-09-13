#include "RaftSimWaterSmoothing.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimWaterSmoothingElisionTest,
    "RaftSim.M4.NativeMeanSmoothingElision",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimWaterSmoothingElisionTest::RunTest(const FString&)
{
    constexpr int32 Nx=37,Ny=29;
    TArray<float> Source,Native; TArray<uint8> Wet;
    for (int32 Y=0;Y<Ny;++Y) for (int32 X=0;X<Nx;++X)
    {
        Source.Add(7.f+X*.013f-Y*.021f+FMath::Sin(X*.6f)*FMath::Cos(Y*.43f));
        Native.Add(Source.Last()+.17f*FMath::Cos(X*.19f)); // crop-handover base differs
        Wet.Add((X+7*Y)%19!=0 && !(X>12 && X<17 && Y>8 && Y<13));
    }
    for (int32 Stride:{1,3}) for (float Strength:{0.f,.4f,1.f})
    {
        // Frozen pre-elision loop: sixteen optical passes, independent fourth
        // pass snapshot. Boundary and all wet-mask holes remain untouched.
        auto Legacy=Source; TArray<float> LegacyHydraulic;
        for (int32 Pass=0;Pass<16;++Pass)
        {
            const auto Previous=Legacy;
            for (int32 Y=Stride;Y<Ny-Stride;++Y) for (int32 X=Stride;X<Nx-Stride;++X)
            {
                const int32 I=Y*Nx+X;
                if (!Wet[I] || !Wet[I-Stride] || !Wet[I+Stride] || !Wet[I-Stride*Nx] || !Wet[I+Stride*Nx]) continue;
                Legacy[I]=URaftSimWaterRuntimeAdapter::ComputeCoupledSmoothedSurfaceHeightMeters(
                    Previous[I],Previous[I-Stride],Previous[I+Stride],Previous[I-Stride*Nx],Previous[I+Stride*Nx],Strength);
            }
            if (Pass==3) LegacyHydraulic=Legacy;
        }
        auto Diagnostic=Source; TArray<float> DiagnosticHydraulic;
        RaftSimWaterSmoothing::Apply(Diagnostic,Wet,Nx,Ny,Stride,Strength,16,4,DiagnosticHydraulic);
        TestTrue(TEXT("legacy/diagnostic optical and hydraulic outputs remain bit-exact"),
            Diagnostic==Legacy && DiagnosticHydraulic==LegacyHydraulic);
        auto Fast=Source; TArray<float> FastHydraulic;
        const int32 Optical=RaftSimWaterSmoothing::OpticalPassCount(true,false,16);
        TestEqual(TEXT("unused native optical output requests no passes"),Optical,0);
        RaftSimWaterSmoothing::Apply(Fast,Wet,Nx,Ny,Stride,Strength,Optical,4,FastHydraulic);
        TestTrue(TEXT("all four hydraulic passes remain bit-exact"),FastHydraulic==LegacyHydraulic);
        for (int32 I=0;I<Source.Num();++I) if (Wet[I]) Fast[I]=Legacy[I]=Native[I];
        TestTrue(TEXT("final native base remains bit-exact including dry holes and boundaries"),Fast==Legacy);
        auto One=Source; TArray<float> OneHydraulic;
        RaftSimWaterSmoothing::Apply(One,Wet,Nx,Ny,Stride,Strength,1,1,OneHydraulic);
        auto EarlyOptical=Source; TArray<float> Four;
        RaftSimWaterSmoothing::Apply(EarlyOptical,Wet,Nx,Ny,Stride,Strength,1,4,Four);
        TestTrue(TEXT("legacy short optical output and full hydraulic output are independent"),
            EarlyOptical==One && Four==LegacyHydraulic);
    }
    TestEqual(TEXT("non-native scene retains optical work"),RaftSimWaterSmoothing::OpticalPassCount(false,false,16),16);
    TestEqual(TEXT("native diagnostic retains requested historical optical work"),RaftSimWaterSmoothing::OpticalPassCount(true,true,16),16);
    return !HasAnyErrors();
}
#endif
