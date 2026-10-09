#include "RaftSimRapidTitles.h"

#include "Misc/PackageName.h"

namespace
{
// Control stations from unreal/Tests/Data/rapid_assessment_reaches.json.
// Unnamed approach riffles and minor reach-end features carry no title.
const FRaftSimRapidTitle GRapids[] = {
    // L_SouthForkAmerican_FullReach
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("chili_bar_hole"), TEXT("Chili Bar Hole"), TEXT("surf"), 36.2f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("bed_and_breakfast"), TEXT("Bed and Breakfast"), TEXT("II"), 338.0f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("meat_grinder"), TEXT("Meat Grinder"), TEXT("III+"), 965.6f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("racehorse_bend"), TEXT("Racehorse Bend"), TEXT("III"), 2092.1f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("maya"), TEXT("Maya"), TEXT("II-III"), 2414.0f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("rock_garden"), TEXT("Rock Garden"), TEXT("II"), 2735.9f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("african_queen"), TEXT("African Queen"), TEXT("II"), 3218.7f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("triple_threat"), TEXT("Triple Threat"), TEXT("III"), 4989.0f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("the_narrows"), TEXT("The Narrows"), TEXT("II+"), 5616.6f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("mini_gorge"), TEXT("Mini Gorge"), TEXT("II-II+"), 6421.3f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("swimmer_s_rapid_chili_bar_run"), TEXT("Swimmer's Rapid (Chili Bar run)"), TEXT("II"), 6646.6f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("troublemaker"), TEXT("Troublemaker"), TEXT("III+"), 8368.6f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("gremlin_s"), TEXT("Gremlin's"), TEXT("II"), 10589.5f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("old_scary"), TEXT("Old Scary"), TEXT("II"), 11362.0f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("blue_house_hole"), TEXT("Blue House Hole"), TEXT("surf"), 11716.0f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("pink_fuzzy_bunny_with_a_fang"), TEXT("Pink Fuzzy Bunny With a Fang"), TEXT("II-II+"), 13502.4f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("barking_dog"), TEXT("Barking Dog"), TEXT("II-II+"), 14854.2f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("killer_fang_falls"), TEXT("Killer Fang Falls"), TEXT("II"), 15176.1f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("dave_moore"), TEXT("Dave Moore"), TEXT("II"), 15916.4f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("current_divider"), TEXT("Current Divider"), TEXT("II-II+"), 16415.3f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("highway_rapid"), TEXT("Highway Rapid"), TEXT("II-II+"), 17912.0f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("swimmer_s_c_to_g"), TEXT("Swimmer's (C to G)"), TEXT("II-II+"), 18443.1f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("cable_car_rapid"), TEXT("Cable Car Rapid"), TEXT("II-II+"), 19183.4f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("airplane_turn"), TEXT("Airplane Turn"), TEXT("II"), 20567.4f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("speed_bump"), TEXT("Speed Bump"), TEXT("surf"), 24639.1f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("splat_rock"), TEXT("Splat Rock"), TEXT("II"), 25154.0f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("fowler_s_rock"), TEXT("Fowler's Rock"), TEXT("III"), 25427.6f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("son_of_fowler"), TEXT("Son of Fowler"), TEXT("II"), 25524.2f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("upper_haystack_canyon"), TEXT("Upper Haystack Canyon"), TEXT("III"), 26071.4f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("lost_hat"), TEXT("Lost Hat"), TEXT("III-"), 26876.0f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("satan_s_cesspool"), TEXT("Satan's Cesspool"), TEXT("III+"), 27197.9f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("son_of_satan"), TEXT("Son of Satan"), TEXT("II+-III"), 27358.8f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("scissors"), TEXT("Scissors"), TEXT("III"), 28002.6f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("lower_haystack_canyon"), TEXT("Lower Haystack Canyon"), TEXT("II+"), 28324.5f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("bouncing_rock"), TEXT("Bouncing Rock"), TEXT("III"), 29290.1f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("pre_op"), TEXT("Pre-Op"), TEXT("III-"), 29611.9f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("hospital_bar"), TEXT("Hospital Bar"), TEXT("III"), 29933.8f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("recovery_room"), TEXT("Recovery Room"), TEXT("II-III"), 30255.7f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("surprise"), TEXT("Surprise"), TEXT("II-III"), 31060.3f, false},
    {TEXT("L_SouthForkAmerican_FullReach"), TEXT("salmon_falls"), TEXT("Salmon Falls"), TEXT("II+"), 32186.9f, false},
    // L_Hance
    {TEXT("L_Hance"), TEXT("hance_main"), TEXT("Hance Rapid"), TEXT("IV-V"), 680.0f, false},
    {TEXT("L_Hance"), TEXT("son_of_hance"), TEXT("Son of Hance"), TEXT("III"), 1260.0f, false},
    // L_UpperHuacas
    {TEXT("L_UpperHuacas"), TEXT("double_drop"), TEXT("Double Drop"), TEXT("III"), 30.0f, false},
    {TEXT("L_UpperHuacas"), TEXT("upper_huacas"), TEXT("Upper Huacas"), TEXT("IV"), 550.0f, false},
    {TEXT("L_UpperHuacas"), TEXT("lower_huacas"), TEXT("Lower Huacas"), TEXT("IV"), 880.0f, false},
    {TEXT("L_UpperHuacas"), TEXT("upper_pinball"), TEXT("Upper Pinball"), TEXT("III"), 1750.0f, false},
    {TEXT("L_UpperHuacas"), TEXT("lower_pinball"), TEXT("Lower Pinball"), TEXT("III"), 1990.0f, false},
    {TEXT("L_UpperHuacas"), TEXT("guatemala"), TEXT("Guatemala"), TEXT("III"), 2280.0f, false},
    // L_Terminator
    {TEXT("L_Terminator"), TEXT("terminator_wave"), TEXT("Terminator Wave"), TEXT("II"), 480.0f, false},
    {TEXT("L_Terminator"), TEXT("terminator_entrance"), TEXT("Terminator Entrance"), TEXT("IV"), 880.0f, false},
    {TEXT("L_Terminator"), TEXT("terminator_core"), TEXT("Terminator"), TEXT("V"), 1000.0f, false},
    {TEXT("L_Terminator"), TEXT("son_of_terminator"), TEXT("Son of Terminator"), TEXT("IV"), 1380.0f, false},
    {TEXT("L_Terminator"), TEXT("khyber_pass"), TEXT("Khyber Pass"), TEXT("IV"), 1680.0f, false},
    {TEXT("L_Terminator"), TEXT("himalayas"), TEXT("Himalayas"), TEXT("IV"), 1820.0f, false},
    // L_Futaleufu_ContinuousContextV1 (Rio Azul confluence to the Pasarela; researched route stations)
    {TEXT("L_Futaleufu_ContinuousContextV1"), TEXT("school_house"), TEXT("School House"), TEXT("II-III"), 5509.9f, false},
    {TEXT("L_Futaleufu_ContinuousContextV1"), TEXT("asleep_at_the_wheel"), TEXT("Asleep at the Wheel"), TEXT("III-IV"), 8312.9f, false},
    {TEXT("L_Futaleufu_ContinuousContextV1"), TEXT("terminator_wave"), TEXT("Terminator Wave"), TEXT("IV"), 11937.5f, false},
    {TEXT("L_Futaleufu_ContinuousContextV1"), TEXT("terminator_entrance"), TEXT("Terminator Entrance"), TEXT("IV"), 12178.7f, false},
    {TEXT("L_Futaleufu_ContinuousContextV1"), TEXT("terminator_core"), TEXT("Terminator"), TEXT("V"), 12472.9f, false},
    {TEXT("L_Futaleufu_ContinuousContextV1"), TEXT("son_of_terminator"), TEXT("Son of Terminator"), TEXT("III-IV"), 12662.1f, false},
    {TEXT("L_Futaleufu_ContinuousContextV1"), TEXT("khyber_pass"), TEXT("Khyber Pass"), TEXT("IV"), 12952.3f, false},
    {TEXT("L_Futaleufu_ContinuousContextV1"), TEXT("himalayas"), TEXT("Himalayas"), TEXT("III-IV"), 13145.4f, false},
    // L_LavaCanyon
    {TEXT("L_LavaCanyon"), TEXT("bidwell"), TEXT("Bidwell Rapid"), TEXT("IV"), 690.0f, false},
    {TEXT("L_LavaCanyon"), TEXT("white_kilometre"), TEXT("White Kilometre"), TEXT("III"), 1530.0f, false},
    {TEXT("L_LavaCanyon"), TEXT("white_mile"), TEXT("White Mile"), TEXT("IV"), 3600.0f, false},
    // L_Zambezi
    {TEXT("L_Zambezi"), TEXT("rapid_1"), TEXT("Against the Wall"), TEXT("IV"), 160.0f, false},
    {TEXT("L_Zambezi"), TEXT("rapid_2"), TEXT("The Bridge"), TEXT("II-III"), 417.9f, false},
    {TEXT("L_Zambezi"), TEXT("rapid_3"), TEXT("Rapid 3"), TEXT("III-IV"), 615.7f, false},
    {TEXT("L_Zambezi"), TEXT("rapid_4"), TEXT("Morning Glory"), TEXT("IV-V"), 1609.1f, false},
    {TEXT("L_Zambezi"), TEXT("rapid_5"), TEXT("Stairway to Heaven"), TEXT("V"), 3136.3f, false},
    {TEXT("L_Zambezi"), TEXT("rapid_6"), TEXT("Devil's Toilet Bowl"), TEXT("III-IV"), 4710.0f, false},
    {TEXT("L_Zambezi"), TEXT("rapid_7"), TEXT("Gulliver's Travels"), TEXT("V"), 6140.0f, false},
    {TEXT("L_Zambezi"), TEXT("rapid_8"), TEXT("Midnight Diner"), TEXT("III-IV"), 7770.0f, false},
    {TEXT("L_Zambezi"), TEXT("rapid_9"), TEXT("Commercial Suicide"), TEXT("V-VI"), 8590.0f, true},
    {TEXT("L_Zambezi"), TEXT("rapid_10"), TEXT("Gnashing Jaws of Death"), TEXT("III-IV"), 9310.0f, false},
    {TEXT("L_Zambezi"), TEXT("rapid_11"), TEXT("Overland Truck Eater"), TEXT("IV-V"), 10560.0f, false},
    {TEXT("L_Zambezi"), TEXT("rapid_12"), TEXT("Three Ugly Sisters"), TEXT("III"), 12040.0f, false},
    {TEXT("L_Zambezi"), TEXT("rapid_13"), TEXT("The Mother"), TEXT("IV"), 12710.0f, false},
    {TEXT("L_Zambezi"), TEXT("rapid_14"), TEXT("Surprise Surprise"), TEXT("III"), 13640.0f, false},
    {TEXT("L_Zambezi"), TEXT("rapid_15"), TEXT("The Washing Machine"), TEXT("IV-V"), 15820.0f, false},
    {TEXT("L_Zambezi"), TEXT("rapid_16"), TEXT("The Terminators"), TEXT("III"), 16120.0f, false},
    {TEXT("L_Zambezi"), TEXT("rapid_17"), TEXT("Double Trouble"), TEXT("IV-V"), 17170.0f, false},
    {TEXT("L_Zambezi"), TEXT("rapid_18"), TEXT("Oblivion"), TEXT("IV-V"), 18370.0f, false},
    {TEXT("L_Zambezi"), TEXT("rapid_19"), TEXT("Rapid 19"), TEXT("II-III"), 22470.0f, false},
    {TEXT("L_Zambezi"), TEXT("rapid_20"), TEXT("Rapid 20"), TEXT("II-III"), 22950.0f, false},
    {TEXT("L_Zambezi"), TEXT("rapid_21"), TEXT("Rapid 21"), TEXT("II-III"), 23960.0f, false},
    {TEXT("L_Zambezi"), TEXT("rapid_22"), TEXT("Morning Shave"), TEXT("II-III"), 24470.0f, false},
    {TEXT("L_Zambezi"), TEXT("rapid_23"), TEXT("Morning Shower"), TEXT("III"), 25250.0f, false},
    {TEXT("L_Zambezi"), TEXT("rapid_24"), TEXT("Rapid 24"), TEXT("II-III"), 27450.0f, false},
    {TEXT("L_Zambezi"), TEXT("rapid_25"), TEXT("Rapid 25"), TEXT("II-III"), 28270.0f, false},
    // L_ZambeziUpperGorge
    {TEXT("L_ZambeziUpperGorge"), TEXT("r1_the_wall"), TEXT("The Wall"), TEXT("IV-V"), 190.0f, false},
    {TEXT("L_ZambeziUpperGorge"), TEXT("r2_the_bridge"), TEXT("The Bridge"), TEXT("III"), 380.0f, false},
    {TEXT("L_ZambeziUpperGorge"), TEXT("r3"), TEXT("Rapid 3"), TEXT("III-IV"), 580.0f, false},
    {TEXT("L_ZambeziUpperGorge"), TEXT("r3_5_pocket"), TEXT("The Pocket"), TEXT("III"), 1180.0f, false},
    {TEXT("L_ZambeziUpperGorge"), TEXT("r4_morning_glory"), TEXT("Morning Glory"), TEXT("IV-V"), 1460.0f, false},
    {TEXT("L_ZambeziUpperGorge"), TEXT("r4b"), TEXT("Rapid 4B"), TEXT("IV"), 1720.0f, false},
    {TEXT("L_ZambeziUpperGorge"), TEXT("r5_stairway_to_heaven"), TEXT("Stairway to Heaven"), TEXT("V"), 2890.0f, false},
    {TEXT("L_ZambeziUpperGorge"), TEXT("r5_5"), TEXT("Rapid 5.5"), TEXT("II-III"), 3120.0f, false},
    // L_Colorado_BadgerCreek (Grand Canyon 5 of 10, about class III)
    {TEXT("L_Colorado_BadgerCreek"), TEXT("badger_creek"), TEXT("Badger Creek"), TEXT("III"), 790.0f, false},
};
}

