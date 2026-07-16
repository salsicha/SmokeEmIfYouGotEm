#include "RaftSimEditorModule.h"
#include "Foliage/RaftSimEditorFoliageInternal.h"
#include "Foliage/RaftSimEditorPveAuthoringInternal.h"

#include "Algo/AllOf.h"
#include "Algo/AnyOf.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetCompilingManager.h"
#include "Animation/SkeletalMeshActor.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/DynamicMeshComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/LightComponent.h"
#include "Components/MeshComponent.h"
#include "Components/ReflectionCaptureComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/SphereReflectionCaptureComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkyAtmosphereComponent.h"
#include "Dom/JsonObject.h"
#include "UDynamicMesh.h"
#include "Editor.h"
#include "Engine/DirectionalLight.h"
#include "Engine/Engine.h"
#include "Engine/ExponentialHeightFog.h"
#include "Engine/PointLight.h"
#include "Engine/SceneCapture2D.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/SkyLight.h"
#include "Engine/SphereReflectionCapture.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/Texture2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "EngineUtils.h"
#include "FileHelpers.h"
#include "Framework/Application/SlateApplication.h"
#include "Framework/Commands/UIAction.h"
#include "Framework/Docking/TabManager.h"
#include "GameFramework/Actor.h"
#include "GameFramework/PlayerStart.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformProcess.h"
#include "HAL/PlatformMisc.h"
#include "ImageUtils.h"
#include "IImageWrapper.h"
#include "IImageWrapperModule.h"
#include "Landscape.h"
#include "LandscapeComponent.h"
#include "LandscapeEditorModule.h"
#include "LandscapeFileFormatInterface.h"
#include "LandscapeNaniteComponent.h"
#include "LandscapeProxy.h"
#include "GeometryScript/MeshAssetFunctions.h"
#include "GeometryScript/MeshBasicEditFunctions.h"
#include "GeometryScript/MeshMaterialFunctions.h"
#include "Materials/MaterialExpressionLandscapeLayerCoords.h"
#include "Materials/Material.h"
#include "Materials/MaterialExpressionAbs.h"
#include "Materials/MaterialExpressionAdd.h"
#include "Materials/MaterialExpressionComponentMask.h"
#include "Materials/MaterialExpressionConstant.h"
#include "Materials/MaterialExpressionConstant2Vector.h"
#include "Materials/MaterialExpressionConstant3Vector.h"
#include "Materials/MaterialExpressionCameraPositionWS.h"
#include "Materials/MaterialExpressionCustom.h"
#include "Materials/MaterialExpressionFrac.h"
#include "Materials/MaterialExpressionFresnel.h"
#include "Materials/MaterialExpressionLinearInterpolate.h"
#include "Materials/MaterialExpressionMaterialFunctionCall.h"
#include "Materials/MaterialExpressionMultiply.h"
#include "Materials/MaterialExpressionOneMinus.h"
#include "Materials/MaterialExpressionObjectPositionWS.h"
#include "Materials/MaterialExpressionSaturate.h"
#include "Materials/MaterialExpressionScalarParameter.h"
#include "Materials/MaterialExpressionSubtract.h"
#include "Materials/MaterialExpressionTextureCoordinate.h"
#include "Materials/MaterialExpressionTextureObjectParameter.h"
#include "Materials/MaterialExpressionTextureSampleParameter2D.h"
#include "Materials/MaterialExpressionTwoSidedSign.h"
#include "Materials/MaterialExpressionVertexColor.h"
#include "Materials/MaterialExpressionVertexNormalWS.h"
#include "Materials/MaterialExpressionVectorParameter.h"
#include "Materials/MaterialExpressionWorldPosition.h"
#include "Materials/MaterialInstanceConstant.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialFunctionInterface.h"
#include "MaterialShared.h"
#include "MeshUtilities.h"
#include "MeshDescription.h"
#include "Misc/CommandLine.h"
#include "Misc/CoreDelegates.h"
#include "Misc/FileHelper.h"
#include "Misc/PackageName.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "Misc/SecureHash.h"
#include "Modules/ModuleManager.h"
#include "NaniteSceneProxy.h"
#include "PlanarCut.h"
#include "PCGGraph.h"
#include "PCGDefaultExecutionSource.h"
#include "PCGData.h"
#include "PCGEdge.h"
#include "PCGNode.h"
#include "PCGPin.h"
#include "PCGSettings.h"
#include "ProceduralMeshComponent.h"
#include "ProceduralMeshConversion.h"
#include "ProceduralVegetation.h"
#include "DataTypes/PVFoliageInfo.h"
#include "DataTypes/PVMeshData.h"
#include "Facades/PVFoliageFacade.h"
#include "GeometryCollection/GeometryCollection.h"
#include "Utils/PVFloatRamp.h"
#include "RaftSimEditorToolRegistry.h"
#include "RaftSimFeatureTuningEditorShell.h"
#include "RaftSimRapidRiverEditorShell.h"
#include "RaftSimReplayDebugViewer.h"
#include "RaftSimToolValidationActions.h"
#include "Styling/CoreStyle.h"
#include "Subsystems/IPCGBaseSubsystem.h"
#include "ToolMenus.h"
#include "TextureCompiler.h"
#include "UObject/SavePackage.h"
#include "UObject/UnrealType.h"
#include "RenderingThread.h"
#include "RenderTimer.h"
#include "DynamicRHI.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "ShaderCompiler.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Docking/SDockTab.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SCheckBox.h"
#include "Widgets/Input/SComboBox.h"
#include "Widgets/Input/SSearchBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Layout/SSeparator.h"
#include "Widgets/Layout/SUniformGridPanel.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Views/SListView.h"
#include "Widgets/SWindow.h"

#define LOCTEXT_NAMESPACE "FRaftSimEditorModule"

DEFINE_LOG_CATEGORY_STATIC(LogRaftSimEditorPveAuthoring, Log, All);
#define LogRaftSimEditor LogRaftSimEditorPveAuthoring

using RaftSimEditorFoliage::AppendNativeCanopyAtlasCurvedCard;
using RaftSimEditorFoliage::AppendNativeCanopyLeafCard;
using RaftSimEditorFoliage::AppendNativeCanopyTaperedSegment;
using RaftSimEditorFoliage::AddComplementaryScreenDitherOpacity;
using RaftSimEditorFoliage::AddPreviewProceduralMeshActor;
using RaftSimEditorFoliage::AddPreviewTwoSectionProceduralMeshActor;
using RaftSimEditorFoliage::ComputePreviewMeshNormals;
using RaftSimEditorFoliage::ConfigureFutaleufuComplementaryTransitionCapture;
using RaftSimEditorFoliage::ConnectPreviewMaterialColorInput;
using RaftSimEditorFoliage::ConnectPreviewMaterialScalarInput;
using RaftSimEditorFoliage::ConnectPreviewMaterialVectorInput;
using RaftSimEditorFoliage::ConvertNativeCanopyProceduralActorToStaticMesh;
using RaftSimEditorFoliage::CreateFutaleufuCordilleraCypressTextureAssets;
using RaftSimEditorFoliage::CreateOrUpdateFutaleufuCypressFarProxyMaterial;
using RaftSimEditorFoliage::CreateOrUpdateFutaleufuNativeCanopyMaterial;
using RaftSimEditorFoliage::EscapeRaftSimJsonString;
using RaftSimEditorFoliage::FRaftSimEnvironmentPreviewSpec;
using RaftSimEditorFoliage::FRaftSimPhotographicCaptureSettings;
using RaftSimEditorFoliage::FindPreviewCaptureCamera;
using RaftSimEditorFoliage::GetPhotographicCaptureSettings;
using RaftSimEditorFoliage::GetRepoRoot;
using RaftSimEditorFoliage::LoadPreviewMesh;
using RaftSimEditorFoliage::SavePreviewWorld;
using RaftSimEditorFoliage::ScalePreviewColor;


