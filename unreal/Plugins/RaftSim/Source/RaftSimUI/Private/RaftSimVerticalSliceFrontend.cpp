#include "RaftSimVerticalSliceFrontend.h"

namespace
{
FRaftSimCareerScenarioDefinition MakeScenario(
    const TCHAR* Id,
    const TCHAR* Name,
    const TCHAR* Briefing,
    const TCHAR* Level,
    ERaftSimLicenseTier Tier,
    int32 Section,
    float StartStation,
    float FinishStation,
    bool bTraining = false,
    bool bFullDescent = false)
{
    FRaftSimCareerScenarioDefinition Scenario;
    Scenario.ScenarioId = FName(Id);
    Scenario.DisplayName = FText::FromString(Name);
    Scenario.Briefing = FText::FromString(Briefing);
    Scenario.LevelName = FName(Level);
    Scenario.RequiredLicense = Tier;
    Scenario.SectionIndex = Section;
    Scenario.StartStationM = StartStation;
    Scenario.FinishStationM = FinishStation;
    Scenario.bTraining = bTraining;
    Scenario.bFullDescent = bFullDescent;
    return Scenario;
}
}

TArray<FRaftSimCareerScenarioDefinition> URaftSimProgressionLibrary::GetScenarioCatalog()
{
    // These are real launch contracts, not menu labels. The four South Fork
    // section bounds share the continuous M4 map and M3 moving-water runtime.
    // Completion checkpoints let a new guide resume the next section at the
    // exact transform already reached in the preceding section.
    return {
        MakeScenario(
            TEXT("training_eddy_basics"), TEXT("Training Eddy: Guide School"),
            TEXT("Learn paddle calls, scouting, high-side response, and swimmer recovery."),
            TEXT("/Game/RaftSim/Maps/L_RaftSimTestTank"),
            ERaftSimLicenseTier::Trainee, 0, -1.0f, -1.0f, true),
        MakeScenario(
            TEXT("south_fork_upper"), TEXT("South Fork I: Chili Bar to Coloma"),
            TEXT("Guide the upper reach, establish crew timing, and finish clean at Coloma."),
            TEXT("/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach"),
            ERaftSimLicenseTier::Trainee, 1, 120.0f, 5200.0f),
        MakeScenario(
            TEXT("south_fork_coloma"), TEXT("South Fork II: Coloma Valley"),
            TEXT("Read the transition water and prepare the crew for the gorge."),
            TEXT("/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach"),
            ERaftSimLicenseTier::TripLeader, 2, 5200.0f, 18500.0f),
        MakeScenario(
            TEXT("south_fork_gorge"), TEXT("South Fork III: Gorge Rapids"),
            TEXT("Run the technical gorge sequence with deliberate lines and rescue readiness."),
            TEXT("/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach"),
            ERaftSimLicenseTier::SeniorGuide, 3, 18500.0f, 33000.0f),
        MakeScenario(
            TEXT("south_fork_lower"), TEXT("South Fork IV: Lower Gorge to Salmon Falls"),
            TEXT("Manage fatigue and finish the long lower reach at the take-out."),
            TEXT("/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach"),
            ERaftSimLicenseTier::SeniorGuide, 4, 33000.0f, 48900.0f),
        MakeScenario(
            TEXT("south_fork_full_descent"), TEXT("South Fork: Full Guided Descent"),
            TEXT("Guide the complete 48.8 km run in one continuous scored trip."),
            TEXT("/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach"),
            ERaftSimLicenseTier::ExpeditionGuide, 5, 120.0f, 48900.0f, false, true),
        MakeScenario(
            TEXT("troublemaker_challenge"), TEXT("Troublemaker Rapid Challenge"),
            TEXT("A short technical challenge at the commercial flow band."),
            TEXT("/Game/RaftSim/Maps/L_Troublemaker"),
            ERaftSimLicenseTier::Trainee, 10, -1.0f, -1.0f),
        MakeScenario(
            TEXT("hance_challenge"), TEXT("Hance Rapid Free Run"),
            TEXT("Bonus large-volume Colorado rapid slice."),
            TEXT("/Game/RaftSim/Maps/L_Hance"),
            ERaftSimLicenseTier::ExpeditionGuide, 11, -1.0f, -1.0f),
        MakeScenario(
            TEXT("upper_huacas_challenge"), TEXT("Upper Huacas Free Run"),
            TEXT("Bonus rain-fed Pacuare rapid slice."),
            TEXT("/Game/RaftSim/Maps/L_UpperHuacas"),
            ERaftSimLicenseTier::ExpeditionGuide, 12, -1.0f, -1.0f),
        MakeScenario(
            TEXT("terminator_challenge"), TEXT("Terminator Free Run"),
            TEXT("Bonus Futaleufu big-water rapid slice."),
            TEXT("/Game/RaftSim/Maps/L_Terminator"),
            ERaftSimLicenseTier::ExpeditionGuide, 13, -1.0f, -1.0f),
        MakeScenario(
            TEXT("lava_canyon_challenge"), TEXT("Lava Canyon Free Run"),
            TEXT("Bonus Chilko rapid slice."),
            TEXT("/Game/RaftSim/Maps/L_LavaCanyon"),
            ERaftSimLicenseTier::ExpeditionGuide, 14, -1.0f, -1.0f)
    };
}