TConstArrayView<FRaftSimRapidTitle> RaftSimRapidTitles::All()
{
    return MakeArrayView(GRapids);
}

TArray<const FRaftSimRapidTitle*> RaftSimRapidTitles::ForMap(const FString& MapName)
{
    FString Short = FPackageName::GetShortName(MapName);
    // PIE worlds carry a "UEDPIE_<n>_" prefix on the map name.
    if (Short.StartsWith(TEXT("UEDPIE_")))
    {
        int32 Underscore = INDEX_NONE;
        if (Short.RightChop(7).FindChar(TEXT('_'), Underscore)) Short = Short.RightChop(8 + Underscore);
    }
    TArray<const FRaftSimRapidTitle*> Found;
    for (const FRaftSimRapidTitle& Rapid : GRapids)
        if (Short == Rapid.MapName) Found.Add(&Rapid);
    return Found;
}

FText RaftSimRapidTitles::GradeLine(const FRaftSimRapidTitle& Rapid)
{
    if (FCString::Strcmp(Rapid.Grade, TEXT("surf")) == 0)
        return NSLOCTEXT("RaftSim", "RapidSurfWave", "SURF WAVE");
    // Typographic dashes in grade ranges ("IV-V" reads as "IV\u2013V").
    FString Grade(Rapid.Grade);
    Grade.ReplaceInline(TEXT("-"), TEXT("\u2013"));
    // A trailing sign is a minus ("III-"), not a range.
    if (Grade.EndsWith(TEXT("\u2013"))) Grade = Grade.LeftChop(1) + TEXT("\u2212");
    FText Line = FText::Format(NSLOCTEXT("RaftSim", "RapidClass", "CLASS {0}"), FText::FromString(Grade));
    if (Rapid.bPortage)
        Line = FText::Format(NSLOCTEXT("RaftSim", "RapidPortage", "{0}   \u00B7   PORTAGE"), Line);
    return Line;
}