namespace RaftSimEditorPve
{
const TArray<FFutaleufuCypressPveFormSpec>& GetFutaleufuCypressPveFormSpecs()
{
    static const TArray<FFutaleufuCypressPveFormSpec> Specs = {
        {TEXT("open_grown_conical"), TEXT("open-grown conical adult"),
         TEXT("OpenGrownConicalAdult"), TEXT("adult"), 18427, 1.13f, 0.82f,
         0.86f, 18.0f, 1.65f, 1.35f, 36, 0.04f, false, 0.5f, 4.0f, 0.20f, 0.68f},
        {TEXT("closed_grove_columnar"), TEXT("closed-grove columnar adult"),
         TEXT("ClosedGroveColumnarAdult"), TEXT("adult"), 22409, 1.18f, 0.74f,
         0.65f, 32.0f, 1.35f, 1.15f, 34, 0.10f, false, 0.4f, 2.0f, 0.14f, 0.76f},
        {TEXT("rocky_slope_asymmetric"), TEXT("rocky-slope asymmetric adult"),
         TEXT("RockySlopeAsymmetricAdult"), TEXT("adult"), 30881, 1.04f, 0.79f,
         0.82f, 12.0f, 1.45f, 1.20f, 30, 0.08f, false, 2.0f, 14.0f, 0.30f, 0.54f},
        {TEXT("storm_damaged"), TEXT("storm-damaged adult"),
         TEXT("StormDamagedAdult"), TEXT("adult"), 41719, 1.09f, 0.67f,
         0.78f, 8.0f, 1.10f, 0.90f, 24, 0.16f, true, 4.0f, 18.0f, 0.42f, 0.36f},
        {TEXT("coigue_transition_edge"), TEXT("coigue-transition edge adult"),
         TEXT("CoigueTransitionEdgeAdult"), TEXT("adult"), 52967, 1.00f, 0.76f,
         0.90f, 20.0f, 1.55f, 1.30f, 36, 0.04f, false, 1.2f, 7.0f, 0.22f, 0.64f},
        {TEXT("grove_intermediate"), TEXT("grove intermediate"),
         TEXT("GroveIntermediate"), TEXT("intermediate"), 64109, 0.60f, 0.68f,
         0.76f, 24.0f, 1.40f, 1.20f, 28, 0.06f, false, 0.7f, 5.0f, 0.18f, 0.70f},
        {TEXT("suppressed_intermediate"), TEXT("suppressed intermediate"),
         TEXT("SuppressedIntermediate"), TEXT("intermediate"), 75211, 0.40f, 0.61f,
         0.58f, 32.0f, 0.95f, 0.80f, 18, 0.18f, true, 0.8f, 4.0f, 0.16f, 0.72f},
        {TEXT("released_intermediate"), TEXT("released intermediate"),
         TEXT("ReleasedIntermediate"), TEXT("intermediate"), 86369, 0.70f, 0.72f,
         0.82f, 18.0f, 1.70f, 1.40f, 34, 0.03f, false, 1.8f, 9.0f, 0.24f, 0.60f}};
    return Specs;
}

const FFutaleufuCypressPveFormSpec* FindFutaleufuCypressPveFormSpec(const FString& Id)
{
    return GetFutaleufuCypressPveFormSpecs().FindByPredicate(
        [&Id](const FFutaleufuCypressPveFormSpec& Spec) { return Spec.Id == Id; });
}

bool SetPveFoliagePaletteMeshes(
    UPCGSettings* Settings,
    const TArray<FString>& MeshObjectPaths)
{
    FArrayProperty* PaletteProperty = Settings
        ? FindFProperty<FArrayProperty>(Settings->GetClass(), TEXT("FoliageInfos"))
        : nullptr;
    FStructProperty* InfoProperty = PaletteProperty
        ? CastField<FStructProperty>(PaletteProperty->Inner)
        : nullptr;
    if (!PaletteProperty || !InfoProperty ||
        InfoProperty->Struct != FPVFoliageInfo::StaticStruct())
    {
        return false;
    }

    FScriptArrayHelper Palette(
        PaletteProperty,
        PaletteProperty->ContainerPtrToValuePtr<void>(Settings));
    Palette.Resize(MeshObjectPaths.Num());
    for (int32 Index = 0; Index < MeshObjectPaths.Num(); ++Index)
    {
        FPVFoliageInfo* Info = reinterpret_cast<FPVFoliageInfo*>(Palette.GetRawPtr(Index));
        *Info = FPVFoliageInfo();
        Info->Mesh = TSoftObjectPtr<UObject>(FSoftObjectPath(MeshObjectPaths[Index]));
        Info->Attributes.Scale = MeshObjectPaths.Num() > 1
            ? static_cast<float>(Index) / static_cast<float>(MeshObjectPaths.Num() - 1)
            : 0.5f;
        Info->Attributes.Light = 0.42f + static_cast<float>(Index) * 0.16f;
        Info->Attributes.Health = 0.82f;
    }
    Settings->Modify();
    return true;
}

bool SetPveGraftPaletteEntryCount(UPCGSettings* Settings, int32 EntryCount)
{
    FArrayProperty* PaletteProperty = Settings
        ? FindFProperty<FArrayProperty>(Settings->GetClass(), TEXT("GraftInfos"))
        : nullptr;
    FStructProperty* InfoProperty = PaletteProperty
        ? CastField<FStructProperty>(PaletteProperty->Inner)
        : nullptr;
    if (!PaletteProperty || !InfoProperty ||
        InfoProperty->Struct->GetName() != TEXT("PVGraftInfo") || EntryCount < 1)
    {
        return false;
    }

    FScriptArrayHelper Palette(
        PaletteProperty,
        PaletteProperty->ContainerPtrToValuePtr<void>(Settings));
    Palette.Resize(EntryCount);
    Settings->Modify();
    return Palette.Num() == EntryCount;
}

bool SetPveNestedFloat(
    UObject* Object,
    const TCHAR* RootStructName,
    const TCHAR* NestedStructName,
    const TCHAR* ValueName,
    float Value)
{
    FStructProperty* RootProperty = Object
        ? FindFProperty<FStructProperty>(Object->GetClass(), RootStructName)
        : nullptr;
    void* RootValue = RootProperty
        ? RootProperty->ContainerPtrToValuePtr<void>(Object)
        : nullptr;
    FStructProperty* NestedProperty = RootProperty
        ? FindFProperty<FStructProperty>(RootProperty->Struct, NestedStructName)
        : nullptr;
    void* NestedValue = NestedProperty
        ? NestedProperty->ContainerPtrToValuePtr<void>(RootValue)
        : nullptr;
    FFloatProperty* FloatProperty = NestedProperty
        ? FindFProperty<FFloatProperty>(NestedProperty->Struct, ValueName)
        : nullptr;
    if (FloatProperty && NestedValue)
    {
        FloatProperty->SetPropertyValue_InContainer(NestedValue, Value);
        Object->Modify();
        return true;
    }

    if (!RootProperty)
    {
        UE_LOG(
            LogRaftSimEditor,
            Warning,
            TEXT("PVE override could not find root struct %s on %s."),
            RootStructName,
            Object ? *Object->GetClass()->GetName() : TEXT("None"));
        return false;
    }
    FString RootText;
    if (!RootProperty->ExportText_InContainer(
            0, RootText, Object, Object, Object, PPF_Copy))
    {
        return false;
    }
    const FString FieldPrefix = FString::Printf(TEXT("%s="), ValueName);
    const int32 FieldStart = RootText.Find(FieldPrefix, ESearchCase::CaseSensitive);
    const int32 ValueStart = FieldStart == INDEX_NONE
        ? INDEX_NONE
        : FieldStart + FieldPrefix.Len();
    const int32 ValueEnd = ValueStart == INDEX_NONE
        ? INDEX_NONE
        : RootText.Find(TEXT(","), ESearchCase::CaseSensitive, ESearchDir::FromStart, ValueStart);
    if (ValueStart == INDEX_NONE || ValueEnd == INDEX_NONE)
    {
        UE_LOG(
            LogRaftSimEditor,
            Warning,
            TEXT("PVE override could not find %s in %s text: %s"),
            ValueName,
            RootStructName,
            *RootText.Left(500));
        return false;
    }
    RootText = RootText.Left(ValueStart) + FString::Printf(TEXT("%.6f"), Value) +
        RootText.Mid(ValueEnd);
    if (!RootProperty->ImportText_InContainer(*RootText, Object, Object, PPF_Copy))
    {
        return false;
    }
    Object->Modify();
    return true;
}

bool SetPveNestedInt(
    UObject* Object,
    const TCHAR* RootStructName,
    const TCHAR* NestedStructName,
    const TCHAR* ValueName,
    int64 Value)
{
    FStructProperty* RootProperty = Object
        ? FindFProperty<FStructProperty>(Object->GetClass(), RootStructName)
        : nullptr;
    void* RootValue = RootProperty
        ? RootProperty->ContainerPtrToValuePtr<void>(Object)
        : nullptr;
    FStructProperty* NestedProperty = RootProperty
        ? FindFProperty<FStructProperty>(RootProperty->Struct, NestedStructName)
        : nullptr;
    void* NestedValue = NestedProperty
        ? NestedProperty->ContainerPtrToValuePtr<void>(RootValue)
        : nullptr;
    FNumericProperty* NumericProperty = NestedProperty
        ? FindFProperty<FNumericProperty>(NestedProperty->Struct, ValueName)
        : nullptr;
    if (!NumericProperty || !NestedValue || !NumericProperty->IsInteger())
    {
        UE_LOG(
            LogRaftSimEditor,
            Warning,
            TEXT("PVE override could not find integer %s.%s.%s on %s."),
            RootStructName,
            NestedStructName,
            ValueName,
            Object ? *Object->GetClass()->GetName() : TEXT("None"));
        return false;
    }
    NumericProperty->SetIntPropertyValue(
        NumericProperty->ContainerPtrToValuePtr<void>(NestedValue),
        static_cast<uint64>(Value));
    Object->Modify();
    return true;
}

bool SetPvePropertyText(
    UObject* Object,
    const TCHAR* ValueName,
    const FString& ValueText)
{
    FProperty* Property = Object
        ? FindFProperty<FProperty>(Object->GetClass(), ValueName)
        : nullptr;
    void* Value = Property
        ? Property->ContainerPtrToValuePtr<void>(Object)
        : nullptr;
    if (!Property || !Value ||
        !Property->ImportText_Direct(*ValueText, Value, Object, PPF_Copy))
    {
        UE_LOG(
            LogRaftSimEditor,
            Warning,
            TEXT("PVE override could not import %s=%s on %s."),
            ValueName,
            *ValueText,
            Object ? *Object->GetClass()->GetName() : TEXT("None"));
        return false;
    }
    Object->Modify();
    return true;
}

bool SetPveNestedText(
    UObject* Object,
    const TCHAR* RootStructName,
    const TCHAR* NestedStructName,
    const TCHAR* ValueName,
    const FString& ValueText)
{
    FStructProperty* RootProperty = Object
        ? FindFProperty<FStructProperty>(Object->GetClass(), RootStructName)
        : nullptr;
    void* RootValue = RootProperty
        ? RootProperty->ContainerPtrToValuePtr<void>(Object)
        : nullptr;
    FStructProperty* NestedProperty = RootProperty
        ? FindFProperty<FStructProperty>(RootProperty->Struct, NestedStructName)
        : nullptr;
    void* NestedValue = NestedProperty
        ? NestedProperty->ContainerPtrToValuePtr<void>(RootValue)
        : nullptr;
    FProperty* ValueProperty = NestedProperty
        ? FindFProperty<FProperty>(NestedProperty->Struct, ValueName)
        : nullptr;
    void* Value = ValueProperty && NestedValue
        ? ValueProperty->ContainerPtrToValuePtr<void>(NestedValue)
        : nullptr;
    if (!ValueProperty || !Value ||
        !ValueProperty->ImportText_Direct(*ValueText, Value, Object, PPF_Copy))
    {
        UE_LOG(
            LogRaftSimEditor,
            Warning,
            TEXT("PVE override could not import %s.%s.%s=%s on %s."),
            RootStructName,
            NestedStructName,
            ValueName,
            *ValueText,
            Object ? *Object->GetClass()->GetName() : TEXT("None"));
        return false;
    }
    Object->Modify();
    return true;
}

bool SetPveStructText(
    UObject* Object,
    const TCHAR* RootStructName,
    const TCHAR* ValueName,
    const FString& ValueText)
{
    FStructProperty* RootProperty = Object
        ? FindFProperty<FStructProperty>(Object->GetClass(), RootStructName)
        : nullptr;
    void* RootValue = RootProperty
        ? RootProperty->ContainerPtrToValuePtr<void>(Object)
        : nullptr;
    FProperty* ValueProperty = RootProperty
        ? FindFProperty<FProperty>(RootProperty->Struct, ValueName)
        : nullptr;
    void* Value = ValueProperty && RootValue
        ? ValueProperty->ContainerPtrToValuePtr<void>(RootValue)
        : nullptr;

    if (!ValueProperty || !Value ||
        !ValueProperty->ImportText_Direct(*ValueText, Value, Object, PPF_Copy))
    {
        UE_LOG(
            LogRaftSimEditor,
            Warning,
            TEXT("PVE override could not import %s.%s=%s on %s."),
            RootStructName,
            ValueName,
            *ValueText,
            Object ? *Object->GetClass()->GetName() : TEXT("None"));
        return false;
    }
    Object->Modify();
    return true;
}

bool SetPveStructBool(
    UObject* Object,
    const TCHAR* RootStructName,
    const TCHAR* ValueName,
    bool Value)
{
    FStructProperty* RootProperty = Object
        ? FindFProperty<FStructProperty>(Object->GetClass(), RootStructName)
        : nullptr;
    void* RootValue = RootProperty
        ? RootProperty->ContainerPtrToValuePtr<void>(Object)
        : nullptr;
    FBoolProperty* BoolProperty = RootProperty
        ? FindFProperty<FBoolProperty>(RootProperty->Struct, ValueName)
        : nullptr;
    if (!BoolProperty || !RootValue)
    {
        UE_LOG(
            LogRaftSimEditor,
            Warning,
            TEXT("PVE override could not find bool %s.%s on %s."),
            RootStructName,
            ValueName,
            Object ? *Object->GetClass()->GetName() : TEXT("None"));
        return false;
    }
    BoolProperty->SetPropertyValue_InContainer(RootValue, Value);
    Object->Modify();
    return true;
}

bool SetPveNestedBool(
    UObject* Object,
    const TCHAR* RootStructName,
    const TCHAR* NestedStructName,
    const TCHAR* ValueName,
    bool Value)
{
    FStructProperty* RootProperty = Object
        ? FindFProperty<FStructProperty>(Object->GetClass(), RootStructName)
        : nullptr;
    void* RootValue = RootProperty
        ? RootProperty->ContainerPtrToValuePtr<void>(Object)
        : nullptr;
    FStructProperty* NestedProperty = RootProperty
        ? FindFProperty<FStructProperty>(RootProperty->Struct, NestedStructName)
        : nullptr;
    void* NestedValue = NestedProperty
        ? NestedProperty->ContainerPtrToValuePtr<void>(RootValue)
        : nullptr;
    FBoolProperty* BoolProperty = NestedProperty
        ? FindFProperty<FBoolProperty>(NestedProperty->Struct, ValueName)
        : nullptr;
    if (!BoolProperty || !NestedValue)
    {
        UE_LOG(
            LogRaftSimEditor,
            Warning,
            TEXT("PVE override could not find bool %s.%s.%s on %s."),
            RootStructName,
            NestedStructName,
            ValueName,
            Object ? *Object->GetClass()->GetName() : TEXT("None"));
        return false;
    }
    BoolProperty->SetPropertyValue_InContainer(NestedValue, Value);
    Object->Modify();
    return true;
}

bool SetPveNestedRamp(
    UObject* Object,
    const TCHAR* RootStructName,
    const TCHAR* NestedStructName,
    const TCHAR* ValueName,
    const TArray<FVector2f>& Points)
{
    FStructProperty* RootProperty = Object
        ? FindFProperty<FStructProperty>(Object->GetClass(), RootStructName)
        : nullptr;
    void* RootValue = RootProperty
        ? RootProperty->ContainerPtrToValuePtr<void>(Object)
        : nullptr;
    FStructProperty* NestedProperty = RootProperty
        ? FindFProperty<FStructProperty>(RootProperty->Struct, NestedStructName)
        : nullptr;
    void* NestedValue = NestedProperty
        ? NestedProperty->ContainerPtrToValuePtr<void>(RootValue)
        : nullptr;
    FStructProperty* RampProperty = NestedProperty
        ? FindFProperty<FStructProperty>(NestedProperty->Struct, ValueName)
        : nullptr;
    FPVFloatRamp* Ramp = RampProperty &&
            RampProperty->Struct == FPVFloatRamp::StaticStruct() && NestedValue
        ? RampProperty->ContainerPtrToValuePtr<FPVFloatRamp>(NestedValue)
        : nullptr;
    if (!Ramp || Points.Num() < 2)
    {
        UE_LOG(
            LogRaftSimEditor,
            Warning,
            TEXT("PVE override could not find ramp %s.%s.%s on %s."),
            RootStructName,
            NestedStructName,
            ValueName,
            Object ? *Object->GetClass()->GetName() : TEXT("None"));
        return false;
    }

    FRichCurve* Curve = Ramp->GetRichCurve();
    Curve->Reset();
    for (const FVector2f& Point : Points)
    {
        const FKeyHandle Handle = Curve->AddKey(Point.X, Point.Y);
        Curve->SetKeyInterpMode(Handle, RCIM_Linear);
    }
    Object->Modify();
    return true;
}

bool SetPveStructFloat(
    UObject* Object,
    const TCHAR* RootStructName,
    const TCHAR* ValueName,
    float Value)
{
    FStructProperty* RootProperty = Object
        ? FindFProperty<FStructProperty>(Object->GetClass(), RootStructName)
        : nullptr;
    void* RootValue = RootProperty
        ? RootProperty->ContainerPtrToValuePtr<void>(Object)
        : nullptr;
    FFloatProperty* FloatProperty = RootProperty
        ? FindFProperty<FFloatProperty>(RootProperty->Struct, ValueName)
        : nullptr;
    if (!FloatProperty || !RootValue)
    {
        UE_LOG(
            LogRaftSimEditor,
            Warning,
            TEXT("PVE override could not find float %s.%s on %s."),
            RootStructName,
            ValueName,
            Object ? *Object->GetClass()->GetName() : TEXT("None"));
        return false;
    }
    FloatProperty->SetPropertyValue_InContainer(RootValue, Value);
    Object->Modify();
    return true;
}

bool SetPveGrowerSeed(UPCGSettings* Settings, int32 Seed)
{
    FStructProperty* ParamsProperty = Settings
        ? FindFProperty<FStructProperty>(Settings->GetClass(), TEXT("GrowerParams"))
        : nullptr;
    FNumericProperty* SeedProperty = ParamsProperty
        ? FindFProperty<FNumericProperty>(ParamsProperty->Struct, TEXT("RandomSeed"))
        : nullptr;
    void* Params = ParamsProperty
        ? ParamsProperty->ContainerPtrToValuePtr<void>(Settings)
        : nullptr;
    if (!SeedProperty || !Params)
    {
        UE_LOG(
            LogRaftSimEditor,
            Warning,
            TEXT("PVE grower override could not find GrowerParams.RandomSeed on %s."),
            Settings ? *Settings->GetClass()->GetName() : TEXT("None"));
        return false;
    }
    void* SeedValue = SeedProperty->ContainerPtrToValuePtr<void>(Params);
    SeedProperty->SetIntPropertyValue(SeedValue, static_cast<uint64>(Seed));
    Settings->Modify();
    return true;
}

bool RedirectPveExport(
    UPCGSettings* Settings,
    const FFutaleufuCypressPveFormSpec& Spec)
{
    FStructProperty* ExportProperty = Settings
        ? FindFProperty<FStructProperty>(Settings->GetClass(), TEXT("ExportSettings"))
        : nullptr;
    if (!ExportProperty)
    {
        return false;
    }
    FString ExportText;
    if (!ExportProperty->ExportText_InContainer(
            0, ExportText, Settings, Settings, Settings, PPF_Copy))
    {
        return false;
    }
    ExportText.ReplaceInline(
        TEXT("/ProceduralVegetationEditor/SampleAssets/StarterContent/ConiferTree_01"),
        TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/PVEFutaleufuCordilleraCypress"));
    ExportText.ReplaceInline(
        TEXT("MeshName=\"PVE_Conifer_01\""),
        *FString::Printf(TEXT("MeshName=\"PVE_CordilleraCypress_%s\""), *Spec.AssetToken));
    if (!ExportProperty->ImportText_InContainer(
            *ExportText, Settings, Settings, PPF_Copy))
    {
        return false;
    }
    Settings->Modify();
    return true;
}

void AppendFutaleufuCordilleraCypressScaleLeafShoot(
    const FVector& Start,
    const FVector& End,
    int32 Seed,
    bool bDenseImbricate,
    TArray<FVector>& WoodyVertices,
    TArray<int32>& WoodyTriangles,
    TArray<FVector>& WoodyNormals,
    TArray<FVector2D>& WoodyUVs,
    TArray<FVector>& LeafVertices,
    TArray<int32>& LeafTriangles,
    TArray<FVector>& LeafNormals,
    TArray<FVector2D>& LeafUVs)
{
    const FVector Axis = End - Start;
    const float LengthCm = Axis.Size();
    if (LengthCm < 4.0f)
    {
        return;
    }
    const FVector Direction = Axis / LengthCm;
    FVector BasisA = FVector::CrossProduct(Direction, FVector::UpVector).GetSafeNormal();
    if (BasisA.IsNearlyZero())
    {
        BasisA = FVector::RightVector;
    }
    const FVector BasisB = FVector::CrossProduct(Direction, BasisA).GetSafeNormal();
    AppendNativeCanopyTaperedSegment(
        Start,
        End,
        FMath::Clamp(LengthCm * 0.010f, 0.28f, 0.58f),
        0.09f,
        5,
        WoodyVertices,
        WoodyTriangles,
        WoodyNormals,
        WoodyUVs);

    const int32 LeafCount = FMath::Clamp(
        FMath::RoundToInt(LengthCm / (bDenseImbricate ? 1.55f : 3.2f)),
        bDenseImbricate ? 10 : 6,
        bDenseImbricate ? 40 : 18);
    constexpr float GoldenAngleDegrees = 137.507764f;
    for (int32 LeafIndex = 0; LeafIndex < LeafCount; ++LeafIndex)
    {
        const float T = (static_cast<float>(LeafIndex) + 0.42f) / LeafCount;
        const float AngleDegrees =
            static_cast<float>(Seed % 360) + LeafIndex * GoldenAngleDegrees;
        const float AngleRadians = FMath::DegreesToRadians(AngleDegrees);
        const FVector Radial =
            (BasisA * FMath::Cos(AngleRadians) + BasisB * FMath::Sin(AngleRadians))
                .GetSafeNormal();
        const float Alternation = LeafIndex % 2 == 0 ? 1.0f : -1.0f;
        const FVector LeafAxis =
            (Direction *
                 (bDenseImbricate ? (0.92f + 0.04f * T) : (0.70f + 0.10f * T)) +
             Radial *
                 (bDenseImbricate ? (0.38f - 0.08f * T) : (0.72f - 0.18f * T)) +
             BasisB * Alternation * (bDenseImbricate ? 0.04f : 0.08f))
                .GetSafeNormal();
        FVector CardRight = FVector::CrossProduct(LeafAxis, Direction).GetSafeNormal();
        if (CardRight.IsNearlyZero())
        {
            CardRight = BasisA;
        }
        const float Variation =
            0.5f + 0.5f * FMath::Sin(static_cast<float>(Seed * 17 + LeafIndex * 29));
        const float LeafHeightCm = bDenseImbricate
            ? FMath::Lerp(4.2f, 5.5f, Variation)
            : FMath::Lerp(2.4f, 3.7f, Variation);
        const float LeafWidthCm = bDenseImbricate
            ? FMath::Lerp(2.2f, 3.0f, 1.0f - Variation * 0.65f)
            : FMath::Lerp(1.25f, 1.85f, 1.0f - Variation * 0.65f);
        const FVector Attachment = FMath::Lerp(Start, End, T) + Radial * 0.18f;
        const FVector Center = Attachment + LeafAxis * LeafHeightCm * 0.46f;
        AppendNativeCanopyLeafCard(
            Center,
            CardRight,
            LeafAxis,
            LeafWidthCm,
            LeafHeightCm,
            Seed + LeafIndex * 5,
            LeafVertices,
            LeafTriangles,
            LeafNormals,
            LeafUVs);
    }
}

bool CreateFutaleufuCypressPvePalette(
    UWorld* World,
    const FString& PaletteMode,
    TArray<FString>& OutLiveTwigPaths,
    FString& OutDeadTwigPath,

    FString& OutSummary)
{
    const bool bCurvedShells = PaletteMode == TEXT("curved_shells");
    const bool bHighDetailHlodCalibratedIrregularCrownMass =
        PaletteMode == TEXT(
            "high_detail_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas");
    const bool bFrozenWpoHighDetailHlodCalibratedIrregularCrownMass =
        PaletteMode == TEXT(
            "frozen_wpo_high_detail_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas");
    const bool bFrozenWpoAzimuthRegisteredPerspectiveDepthHlodCalibratedIrregularCrownMass =
        PaletteMode == TEXT(
            "frozen_wpo_azimuth_registered_perspective_depth_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas");
    const bool bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMass =
        PaletteMode == TEXT(
            "frozen_wpo_azimuth_registered_perspective_complementary_transition_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas");
    const bool bFrozenWpoAzimuthRegisteredPerspectiveHlodCalibratedIrregularCrownMass =
        PaletteMode == TEXT(
            "frozen_wpo_azimuth_registered_perspective_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas") ||
        bFrozenWpoAzimuthRegisteredPerspectiveDepthHlodCalibratedIrregularCrownMass ||
        bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMass;
    const bool bFrozenWpoAzimuthRegisteredHlodCalibratedIrregularCrownMass =
        PaletteMode == TEXT(
            "frozen_wpo_azimuth_registered_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas") ||
        bFrozenWpoAzimuthRegisteredPerspectiveHlodCalibratedIrregularCrownMass;
    const bool bFrozenWpoHlodCalibratedIrregularCrownMass =
        PaletteMode == TEXT(
            "frozen_wpo_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas") ||
        bFrozenWpoHighDetailHlodCalibratedIrregularCrownMass ||
        bFrozenWpoAzimuthRegisteredHlodCalibratedIrregularCrownMass;
    const bool bHlodCalibratedIrregularCrownMassCompoundBranchletAtlas =
        PaletteMode ==
            TEXT("hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas") ||
        bHighDetailHlodCalibratedIrregularCrownMass ||
        bFrozenWpoHlodCalibratedIrregularCrownMass;
    const bool bIrregularCrownMassCompoundBranchletAtlas =
        PaletteMode == TEXT("irregular_crown_mass_compound_branchlet_atlas") ||
        bHlodCalibratedIrregularCrownMassCompoundBranchletAtlas;
    const bool bAsyncSecondaryCompoundBranchletAtlas =
        PaletteMode == TEXT("async_secondary_compound_branchlet_atlas") ||
        bIrregularCrownMassCompoundBranchletAtlas;
    const bool bDeTieredCompoundBranchletAtlas =
        PaletteMode == TEXT("detiered_compound_branchlet_atlas") ||
        bAsyncSecondaryCompoundBranchletAtlas;
    const bool bCompoundBranchletAtlas =
        PaletteMode == TEXT("compound_branchlet_atlas") ||
        bDeTieredCompoundBranchletAtlas;
    const bool bTerminalClusterBotanicalShoot =
        PaletteMode == TEXT("terminal_cluster_botanical_shoot");
    const bool bHierarchicalBotanicalShootCluster =
        PaletteMode == TEXT("hierarchical_botanical_shoot_cluster");
    const bool bBranchletMassBotanicalFlattenedSprayHierarchy =
        PaletteMode == TEXT("branchlet_mass_botanical_flattened_spray_hierarchy") ||
        bHierarchicalBotanicalShootCluster || bTerminalClusterBotanicalShoot ||
        bCompoundBranchletAtlas;
    const bool bDenseBotanicalFlattenedSprayHierarchy =
        PaletteMode == TEXT("dense_botanical_flattened_spray_hierarchy") ||
        bBranchletMassBotanicalFlattenedSprayHierarchy;
    const bool bBotanicalFlattenedSprayHierarchy =
        PaletteMode == TEXT("botanical_flattened_spray_hierarchy") ||
        bDenseBotanicalFlattenedSprayHierarchy;
    const bool bDenseAuthoredScaleLeafHierarchy =
        PaletteMode == TEXT("dense_authored_scale_leaf_hierarchy");
    const bool bAuthoredScaleLeafHierarchy =
        PaletteMode == TEXT("authored_scale_leaf_hierarchy") ||
        bDenseAuthoredScaleLeafHierarchy;
    const bool bCompactConnectedTwigHierarchy =
        PaletteMode == TEXT("compact_connected_twig_hierarchy");
    const bool bConnectedTwigHierarchy =
        PaletteMode == TEXT("connected_twig_hierarchy") ||
        bCompactConnectedTwigHierarchy || bAuthoredScaleLeafHierarchy ||
        bBotanicalFlattenedSprayHierarchy;
    const bool bTwigHierarchy =
        PaletteMode == TEXT("twig_hierarchy") || bConnectedTwigHierarchy;
    TMap<FString, UTexture2D*> Textures;
    if (!World || !CreateFutaleufuCordilleraCypressTextureAssets(Textures, OutSummary))
    {
        return false;
    }
    const FString UnfrozenLiveMaterialName = bBotanicalFlattenedSprayHierarchy
        ? (bCompoundBranchletAtlas
            ? (bDeTieredCompoundBranchletAtlas
                ? (bAsyncSecondaryCompoundBranchletAtlas
                    ? (bIrregularCrownMassCompoundBranchletAtlas
                        ? TEXT("M_RaftSim_FutaleufuCordilleraCypress_V24_IrregularCrownMassCompoundBranchletAtlasLiveTwigs")
                        : TEXT("M_RaftSim_FutaleufuCordilleraCypress_V23_AsyncSecondaryCompoundBranchletAtlasLiveTwigs"))
                    : TEXT("M_RaftSim_FutaleufuCordilleraCypress_V22_DeTieredCompoundBranchletAtlasLiveTwigs"))
                : TEXT("M_RaftSim_FutaleufuCordilleraCypress_V21_CompoundBranchletAtlasLiveTwigs"))
            : (bTerminalClusterBotanicalShoot
            ? TEXT("M_RaftSim_FutaleufuCordilleraCypress_V20_4_TerminalClusterBotanicalShootLiveTwigs")
            : (bHierarchicalBotanicalShootCluster
            ? TEXT("M_RaftSim_FutaleufuCordilleraCypress_V20_3_HierarchicalBotanicalShootClusterLiveTwigs")
            : (bBranchletMassBotanicalFlattenedSprayHierarchy
            ? TEXT("M_RaftSim_FutaleufuCordilleraCypress_V20_2_BranchletMassBotanicalFlattenedSprayHierarchyLiveTwigs")
            : (bDenseBotanicalFlattenedSprayHierarchy
                ? TEXT("M_RaftSim_FutaleufuCordilleraCypress_V20_1_DenseBotanicalFlattenedSprayHierarchyLiveTwigs")
                : TEXT("M_RaftSim_FutaleufuCordilleraCypress_V20_BotanicalFlattenedSprayHierarchyLiveTwigs"))))))
        : (bDenseAuthoredScaleLeafHierarchy
        ? TEXT("M_RaftSim_FutaleufuCordilleraCypress_V19_1_DenseAuthoredScaleLeafHierarchyLiveTwigs")
        : (bAuthoredScaleLeafHierarchy
        ? TEXT("M_RaftSim_FutaleufuCordilleraCypress_V19_AuthoredScaleLeafHierarchyLiveTwigs")
        : (bCompactConnectedTwigHierarchy
        ? TEXT("M_RaftSim_FutaleufuCordilleraCypress_V18_2_CompactConnectedTwigHierarchyLiveTwigs")
        : (bConnectedTwigHierarchy
        ? TEXT("M_RaftSim_FutaleufuCordilleraCypress_V18_1_ConnectedTwigHierarchyLiveTwigs")
        : (bTwigHierarchy
               ? TEXT("M_RaftSim_FutaleufuCordilleraCypress_V18_TwigHierarchyLiveTwigs")
        : (bCurvedShells
               ? TEXT("M_RaftSim_FutaleufuCordilleraCypress_V17_CurvedShellLiveTwigs")
               : TEXT("M_RaftSim_FutaleufuCordilleraCypress_V16_PveLiveTwigs")))))));
    const FString LiveMaterialName = bFrozenWpoHlodCalibratedIrregularCrownMass
        ? (bFrozenWpoAzimuthRegisteredHlodCalibratedIrregularCrownMass
            ? (bFrozenWpoAzimuthRegisteredPerspectiveHlodCalibratedIrregularCrownMass
                ? (bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMass
                    ? TEXT("M_RaftSim_FutaleufuCordilleraCypress_V32_FrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCompoundBranchletAtlasLiveTwigs")
                    : (bFrozenWpoAzimuthRegisteredPerspectiveDepthHlodCalibratedIrregularCrownMass
                        ? TEXT("M_RaftSim_FutaleufuCordilleraCypress_V31_FrozenWpoAzimuthRegisteredPerspectiveDepthHlodCalibratedIrregularCrownMassCompoundBranchletAtlasLiveTwigs")
                        : TEXT("M_RaftSim_FutaleufuCordilleraCypress_V30_FrozenWpoAzimuthRegisteredPerspectiveHlodCalibratedIrregularCrownMassCompoundBranchletAtlasLiveTwigs")))
                : TEXT("M_RaftSim_FutaleufuCordilleraCypress_V29_FrozenWpoAzimuthRegisteredHlodCalibratedIrregularCrownMassCompoundBranchletAtlasLiveTwigs"))
            : (bFrozenWpoHighDetailHlodCalibratedIrregularCrownMass
            ? TEXT("M_RaftSim_FutaleufuCordilleraCypress_V28_FrozenWpoHighDetailHlodCalibratedIrregularCrownMassCompoundBranchletAtlasLiveTwigs")
            : TEXT("M_RaftSim_FutaleufuCordilleraCypress_V27_FrozenWpoHlodCalibratedIrregularCrownMassCompoundBranchletAtlasLiveTwigs")))
        : UnfrozenLiveMaterialName;
    UMaterial* LiveMaterial = CreateOrUpdateFutaleufuNativeCanopyMaterial(
        LiveMaterialName,
        true,
        Textures,
        OutSummary,
        false,
        bBotanicalFlattenedSprayHierarchy
            ? (bCompoundBranchletAtlas
                ? TEXT("CompoundBranchlet")
                : TEXT("BotanicalSpray"))
            : (bAuthoredScaleLeafHierarchy
            ? TEXT("Scale")
            : (bTwigHierarchy ? TEXT("Twig") : TEXT("Near"))),
        bFrozenWpoHlodCalibratedIrregularCrownMass,
        bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMass);
    const FString BarkMaterialName =
        bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMass
        ? TEXT("M_RaftSim_FutaleufuCordilleraCypress_V32_ComplementaryTransitionBark")
        : TEXT("M_RaftSim_FutaleufuCordilleraCypress_Bark");
    UMaterial* BarkMaterial = CreateOrUpdateFutaleufuNativeCanopyMaterial(
        BarkMaterialName,
        false,
        Textures,
        OutSummary,
        false,
        FString(),
        false,
        bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMass);
    if (!LiveMaterial || !BarkMaterial)
    {
        return false;
    }

    const FString UnfrozenPaletteRoot = bBotanicalFlattenedSprayHierarchy
        ? (bCompoundBranchletAtlas
            ? (bDeTieredCompoundBranchletAtlas
                ? (bAsyncSecondaryCompoundBranchletAtlas
                    ? (bIrregularCrownMassCompoundBranchletAtlas
                        ? (bHlodCalibratedIrregularCrownMassCompoundBranchletAtlas
                            ? (bHighDetailHlodCalibratedIrregularCrownMass
                                ? TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/"
                                       "PVEFutaleufuCordilleraCypressHighDetailHlodCalibratedIrregularCrownMassCompoundBranchletAtlas/Palette/")
                                : TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/"
                                       "PVEFutaleufuCordilleraCypressHlodCalibratedIrregularCrownMassCompoundBranchletAtlas/Palette/"))
                            : TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/"
                                   "PVEFutaleufuCordilleraCypressIrregularCrownMassCompoundBranchletAtlas/Palette/"))
                        : TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/"
                               "PVEFutaleufuCordilleraCypressAsyncSecondaryCompoundBranchletAtlas/Palette/"))
                    : TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/"
                           "PVEFutaleufuCordilleraCypressDeTieredCompoundBranchletAtlas/Palette/"))
                : TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/"
                       "PVEFutaleufuCordilleraCypressCompoundBranchletAtlas/Palette/"))
            : (bTerminalClusterBotanicalShoot
            ? TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/"
                   "PVEFutaleufuCordilleraCypressTerminalClusterBotanicalShoot/Palette/")
            : (bHierarchicalBotanicalShootCluster
            ? TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/"
                   "PVEFutaleufuCordilleraCypressHierarchicalBotanicalShootCluster/Palette/")
            : (bBranchletMassBotanicalFlattenedSprayHierarchy
            ? TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/"
                   "PVEFutaleufuCordilleraCypressBranchletMassBotanicalFlattenedSprayHierarchy/Palette/")
            : (bDenseBotanicalFlattenedSprayHierarchy
                ? TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/"
                       "PVEFutaleufuCordilleraCypressDenseBotanicalFlattenedSprayHierarchy/Palette/")
                : TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/"
                       "PVEFutaleufuCordilleraCypressBotanicalFlattenedSprayHierarchy/Palette/"))))))
        : (bDenseAuthoredScaleLeafHierarchy
        ? TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/"
               "PVEFutaleufuCordilleraCypressDenseAuthoredScaleLeafHierarchy/Palette/")
        : (bAuthoredScaleLeafHierarchy
        ? TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/"
               "PVEFutaleufuCordilleraCypressAuthoredScaleLeafHierarchy/Palette/")
        : (bCompactConnectedTwigHierarchy
        ? TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/"
               "PVEFutaleufuCordilleraCypressCompactConnectedTwigHierarchy/Palette/")
        : (bConnectedTwigHierarchy
               ? TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/"
                      "PVEFutaleufuCordilleraCypressConnectedTwigHierarchy/Palette/")
        : (bTwigHierarchy
               ? TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/"
                      "PVEFutaleufuCordilleraCypressTwigHierarchy/Palette/")
        : (bCurvedShells
               ? TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/"
                      "PVEFutaleufuCordilleraCypressCurvedShell/Palette/")
               : TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/"
                      "PVEFutaleufuCordilleraCypress/Palette/")))))));
    const FString PaletteRoot = bFrozenWpoHlodCalibratedIrregularCrownMass
        ? (bFrozenWpoAzimuthRegisteredHlodCalibratedIrregularCrownMass
            ? (bFrozenWpoAzimuthRegisteredPerspectiveHlodCalibratedIrregularCrownMass
                ? (bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMass
                    ? TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/"
                           "PVEFutaleufuCordilleraCypressFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCompoundBranchletAtlas/Palette/")
                    : (bFrozenWpoAzimuthRegisteredPerspectiveDepthHlodCalibratedIrregularCrownMass
                        ? TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/"
                               "PVEFutaleufuCordilleraCypressFrozenWpoAzimuthRegisteredPerspectiveDepthHlodCalibratedIrregularCrownMassCompoundBranchletAtlas/Palette/")
                        : TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/"
                               "PVEFutaleufuCordilleraCypressFrozenWpoAzimuthRegisteredPerspectiveHlodCalibratedIrregularCrownMassCompoundBranchletAtlas/Palette/")))
                : TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/"
                       "PVEFutaleufuCordilleraCypressFrozenWpoAzimuthRegisteredHlodCalibratedIrregularCrownMassCompoundBranchletAtlas/Palette/"))
            : (bFrozenWpoHighDetailHlodCalibratedIrregularCrownMass
            ? TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/"
                   "PVEFutaleufuCordilleraCypressFrozenWpoHighDetailHlodCalibratedIrregularCrownMassCompoundBranchletAtlas/Palette/")
            : TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/"
                   "PVEFutaleufuCordilleraCypressFrozenWpoHlodCalibratedIrregularCrownMassCompoundBranchletAtlas/Palette/")))
        : UnfrozenPaletteRoot;
    OutLiveTwigPaths.Reset();
    for (int32 TwigIndex = 0; TwigIndex < 3; ++TwigIndex)
    {
        TArray<FVector> Vertices;
        TArray<int32> Triangles;
        TArray<FVector> Normals;
        TArray<FVector2D> UVs;
        TArray<FVector> BarkVertices;
        TArray<int32> BarkTriangles;
        TArray<FVector> BarkNormals;
        TArray<FVector2D> BarkUVs;
        const float LengthCm = 88.0f + static_cast<float>(TwigIndex) * 10.0f;
        const float WidthCm = 50.0f + static_cast<float>(TwigIndex) * 6.0f;
        if (bBotanicalFlattenedSprayHierarchy)
        {
            const FVector MainStart(-4.0f, 0.0f, -0.5f);
            const FVector MainEnd(
                52.0f + TwigIndex * 5.0f,
                TwigIndex == 1 ? 1.5f : -1.0f,
                5.0f + TwigIndex * 1.2f);
            const FVector MainAxis = (MainEnd - MainStart).GetSafeNormal();
            const FVector MainRight = FVector::RightVector.RotateAngleAxis(
                static_cast<float>(TwigIndex - 1) * 12.0f,
                MainAxis);
            const FVector MainUp = FVector::CrossProduct(
                MainAxis, MainRight).GetSafeNormal();
            AppendNativeCanopyTaperedSegment(
                MainStart,
                MainEnd,
                1.08f + TwigIndex * 0.10f,
                0.20f,
                7,
                BarkVertices,
                BarkTriangles,
                BarkNormals,
                BarkUVs);
            const int32 MainSprayLayerCount =
                bCompoundBranchletAtlas
                    ? 2
                    : (bDenseBotanicalFlattenedSprayHierarchy ? 3 : 1);
            for (int32 LayerIndex = 0; LayerIndex < MainSprayLayerCount; ++LayerIndex)
            {
                const float LayerOffset = static_cast<float>(LayerIndex) - 1.0f;
                const FVector LayerRight = MainRight.RotateAngleAxis(
                    LayerOffset * 16.0f,
                    MainAxis);
                AppendNativeCanopyAtlasCurvedCard(
                    MainStart - MainAxis * 1.0f + MainRight * LayerOffset * 2.2f,
                    MainAxis,
                    LayerRight,
                    ((bCompoundBranchletAtlas ? 28.0f : 24.0f) +
                     TwigIndex * 1.8f) *
                        (1.0f - FMath::Abs(LayerOffset) * 0.08f),
                    (FVector::Distance(MainStart, MainEnd) + 3.0f) *
                        (1.0f - FMath::Abs(LayerOffset) * 0.05f),
                    3.2f + TwigIndex * 0.5f + LayerIndex * 0.35f,
                    (TwigIndex % 2 == 0 ? -1.5f : 1.5f) + LayerOffset * 0.8f,
                    bCompoundBranchletAtlas ? 7 : 6,
                    (TwigIndex * 5 + LayerIndex * 7) % 16,
                    Vertices,
                    Triangles,
                    Normals,
                    UVs);
            }

            const int32 BranchletPairCount =
                bHierarchicalBotanicalShootCluster
                    ? 5
                    : (bBranchletMassBotanicalFlattenedSprayHierarchy ? 6 : 4);
            for (int32 PairIndex = 0; PairIndex < BranchletPairCount; ++PairIndex)
            {
                for (int32 SideIndex = 0; SideIndex < 2; ++SideIndex)
                {
                    const float Side = SideIndex == 0 ? -1.0f : 1.0f;
                    const float BranchAttachT =
                        bHierarchicalBotanicalShootCluster
                            ? 0.11f + PairIndex * 0.17f + Side * 0.012f
                            : (bBranchletMassBotanicalFlattenedSprayHierarchy
                            ? 0.10f + PairIndex * 0.145f
                            : 0.16f + PairIndex * 0.19f);
                    const FVector BranchStart = FMath::Lerp(
                        MainStart, MainEnd, BranchAttachT);
                    const float BranchVertical =
                        bBranchletMassBotanicalFlattenedSprayHierarchy
                            ? (static_cast<float>(PairIndex % 3) - 1.0f) * 0.075f +
                                  TwigIndex * 0.025f
                            : (PairIndex == 1 ? 0.14f : -0.025f) +
                                  TwigIndex * 0.025f;
                    const FVector BranchAxis = FVector(
                        0.72f + PairIndex * 0.045f,
                        Side * (0.66f - PairIndex * 0.075f),
                        BranchVertical)
                                                   .GetSafeNormal();

                    const float BranchLength =
                        31.0f - PairIndex * 2.2f + TwigIndex * 1.5f;
                    AppendNativeCanopyTaperedSegment(
                        BranchStart - BranchAxis * 0.4f,
                        BranchStart + BranchAxis * BranchLength *
                            (bHierarchicalBotanicalShootCluster
                                 ? 0.60f
                                 : (bBranchletMassBotanicalFlattenedSprayHierarchy
                                 ? 0.68f
                                 : 0.82f)),
                        0.58f - PairIndex * 0.055f,
                        0.10f,
                        6,
                        BarkVertices,
                        BarkTriangles,
                        BarkNormals,
                        BarkUVs);
                    FVector BranchRight = FVector::CrossProduct(
                        FVector::UpVector, BranchAxis).GetSafeNormal();
                    if (BranchRight.IsNearlyZero())
                    {
                        BranchRight = MainRight;
                    }
                    BranchRight = BranchRight.RotateAngleAxis(
                        Side * (10.0f + PairIndex * 6.0f) + TwigIndex * 3.0f,
                        BranchAxis);
                    const int32 CardIndex = 1 + PairIndex * 2 + SideIndex;
                    const int32 BranchSprayLayerCount =
                        bCompoundBranchletAtlas
                            ? 1
                            : (bDenseBotanicalFlattenedSprayHierarchy ? 2 : 1);
                    for (int32 LayerIndex = 0;
                         LayerIndex < BranchSprayLayerCount;
                         ++LayerIndex)
                    {
                        const float LayerSide = LayerIndex == 0 ? -1.0f : 1.0f;
                        const FVector LayerRight = BranchRight.RotateAngleAxis(
                            LayerSide * (11.0f + PairIndex * 1.5f),
                            BranchAxis);
                        AppendNativeCanopyAtlasCurvedCard(
                            BranchStart + BranchAxis * (1.5f + LayerIndex * 2.1f) +
                                BranchRight * LayerSide * 1.4f,
                            BranchAxis,
                            LayerRight,
                            ((bCompoundBranchletAtlas ? 22.0f : 18.0f) -
                             PairIndex * 0.8f + TwigIndex * 0.8f) *
                                (LayerIndex == 0 ? 1.0f : 0.92f) *
                                (bHierarchicalBotanicalShootCluster ? 0.78f : 1.0f),
                            BranchLength *
                                (bCompoundBranchletAtlas ? 1.10f : 1.0f) *
                                (LayerIndex == 0 ? 1.0f : 0.90f) *
                                (bHierarchicalBotanicalShootCluster ? 0.82f : 1.0f),
                            2.4f + PairIndex * 0.35f + LayerIndex * 0.4f,
                            Side * (1.2f + PairIndex * 0.28f) + LayerSide * 0.6f,
                            bCompoundBranchletAtlas ? 6 : 5,
                            (TwigIndex * 5 + CardIndex * 3 + LayerIndex * 7) % 16,
                            Vertices,
                            Triangles,
                            Normals,
                            UVs);
                    }
                    if (bHierarchicalBotanicalShootCluster)
                    {
                        for (int32 SubshootIndex = 0; SubshootIndex < 2; ++SubshootIndex)
                        {
                            const float SubshootSide =
                                SubshootIndex == 0 ? -1.0f : 1.0f;
                            const float SubshootAttach = 0.40f + SubshootIndex * 0.24f;
                            const FVector SubshootStart =
                                BranchStart + BranchAxis * BranchLength * SubshootAttach;
                            const FVector SubshootAxis =
                                (BranchAxis * 0.58f + MainAxis * 0.18f +
                                 MainRight * Side * SubshootSide * 0.36f +
                                 MainUp * (SubshootIndex == 0 ? -0.08f : 0.10f))
                                    .GetSafeNormal();
                            const float SubshootLength =
                                13.0f - PairIndex * 0.7f + TwigIndex * 0.5f;
                            AppendNativeCanopyTaperedSegment(
                                SubshootStart - SubshootAxis * 0.25f,
                                SubshootStart + SubshootAxis * SubshootLength * 0.54f,
                                0.26f - PairIndex * 0.018f,
                                0.045f,
                                5,
                                BarkVertices,
                                BarkTriangles,
                                BarkNormals,
                                BarkUVs);
                            FVector SubshootRight = FVector::CrossProduct(
                                MainUp, SubshootAxis).GetSafeNormal();
                            if (SubshootRight.IsNearlyZero())
                            {
                                SubshootRight = BranchRight;
                            }
                            SubshootRight = SubshootRight.RotateAngleAxis(
                                Side * SubshootSide * (8.0f + PairIndex * 2.0f),
                                SubshootAxis);
                            AppendNativeCanopyAtlasCurvedCard(
                                SubshootStart + SubshootAxis * 0.8f,
                                SubshootAxis,
                                SubshootRight,
                                9.5f - PairIndex * 0.35f + TwigIndex * 0.3f,
                                SubshootLength,
                                1.8f + PairIndex * 0.18f,
                                Side * SubshootSide * 0.85f,
                                4,
                                (TwigIndex * 11 + CardIndex * 5 +
                                 SubshootIndex * 7) % 16,
                                Vertices,
                                Triangles,
                                Normals,
                            UVs);
                        }
                    }
                    if (bTerminalClusterBotanicalShoot)
                    {
                        for (int32 TerminalIndex = 0; TerminalIndex < 2; ++TerminalIndex)
                        {
                            const float TerminalSide = TerminalIndex == 0 ? -1.0f : 1.0f;
                            const float TerminalAttach = 0.69f + TerminalIndex * 0.13f;
                            const FVector TerminalStart =
                                BranchStart + BranchAxis * BranchLength * TerminalAttach;
                            const FVector TerminalAxis =
                                (BranchAxis * 0.76f +
                                 MainRight * Side * TerminalSide * 0.25f +
                                 MainUp * (TerminalIndex == 0 ? -0.045f : 0.065f))
                                    .GetSafeNormal();
                            const float TerminalLength =
                                9.8f - PairIndex * 0.35f + TwigIndex * 0.35f;
                            AppendNativeCanopyTaperedSegment(
                                TerminalStart - TerminalAxis * 0.18f,
                                TerminalStart + TerminalAxis * TerminalLength * 0.28f,
                                0.16f - PairIndex * 0.010f,
                                0.035f,
                                5,
                                BarkVertices,
                                BarkTriangles,
                                BarkNormals,
                                BarkUVs);
                            FVector TerminalRight = FVector::CrossProduct(
                                MainUp, TerminalAxis).GetSafeNormal();
                            if (TerminalRight.IsNearlyZero())
                            {
                                TerminalRight = BranchRight;
                            }
                            TerminalRight = TerminalRight.RotateAngleAxis(
                                Side * TerminalSide * (6.0f + PairIndex * 1.5f),
                                TerminalAxis);
                            AppendNativeCanopyAtlasCurvedCard(
                                TerminalStart + TerminalAxis * 0.45f,
                                TerminalAxis,
                                TerminalRight,
                                8.4f - PairIndex * 0.24f + TwigIndex * 0.25f,
                                TerminalLength,
                                1.35f + PairIndex * 0.12f,
                                Side * TerminalSide * 0.55f,
                                4,
                                (TwigIndex * 13 + CardIndex * 7 +
                                 TerminalIndex * 5) % 16,
                                Vertices,
                                Triangles,
                                Normals,
                                UVs);
                        }
                    }
                }
            }
        }
        else if (bAuthoredScaleLeafHierarchy)
        {
            const FVector MainStart(-4.0f, 0.0f, -0.5f);
            const FVector MainEnd(
                50.0f + TwigIndex * 5.0f,
                TwigIndex == 1 ? 1.5f : -1.0f,
                5.0f + TwigIndex * 1.2f);
            AppendFutaleufuCordilleraCypressScaleLeafShoot(
                MainStart,
                MainEnd,
                1000 + TwigIndex * 131,
                bDenseAuthoredScaleLeafHierarchy,
                BarkVertices,
                BarkTriangles,
                BarkNormals,
                BarkUVs,
                Vertices,
                Triangles,
                Normals,
                UVs);
            const FVector MainAxis = (MainEnd - MainStart).GetSafeNormal();
            FVector MainRight = FVector::CrossProduct(MainAxis, FVector::UpVector).GetSafeNormal();
            if (MainRight.IsNearlyZero())
            {
                MainRight = FVector::RightVector;
            }
            const FVector MainUp = FVector::CrossProduct(MainRight, MainAxis).GetSafeNormal();
            const int32 PairCount = bDenseAuthoredScaleLeafHierarchy ? 6 : 5;
            for (int32 PairIndex = 0; PairIndex < PairCount; ++PairIndex)
            {
                const float AttachT = bDenseAuthoredScaleLeafHierarchy
                    ? 0.12f + PairIndex * 0.14f
                    : 0.16f + PairIndex * 0.16f;
                for (int32 SideIndex = 0; SideIndex < 2; ++SideIndex)
                {
                    const float Side = SideIndex == 0 ? -1.0f : 1.0f;
                    const FVector BranchStart = FMath::Lerp(MainStart, MainEnd, AttachT);
                    const FVector BranchDirection =
                        (MainAxis * (0.58f + PairIndex * 0.045f) +
                         MainRight * Side * (0.78f - PairIndex * 0.065f) +
                         MainUp * ((PairIndex == 1 ? 0.20f : -0.04f) +
                                   TwigIndex * 0.025f))
                            .GetSafeNormal();
                    const float BranchLengthCm = bDenseAuthoredScaleLeafHierarchy
                        ? 22.0f - PairIndex * 1.1f + TwigIndex * 1.2f
                        : 25.0f - PairIndex * 1.6f + TwigIndex * 1.4f;
                    AppendFutaleufuCordilleraCypressScaleLeafShoot(
                        BranchStart - BranchDirection * 0.35f,
                        BranchStart + BranchDirection * BranchLengthCm,
                        2000 + TwigIndex * 251 + PairIndex * 37 + SideIndex * 503,
                        bDenseAuthoredScaleLeafHierarchy,
                        BarkVertices,
                        BarkTriangles,
                        BarkNormals,
                        BarkUVs,
                        Vertices,
                        Triangles,
                        Normals,
                        UVs);
                }
            }
        }
        else if (bConnectedTwigHierarchy)
        {
            const FVector MainStart(-4.0f, 0.0f, -0.5f);
            const FVector MainEnd(
                (bCompactConnectedTwigHierarchy ? 50.0f : 60.0f) + TwigIndex * 5.0f,
                TwigIndex == 1 ? 1.5f : -1.0f,
                5.0f + TwigIndex * 1.2f);
            AppendNativeCanopyTaperedSegment(
                MainStart,
                MainEnd,
                (bCompactConnectedTwigHierarchy ? 1.05f : 1.75f) + TwigIndex * 0.12f,
                bCompactConnectedTwigHierarchy ? 0.22f : 0.34f,
                7,
                BarkVertices,
                BarkTriangles,
                BarkNormals,
                BarkUVs);

            const FVector MainAxis = (MainEnd - MainStart).GetSafeNormal();
            const FVector MainRight = FVector::RightVector.RotateAngleAxis(
                static_cast<float>(TwigIndex - 1) * 17.0f,
                MainAxis);
            AppendNativeCanopyAtlasCurvedCard(
                MainStart - MainAxis * 1.5f,
                MainAxis,
                MainRight,
                (bCompactConnectedTwigHierarchy ? 38.0f : 31.0f) + TwigIndex * 2.5f,
                FVector::Distance(MainStart, MainEnd) + 4.0f,
                5.8f + TwigIndex * 0.8f,
                TwigIndex % 2 == 0 ? -2.4f : 2.4f,
                5,
                TwigIndex * 5,
                Vertices,
                Triangles,
                Normals,
                UVs);

            for (int32 PairIndex = 0; PairIndex < 4; ++PairIndex)
            {
                for (int32 SideIndex = 0; SideIndex < 2; ++SideIndex)
                {
                    const float Side = SideIndex == 0 ? -1.0f : 1.0f;
                    const FVector BranchStart(
                        8.0f + PairIndex * 12.0f,
                        0.0f,
                        0.5f + PairIndex * 1.0f);
                    const FVector BranchAxis = FVector(
                        0.72f + PairIndex * 0.04f,
                        Side * (0.64f - PairIndex * 0.07f),
                        (PairIndex == 1 ? 0.17f : -0.035f) + TwigIndex * 0.03f)
                                                   .GetSafeNormal();
                    const float BranchLength =
                        36.0f - PairIndex * 2.5f + TwigIndex * 2.0f;
                    const float WoodyBranchLength = bCompactConnectedTwigHierarchy
                        ? 8.0f + PairIndex * 0.6f
                        : BranchLength * 0.88f;
                    const FVector BranchEnd = BranchStart + BranchAxis * WoodyBranchLength;
                    AppendNativeCanopyTaperedSegment(
                        BranchStart - BranchAxis *
                            (bCompactConnectedTwigHierarchy ? 0.5f : 1.0f),
                        BranchEnd,
                        (bCompactConnectedTwigHierarchy ? 0.62f : 1.05f) -
                            PairIndex * 0.07f,
                        bCompactConnectedTwigHierarchy ? 0.12f : 0.16f,
                        6,
                        BarkVertices,
                        BarkTriangles,
                        BarkNormals,
                        BarkUVs);

                    FVector BranchRight =
                        FVector::CrossProduct(FVector::UpVector, BranchAxis).GetSafeNormal();
                    if (BranchRight.IsNearlyZero())
                    {
                        BranchRight = FVector::RightVector;
                    }
                    BranchRight = BranchRight.RotateAngleAxis(
                        Side * (15.0f + PairIndex * 8.0f) + TwigIndex * 4.0f,
                        BranchAxis);
                    const int32 CardIndex = 1 + PairIndex * 2 + SideIndex;
                    AppendNativeCanopyAtlasCurvedCard(
                        BranchStart + BranchAxis *
                            (bCompactConnectedTwigHierarchy ? 4.0f : -2.0f),
                        BranchAxis,
                        BranchRight,
                        26.0f - PairIndex * 1.2f + TwigIndex * 1.2f,
                        BranchLength,
                        4.0f + PairIndex * 0.55f,
                        Side * (1.8f + PairIndex * 0.4f),
                        4,
                        (TwigIndex * 5 + CardIndex * 3) % 16,

                        Vertices,
                        Triangles,
                        Normals,
                        UVs);
                }
            }
        }
        else if (bTwigHierarchy)
        {
            const FVector CentralAxis = FVector::ForwardVector;
            const FVector CentralRight = FVector::RightVector.RotateAngleAxis(
                static_cast<float>(TwigIndex - 1) * 14.0f,
                CentralAxis);
            AppendNativeCanopyAtlasCurvedCard(
                FVector::ZeroVector,
                CentralAxis,
                CentralRight,
                18.0f + TwigIndex * 1.5f,
                46.0f + TwigIndex * 4.0f,
                4.2f + TwigIndex * 0.7f,
                TwigIndex % 2 == 0 ? -1.8f : 1.8f,
                4,
                TwigIndex * 5,
                Vertices,
                Triangles,
                Normals,
                UVs);
            for (int32 PairIndex = 0; PairIndex < 3; ++PairIndex)
            {
                for (int32 SideIndex = 0; SideIndex < 2; ++SideIndex)
                {
                    const float Side = SideIndex == 0 ? -1.0f : 1.0f;
                    const FVector Axis = FVector(
                        0.78f + PairIndex * 0.045f,
                        Side * (0.52f - PairIndex * 0.065f),
                        (PairIndex == 1 ? 0.13f : -0.06f) + TwigIndex * 0.025f)
                                             .GetSafeNormal();
                    FVector Right = FVector::CrossProduct(FVector::UpVector, Axis).GetSafeNormal();
                    if (Right.IsNearlyZero())
                    {
                        Right = FVector::RightVector;
                    }
                    Right = Right.RotateAngleAxis(
                        Side * (18.0f + PairIndex * 9.0f) + TwigIndex * 4.0f,
                        Axis);
                    const int32 CardIndex = 1 + PairIndex * 2 + SideIndex;
                    AppendNativeCanopyAtlasCurvedCard(
                        FVector(7.0f + PairIndex * 9.0f, 0.0f, PairIndex * 0.8f),
                        Axis,
                        Right,
                        13.5f - PairIndex * 0.8f + TwigIndex * 0.6f,
                        32.0f - PairIndex * 2.2f + TwigIndex * 1.8f,
                        3.2f + PairIndex * 0.5f,
                        Side * (1.5f + PairIndex * 0.35f),
                        4,
                        (TwigIndex * 5 + CardIndex * 3) % 16,
                        Vertices,
                        Triangles,
                        Normals,
                        UVs);
                }
            }
        }
        else
        {
            for (int32 PlaneIndex = 0; PlaneIndex < 3; ++PlaneIndex)
            {
                const float RollDegrees =
                    static_cast<float>(PlaneIndex - 1) * (32.0f + TwigIndex * 4.0f);
                const FVector Right = FVector::RightVector.RotateAngleAxis(
                    RollDegrees,
                    FVector::ForwardVector);
                if (bCurvedShells)
                {
                    const float ShellLength = LengthCm * (PlaneIndex == 1 ? 1.0f : 0.88f);
                    AppendNativeCanopyAtlasCurvedCard(
                        FVector(0.0f, 0.0f, static_cast<float>(PlaneIndex - 1) * 2.5f),
                        FVector::ForwardVector,
                        Right,
                        WidthCm * (PlaneIndex == 1 ? 0.92f : 0.68f),
                        ShellLength,
                        (6.5f + TwigIndex * 1.2f) * (PlaneIndex == 1 ? 1.0f : 0.72f),
                        (2.4f + TwigIndex * 0.6f) * (PlaneIndex == 0 ? -1.0f : 1.0f),
                        6,
                        TwigIndex * 4 + PlaneIndex,
                        Vertices,
                        Triangles,
                        Normals,
                        UVs);
                }
                else
                {
                    AppendNativeCanopyLeafCard(
                        FVector(LengthCm * 0.5f, 0.0f, static_cast<float>(PlaneIndex - 1) * 2.5f),
                        Right,
                        FVector::ForwardVector,
                        WidthCm * (PlaneIndex == 1 ? 1.0f : 0.74f),
                        LengthCm * (PlaneIndex == 1 ? 1.0f : 0.86f),
                        TwigIndex * 4 + PlaneIndex,
                        Vertices,
                        Triangles,
                        Normals,
                        UVs);
                }
            }
        }
        const FString UnfrozenPaletteAssetToken = bConnectedTwigHierarchy
            ? (bBotanicalFlattenedSprayHierarchy
                   ? (bCompoundBranchletAtlas
                        ? (bDeTieredCompoundBranchletAtlas
                            ? (bAsyncSecondaryCompoundBranchletAtlas
                                ? (bIrregularCrownMassCompoundBranchletAtlas
                                    ? (bHlodCalibratedIrregularCrownMassCompoundBranchletAtlas
                                        ? (bHighDetailHlodCalibratedIrregularCrownMass
                                            ? TEXT("V26_HighDetailHlodCalibratedIrregularCrownMassCompoundBranchletAtlas_Pve")
                                            : TEXT("V25_HlodCalibratedIrregularCrownMassCompoundBranchletAtlas_Pve"))
                                        : TEXT("V24_IrregularCrownMassCompoundBranchletAtlas_Pve"))
                                    : TEXT("V23_AsyncSecondaryCompoundBranchletAtlas_Pve"))
                                : TEXT("V22_DeTieredCompoundBranchletAtlas_Pve"))
                            : TEXT("V21_CompoundBranchletAtlas_Pve"))
                        : (bTerminalClusterBotanicalShoot
                        ? TEXT("V20_4_TerminalClusterBotanicalShoot_Pve")
                        : (bHierarchicalBotanicalShootCluster
                        ? TEXT("V20_3_HierarchicalBotanicalShootCluster_Pve")
                        : (bBranchletMassBotanicalFlattenedSprayHierarchy
                        ? TEXT("V20_2_BranchletMassBotanicalFlattenedSprayHierarchy_Pve")
                        : (bDenseBotanicalFlattenedSprayHierarchy
                            ? TEXT("V20_1_DenseBotanicalFlattenedSprayHierarchy_Pve")
                            : TEXT("V20_BotanicalFlattenedSprayHierarchy_Pve"))))))
                   : (bDenseAuthoredScaleLeafHierarchy
                   ? TEXT("V19_1_DenseAuthoredScaleLeafHierarchy_Pve")
                   : (bAuthoredScaleLeafHierarchy
                   ? TEXT("V19_AuthoredScaleLeafHierarchy_Pve")
                   : (bCompactConnectedTwigHierarchy
                   ? TEXT("V18_2_CompactConnectedTwigHierarchy_Pve")
                   : TEXT("V18_1_ConnectedTwigHierarchy_Pve")))))
            : (bTwigHierarchy
                   ? TEXT("V18_TwigHierarchy_Pve")
                   : (bCurvedShells ? TEXT("V17_CurvedShell_Pve") : TEXT("V16_Pve")));
        const FString PaletteAssetToken = bFrozenWpoHlodCalibratedIrregularCrownMass
            ? (bFrozenWpoAzimuthRegisteredHlodCalibratedIrregularCrownMass
                ? (bFrozenWpoAzimuthRegisteredPerspectiveHlodCalibratedIrregularCrownMass
                    ? (bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMass
                        ? TEXT("V32_FrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCompoundBranchletAtlas_Pve")
                        : (bFrozenWpoAzimuthRegisteredPerspectiveDepthHlodCalibratedIrregularCrownMass
                            ? TEXT("V31_FrozenWpoAzimuthRegisteredPerspectiveDepthHlodCalibratedIrregularCrownMassCompoundBranchletAtlas_Pve")
                            : TEXT("V30_FrozenWpoAzimuthRegisteredPerspectiveHlodCalibratedIrregularCrownMassCompoundBranchletAtlas_Pve")))
                    : TEXT("V29_FrozenWpoAzimuthRegisteredHlodCalibratedIrregularCrownMassCompoundBranchletAtlas_Pve"))
                : (bFrozenWpoHighDetailHlodCalibratedIrregularCrownMass
                ? TEXT("V28_FrozenWpoHighDetailHlodCalibratedIrregularCrownMassCompoundBranchletAtlas_Pve")
                : TEXT("V27_FrozenWpoHlodCalibratedIrregularCrownMassCompoundBranchletAtlas_Pve")))
            : UnfrozenPaletteAssetToken;
        const FString AssetName = FString::Printf(
            TEXT("SM_RaftSim_FutaleufuCordilleraCypress_%sLiveTwig_%c"),
            *PaletteAssetToken,
            TCHAR('A' + TwigIndex));
        const FString PackagePath = PaletteRoot + AssetName;
        AActor* Actor = bConnectedTwigHierarchy
            ? AddPreviewTwoSectionProceduralMeshActor(
                  World,
                  AssetName + TEXT("_Source"),
                  BarkVertices,
                  BarkTriangles,
                  BarkNormals,
                  BarkUVs,
                  BarkMaterial,
                  Vertices,
                  Triangles,
                  Normals,
                  UVs,
                  LiveMaterial)
            : AddPreviewProceduralMeshActor(
                  World,
                  AssetName + TEXT("_Source"),
                  Vertices,
                  Triangles,
                  Normals,
                  UVs,
                  FLinearColor::White,
                  LiveMaterial,
                  nullptr,
                  false);
        UStaticMesh* Mesh = ConvertNativeCanopyProceduralActorToStaticMesh(
            Actor,
            PackagePath,
            LiveMaterial,
            false,
            ENaniteShapePreservation::None,
            OutSummary);
        if (Actor)
        {
            Actor->Destroy();
        }
        if (!Mesh)
        {
            return false;
        }
        if (bConnectedTwigHierarchy && Mesh->GetStaticMaterials().Num() != 2)
        {
            OutSummary += FString::Printf(
                TEXT("Connected live twig %s did not preserve its bark and foliage material slots.\n"),
                *PackagePath);
            return false;
        }
        OutLiveTwigPaths.Add(PackagePath + TEXT(".") + AssetName);
    }

    TArray<FVector> DeadVertices;
    TArray<int32> DeadTriangles;
    TArray<FVector> DeadNormals;
    TArray<FVector2D> DeadUVs;
    AppendNativeCanopyTaperedSegment(
        FVector::ZeroVector,
        FVector(54.0f, 0.0f, 5.0f),
        2.2f,
        0.35f,
        7,
        DeadVertices,
        DeadTriangles,
        DeadNormals,
        DeadUVs);
    for (int32 SideIndex = 0; SideIndex < 4; ++SideIndex)
    {
        const float Side = SideIndex % 2 == 0 ? -1.0f : 1.0f;
        const FVector BranchStart(17.0f + SideIndex * 8.0f, 0.0f, 2.0f + SideIndex * 0.8f);
        AppendNativeCanopyTaperedSegment(
            BranchStart,
            BranchStart + FVector(14.0f, Side * (9.0f + SideIndex * 1.5f), 6.0f),
            1.0f,
            0.18f,
            6,
            DeadVertices,
            DeadTriangles,
            DeadNormals,
            DeadUVs);
    }
    const FString DeadAssetName =
        TEXT("SM_RaftSim_FutaleufuCordilleraCypress_V16_PveDeadTwig");
    const FString DeadPackagePath = PaletteRoot + DeadAssetName;
    AActor* DeadActor = AddPreviewProceduralMeshActor(
        World,
        DeadAssetName + TEXT("_Source"),
        DeadVertices,
        DeadTriangles,
        DeadNormals,
        DeadUVs,
        FLinearColor::White,
        BarkMaterial,
        nullptr,
        false);
    UStaticMesh* DeadMesh = ConvertNativeCanopyProceduralActorToStaticMesh(
        DeadActor,
        DeadPackagePath,
        BarkMaterial,
        true,
        ENaniteShapePreservation::None,
        OutSummary);
    if (DeadActor)
    {
        DeadActor->Destroy();
    }
    if (!DeadMesh)
    {
        return false;
    }
    OutDeadTwigPath = DeadPackagePath + TEXT(".") + DeadAssetName;
    return true;
}