bool URaftSimProgressionLibrary::FindScenario(
    FName ScenarioId, FRaftSimCareerScenarioDefinition& OutScenario)
{
    for (const FRaftSimCareerScenarioDefinition& Scenario : GetScenarioCatalog())
    {
        if (Scenario.ScenarioId == ScenarioId)
        {
            OutScenario = Scenario;
            return true;
        }
    }
    return false;
}

ERaftSimMedal URaftSimProgressionLibrary::CalculateMedal(
    float OverallScore, float SafetyScore, bool bAssistUsed)
{
    const float Overall = FMath::Clamp(OverallScore, 0.0f, 1.0f);
    const float Safety = FMath::Clamp(SafetyScore, 0.0f, 1.0f);
    if (Overall >= 0.90f && Safety >= 0.90f && !bAssistUsed)
    {
        return ERaftSimMedal::Gold;
    }
    if (Overall >= 0.72f && Safety >= 0.65f)
    {
        return ERaftSimMedal::Silver;
    }
    if (Overall >= 0.45f && Safety >= 0.35f)
    {
        return ERaftSimMedal::Bronze;
    }
    return ERaftSimMedal::None;
}

FText URaftSimProgressionLibrary::MedalDisplayName(ERaftSimMedal Medal)
{
    switch (Medal)
    {
        case ERaftSimMedal::Bronze: return NSLOCTEXT("RaftSim", "BronzeMedal", "Bronze");
        case ERaftSimMedal::Silver: return NSLOCTEXT("RaftSim", "SilverMedal", "Silver");
        case ERaftSimMedal::Gold: return NSLOCTEXT("RaftSim", "GoldMedal", "Gold");
        default: return NSLOCTEXT("RaftSim", "NoMedal", "No medal");
    }
}

FText URaftSimProgressionLibrary::LicenseDisplayName(ERaftSimLicenseTier Tier)
{
    switch (Tier)
    {
        case ERaftSimLicenseTier::TripLeader:
            return NSLOCTEXT("RaftSim", "TripLeader", "Trip Leader");
        case ERaftSimLicenseTier::SeniorGuide:
            return NSLOCTEXT("RaftSim", "SeniorGuide", "Senior Guide");
        case ERaftSimLicenseTier::ExpeditionGuide:
            return NSLOCTEXT("RaftSim", "ExpeditionGuide", "Expedition Guide");
        default:
            return NSLOCTEXT("RaftSim", "Trainee", "Guide Trainee");
    }
}
