#include "RaftSimCrewChatter.h"

#include "RaftSimCrewRoster.h"

void FRaftSimCrewChatter::Say(FName PassengerId, const TArray<FText>& Lines, bool bImportant)
{
    if (Lines.IsEmpty())
    {
        return;
    }
    // Ordinary chatter never piles up behind itself.
    if (!bImportant && Pending.Num() >= 1)
    {
        return;
    }
    const FText& Line = Lines[Random.RandRange(0, Lines.Num() - 1)];
    Pending.Add({FText::Format(NSLOCTEXT("RaftSim", "CrewLine", "{0}: {1}"),
        URaftSimCrewRoster::GetFirstName(PassengerId), Line), bImportant});
}

bool FRaftSimCrewChatter::Tick(const ARaftSimRaftActor& Raft, float DeltaSeconds, FText& OutLine)
{
    const float Dt = FMath::Clamp(DeltaSeconds, 0.0f, 0.25f);
    const TArray<FRaftSimCrewIdentity>& Roster = URaftSimCrewRoster::GetRoster();

    // A flip: the guide calls it, then the boat takes stock.
    const ERaftSimRaftMode Mode = Raft.GetRaftMode();
    if (Mode != LastMode && Mode == ERaftSimRaftMode::Capsized)
    {
        Say(TEXT("guide"), URaftSimCrewRoster::GetIdentity(TEXT("guide")).FlipLines, true);
        const FRaftSimCrewIdentity& Other = Roster[Random.RandRange(1, Roster.Num() - 1)];
        Say(Other.PassengerId, Other.FlipLines, true);
    }
    LastMode = Mode;

    // Swims and rescues, in the swimmer's own words.
    for (const FRaftSimCrewIdentity& Person : Roster)
    {
        const bool bSwimming = Raft.IsPassengerSwimming(Person.PassengerId);
        const bool* bWas = WasSwimming.Find(Person.PassengerId);
        if (bWas && *bWas != bSwimming && Mode != ERaftSimRaftMode::Capsized)
        {
            Say(Person.PassengerId, bSwimming ? Person.OverboardLines : Person.RescuedLines, true);
        }
        WasSwimming.Add(Person.PassengerId, bSwimming);
    }

    // Big water from how hard the boat is being thrown about (smoothed turn
    // rate of the hull), and the run-out once it settles.
    const FQuat Rotation = Raft.GetActorQuat();
    if (bHasLastRotation && Dt > KINDA_SMALL_NUMBER)
    {
        const float TurnDeg = FMath::RadiansToDegrees(Rotation.AngularDistance(LastRotation));
        SmoothedTurnRateDegPerS = FMath::FInterpTo(SmoothedTurnRateDegPerS, TurnDeg / Dt, Dt, 3.0f);
    }
    LastRotation = Rotation;
    bHasLastRotation = true;
    SecondsSinceBigWaterLine += Dt;
    const bool bRough = SmoothedTurnRateDegPerS > 16.0f;
    RoughSeconds = bRough ? RoughSeconds + Dt : 0.0f;
    CalmSeconds = SmoothedTurnRateDegPerS < 5.0f ? CalmSeconds + Dt : 0.0f;
    if (Mode == ERaftSimRaftMode::Upright && Raft.GetSwimmerCount() == 0)
    {
        if (!bInBigWater && RoughSeconds > 0.6f)
        {
            bInBigWater = true;
            if (SecondsSinceBigWaterLine > 20.0f)
            {
                // Nervous people speak up more; the guide calls about a third.
                float Total = 0.0f;
                for (const FRaftSimCrewIdentity& Person : Roster)
                {
                    Total += Person.PassengerId == TEXT("guide") ? 0.6f : 0.4f + Person.Nerves;
                }
                float Pick = Random.FRandRange(0.0f, Total);
                for (const FRaftSimCrewIdentity& Person : Roster)
                {
                    Pick -= Person.PassengerId == TEXT("guide") ? 0.6f : 0.4f + Person.Nerves;
                    if (Pick <= 0.0f)
                    {
                        Say(Person.PassengerId, Person.BigWaterLines, false);
                        break;
                    }
                }
                SecondsSinceBigWaterLine = 0.0f;
            }
        }
        else if (bInBigWater && CalmSeconds > 4.0f)
        {
            bInBigWater = false;
            const FRaftSimCrewIdentity& Person = Roster[Random.RandRange(0, Roster.Num() - 1)];
            Say(Person.PassengerId, Person.CleanRunLines, false);
        }
    }

    Cooldown -= Dt;
    if (Cooldown <= 0.0f && !Pending.IsEmpty())
    {
        OutLine = Pending[0].Text;
        Pending.RemoveAt(0);
        Cooldown = 3.6f;
        return true;
    }
    return false;
}