UPCGSettings* FindPveSettingsByClassName(
    const UPCGGraph* Graph,
    const TCHAR* ClassName)
{
    if (!Graph)
    {
        return nullptr;
    }
    for (UPCGNode* Node : Graph->GetNodes())
    {
        UPCGSettings* Settings = Node ? Node->GetSettings() : nullptr;
        if (Settings && Settings->GetClass()->GetName() == ClassName)
        {
            return Settings;
        }
    }
    return nullptr;
}

UPCGNode* AddProjectPveNode(
    UPCGGraph* Graph,
    const TCHAR* ClassName,
    UPCGSettings*& OutSettings)
{
    const FString ClassPath = FString::Printf(
        TEXT("/Script/ProceduralVegetation.%s"), ClassName);
    UClass* SettingsClass = FindObject<UClass>(nullptr, *ClassPath);
    OutSettings = nullptr;
    return Graph && SettingsClass
        ? Graph->AddNodeOfType(SettingsClass, OutSettings)
        : nullptr;
}

bool ConfigureFutaleufuCypressPveGrower(
    UPCGSettings* Settings,
    const FFutaleufuCypressPveFormSpec& Spec,
    bool bBranchletGrower,
    bool bDeTieredCrown,
    int32 BranchTemplateIndex)
{
    if (!Settings)
    {
        return false;
    }

    const bool bDeTieredMain = bDeTieredCrown && !bBranchletGrower;
    const int32 AsyncBranchTemplateIndex =
        bBranchletGrower ? FMath::Clamp(BranchTemplateIndex, 0, 2) : 0;
    bool bConfigured = SetPveGrowerSeed(
        Settings,
        Spec.Seed + (bBranchletGrower ? 7919 + AsyncBranchTemplateIndex * 104729 : 0));

    bConfigured &= SetPveStructText(
        Settings,
        TEXT("GrowerParams"),
        TEXT("GrowthCycles"),
        bBranchletGrower ? TEXT("6") : TEXT("44"));
    bConfigured &= SetPveStructBool(
        Settings,
        TEXT("GrowerParams"),
        TEXT("bSenescence"),
        bBranchletGrower ? false : Spec.bAllowSenescence);
    bConfigured &= SetPveStructBool(
        Settings,
        TEXT("GrowerParams"),
        TEXT("bBranchPhyllotaxySameAsTrunk"),
        false);
    bConfigured &= SetPveStructBool(
        Settings,
        TEXT("GrowerParams"),
        TEXT("bBranchPhototropismSameAsTrunk"),
        false);
    bConfigured &= SetPveStructBool(
        Settings,
        TEXT("GrowerParams"),
        TEXT("bBranchDirectionalSameAsTrunk"),
        false);
    bConfigured &= SetPveStructBool(
        Settings,
        TEXT("GrowerParams"),
        TEXT("bBranchAuxinConditionSameAsTrunk"),
        false);
    bConfigured &= SetPveNestedBool(
        Settings,
        TEXT("GrowerParams"),
        TEXT("Bifurcation"),
        TEXT("bEnableBifurcation"),
        false);
    bConfigured &= SetPveNestedBool(
        Settings,
        TEXT("GrowerParams"),
        TEXT("BranchBifurcation"),
        TEXT("bEnableBifurcation"),
        false);

    bConfigured &= SetPveNestedInt(
        Settings,
        TEXT("GrowerParams"),
        TEXT("TrunkGrowth"),
        TEXT("MaxGeneration"),
        2);
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("TrunkGrowth"),
        TEXT("IncrementalRadius"),
        bBranchletGrower ? 0.0022f : 0.0062f);
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("TrunkGrowth"),
        TEXT("PlantTargetLength"),
        bBranchletGrower ? 1.45f : 22.5f);
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("TrunkGrowth"),
        TEXT("BranchTargetLength"),
        bBranchletGrower ? 0.56f : 6.1f);
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("TrunkGrowth"),
        TEXT("SegmentLength"),
        bBranchletGrower ? 0.24f : 0.56f);
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("TrunkGrowth"),
        TEXT("BranchScale"),
        bBranchletGrower ? 0.74f : Spec.BranchScale);
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("TrunkGrowth"),
        TEXT("LengthBias"),
        bBranchletGrower ? 0.88f : 0.94f);
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("TrunkGrowth"),
        TEXT("AxillaryParentGrowth"),
        bBranchletGrower ? 0.78f : FMath::Min(2.0f, Spec.AxillaryParentGrowth * 0.95f));
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("TrunkGrowth"),
        TEXT("AxillaryChildGrowth"),
        bBranchletGrower ? 0.28f : 0.0f);
    bConfigured &= SetPveNestedBool(
        Settings,
        TEXT("GrowerParams"),
        TEXT("TrunkGrowth"),
        TEXT("bAxillaryRetry"),
        true);
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("TrunkGrowth"),
        TEXT("ApicalParentGrowth"),
        bBranchletGrower ? 1.15f : 1.25f);
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("TrunkGrowth"),
        TEXT("ApicalChildGrowth"),
        bBranchletGrower ? 0.76f : 0.82f);
    bConfigured &= SetPveNestedText(
        Settings,
        TEXT("GrowerParams"),
        TEXT("TrunkGrowth"),
        TEXT("AxillaryRampBasis"),
        TEXT("PlantTargetLength"));
    bConfigured &= SetPveNestedText(
        Settings,
        TEXT("GrowerParams"),
        TEXT("TrunkGrowth"),
        TEXT("ApicalRampBasis"),
        TEXT("PlantTargetLength"));
    bConfigured &= SetPveNestedBool(
        Settings,
        TEXT("GrowerParams"),
        TEXT("TrunkGrowth"),
        TEXT("bAxillaryUseChildGradient"),
        true);
    bConfigured &= SetPveNestedBool(
        Settings,
        TEXT("GrowerParams"),
        TEXT("TrunkGrowth"),
        TEXT("bApicalUseChildGradient"),
        true);
    bConfigured &= SetPveNestedText(
        Settings,
        TEXT("GrowerParams"),
        TEXT("TrunkGrowth"),
        TEXT("AxillaryChildRampBasis"),
        TEXT("BranchTargetLength"));
    bConfigured &= SetPveNestedText(
        Settings,
        TEXT("GrowerParams"),
        TEXT("TrunkGrowth"),
        TEXT("ApicalChildRampBasis"),
        TEXT("BranchTargetLength"));
    bConfigured &= SetPveNestedRamp(
        Settings,
        TEXT("GrowerParams"),
        TEXT("TrunkGrowth"),
        TEXT("AxillaryPriorityGradient"),
        bBranchletGrower
            ? (AsyncBranchTemplateIndex == 1
                ? TArray<FVector2f>{{0.0f, 0.08f}, {0.16f, 0.72f}, {0.38f, 0.24f}, {0.61f, 0.86f}, {0.84f, 0.42f}, {1.0f, 0.18f}}
                : (AsyncBranchTemplateIndex == 2
                    ? TArray<FVector2f>{{0.0f, 0.18f}, {0.25f, 0.42f}, {0.47f, 0.82f}, {0.68f, 0.30f}, {0.90f, 0.76f}, {1.0f, 0.16f}}
                    : TArray<FVector2f>{{0.0f, 0.15f}, {0.22f, 0.86f}, {0.82f, 0.72f}, {1.0f, 0.34f}}))
            : (bDeTieredMain
                ? TArray<FVector2f>{{0.0f, 0.0f}, {0.08f, 0.18f}, {0.18f, 0.68f}, {0.52f, 0.88f}, {0.78f, 0.74f}, {1.0f, 0.22f}}
                : TArray<FVector2f>{{0.0f, 0.0f}, {0.12f, 0.0f}, {0.18f, 0.64f}, {0.72f, 0.84f}, {1.0f, 0.56f}}));
    bConfigured &= SetPveNestedRamp(
        Settings,
        TEXT("GrowerParams"),
        TEXT("TrunkGrowth"),
        TEXT("AxillaryPriorityChildGradient"),
        TArray<FVector2f>{{0.0f, 0.12f}, {0.18f, 0.82f}, {0.78f, 0.68f}, {1.0f, 0.28f}});
    bConfigured &= SetPveNestedRamp(
        Settings,
        TEXT("GrowerParams"),
        TEXT("TrunkGrowth"),
        TEXT("ApicalPriorityGradient"),
        TArray<FVector2f>{{0.0f, 1.0f}, {0.86f, 1.0f}, {1.0f, 0.08f}});
    bConfigured &= SetPveNestedRamp(
        Settings,
        TEXT("GrowerParams"),
        TEXT("TrunkGrowth"),
        TEXT("ApicalPriorityChildGradient"),
        TArray<FVector2f>{{0.0f, 1.0f}, {0.72f, 0.78f}, {1.0f, 0.05f}});

    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("Phyllotaxy"),
        TEXT("AxilAngle"),
        bBranchletGrower ? 12.0f : Spec.PrimaryAxilAngle);
    bConfigured &= SetPveNestedText(
        Settings,
        TEXT("GrowerParams"),
        TEXT("Phyllotaxy"),
        TEXT("Type"),
        bBranchletGrower ? TEXT("Alternate") : TEXT("Spiral"));
    bConfigured &= SetPveNestedText(
        Settings,
        TEXT("GrowerParams"),
        TEXT("Phyllotaxy"),
        TEXT("Formation"),
        TEXT("Pentasticious"));
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("Phyllotaxy"),
        TEXT("AdditionalAngle"),
        bBranchletGrower
            ? (AsyncBranchTemplateIndex == 1
                ? 71.0f
                : (AsyncBranchTemplateIndex == 2 ? 223.5f : 4.0f))
            : (bDeTieredMain ? 137.507764f : 7.5f));
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("Phyllotaxy"),
        TEXT("Offset"),
        FMath::Fmod(
            static_cast<float>(Spec.Seed) * 0.013f +
                static_cast<float>(AsyncBranchTemplateIndex) * 113.0f,
            360.0f));
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("Phyllotaxy"),
        TEXT("Flatten"),
        bBranchletGrower ? 0.88f : 0.0f);
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("Phyllotaxy"),
        TEXT("Stagger"),
        bBranchletGrower
            ? (AsyncBranchTemplateIndex == 1
                ? 0.07f
                : (AsyncBranchTemplateIndex == 2 ? 0.10f : 0.04f))
            : (bDeTieredMain ? 0.14f : 0.035f));
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("BranchPhyllotaxy"),
        TEXT("AxilAngle"),
        bBranchletGrower ? 58.0f : 54.0f);
    bConfigured &= SetPveNestedText(
        Settings,
        TEXT("GrowerParams"),
        TEXT("BranchPhyllotaxy"),
        TEXT("Type"),
        TEXT("Alternate"));
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("BranchPhyllotaxy"),
        TEXT("Flatten"),
        bBranchletGrower ? 0.92f : (bDeTieredMain ? 0.60f : 0.78f));
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("BranchPhyllotaxy"),
        TEXT("Stagger"),
        bBranchletGrower ? 0.04f : (bDeTieredMain ? 0.16f : 0.08f));
    bConfigured &= SetPveNestedBool(
        Settings,
        TEXT("GrowerParams"),
        TEXT("BranchPhyllotaxy"),
        TEXT("bReset"),
        true);

    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("Auxin"),
        TEXT("AuxinFalloff"),
        bBranchletGrower ? 0.42f : 0.35f);
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("Auxin"),
        TEXT("ApicalDominance"),
        bBranchletGrower ? 0.32f : 0.42f);
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("Auxin"),
        TEXT("RadicalAuxin"),
        bBranchletGrower ? 0.04f : 0.38f);
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("BranchAuxin"),
        TEXT("AuxinFalloff"),
        bBranchletGrower ? 0.42f : 0.35f);
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("BranchAuxin"),
        TEXT("ApicalDominance"),
        bBranchletGrower ? 0.24f : 0.48f);

    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("Phototropism"),
        TEXT("Apical"),
        bBranchletGrower ? 0.08f : 0.02f);
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("Phototropism"),
        TEXT("Axillary"),
        bBranchletGrower ? 0.18f : 0.08f);
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("Phototropism"),
        TEXT("LightRequirement"),
        bBranchletGrower ? 0.08f : 0.12f);
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),

        TEXT("BranchPhototropism"),
        TEXT("Apical"),
        bBranchletGrower ? 0.08f : 0.04f);
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("BranchPhototropism"),
        TEXT("Axillary"),
        bBranchletGrower ? 0.16f : 0.08f);
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("BranchPhototropism"),
        TEXT("LightRequirement"),
        0.08f);

    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("Directional"),
        TEXT("ApicalRandomAngle"),
        bBranchletGrower ? 1.5f : (bDeTieredMain ? 1.5f : Spec.ApicalRandomAngle));
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("Directional"),
        TEXT("AxillaryRandomAngle"),
        bBranchletGrower ? 5.0f : (bDeTieredMain ? 12.0f : Spec.AxillaryRandomAngle));
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("BranchDirectional"),
        TEXT("ApicalRandomAngle"),
        bBranchletGrower ? 2.5f : FMath::Max(1.0f, Spec.ApicalRandomAngle * 0.75f));
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("BranchDirectional"),
        TEXT("AxillaryRandomAngle"),
        bBranchletGrower ? 7.0f : (bDeTieredMain ? 15.0f : Spec.AxillaryRandomAngle));
    bConfigured &= SetPveNestedInt(
        Settings,
        TEXT("GrowerParams"),
        TEXT("Foliage"),
        TEXT("Density"),
        bBranchletGrower ? 2 : 1);
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("Foliage"),
        TEXT("EthyleneBuildup"),
        0.04f);
    bConfigured &= SetPveNestedFloat(
        Settings,
        TEXT("GrowerParams"),
        TEXT("Foliage"),
        TEXT("EthyleneThreshold"),
        0.82f);
    return bConfigured;
}

} // namespace RaftSimEditorPve


#undef LogRaftSimEditor
#undef LOCTEXT_NAMESPACE
