#include "RaftSimLiveWaterWindow.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimWetSurfaceInterpolation.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS && RAFTSIM_HAS_LIVE_SOLVER
#include "raftsim_water/solver.hpp"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimWaterDryRockSamplingTest,
    "RaftSim.M3.WaterDryRockSampling",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimWaterDryRockSamplingTest::RunTest(const FString&)
{
    // Exact still pool eta=1, with a dry rock ramp from bed=0 to bed=2.
    // This tests sampling, not solver evolution or river bathymetry inference.
    for (bool AlongY : {false, true})
    {
        auto Window=FRaftSimLiveWaterWindow::CreateFlatTank(FVector2D(-5432.,3600.),12,12,1,1,1);
        if (!TestTrue(TEXT("native tank loads"),Window.IsValid())) return false;
        auto Scenario=Window->Solver->scenario();
        for (int32 R=0; R<12; ++R) for (int32 C=0; C<12; ++C)
        {
            const bool Dry=(AlongY ? R : C)>=6;
            Scenario.bed(R,C)=Dry ? 2. : 0.;
            Scenario.initial.h(R,C)=Dry ? 0. : 1.;
            Scenario.initial.eta(R,C)=Dry ? 2. : 1.;
            Scenario.initial.wet.values[R*12+C]=Dry ? 0 : 1;
        }
        raftsim::SolverConfig Config;
        Config.solver_mode="finite_volume"; Config.disable_fixture_calibrations=true;
        Window->Solver=MakePimpl<raftsim::ReducedShallowWaterSolver>(MoveTemp(Scenario),Config);
        const double Volume=Window->TotalWaterVolumeM3();
        const double Time=Window->SimTimeSeconds();
        for (double Fraction : {.0,.25,.5,.75,1.})
        {
            const FVector2D Offset=AlongY ? FVector2D(4.25,5.+Fraction) : FVector2D(5.+Fraction,4.25);
            const auto Sample=Window->Sample(Window->OriginM+Offset);
            const double Bed=2.*Fraction, Depth=FMath::Max(1.-Bed,0.);
            TestTrue(TEXT("sample retains modeled ramp bed"),Sample.bValid && Sample.BedHeightM==float(Bed));
            TestEqual(TEXT("pool depth terminates at bed intersection"),Sample.DepthM,float(Depth));
            TestEqual(TEXT("dry rock is not a free-surface contributor"),Sample.SurfaceHeightM,float(Bed+Depth));
            TestEqual(TEXT("no phantom wet sheet uphill of pool"),Sample.bWet,Depth>1.e-4);
            if (Sample.bWet) TestTrue(TEXT("still pool has an upward normal"),Sample.SurfaceNormal.Equals(FVector::UpVector,1.e-6));
        }
        TestEqual(TEXT("sampling changes no conserved volume"),Window->TotalWaterVolumeM3(),Volume);
        TestEqual(TEXT("sampling does not advance time"),Window->SimTimeSeconds(),Time);
        auto Shifted=FRaftSimLiveWaterWindow::CreateFlatTank(FVector2D(-5431.75,3600.25),12,12,1,1,1);
        TestTrue(TEXT("legacy fractional transfer remains available"),Shifted->TransferOverlapStateFrom(*Window)>0);
        TestEqual(TEXT("legacy transfer keeps raw depth, not clipped point depth"),
            Shifted->Solver->state().h(AlongY ? 5 : 4,AlongY ? 4 : 5),.75);

        FString Error;
        const FString Root=URaftSimWaterRuntimeAdapter::ResolveRuntimeDataPath(
            TEXT("tmp/cartesian-dry-rock-fixture-v1"));
        const FVector2D Origin(-5432.,3600.);
        auto Shared=FRaftSimLiveWaterWindow::CreateFromCookedFields(
            Root/(AlongY ? TEXT("y/packet") : TEXT("x/packet")),TEXT("analytic"),
            Origin+FVector2D(12.,12.),FVector2D(16.,16.),.035f,Error,false);
        if (!TestTrue(*FString::Printf(TEXT("dry-rock atlas fixture loads: %s"),*Error),Shared.IsValid())) return false;
        const double SharedVolume=Shared->TotalWaterVolumeM3();
        for (double Fraction : {.0,.25,.5,.75,1.})
        {
            const FVector2D Offset=AlongY ? FVector2D(4.25,5.+Fraction) : FVector2D(5.+Fraction,4.25);
            const double Bed=2.*Fraction, Depth=FMath::Max(1.-Bed,0.);
            for (const auto Sample : {Shared->Sample(Origin+Offset),Shared->SamplePresentationSource(Origin+Offset)})
            {
                TestTrue(TEXT("shared and live paths preserve datum and bed"),Sample.bValid && Sample.BedHeightM==float(220.+Bed));
                TestEqual(TEXT("shared/live pool depth"),Sample.DepthM,float(Depth));
                TestEqual(TEXT("shared/live pool elevation"),Sample.SurfaceHeightM,float(220.+Bed+Depth));
                TestEqual(TEXT("shared/live dry intersection"),Sample.bWet,Depth>1.e-4);
                if (Sample.bWet) TestTrue(TEXT("shared/live flat pool normal"),Sample.SurfaceNormal.Equals(FVector::UpVector,1.e-6));
            }
        }
        TestEqual(TEXT("shared sampling does not change solver volume"),Shared->TotalWaterVolumeM3(),SharedVolume);
    }

    const bool Available[4]={true,true,true,true};
    const double FlatBed[4]={0.,0.,0.,0.},FrontDepth[4]={1.,0.,1.,0.};
    for (double X : {.01,.25,.75,.99})
    {
        double H=1.-X,Eta=H; FVector Normal;
        TestTrue(TEXT("flat-bed wetting front is mixed"),RaftSimWetSurfaceInterpolation::ResolveMixed(
            FlatBed,FrontDepth,Available,X,.37,0.,1.,1.,H,Eta,Normal));
        TestTrue(TEXT("no water is added at a lower dry wetting front"),FMath::Abs(H-(1.-X))<1.e-14 && Eta==H);
    }
    const double Film[4]={1.e-12,2.e-12,3.e-12,4.e-12};
    double H=7.,Eta=8.; FVector Normal(1.,2.,3.);
    TestFalse(TEXT("arbitrarily thin all-positive film bypasses correction"),
        RaftSimWetSurfaceInterpolation::ResolveMixed(FlatBed,Film,Available,.3,.4,0.,1.,1.,H,Eta,Normal));
    TestTrue(TEXT("bypass leaves all output channels unchanged"),H==7. && Eta==8. && Normal==FVector(1.,2.,3.));

    // Deferring the central-difference normal is valid only if every branch
    // that returns true completely replaces it, including entirely dry cells.
    for (int32 Mask=0; Mask<16; ++Mask)
    {
        double Corners[4];
        for (int32 I=0; I<4; ++I) Corners[I]=(Mask & (1<<I)) ? .2+.13*I : 0.;
        for (double X : {0.,.37,1.}) for (double Y : {0.,.61,1.})
        {
            double D1=9.,E1=10.,D2=D1,E2=E1;
            FVector N1(1.,2.,3.),N2(-4.,5.,-6.);
            const bool Mixed1=RaftSimWetSurfaceInterpolation::ResolveMixed(
                FlatBed,Corners,Available,X,Y,0.,1.,1.,D1,E1,N1);
            const bool Mixed2=RaftSimWetSurfaceInterpolation::ResolveMixed(
                FlatBed,Corners,Available,X,Y,0.,1.,1.,D2,E2,N2);
            TestEqual(TEXT("mixed decision independent of incoming normal"),Mixed1,Mixed2);
            if (Mixed1)
                TestTrue(TEXT("mixed/dry outputs completely replace incoming normal"),D1==D2 && E1==E2 && N1==N2);
            else
                TestTrue(TEXT("all-wet branch requires the original central normal"),Mask==15 && N1==FVector(1.,2.,3.) && N2==FVector(-4.,5.,-6.));
        }
    }

    // Independent numerical derivative of the same nonuniform mixed surface.
    const double UnevenBed[4]={0.,2.,.1,.2},MixedDepth[4]={1.,0.,1.3,0.};
    const auto Evaluate=[&](double X,double Y,FVector& OutNormal)
    {
        const double B=(1.-Y)*((1.-X)*UnevenBed[0]+X*UnevenBed[1])+
            Y*((1.-X)*UnevenBed[2]+X*UnevenBed[3]);
        double D=0.,E=0.;
        RaftSimWetSurfaceInterpolation::ResolveMixed(UnevenBed,MixedDepth,Available,X,Y,B,1.,1.,D,E,OutNormal);
        return E;
    };
    FVector Actual,Unused; Evaluate(.2,.3,Actual);
    const double Step=1.e-5;
    const double Dx=(Evaluate(.2+Step,.3,Unused)-Evaluate(.2-Step,.3,Unused))/(2.*Step);
    const double Dy=(Evaluate(.2,.3+Step,Unused)-Evaluate(.2,.3-Step,Unused))/(2.*Step);
    TestTrue(TEXT("mixed normal differentiates its actual reconstructed stage"),
        Actual.Equals(FVector(-Dx,-Dy,1.).GetSafeNormal(),1.e-8));
    return !HasAnyErrors();
}
#endif
