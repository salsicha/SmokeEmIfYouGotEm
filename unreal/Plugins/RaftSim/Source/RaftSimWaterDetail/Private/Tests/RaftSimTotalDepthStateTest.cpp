#include "Misc/AutomationTest.h"
#include "RaftSimTotalDepthStateGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTotalDepthStateTest,"RaftSim.WaterDetail.ConservedTotalStateGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FTotalDepthStateTest::RunTest(const FString&)
{
    if(GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("A real SM5+ GPU is required for total-depth storage evidence"));return false; }
    const FIntPoint Size(17,13);constexpr int32 Count=17*13;
    const TArray<FIntPoint> Shifts={{0,0},{3,-2},{-4,1},{16,0},{-2,-12},{0,4}};
    bool Passed=true,RefusedInvalid=true;int32 ExactCells=0,TinyCells=0;float MaximumSurfaceError=0;
    FString Error;
    ENQUEUE_RENDER_COMMAND(RaftSimTotalDepthStateTest)([&](FRHICommandListImmediate& Cmd)
    {
        for(int32 Case=0;Case<Shifts.Num()+1;++Case)
        {
            const bool Invalid=Case==Shifts.Num();
            const FIntPoint Shift=Invalid ? FIntPoint::ZeroValue : Shifts[Case];
            TArray<FVector4f> Before,Entering,Expected,PriorExchange;
            TArray<FVector2f> Reference;
            for(int32 I=0;I<Count;++I)
            {
                const float H=I%7==0 ? 1e-30f : I%5==0 ? 1e-12f : .1f+.01f*(I%11);
                Before.Add(FVector4f(H,2*H,-3*H,1.f+.03f*I));
                Entering.Add(FVector4f(.2f,.02f,-.04f,2.f));
                PriorExchange.Add(FVector4f(.125f,-.25f,.5f,-.125f));
                const float Bed=.02f*(I%17)+.03f*(I/17);
                // Changing and completely dry reference means cannot erase
                // retained water. This is not a physical bed-change operation.
                Reference.Add(FVector2f(Bed,I%3==0 ? Bed : Bed+.1f+.02f*Case));
            }
            if(Invalid)
            {
                Before[0].X=-.1f;Before[1].W=-2;Before[2]=FVector4f(0,1,0,0);
                const uint32 NaNBits=0x7fc01234u;FMemory::Memcpy(&Before[3].X,&NaNBits,4);
                FMemory::Memcpy(&Reference[4].X,&NaNBits,4);
            }
            uint32 Retained=0;
            for(int32 Y=0;Y<Size.Y;++Y)for(int32 X=0;X<Size.X;++X)
            {
                const int32 OldX=X+Shift.X,OldY=Y+Shift.Y;
                const bool Inside=OldX>=0 && OldX<Size.X && OldY>=0 && OldY<Size.Y;
                Expected.Add(Inside ? Before[OldY*Size.X+OldX] : Entering[Y*Size.X+X]);
                Retained+=Inside;
            }
            FRDGBuilder Graph(Cmd);
            auto Previous=CreateStructuredBuffer(Graph,TEXT("TotalStateTest.Previous"),TConstArrayView<FVector4f>(Before));
            auto New=CreateStructuredBuffer(Graph,TEXT("TotalStateTest.Entering"),TConstArrayView<FVector4f>(Entering));
            auto Ref=CreateStructuredBuffer(Graph,TEXT("TotalStateTest.Reference"),TConstArrayView<FVector2f>(Reference));
            if(Case==0)
            {
                RefusedInvalid &= !RaftSimTransferTotalDepthStateGPU(Graph,nullptr,New,Ref,Size,Shift,.5f,Error).State;
                RefusedInvalid &= !RaftSimTransferTotalDepthStateGPU(Graph,Previous,Ref,Ref,Size,Shift,.5f,Error).State;
                RefusedInvalid &= !RaftSimTransferTotalDepthStateGPU(Graph,Previous,New,Ref,{16,13},Shift,.5f,Error).State;
                RefusedInvalid &= !RaftSimTransferTotalDepthStateGPU(Graph,Previous,New,Ref,Size,{17,0},.5f,Error).State;
                RefusedInvalid &= !RaftSimTransferTotalDepthStateGPU(Graph,Previous,New,Ref,Size,{MIN_int32,0},.5f,Error).State;
                RefusedInvalid &= !RaftSimTransferTotalDepthStateGPU(Graph,Previous,New,Ref,Size,Shift,0,Error).State;
                RefusedInvalid &= !RaftSimTransferTotalDepthStateGPU(Graph,Previous,New,Ref,{MAX_int32,13},Shift,.5f,Error).State;
            }
            auto Prior=CreateStructuredBuffer(Graph,TEXT("TotalStateTest.PreviousExchange"),PriorExchange);
            auto Result=RaftSimTransferTotalDepthStateGPU(Graph,Previous,New,Ref,Size,Shift,.5f,Error,Prior);
            if(!Result.State || !Error.IsEmpty()) { Passed=false;Graph.Execute();return; }
            FRHIGPUBufferReadback StateRead(TEXT("TotalStateTest.State")),SurfaceRead(TEXT("TotalStateTest.Surface")),DiagRead(TEXT("TotalStateTest.Diagnostics")),ExchangeRead(TEXT("TotalStateTest.Exchange"));
            AddEnqueueCopyPass(Graph,&StateRead,Result.State,Count*16);
            AddEnqueueCopyPass(Graph,&SurfaceRead,Result.Surface,Count*16);
            AddEnqueueCopyPass(Graph,&DiagRead,Result.Diagnostics,16);
            AddEnqueueCopyPass(Graph,&ExchangeRead,Result.WindowExchange,Count*16);
            Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
            const auto* State=static_cast<const FVector4f*>(StateRead.Lock(Count*16));
            const auto* Surface=static_cast<const FVector4f*>(SurfaceRead.Lock(Count*16));
            const auto* Diagnostics=static_cast<const uint32*>(DiagRead.Lock(16));
            const auto* Exchange=static_cast<const FVector4f*>(ExchangeRead.Lock(Count*16));
            if(!State || !Surface || !Diagnostics || !Exchange) { Passed=false;return; }
            Passed &= Diagnostics[0]==(Invalid ? 4u : 0u) && Diagnostics[1]==(Invalid ? 1u : 0u) &&
                Diagnostics[2]==Retained && Diagnostics[3]==Count-Retained;
            if(Invalid)
            {
                Passed &= State[0].X==-.1f && State[1].W==-2 && State[2].X==0 && State[2].Y==1 && !FMath::IsFinite(State[3].X);
            }
            else
            {
                auto Height=[&](int32 X,int32 Y)
                { const int32 I=Y*Size.X+X;return (Reference[I].X-Reference[I].Y)+Expected[I].X; };
                for(int32 Y=0;Y<Size.Y;++Y)for(int32 X=0;X<Size.X;++X)
                {
                    const int32 I=Y*Size.X+X,L=FMath::Max(X-1,0),R=FMath::Min(X+1,Size.X-1),
                        B=FMath::Max(Y-1,0),T=FMath::Min(Y+1,Size.Y-1);
                    Passed &= FMemory::Memcmp(&State[I],&Expected[I],16)==0;
                    const FIntPoint Old=FIntPoint(X,Y)+Shift,Next=FIntPoint(X,Y)-Shift;
                    const bool RetainedCell=Old.X>=0 && Old.Y>=0 && Old.X<Size.X && Old.Y<Size.Y;
                    const bool Departed=Next.X<0 || Next.Y<0 || Next.X>=Size.X || Next.Y>=Size.Y;
                    const FVector4f Inventory=(PriorExchange[I]+(RetainedCell?FVector4f(0,0,0,0):Entering[I]))-
                        (Departed?Before[I]:FVector4f(0,0,0,0));
                    Passed &= Exchange[I]==Inventory;
                    ++ExactCells;TinyCells+=State[I].X>0 && State[I].X<1e-10f;
                    const FVector4f Target(Height(X,Y),(Height(R,Y)-Height(L,Y))/((R-L)*.5f),
                        (Height(X,T)-Height(X,B))/((T-B)*.5f),1-FMath::Exp(-Expected[I].W));
                    for(int32 A=0;A<4;++A)
                    {
                        if(!FMath::IsFinite(Surface[I][A]))Passed=false;
                        MaximumSurfaceError=FMath::Max(MaximumSurfaceError,FMath::Abs(Surface[I][A]-Target[A]));
                    }
                }
            }
            StateRead.Unlock();SurfaceRead.Unlock();DiagRead.Unlock();ExchangeRead.Unlock();
        }
    });
    FlushRenderingCommands();
    TestTrue(TEXT("invalid transfer descriptors rejected without allocation/mutation"),RefusedInvalid);
    TestTrue(TEXT("exact h/hu/hv/foam survives signed window shifts and changed/dry means; invalid values are reported, not repaired"),Passed && TinyCells>0);
    TestTrue(TEXT("one derived surface matches the same transferred state"),MaximumSurfaceError<2e-6f);
    AddInfo(FString::Printf(TEXT("Total-depth GPU storage checked %d exact cells, %d tiny wet cells; derived surface max error %.9g; no evolution or scene acceptance claimed"),
        ExactCells,TinyCells,MaximumSurfaceError));
    if(!Error.IsEmpty())AddError(Error);
    return !HasAnyErrors();
}
#endif
