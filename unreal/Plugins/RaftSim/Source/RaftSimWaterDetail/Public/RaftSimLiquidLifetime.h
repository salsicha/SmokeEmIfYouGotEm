#pragma once
#include "CoreMinimal.h"

// A token is valid only in one open, aligned native tick of one regional
// generation. Birth identity is (Generation, owner, uint32 native UniqueID).
// Restart creates a NEW coordinator and native datasets, never clears this one.
struct FRaftSimLiquidTickToken
{
    FGuid Generation;
    uint32 Step=0;
    uint32 TransferEpoch=0;
};

struct FRaftSimLiquidBirthPlan
{
    uint32 Owner=0,Rate=0,Events=0;
    bool Reset=false;
};

class FRaftSimLiquidLifetime
{
    FGuid Generation;
    TArray<uint64> Births;
    uint32 Step=0;
    bool Open=false,Claimed=false,Failed=false;
    bool Reject(FString& Error,const TCHAR* Message)
    { Failed=true;Error=Message;return false; }
    bool Matches(const FRaftSimLiquidTickToken& Token) const
    { return !Failed && Open && Token.Generation==Generation && Token.Step==Step && Token.TransferEpoch==Step-1; }
public:
    bool Initialize(const FGuid& Id,uint32 Owners,FString& Error)
    {
        if(Failed || Generation.IsValid() || !Id.IsValid() || Owners<2 || Owners>16)
            return Reject(Error,TEXT("Liquid generation requires fresh coordinator and complete owners"));
        Generation=Id;Births.Init(0,Owners);Error.Reset();return true;
    }
    bool BeginStep(uint32 NativeStep,TConstArrayView<FRaftSimLiquidBirthPlan> Plans,
        FRaftSimLiquidTickToken& Token,FString& Error)
    {
        Token={};
        if(Failed || !Generation.IsValid() || Open || NativeStep!=Step+1 ||
            NativeStep>=0x7fffffffu || Plans.Num()!=Births.Num())
            return Reject(Error,TEXT("Liquid tick skipped/repeated or acquire-tag epoch exhausted"));
        TArray<uint64> Next=Births;TSet<uint32> Seen;
        for(const auto& P:Plans)
        {
            if(P.Owner>=uint32(Births.Num()) || Seen.Contains(P.Owner) || P.Reset!=(Step==0))
                return Reject(Error,TEXT("Unexpected native reset or incomplete liquid generation participants"));
            Seen.Add(P.Owner);
            Next[P.Owner]+=uint64(P.Rate)+uint64(P.Events);
            // All uint32 bit patterns are valid identity words, including the
            // signed-negative half. The NEXT birth after 2^32 would alias zero.
            if(Next[P.Owner]>uint64(MAX_uint32)+1)
                return Reject(Error,TEXT("Native liquid birth sequence would wrap; fresh generation required"));
        }
        Births=MoveTemp(Next);Step=NativeStep;Open=true;Claimed=false;
        Token={Generation,Step,Step-1};Error.Reset();return true;
    }
    bool ClaimTransfer(const FRaftSimLiquidTickToken& Token,FString& Error)
    {
        if(!Matches(Token) || Step<2 || Claimed)
            return Reject(Error,TEXT("Stale generation, closed tick or duplicate native liquid transfer"));
        Claimed=true;Error.Reset();return true;
    }
    bool EndStep(const FRaftSimLiquidTickToken& Token,FString& Error)
    {
        if(!Matches(Token)) return Reject(Error,TEXT("Liquid tick closed with stale generation or step"));
        Open=false;Error.Reset();return true;
    }
    const FGuid& GetGeneration() const { return Generation; }
    const TArray<uint64>& GetBirths() const { return Births; }
    uint32 GetStep() const { return Step; }
    bool IsFailed() const { return Failed; }
};
