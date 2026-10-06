#pragma once

#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/TextBlock.h"
#include "Styling/CoreStyle.h"

/**
 * Shared, asset-free presentation for the front end and in-river interfaces:
 * a golden-hour river palette (evergreen ink, river teal, sunrise amber, bone),
 * Roboto's display weights, and rounded game-style surfaces.
 */
namespace RaftSimUITheme
{
inline FLinearColor Ink() { return FLinearColor(0.006f, 0.014f, 0.016f); }
inline FLinearColor Panel() { return FLinearColor(0.012f, 0.026f, 0.028f, 0.80f); }
inline FLinearColor PanelSolid() { return FLinearColor(0.014f, 0.030f, 0.032f, 0.96f); }
inline FLinearColor Paper() { return FLinearColor(0.94f, 0.91f, 0.82f); }
inline FLinearColor Muted() { return FLinearColor(0.52f, 0.64f, 0.62f); }
inline FLinearColor Gold() { return FLinearColor(1.00f, 0.60f, 0.18f); }
inline FLinearColor River() { return FLinearColor(0.16f, 0.74f, 0.68f); }
inline FLinearColor Moss() { return FLinearColor(0.45f, 0.66f, 0.24f); }
inline FLinearColor Danger() { return FLinearColor(1.00f, 0.32f, 0.16f); }

/** Roboto typeface with optional letter spacing (1/1000 em). */
inline FSlateFontInfo Font(FName Typeface, int32 Size, int32 LetterSpacing = 0)
{
    FSlateFontInfo Info = FCoreStyle::GetDefaultFontStyle(Typeface, Size);
    Info.LetterSpacing = LetterSpacing;
    return Info;
}
inline FSlateFontInfo Display(int32 Size) { return Font("Black", Size, 40); }
inline FSlateFontInfo Label(int32 Size) { return Font("BoldCondensed", Size, 160); }
inline FSlateFontInfo Body(int32 Size) { return Font("Regular", Size); }
inline FSlateFontInfo Strong(int32 Size) { return Font("Medium", Size); }

inline void Style(UTextBlock* Widget, const FSlateFontInfo& Info, FLinearColor Color, bool bShadow = false)
{
    Widget->SetFont(Info);
    Widget->SetColorAndOpacity(Color);
    if (bShadow)
    {
        Widget->SetShadowOffset(FVector2D(0.0f, 2.0f));
        Widget->SetShadowColorAndOpacity(FLinearColor(0.0f, 0.0f, 0.0f, 0.65f));
    }
}

inline void Text(UTextBlock* Widget, int32 Size, FLinearColor Color, bool Bold = false)
{
    Widget->SetFont(FCoreStyle::GetDefaultFontStyle(Bold ? "Bold" : "Regular", Size));
    Widget->SetColorAndOpacity(Color);
    Widget->SetAutoWrapText(true);
}

inline FSlateBrush Rounded(FLinearColor Fill, float Radius, FLinearColor Outline = FLinearColor::Transparent,
    float OutlineWidth = 0.0f)
{
    FSlateBrush Brush;
    Brush.DrawAs = ESlateBrushDrawType::RoundedBox;
    Brush.TintColor = Fill;
    Brush.OutlineSettings.CornerRadii = FVector4(Radius, Radius, Radius, Radius);
    Brush.OutlineSettings.RoundingType = ESlateBrushRoundingType::FixedRadius;
    Brush.OutlineSettings.Color = Outline;
    Brush.OutlineSettings.Width = OutlineWidth;
    return Brush;
}

inline FSlateBrush Fill(FLinearColor Color) { return Rounded(Color, 5.0f); }

inline FSlateBrush None()
{
    FSlateBrush Brush;
    Brush.DrawAs = ESlateBrushDrawType::NoDrawType;
    return Brush;
}

inline void Card(UBorder* Widget, FMargin Padding = FMargin(20.0f))
{
    Widget->SetBrush(Rounded(Panel(), 10.0f, FLinearColor(1, 1, 1, 0.06f), 1.0f));
    Widget->SetPadding(Padding);
}

/** Visual states for one focusable surface; focus swaps to Focused. */
struct FButtonLook
{
    FButtonStyle Normal;
    FButtonStyle Focused;
};

inline FButtonStyle MakeStyle(const FSlateBrush& Normal, const FSlateBrush& Hovered,
    const FSlateBrush& Pressed, FMargin Padding)
{
    FButtonStyle Style;
    Style.SetNormal(Normal);
    Style.SetHovered(Hovered);
    Style.SetPressed(Pressed);
    Style.SetDisabled(Rounded(FLinearColor(0.02f, 0.03f, 0.03f, 0.55f), 8.0f));
    Style.SetNormalPadding(Padding);
    Style.SetPressedPadding(Padding);
    return Style;
}

/** Translucent row with an amber frame on hover and focus (settings, actions). */
inline FButtonLook RowLook(float Radius = 8.0f)
{
    const FMargin Padding(14.0f, 9.0f);
    const FSlateBrush Rest = Rounded(FLinearColor(0.016f, 0.036f, 0.038f, 0.86f), Radius,
        FLinearColor(1, 1, 1, 0.07f), 1.0f);
    const FSlateBrush Lit = Rounded(FLinearColor(0.10f, 0.075f, 0.035f, 0.88f), Radius, Gold(), 2.0f);
    FButtonLook Look;
    Look.Normal = MakeStyle(Rest, Lit, Lit, Padding);
    Look.Focused = MakeStyle(Lit, Lit, Lit, Padding);
    return Look;
}

/** Text-only navigation entry: invisible at rest, a warm bar when active. */
inline FButtonLook NavLook()
{
    const FMargin Padding(12.0f, 6.0f);
    const FSlateBrush Lit = Rounded(FLinearColor(1.0f, 0.60f, 0.18f, 0.16f), 6.0f, Gold(), 1.5f);
    FButtonLook Look;
    Look.Normal = MakeStyle(None(), Lit, Lit, Padding);
    Look.Focused = MakeStyle(Lit, Lit, Lit, Padding);
    return Look;
}

/** Picture card: a thin frame that turns into a bright amber border on focus. */
inline FButtonLook CardLook()
{
    const FMargin Padding(3.0f);
    const FSlateBrush Rest = Rounded(FLinearColor(0.0f, 0.0f, 0.0f, 0.55f), 6.0f,
        FLinearColor(1, 1, 1, 0.14f), 1.0f);
    const FSlateBrush Lit = Rounded(Gold(), 6.0f, FLinearColor(1.0f, 0.85f, 0.55f), 2.0f);
    FButtonLook Look;
    Look.Normal = MakeStyle(Rest, Lit, Lit, Padding);
    Look.Focused = MakeStyle(Lit, Lit, Lit, Padding);
    return Look;
}

/** The call to action: solid amber. */
inline FButtonLook PrimaryLook()
{
    const FMargin Padding(22.0f, 12.0f);
    const FSlateBrush Rest = Rounded(FLinearColor(0.85f, 0.46f, 0.10f), 8.0f);
    const FSlateBrush Lit = Rounded(FLinearColor(1.0f, 0.66f, 0.22f), 8.0f, FLinearColor(1.0f, 0.92f, 0.70f), 2.0f);
    FButtonLook Look;
    Look.Normal = MakeStyle(Rest, Lit, Lit, Padding);
    Look.Focused = MakeStyle(Lit, Lit, Lit, Padding);
    return Look;
}

inline void Button(UButton* Widget)
{
    Widget->SetStyle(RowLook().Normal);
}
}
