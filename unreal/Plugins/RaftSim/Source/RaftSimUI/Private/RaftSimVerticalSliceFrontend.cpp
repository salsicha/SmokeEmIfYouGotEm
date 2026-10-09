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
    // These are launch contracts, not menu labels. South Fork bounds match
    // reconstruction_2026_09/full_reach/playable_route/session_contracts.json.
    // Named boundaries are provisional guide mileage, not surveyed landmarks.
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
            ERaftSimLicenseTier::Trainee, 1, 120.0f, 9012.3264f),
        MakeScenario(
            TEXT("south_fork_coloma"), TEXT("South Fork II: Coloma Valley"),
            TEXT("Read the transition water and prepare the crew for the gorge."),
            TEXT("/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach"),
            ERaftSimLicenseTier::TripLeader, 2, 9012.3264f, 25427.6352f),
        MakeScenario(
            TEXT("south_fork_gorge"), TEXT("South Fork III: Gorge Rapids"),
            TEXT("Run the technical gorge sequence with deliberate lines and rescue readiness."),
            TEXT("/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach"),
            ERaftSimLicenseTier::SeniorGuide, 3, 25427.6352f, 29933.0304f),
        MakeScenario(
            TEXT("south_fork_lower"), TEXT("South Fork IV: Lower Gorge to Salmon Falls"),
            TEXT("Manage fatigue and finish the long lower reach at the take-out."),
            TEXT("/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach"),
            ERaftSimLicenseTier::SeniorGuide, 4, 29933.0304f, 33280.0f),
        MakeScenario(
            TEXT("south_fork_full_descent"), TEXT("South Fork: Full Guided Descent"),
            TEXT("Guide the reconstructed 33.2 km playable reach, including Troublemaker, in one continuous scored trip."),
            TEXT("/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach"),
            ERaftSimLicenseTier::ExpeditionGuide, 5, 120.0f, 33280.0f, false, true),
        MakeScenario(
            TEXT("hance_challenge"), TEXT("Hance Rapid Free Run"),
            TEXT("Keep the boat in position through Hance and continue into Son of Hance without a reset."),
            TEXT("/Game/RaftSim/Maps/L_Hance"),
            ERaftSimLicenseTier::ExpeditionGuide, 11, 520.0f, 1500.0f),
        MakeScenario(
            TEXT("upper_huacas_challenge"), TEXT("Upper Huacas Free Run"),
            TEXT("Run the Huacas gorge, prepare both Lower Pinball moves, and continue through Guatemala."),
            TEXT("/Game/RaftSim/Maps/L_UpperHuacas"),
            ERaftSimLicenseTier::ExpeditionGuide, 12, 280.0f, 2328.0f),
        MakeScenario(
            TEXT("terminator_challenge"), TEXT("Terminator Free Run"),
            TEXT("Link Terminator's entrance, crux, and exit moves into Khyber Pass and the Himalayas."),
            TEXT("/Game/RaftSim/Maps/L_Terminator"),
            ERaftSimLicenseTier::ExpeditionGuide, 13, 750.0f, 2380.0f),
        MakeScenario(
            TEXT("futaleufu_continuous"), TEXT("Futaleufu: Rio Azul to the Pasarela"),
            TEXT("One continuous descent from the Rio Azul confluence through School House, Asleep at the Wheel, "
                 "the Terminator series, Khyber Pass and the Himalayas to the Pasarela footbridge. "
                 "Terrain is source-captured; the riverbed is inferred. The inflow (30 m3/s Azul + 370 m3/s "
                 "mainstem) is a construction value; the run carries about 390 m3/s while the upper "
                 "backwater still fills."),
            TEXT("/Game/RaftSim/Maps/Continuous/L_Futaleufu_ContinuousContextV1"),
            ERaftSimLicenseTier::ExpeditionGuide, 18, 5420.0f, 15900.0f),
        MakeScenario(
            TEXT("lava_canyon_challenge"), TEXT("Lava Canyon Free Run"),
            TEXT("Manage position, crew fatigue, and swimmer recovery through the continuous Lava Canyon section."),
            TEXT("/Game/RaftSim/Maps/L_LavaCanyon"),
            ERaftSimLicenseTier::ExpeditionGuide, 14, 600.0f, 3975.0f),
        // Rapid stations and the Mukuni Beach finish are observed
        // (observed_rapids/batoka_run_observed_rapids.json: Sentinel-2
        // whitewater, side-stream confluences, outfitter km); Rapid 25 is at
        // ~28.3 km, past the stylised map's 27.36 km end.
        MakeScenario(
            TEXT("zambezi_reference_run"), TEXT("Zambezi: Boiling Pot to Mukuni Beach"),
            TEXT("Runnable Reference Free Run: guide the source-scale Batoka Gorge corridor "
                 "past all 25 rapids at their observed stations to Mukuni Beach. Water and "
                 "missing bathymetry are procedural, with each rapid's observed whitewater, "
                 "pending guide and rapid-specific hydraulic review; Rapid 9 is a mandatory "
                 "portage."),
            TEXT("/Game/RaftSim/Maps/L_Zambezi"),
            ERaftSimLicenseTier::ExpeditionGuide, 15, 0.0f, 28950.0f),
        // Stations are the upper-gorge progress map's (Sentinel-2 midline);
        // they match the map's run manager and the export's checked launch.
        MakeScenario(
            TEXT("zambezi_upper_gorge_challenge"), TEXT("Zambezi: Boiling Pot to Stairway to Heaven"),
            TEXT("Evidence-based low-water upper Batoka Gorge (283 m3/s, the 2025-10-03 Sentinel-2 day): "
                 "banks, whitewater and terrain are measured; the bed and gorge walls are inferred."),
            TEXT("/Game/RaftSim/Maps/L_ZambeziUpperGorge"),
            ERaftSimLicenseTier::ExpeditionGuide, 16, 212.7f, 3382.0f),
        MakeScenario(
            TEXT("catalog_badger_creek"), TEXT("Colorado: Badger Creek"),
            TEXT("8000 cfs construction reach. Set up beside the upper-right hydraulic, "
                 "then keep the oar raft square through the following waves. "
                 "2021 surveyed water profile; rapid bed and individual hydraulics are inferred. "
                 "Difficulty calibration is in progress."),
            TEXT("/Game/RaftSim/Maps/Catalog/L_Colorado_BadgerCreek"),
            ERaftSimLicenseTier::ExpeditionGuide, 17, 300.0f, 1300.0f)
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
