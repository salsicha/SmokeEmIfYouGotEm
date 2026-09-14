#pragma once
#include "CoreMinimal.h"
#include "Misc/ScopeLock.h"

// Immutable resolved texture, including its own registration row. This exact
// payload is uploaded for shading and sampled for support; never combine it
// with the simulation's newer origin or clock.
struct FRaftSimDetailPresentationFrame
{
    FIntPoint Size=FIntPoint::ZeroValue; // data rows; texture has one extra row
    TArray<FVector4f> Pixels;
    uint64 Sequence=0;
    double ElapsedSeconds=0,SimulationSeconds=0;
    bool bGPUClockMetadata=false;
    // Attach the host timestamp captured WITH this legacy GPU readback.
    bool WriteHostClockMetadata()
    {
        if(bGPUClockMetadata || !Validate())return false;
        const float High=float(SimulationSeconds),Low=float(SimulationSeconds-double(High));
        if(!FMath::IsFinite(High) || !FMath::IsFinite(Low))return false;
        Pixels[Size.X*Size.Y+1]=FVector4f(High,Low,0,3);
        return true;
    }
    // Adopt only the clock carried by this completed GPU texture. The older
    // detail solver uses repeated registration metadata and keeps its existing
    // host clock path; it must not silently interpret that row as a GPU time.
    bool AdoptGPUClock()
    {
        if(Size.X<2 || Size.Y<2 || Pixels.Num()!=int64(Size.X)*(Size.Y+1))return false;
        const auto Clock=Pixels[Size.X*Size.Y+1];
        if(Clock.ContainsNaN() || Clock.W!=2.f || Clock.Z!=0.f)return false;
        SimulationSeconds=double(Clock.X)+double(Clock.Y);bGPUClockMetadata=true;
        return FMath::IsFinite(SimulationSeconds);
    }
    bool Validate() const
    {
        if (Size.X<2 || Size.Y<2 || Pixels.Num()!=int64(Size.X)*(Size.Y+1) || !Sequence ||
            !FMath::IsFinite(ElapsedSeconds) || !FMath::IsFinite(SimulationSeconds)) return false;
        const FVector4f M=Pixels[Size.X*Size.Y];
        if (M.W!=1.f || M.Z<=0.f) return false;
        if(bGPUClockMetadata)
        {
            const auto Clock=Pixels[Size.X*Size.Y+1];
            if(Clock.W!=2.f || Clock.Z!=0.f || SimulationSeconds!=double(Clock.X)+double(Clock.Y))return false;
        }
        for (const auto& P:Pixels) if (P.ContainsNaN()) return false;
        if(!bGPUClockMetadata && Pixels[Size.X*Size.Y+1].W==3.f)
        {
            const auto Clock=Pixels[Size.X*Size.Y+1];
            const float High=float(SimulationSeconds),Low=float(SimulationSeconds-double(High));
            if(Clock.Z!=0.f || Clock.X!=High || Clock.Y!=Low)return false;
        }
        return true;
    }
    FVector4f SampleField(FVector2f FieldM) const
    {
        if (Size.X<2 || Size.Y<2 || Pixels.Num()!=int64(Size.X)*(Size.Y+1) || FieldM.ContainsNaN()) return FVector4f(0,0,0,0);
        const auto M=Pixels[Size.X*Size.Y];
        if (M.W!=1.f || M.Z<=0.f) return FVector4f(0,0,0,0);
        const FVector2f P=(FieldM-FVector2f(M.X,M.Y))/M.Z;
        if (P.X<0 || P.Y<0 || P.X>Size.X-1 || P.Y>Size.Y-1) return FVector4f(0,0,0,0);
        const int32 X=FMath::Clamp(FMath::FloorToInt(P.X),0,Size.X-2);
        const int32 Y=FMath::Clamp(FMath::FloorToInt(P.Y),0,Size.Y-2);
        return FMath::Lerp(FMath::Lerp(Pixels[Y*Size.X+X],Pixels[Y*Size.X+X+1],P.X-X),
            FMath::Lerp(Pixels[(Y+1)*Size.X+X],Pixels[(Y+1)*Size.X+X+1],P.X-X),P.Y-Y);
    }
    float DisplacementCm(const FVector& WorldCm,float NorthSign) const
    {
        // Match the material custom node's float world-coordinate conversion.
        return 100.f*SampleField(FVector2f(float(WorldCm.X)*.01f,float(WorldCm.Y)*(.01f*NorthSign))).X;
    }
};

class FRaftSimDetailFrameMailbox
{
public:
    bool Publish(TSharedPtr<const FRaftSimDetailPresentationFrame,ESPMode::ThreadSafe> Frame)
    {
        if (!Frame || !Frame->Validate()) return false;
        FScopeLock Lock(&Mutex);
        if (Frame->Sequence<=LatestSequence) return false;
        LatestSequence=Frame->Sequence; Pending=MoveTemp(Frame); return true;
    }
    TSharedPtr<const FRaftSimDetailPresentationFrame,ESPMode::ThreadSafe> TakeLatest()
    {
        FScopeLock Lock(&Mutex); return MoveTemp(Pending);
    }
private:
    FCriticalSection Mutex;
    uint64 LatestSequence=0;
    TSharedPtr<const FRaftSimDetailPresentationFrame,ESPMode::ThreadSafe> Pending;
};
