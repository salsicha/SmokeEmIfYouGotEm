#include "Misc/AutomationTest.h"
#include "../Materials/RaftSimLiquidPressureColoring.h"
#include "../Materials/RaftSimLiquidRegionalProjection.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidPressureColoringTest,
    "RaftSim.Editor.LiquidPressureColoring",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLiquidPressureColoringTest::RunTest(const FString&)
{
    using namespace RaftSimLiquidPressureColoring;
    // Exhaust every even supported X extent, including the full rapid's 494.
    // Coverage and dependency checks cover both phase origins in Y and Z.
    for (int32 NX=4;NX<=4096;NX+=2)
        for (int32 Y=0;Y<4;++Y) for (int32 Z=0;Z<4;++Z)
        {
            TArray<int32> Visits,Color;Visits.Init(0,NX);Color.Init(-1,NX);
            for (int32 Phase=0;Phase<2;++Phase)
                for (int32 T=0;T<NX/2;++T)
                {
                    const int32 Base=X(T,Y,Z,Phase);
                    for (int32 Lane=0;Lane<Lanes(Base,NX);++Lane)
                    {
                        const int32 P=Base+Lane;
                        if (P<0 || P>=NX || ++Visits[P]!=1 || ((P/2+Y/2+Z/2+Phase)%2)!=0)
                        { AddError(FString::Printf(TEXT("Invalid pressure ownership NX=%d P=%d"),NX,P));return false; }
                        Color[P]=Phase;
                    }
                }
            for (int32 P=0;P<NX;++P)
                if (Visits[P]!=1 || (P+2<NX && Color[P]==Color[P+2]))
                { AddError(TEXT("Skipped/duplicated cell or same-phase pressure dependency"));return false; }
        }
    TestEqual(TEXT("Final thread visits both lanes at 494"),Lanes(X(246,0,0,0),494),2);
    TestEqual(TEXT("Opposite phase skips the out-of-range base"),Lanes(X(246,0,0,1),494),0);
    TestEqual(TEXT("Old 68-cell dispatch remains single-lane"),Lanes(X(33,0,0,1),68),1);
    const FString Code=Wrap(TEXT("Pressure=0; int3 p=int3(IndexX,IndexY,IndexZ); Grid.SetFloatValue(p.x,p.y,p.z,Pressure);\n"),TEXT("Grid"));
    TestTrue(TEXT("Native dimension is read, not inferred from fixture"),Code.Contains(TEXT("Grid.GetNumCells(pressureNX,pressureNY,pressureNZ)")));
    TestTrue(TEXT("The additional lane actually changes the pressure index"),Code.Contains(TEXT("int3 p=int3(IndexX+pressureLane,IndexY,IndexZ)")));
    TestTrue(TEXT("All body reads and writes are within the guarded loop"),Code.Find(TEXT("for(int pressureLane"))<Code.Find(TEXT("Grid.SetFloatValue")));
    // Real South Fork cuts, including the reflected-Y 98/34/0 phase origins
    // and partial 110-cell X dispatch. Compare to PARENT coordinates, not a
    // second regional formula; visit each physical cell once in two phases.
    using namespace RaftSimLiquidRegionalProjection;
    RaftSimLiquidRegionalState::FParent Parent;Parent.Cells=FIntVector(490,162,24);Parent.Spacing=FVector(50,50,800.0/24);
    int32 PhysicalVisits=0,Shifted=0;
    for (int32 FY:{0,64,128}) for (int32 FX:{0,128,256,384})
    {
        RaftSimLiquidRegionalState::FState R;R.FirstCell=FIntPoint(FX,FY);
        R.Cells=FIntVector(FMath::Min(128,490-FX),FMath::Min(64,162-FY),24);
        R.ComputationalCells=R.Cells+FIntVector(4,4,0);R.Extent=FVector(R.ComputationalCells)*Parent.Spacing;
        FLayout L;FString Error;
        if (!TestTrue(TEXT("Actual region pressure layout"),Build(Parent,R,L,Error))) return false;
        Shifted+=L.Phase()!=0;
        for (int32 Y=0;Y<R.ComputationalCells.Y;++Y) for (int32 Z=0;Z<24;++Z)
            for (int32 Phase=0;Phase<2;++Phase) for (int32 T=0;T<R.ComputationalCells.X/2;++T)
            {
                const int32 Base=X(T,Y,Z,Phase,L.Phase());
                for (int32 Lane=0;Lane<Lanes(Base,R.ComputationalCells.X);++Lane)
                {
                    const int32 PX=Base+Lane,GX=PX+FX,GY=Y+162-FY-R.Cells.Y;
                    if (((GX/2+GY/2+Z/2)%2)!=Phase) { AddError(TEXT("Regional update uses the wrong global pressure phase"));return false; }
                    const bool Interior=PX>=2 && Y>=2 && PX<R.Cells.X+2 && Y<R.Cells.Y+2;
                    const bool InParent=GX>=2 && GY>=2 && GX<492 && GY<164;
                    if (L.Shared(FIntPoint(PX,Y))!=(!Interior && InParent))
                    { AddError(TEXT("Shared pressure ownership differs from parent physical extent"));return false; }
                    PhysicalVisits+=Interior;
                }
            }
        auto Invalid=R;Invalid.FirstCell.X+=1;
        TestFalse(TEXT("Odd cut cannot silently change pressure coloring"),Build(Parent,Invalid,L,Error));
    }
    TestEqual(TEXT("Every parent physical cell visited once, without trimming"),PhysicalVisits,490*162*24);
    TestEqual(TEXT("Eight regions require the opposite local phase"),Shifted,8);
    return true;
}
