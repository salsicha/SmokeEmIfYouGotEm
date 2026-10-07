#include "RaftSimCrewRoster.h"

namespace
{
TArray<FText> Lines(std::initializer_list<const TCHAR*> Source)
{
    TArray<FText> Result;
    for (const TCHAR* Line : Source)
    {
        Result.Add(FText::FromString(Line));
    }
    return Result;
}

FRaftSimCrewGarmentLook Garment(
    const TCHAR* Name, FLinearColor Base, float Roughness, float Heather = 0.05f)
{
    FRaftSimCrewGarmentLook Look;
    Look.Name = FText::FromString(Name);
    Look.BaseColor = Base;
    Look.Roughness = Roughness;
    Look.HeatherAmount = Heather;
    return Look;
}

TArray<FRaftSimCrewIdentity> BuildRoster()
{
    TArray<FRaftSimCrewIdentity> Roster;

    // Stern seat. Gear colours are linear albedo, matched to the project's
    // safety-gear palette (dark-tuned for the bright-water exposure).
    {
        FRaftSimCrewIdentity Guide;
        Guide.PassengerId = TEXT("guide");
        Guide.DisplayName = FText::FromString(TEXT("Rhys Calloway"));
        Guide.FirstName = FText::FromString(TEXT("Rhys"));
        Guide.Age = 41;
        Guide.Hometown = FText::FromString(TEXT("Queenstown, New Zealand"));
        Guide.Occupation = FText::FromString(TEXT("Head guide, eighteen seasons on the Zambezi"));
        Guide.Personality = FText::FromString(
            TEXT("Calm and wry. Calls the lines early, never raises his voice, and counts heads after every rapid."));
        Guide.HelmetColor = FLinearColor(0.020f, 0.022f, 0.026f);
        Guide.PfdColor = FLinearColor(0.30f, 0.012f, 0.006f);
        // Sun-faded guide kit: a long-sleeved UPF shirt and quick-dry shorts.
        Guide.Top = Garment(TEXT("long-sleeved sun shirt"), FLinearColor(0.20f, 0.26f, 0.31f), 0.80f, 0.06f);
        Guide.Bottom = Garment(TEXT("quick-dry shorts"), FLinearColor(0.085f, 0.085f, 0.050f), 0.70f, 0.02f);
        Guide.WetsuitTint = FLinearColor(0.014f, 0.016f, 0.018f);
        Guide.JacketColor = FLinearColor(0.020f, 0.060f, 0.100f);
        Guide.bWearsSunglasses = true;
        Guide.EyewearFrameColor = FLinearColor(0.010f, 0.010f, 0.012f);
        Guide.LensColor = FLinearColor(0.012f, 0.030f, 0.070f);
        Guide.bRescueKit = true;
        Guide.Nerves = 0.05f;
        Guide.SwimAbility = ERaftSimCrewSwimAbility::Strong;
        // Reads the water: long scans across the river, back to the line.
        Guide.GazeRangeDeg = 26.0f;
        Guide.GazeHoldSeconds = 2.6f;
        Guide.GazeDownDeg = 2.0f;
        Guide.BigWaterLines = Lines({TEXT("Here we go. Dig in when I call it."), TEXT("Eyes on me, paddles ready."),
            TEXT("Big one coming. Lean in and keep paddling.")});
        Guide.CleanRunLines = Lines({TEXT("Nice work, team. Paddles up!"), TEXT("That's how it's done."),
            TEXT("Textbook. Everyone breathe.")});
        Guide.OverboardLines = Lines({TEXT("I'm fine! Keep the boat straight!")});
        Guide.RescuedLines = Lines({TEXT("Right. Where were we?")});
        Guide.FlipLines = Lines({TEXT("Flip! Grab the boat and stay upstream of it!"), TEXT("Everyone okay? Sound off!")});
        Roster.Add(Guide);
    }
    // paddler_1: front left, the Crew01 body.
    {
        FRaftSimCrewIdentity Kwame;
        Kwame.PassengerId = TEXT("paddler_1");
        Kwame.DisplayName = FText::FromString(TEXT("Kwame Asante"));
        Kwame.FirstName = FText::FromString(TEXT("Kwame"));
        Kwame.Age = 29;
        Kwame.Hometown = FText::FromString(TEXT("Accra, Ghana (lives in London)"));
        Kwame.Occupation = FText::FromString(TEXT("Software engineer"));
        Kwame.Personality = FText::FromString(
            TEXT("Loud, generous and a little overconfident. Claimed the front seat and paddles like he means it."));
        Kwame.HelmetColor = FLinearColor(0.32f, 0.015f, 0.008f);
        Kwame.PfdColor = FLinearColor(0.42f, 0.060f, 0.004f);
        // A loose white T-shirt and loud tropical board shorts.
        Kwame.Top = Garment(TEXT("loose white T-shirt"), FLinearColor(0.60f, 0.60f, 0.58f), 0.88f, 0.03f);
        Kwame.Bottom = Garment(TEXT("tropical board shorts"), FLinearColor(0.010f, 0.090f, 0.20f), 0.55f, 0.0f);
        Kwame.Bottom.AccentColor = FLinearColor(0.55f, 0.36f, 0.030f);
        Kwame.Bottom.PrintAmount = 1.0f;
        Kwame.Bottom.PrintScaleCm = 18.0f;
        // Everyone on the water wears sunglasses (2026-10-07): Kwame's are
        // matte black wraparounds with smoke lenses.
        Kwame.bWearsSunglasses = true;
        Kwame.EyewearFrameColor = FLinearColor(0.012f, 0.012f, 0.014f);
        Kwame.LensColor = FLinearColor(0.020f, 0.022f, 0.024f);
        Kwame.WetsuitTint = FLinearColor(0.010f, 0.011f, 0.012f);
        Kwame.JacketColor = FLinearColor(0.10f, 0.20f, 0.010f);
        Kwame.Nerves = 0.12f;
        Kwame.SwimAbility = ERaftSimCrewSwimAbility::Strong;
        // Looks everywhere: the walls, the crew, back at the guide.
        Kwame.GazeRangeDeg = 32.0f;
        Kwame.GazeHoldSeconds = 1.8f;
        Kwame.GazeDownDeg = 0.0f;
        Kwame.BigWaterLines = Lines({TEXT("Let's goooo! Front row!"), TEXT("Is that all you've got, Zambezi?"),
            TEXT("Dig! Dig! Dig!")});
        Kwame.CleanRunLines = Lines({TEXT("That's what I'm talking about!"), TEXT("Again! Run it again!"),
            TEXT("Front row for life.")});
        Kwame.OverboardLines = Lines({TEXT("Okay, okay, I'm swimming! Water's warm at least!"),
            TEXT("Feet up! I know, I know!")});
        Kwame.RescuedLines = Lines({TEXT("Thanks, man. Let's not do that again."), TEXT("I meant to do that.")});
        Kwame.FlipLines = Lines({TEXT("Whoa! Everyone grab a line!")});
        Roster.Add(Kwame);
    }
    // paddler_2: front right, the Crew02 body.
    {
        FRaftSimCrewIdentity Kenji;
        Kenji.PassengerId = TEXT("paddler_2");
        Kenji.DisplayName = FText::FromString(TEXT("Kenji Watanabe"));
        Kenji.FirstName = FText::FromString(TEXT("Kenji"));
        Kenji.Age = 52;
        Kenji.Hometown = FText::FromString(TEXT("Osaka, Japan"));
        Kenji.Occupation = FText::FromString(TEXT("Retired railway engineer"));
        Kenji.Personality = FText::FromString(
            TEXT("Methodical and quietly funny. Third trip down the gorge; keeps perfect time and reads the river."));
        Kenji.HelmetColor = FLinearColor(0.42f, 0.46f, 0.50f);
        Kenji.PfdColor = FLinearColor(0.006f, 0.030f, 0.140f);
        // A navy-and-cream striped T-shirt and stone walking shorts.
        Kenji.Top = Garment(TEXT("striped T-shirt"), FLinearColor(0.52f, 0.50f, 0.44f), 0.86f, 0.02f);
        Kenji.Top.AccentColor = FLinearColor(0.010f, 0.016f, 0.055f);
        Kenji.Top.StripeAmount = 1.0f;
        Kenji.Top.StripePeriodCm = 2.4f;
        Kenji.Bottom = Garment(TEXT("stone walking shorts"), FLinearColor(0.22f, 0.20f, 0.16f), 0.80f, 0.03f);
        Kenji.WetsuitTint = FLinearColor(0.008f, 0.012f, 0.022f);
        Kenji.JacketColor = FLinearColor(0.060f, 0.064f, 0.070f);
        // Prescription sunglasses: the thin titanium frame with grey-green
        // tinted lenses.
        Kenji.bWearsSunglasses = true;
        Kenji.EyewearFrameColor = FLinearColor(0.25f, 0.25f, 0.27f);
        Kenji.LensColor = FLinearColor(0.030f, 0.040f, 0.030f);
        Kenji.Nerves = 0.35f;
        Kenji.SwimAbility = ERaftSimCrewSwimAbility::Average;
        // Steady eyes front; the occasional look at the gorge walls.
        Kenji.GazeRangeDeg = 10.0f;
        Kenji.GazeHoldSeconds = 5.5f;
        Kenji.GazeDownDeg = 3.0f;
        Kenji.BigWaterLines = Lines({TEXT("Paddles ready. Timing, everyone."), TEXT("Steady... steady..."),
            TEXT("Ah. That is a large wave.")});
        Kenji.CleanRunLines = Lines({TEXT("Very clean. Well done, everyone."),
            TEXT("Good timing. Like a train schedule.")});
        Kenji.OverboardLines = Lines({TEXT("Feet downstream... feet up... I remember."), TEXT("I am... swimming now.")});
        Kenji.RescuedLines = Lines({TEXT("Thank you. Arigatou."), TEXT("My glasses are still on. Excellent.")});
        Kenji.FlipLines = Lines({TEXT("Upside down. Interesting.")});
        Roster.Add(Kenji);
    }
    // paddler_3: second row left, the Crew03 body.
    {
        FRaftSimCrewIdentity Ingrid;
        Ingrid.PassengerId = TEXT("paddler_3");
        Ingrid.DisplayName = FText::FromString(TEXT("Ingrid Solberg"));
        Ingrid.FirstName = FText::FromString(TEXT("Ingrid"));
        Ingrid.Age = 34;
        Ingrid.Hometown = FText::FromString(TEXT("Bergen, Norway"));
        Ingrid.Occupation = FText::FromString(TEXT("Ski patroller"));
        Ingrid.Personality = FText::FromString(
            TEXT("Competitive adrenaline seeker. Always asks for the biggest line and laughs when she swims."));
        Ingrid.HelmetColor = FLinearColor(0.55f, 0.25f, 0.006f);
        Ingrid.PfdColor = FLinearColor(0.32f, 0.008f, 0.003f);
        // Training kit: a coral sleeveless top and black three-quarter leggings.
        Ingrid.Top = Garment(TEXT("coral sleeveless top"), FLinearColor(0.55f, 0.11f, 0.065f), 0.55f, 0.0f);
        Ingrid.Bottom = Garment(TEXT("black three-quarter leggings"), FLinearColor(0.012f, 0.012f, 0.014f), 0.48f, 0.0f);
        Ingrid.WetsuitTint = FLinearColor(0.008f, 0.016f, 0.016f);
        Ingrid.JacketColor = FLinearColor(0.14f, 0.020f, 0.12f);
        Ingrid.bWearsSunglasses = true;
        Ingrid.EyewearFrameColor = FLinearColor(0.60f, 0.60f, 0.62f);
        Ingrid.LensColor = FLinearColor(0.10f, 0.045f, 0.010f);
        Ingrid.Nerves = 0.04f;
        Ingrid.SwimAbility = ERaftSimCrewSwimAbility::Strong;
        // Hunts the next feature downstream.
        Ingrid.GazeRangeDeg = 22.0f;
        Ingrid.GazeHoldSeconds = 3.0f;
        Ingrid.GazeDownDeg = 1.0f;
        Ingrid.BigWaterLines = Lines({TEXT("Take the big line, Rhys!"), TEXT("Yes! Straight through the middle!"),
            TEXT("Hit it! Hit it!")});
        Ingrid.CleanRunLines = Lines({TEXT("Can we go back up and do that again?"), TEXT("That's the best one yet!")});
        Ingrid.OverboardLines = Lines({TEXT("Ha! Over here! I'm fine!"), TEXT("Best swim of my life!")});
        Ingrid.RescuedLines = Lines({TEXT("Thanks. That was brilliant."), TEXT("Next time I'm staying in. Maybe.")});
        Ingrid.FlipLines = Lines({TEXT("We flipped! Everyone okay?")});
        Roster.Add(Ingrid);
    }
    // paddler_4: second row right, the Crew04 body.
    {
        FRaftSimCrewIdentity Amara;
        Amara.PassengerId = TEXT("paddler_4");
        Amara.DisplayName = FText::FromString(TEXT("Amara Okafor"));
        Amara.FirstName = FText::FromString(TEXT("Amara"));
        Amara.Age = 23;
        Amara.Hometown = FText::FromString(TEXT("Manchester, England (born in Lagos)"));
        Amara.Occupation = FText::FromString(TEXT("Medical student"));
        Amara.Personality = FText::FromString(
            TEXT("First time on a river. Terrified at the top of every rapid and thrilled at the bottom."));
        Amara.HelmetColor = FLinearColor(0.010f, 0.18f, 0.16f);
        Amara.PfdColor = FLinearColor(0.42f, 0.20f, 0.004f);
        // An oversized lavender T-shirt and charcoal running shorts.
        Amara.Top = Garment(TEXT("oversized lavender T-shirt"), FLinearColor(0.28f, 0.20f, 0.46f), 0.88f, 0.08f);
        Amara.Bottom = Garment(TEXT("charcoal running shorts"), FLinearColor(0.035f, 0.035f, 0.040f), 0.60f, 0.0f);
        Amara.WetsuitTint = FLinearColor(0.011f, 0.010f, 0.012f);
        // Tortoiseshell-brown sport frame with brown lenses.
        Amara.bWearsSunglasses = true;
        Amara.EyewearFrameColor = FLinearColor(0.085f, 0.035f, 0.012f);
        Amara.LensColor = FLinearColor(0.060f, 0.030f, 0.012f);
        Amara.JacketColor = FLinearColor(0.30f, 0.020f, 0.060f);
        Amara.Nerves = 0.80f;
        Amara.SwimAbility = ERaftSimCrewSwimAbility::Weak;
        // Eyes glued to the water ahead; quick nervous glances.
        Amara.GazeRangeDeg = 14.0f;
        Amara.GazeHoldSeconds = 1.4f;
        Amara.GazeDownDeg = 7.0f;
        Amara.BigWaterLines = Lines({TEXT("Oh no, oh no, that's huge..."), TEXT("Is it supposed to be that big?!"),
            TEXT("Okay. Okay. Paddling. I'm paddling!")});
        Amara.CleanRunLines = Lines({TEXT("I can't believe we did that!"), TEXT("I was screaming, wasn't I? Again!"),
            TEXT("My hands are shaking. That was amazing.")});
        Amara.OverboardLines = Lines({TEXT("Help! Help me!"), TEXT("Rope! Throw me the rope!")});
        Amara.RescuedLines = Lines({TEXT("Never letting go of this rope again."), TEXT("Thank you, thank you, thank you.")});
        Amara.FlipLines = Lines({TEXT("We flipped?! Where's the boat?!")});
        Roster.Add(Amara);
    }
    return Roster;
}
}

const TArray<FRaftSimCrewIdentity>& URaftSimCrewRoster::GetRoster()
{
    static const TArray<FRaftSimCrewIdentity> Roster = BuildRoster();
    return Roster;
}

const FRaftSimCrewIdentity& URaftSimCrewRoster::GetIdentity(FName PassengerId)
{
    const TArray<FRaftSimCrewIdentity>& Roster = GetRoster();
    for (const FRaftSimCrewIdentity& Identity : Roster)
    {
        if (Identity.PassengerId == PassengerId)
        {
            return Identity;
        }
    }
    return Roster[0];
}

const FRaftSimCrewIdentity& URaftSimCrewRoster::GetIdentityForVariant(int32 VariantIndex, bool bGuide)
{
    const TArray<FRaftSimCrewIdentity>& Roster = GetRoster();
    return bGuide ? Roster[0] : Roster[1 + FMath::Abs(VariantIndex) % 4];
}

FText URaftSimCrewRoster::GetDisplayName(FName PassengerId)
{
    return GetIdentity(PassengerId).DisplayName;
}

FText URaftSimCrewRoster::GetFirstName(FName PassengerId)
{
    return GetIdentity(PassengerId).FirstName;
}
