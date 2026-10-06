#pragma once

#include "CoreMinimal.h"

/**
 * Named rapids along each playable reach, for the on-screen title as the boat
 * approaches. Stations are the run's own progress coordinate (the same one the
 * HUD route ribbon and the rapid assessment plans use); ControlStationM is the
 * rapid's main feature. Grades are the catalogued class, not a game rating.
 * Source: unreal/Tests/Data/rapid_assessment_reaches.json (kept in step by
 * RaftSim.UI.RapidTitlesMatchAssessmentPlans).
 */
struct FRaftSimRapidTitle
{
    const TCHAR* MapName;
    const TCHAR* Id;
    const TCHAR* Name;
    const TCHAR* Grade;
    float ControlStationM;
    bool bPortage;
};

namespace RaftSimRapidTitles
{
/** Every titled rapid, in reach order per map. */
TConstArrayView<FRaftSimRapidTitle> All();

/** The titled rapids on one map (short package name, PIE prefix stripped). */
TArray<const FRaftSimRapidTitle*> ForMap(const FString& MapName);

/** "CLASS IV–V", "SURF WAVE", "CLASS V–VI · PORTAGE". */
FText GradeLine(const FRaftSimRapidTitle& Rapid);
}
