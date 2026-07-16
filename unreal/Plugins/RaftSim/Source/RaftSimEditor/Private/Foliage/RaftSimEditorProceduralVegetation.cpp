#include "RaftSimEditorModule.h"
#include "Foliage/RaftSimEditorFoliageInternal.h"

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

DEFINE_LOG_CATEGORY_STATIC(LogRaftSimEditor, Log, All);

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


namespace
{
void AddPreviewLightRig(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec)
{
    RaftSimEditorFoliage::AddPvePreviewLightRig(World, Spec);
}

template <typename... TArgs>
decltype(auto) CapturePreviewImageForSpec(TArgs&&... Args)
{
    return RaftSimEditorFoliage::CapturePvePreviewImageForSpec(
        Forward<TArgs>(Args)...);
}

template <typename... TArgs>
decltype(auto) CaptureFutaleufuComplementaryTransitionMotionSequence(
    TArgs&&... Args)
{
    return RaftSimEditorFoliage::
        CapturePveFutaleufuComplementaryTransitionMotionSequence(
            Forward<TArgs>(Args)...);
}

struct FFutaleufuCypressPveFormSpec
{
    FString Id;
    FString DisplayName;
    FString AssetToken;
    FString LifeStage;
    int32 Seed = 0;
    float WholeTreeScale = 1.0f;
    float LiveTwigScale = 1.0f;
    float BranchScale = 0.8f;
    float PrimaryAxilAngle = 72.0f;
    float AxillaryParentGrowth = 1.4f;
    float AxillaryChildGrowth = 1.2f;
    int32 GraftDensity = 20;
    float GraftRelativeStart = 0.1f;
    bool bAllowSenescence = false;
    float ApicalRandomAngle = 2.0f;
    float AxillaryRandomAngle = 5.0f;
    float GravityStrength = 0.2f;
    float GravityAngleCorrection = 0.65f;
};

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

enum class EPveAtlasMaterialLayer : uint8
{
    Combined,
    Trunk,
    Foliage,
};

struct FRaftSimPveMultiViewAtlasBakeResult
{
    bool bAtlasFilesSaved = false;
    bool bTextureAssetsSaved = false;
    bool bMaterialSaved = false;
    bool bRelightableMaterialSaved = false;
    bool bRelightableTrunkMaterialSaved = false;
    bool bRelightableFoliageMaterialSaved = false;
    bool bProxyActorCreated = false;
    int32 ViewCount = 0;
    int32 TileResolution = 0;
    int32 AtlasResolution = 0;
    float OrthoWidthCm = 0.0f;
    float AzimuthOffsetDegrees = 0.0f;
    bool bPerspectiveCapture = false;
    float CaptureRadiusCm = 0.0f;
    float PerspectiveHorizontalFovDegrees = 0.0f;
    bool bDepthParallaxEnabled = false;
    float DepthParallaxScaleCm = 0.0f;
    bool bComplementaryTransitionEnabled = false;
    int32 ProxyVertexCount = 0;
    int32 ProxyTriangleCount = 0;
    int64 MaterialIdentityFallbackPixelCount = 0;
    float MinimumCoverage = 1.0f;
    float MaximumCoverage = 0.0f;
    FLinearColor ColorGain = FLinearColor::White;
    FString OpacitySource;
    FString ManifestRelativePath;
    FString BaseColorRelativePath;
    FString AlbedoRelativePath;
    FString NormalRelativePath;
    FString OpacityRelativePath;
    FString DepthRelativePath;
    FString MaterialIdentityRelativePath;
    FString BaseColorDigest;
    FString AlbedoDigest;
    FString NormalDigest;
    FString OpacityDigest;
    FString DepthDigest;
    FString MaterialIdentityDigest;
    FString BaseColorAssetPath;
    FString AlbedoAssetPath;
    FString NormalAssetPath;
    FString OpacityAssetPath;
    FString DepthAssetPath;
    FString MaterialIdentityAssetPath;
    FString MaterialAssetPath;
    FString RelightableMaterialAssetPath;
    FString RelightableTrunkMaterialAssetPath;
    FString RelightableFoliageMaterialAssetPath;
    UMaterial* Material = nullptr;
    UMaterial* RelightableMaterial = nullptr;
    UMaterial* RelightableTrunkMaterial = nullptr;
    UMaterial* RelightableFoliageMaterial = nullptr;
    AStaticMeshActor* ProxyActor = nullptr;

    bool IsReady() const
    {
        return bAtlasFilesSaved && bTextureAssetsSaved && bMaterialSaved &&
            bProxyActorCreated && ViewCount == 16 &&
            (TileResolution == 512 || TileResolution == 1024) &&
            AtlasResolution == TileResolution * 4 && MinimumCoverage >= 0.002f &&
            MaximumCoverage <= 0.85f &&
            (!bDepthParallaxEnabled ||
             (ProxyVertexCount == 1089 && ProxyTriangleCount == 2048));
    }

    bool IsRelightableReady() const
    {
        return IsReady() && bRelightableMaterialSaved &&
            !AlbedoRelativePath.IsEmpty() && !AlbedoDigest.IsEmpty() &&
            !AlbedoAssetPath.IsEmpty() && !MaterialIdentityRelativePath.IsEmpty() &&
            !MaterialIdentityDigest.IsEmpty() && !MaterialIdentityAssetPath.IsEmpty() &&
            !RelightableMaterialAssetPath.IsEmpty() &&
            RelightableMaterial != nullptr;
    }

    bool IsSplitRelightableReady() const
    {
        return IsRelightableReady() && bRelightableTrunkMaterialSaved &&
            bRelightableFoliageMaterialSaved &&
            !RelightableTrunkMaterialAssetPath.IsEmpty() &&
            !RelightableFoliageMaterialAssetPath.IsEmpty() &&
            RelightableTrunkMaterial != nullptr &&
            RelightableFoliageMaterial != nullptr;
    }
};

bool SavePveAtlasPng(
    const FString& AbsolutePath,
    int32 Width,
    int32 Height,
    const TArray<FColor>& Pixels)
{
    if (Width <= 0 || Height <= 0 || Pixels.Num() != Width * Height)
    {
        return false;
    }
    TArray64<uint8> CompressedPng;
    FImageUtils::PNGCompressImageArray(
        Width,
        Height,
        MakeArrayView(Pixels),
        CompressedPng);
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(AbsolutePath), true);
    return !CompressedPng.IsEmpty() &&
        FFileHelper::SaveArrayToFile(CompressedPng, *AbsolutePath);
}

void DilatePveAtlasTileRgb(
    TArray<FColor>& Pixels,
    int32 AtlasWidth,
    int32 TileOriginX,
    int32 TileOriginY,
    int32 TileSize,
    int32 Iterations)
{
    if (Pixels.Num() != AtlasWidth * AtlasWidth || TileSize <= 0 || Iterations <= 0)
    {
        return;
    }
    TArray<uint8> Filled;
    Filled.SetNumZeroed(TileSize * TileSize);
    for (int32 Y = 0; Y < TileSize; ++Y)
    {
        for (int32 X = 0; X < TileSize; ++X)
        {
            Filled[Y * TileSize + X] =
                Pixels[(TileOriginY + Y) * AtlasWidth + TileOriginX + X].A > 0 ? 1 : 0;
        }
    }
    static const FIntPoint Neighbors[] = {
        FIntPoint(-1, 0), FIntPoint(1, 0), FIntPoint(0, -1), FIntPoint(0, 1),
        FIntPoint(-1, -1), FIntPoint(1, -1), FIntPoint(-1, 1), FIntPoint(1, 1)};
    for (int32 Iteration = 0; Iteration < Iterations; ++Iteration)
    {
        const TArray<uint8> PreviousFilled = Filled;
        const TArray<FColor> PreviousPixels = Pixels;
        bool bChanged = false;
        for (int32 Y = 0; Y < TileSize; ++Y)
        {
            for (int32 X = 0; X < TileSize; ++X)
            {
                const int32 LocalIndex = Y * TileSize + X;
                if (PreviousFilled[LocalIndex])
                {
                    continue;
                }
                int32 Red = 0;
                int32 Green = 0;
                int32 Blue = 0;
                int32 Count = 0;
                for (const FIntPoint& Offset : Neighbors)
                {
                    const int32 NeighborX = X + Offset.X;
                    const int32 NeighborY = Y + Offset.Y;
                    if (NeighborX < 0 || NeighborY < 0 ||
                        NeighborX >= TileSize || NeighborY >= TileSize ||
                        !PreviousFilled[NeighborY * TileSize + NeighborX])
                    {
                        continue;
                    }
                    const FColor& Neighbor = PreviousPixels[
                        (TileOriginY + NeighborY) * AtlasWidth + TileOriginX + NeighborX];
                    Red += Neighbor.R;
                    Green += Neighbor.G;
                    Blue += Neighbor.B;
                    ++Count;
                }
                if (Count > 0)
                {
                    FColor& Pixel = Pixels[
                        (TileOriginY + Y) * AtlasWidth + TileOriginX + X];
                    Pixel.R = static_cast<uint8>(Red / Count);
                    Pixel.G = static_cast<uint8>(Green / Count);
                    Pixel.B = static_cast<uint8>(Blue / Count);
                    Filled[LocalIndex] = 1;
                    bChanged = true;
                }
            }
        }
        if (!bChanged)
        {
            break;
        }
    }
}

UTexture2D* CreateOrUpdateLocalPveAtlasTexture(
    const FString& PackagePath,
    const TArray<FColor>& Pixels,
    int32 Resolution,
    TextureCompressionSettings CompressionSettings,
    bool bSrgb,
    bool bScaleAlphaCoverage,
    FString& OutSummary)
{
    if (Pixels.Num() != Resolution * Resolution || Resolution <= 0)
    {
        OutSummary += FString::Printf(TEXT("Invalid local PVE atlas pixels for %s.\n"), *PackagePath);
        return nullptr;
    }
    const FString AssetName = FPackageName::GetLongPackageAssetName(PackagePath);
    const FString ObjectPath = FString::Printf(TEXT("%s.%s"), *PackagePath, *AssetName);
    UTexture2D* Texture = LoadObject<UTexture2D>(nullptr, *ObjectPath);
    UPackage* Package = Texture ? Texture->GetOutermost() : CreatePackage(*PackagePath);
    if (!Package)
    {
        OutSummary += FString::Printf(TEXT("Could not create local PVE atlas package %s.\n"), *PackagePath);
        return nullptr;
    }
    if (!Texture)
    {
        Texture = NewObject<UTexture2D>(
            Package,
            *AssetName,
            RF_Public | RF_Standalone | RF_Transactional);
        if (Texture)
        {
            FAssetRegistryModule::AssetCreated(Texture);
        }
    }
    if (!Texture)
    {
        OutSummary += FString::Printf(TEXT("Could not create local PVE atlas texture %s.\n"), *ObjectPath);
        return nullptr;
    }

    Texture->Modify();
    Texture->Source.Init(Resolution, Resolution, 1, 1, TSF_BGRA8);
    uint8* MipData = Texture->Source.LockMip(0);
    for (int64 PixelIndex = 0; PixelIndex < Pixels.Num(); ++PixelIndex)
    {
        const FColor& Pixel = Pixels[PixelIndex];
        *MipData++ = Pixel.B;
        *MipData++ = Pixel.G;
        *MipData++ = Pixel.R;
        *MipData++ = Pixel.A;
    }
    Texture->Source.UnlockMip(0);
    Texture->SRGB = bSrgb;
    Texture->CompressionSettings = CompressionSettings;
    Texture->CompressionNoAlpha = !bScaleAlphaCoverage;
    Texture->MipGenSettings = TMGS_Sharpen4;
    Texture->LODGroup = bSrgb
        ? TEXTUREGROUP_Impostor
        : TEXTUREGROUP_ImpostorNormalDepth;
    Texture->AddressX = TA_Clamp;
    Texture->AddressY = TA_Clamp;
    Texture->VirtualTextureStreaming = false;
    // Exact-camera review runs immediately after generation, so the atlas must not
    // briefly fall back to a low resident mip while texture streaming catches up.

    Texture->NeverStream = true;
    Texture->bDoScaleMipsForAlphaCoverage = bScaleAlphaCoverage;
    Texture->AlphaCoverageThresholds = bScaleAlphaCoverage
        ? FVector4(0.0f, 0.0f, 0.0f, 0.38f)
        : FVector4::Zero();
    Texture->SetModernSettingsForNewOrChangedTexture();
    Texture->PostEditChange();
    Texture->MarkPackageDirty();
    Package->MarkPackageDirty();

    const FString Filename = FPackageName::LongPackageNameToFilename(
        PackagePath,
        FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Texture, *Filename, SaveArgs))
    {
        OutSummary += FString::Printf(TEXT("Could not save local PVE atlas texture %s.\n"), *ObjectPath);
        return nullptr;
    }
    OutSummary += FString::Printf(TEXT("Saved local PVE atlas texture %s.\n"), *ObjectPath);
    return Texture;
}

UMaterial* CreateOrUpdateLocalPveAtlasMaterial(
    const FString& PackagePath,
    UTexture2D* BaseColorTexture,
    UTexture2D* NormalTexture,
    UTexture2D* OpacityTexture,
    UTexture2D* DepthTexture,
    UTexture2D* MaterialIdentityTexture,
    bool bUseColorCorrectShading,
    const FLinearColor& AtlasColorGainDefault,
    float AtlasAzimuthOffsetDegrees,
    bool bUseDepthParallax,
    float DepthParallaxScaleCm,
    bool bEnableComplementaryTransition,
    bool bUseLitShading,
    EPveAtlasMaterialLayer MaterialLayer,
    FString& OutSummary)
{
    if (!BaseColorTexture || !NormalTexture || !OpacityTexture || !DepthTexture ||
        !MaterialIdentityTexture)
    {
        OutSummary += TEXT(
            "Local PVE atlas material is missing color, normal, depth, opacity, or material-identity texture.\n");
        return nullptr;
    }
    const FString AssetName = FPackageName::GetLongPackageAssetName(PackagePath);
    const FString ObjectPath = FString::Printf(TEXT("%s.%s"), *PackagePath, *AssetName);
    UMaterial* Material = LoadObject<UMaterial>(nullptr, *ObjectPath);
    UPackage* Package = Material ? Material->GetOutermost() : CreatePackage(*PackagePath);
    if (!Package)
    {
        OutSummary += FString::Printf(TEXT("Could not create local PVE atlas material package %s.\n"), *PackagePath);
        return nullptr;
    }
    if (!Material)
    {
        Material = NewObject<UMaterial>(
            Package,
            *AssetName,
            RF_Public | RF_Standalone | RF_Transactional);
        if (Material)
        {
            FAssetRegistryModule::AssetCreated(Material);
        }
    }
    if (!Material)
    {
        OutSummary += FString::Printf(TEXT("Could not create local PVE atlas material %s.\n"), *ObjectPath);
        return nullptr;
    }

    Material->Modify();
    Material->GetExpressionCollection().Empty();
    const bool bTrunkLayer = MaterialLayer == EPveAtlasMaterialLayer::Trunk;
    const bool bFoliageLayer = MaterialLayer == EPveAtlasMaterialLayer::Foliage;
    Material->SetShadingModel(
        bUseLitShading
            ? (bFoliageLayer ? MSM_TwoSidedFoliage : MSM_DefaultLit)
            : MSM_Unlit);
    Material->BlendMode = BLEND_Masked;
    Material->TwoSided = true;
    Material->bTangentSpaceNormal = !bUseLitShading;
    Material->DitheredLODTransition = true;
    Material->OpacityMaskClipValue = 0.38f;

    auto AddExpression = [Material](auto* Expression, int32 EditorX, int32 EditorY)
    {
        Expression->MaterialExpressionEditorX = EditorX;
        Expression->MaterialExpressionEditorY = EditorY;
        Material->GetExpressionCollection().AddExpression(Expression);
        return Expression;
    };
    UMaterialExpressionTextureCoordinate* TexCoord =
        AddExpression(NewObject<UMaterialExpressionTextureCoordinate>(Material), -1400, -480);
    UMaterialExpressionWorldPosition* WorldPosition =
        AddExpression(NewObject<UMaterialExpressionWorldPosition>(Material), -1400, 520);
    WorldPosition->WorldPositionShaderOffset = WPT_ExcludeAllShaderOffsets;
    UMaterialExpressionObjectPositionWS* ObjectPosition =
        AddExpression(NewObject<UMaterialExpressionObjectPositionWS>(Material), -1400, 700);
    UMaterialExpressionCameraPositionWS* CameraPosition =
        AddExpression(NewObject<UMaterialExpressionCameraPositionWS>(Material), -1400, 880);
    UMaterialExpressionScalarParameter* AtlasAzimuthOffsetTurns =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), -1400, -240);
    AtlasAzimuthOffsetTurns->ParameterName = TEXT("AtlasAzimuthOffsetTurns");
    AtlasAzimuthOffsetTurns->DefaultValue = AtlasAzimuthOffsetDegrees / 360.0f;
    UMaterialExpressionScalarParameter* AtlasFrameOverride =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), -1400, -60);
    AtlasFrameOverride->ParameterName = TEXT("AtlasFrameOverride");
    AtlasFrameOverride->DefaultValue = -1.0f;
    AtlasFrameOverride->SliderMin = -1.0f;
    AtlasFrameOverride->SliderMax = 15.0f;

    UMaterialExpressionCustom* AtlasUv =
        AddExpression(NewObject<UMaterialExpressionCustom>(Material), -1060, -420);
    AtlasUv->Description = TEXT("Select nearest 8x2 upper-hemisphere frame in a 4x4 atlas");
    AtlasUv->OutputType = CMOT_Float2;
    AtlasUv->Code =
        TEXT("float3 ViewToCamera = normalize((float3)(CameraPos - ObjectPos));\n")
        TEXT("float Azimuth = atan2(ViewToCamera.y, ViewToCamera.x);\n")
        TEXT("float NormalizedAzimuth = frac(Azimuth / 6.28318530718 - AzimuthOffsetTurns + 1.0);\n")
        TEXT("float AzimuthFrame = floor(NormalizedAzimuth * 8.0 + 0.5);\n")
        TEXT("AzimuthFrame -= floor(AzimuthFrame / 8.0) * 8.0;\n")
        TEXT("float ElevationFrame = ViewToCamera.z > 0.2164396149 ? 1.0 : 0.0;\n")
        TEXT("float AutomaticFrame = ElevationFrame * 8.0 + AzimuthFrame;\n")
        TEXT("float Frame = FrameOverride >= -0.5 ? clamp(floor(FrameOverride + 0.5), 0.0, 15.0) : AutomaticFrame;\n")
        TEXT("float2 Cell = float2(Frame - floor(Frame / 4.0) * 4.0, floor(Frame / 4.0));\n")
        TEXT("float2 PlaneUv = float2(UV.x, 1.0 - UV.y);\n")
        TEXT("return (clamp(PlaneUv, 0.001, 0.999) + Cell) * 0.25;");
    FCustomInput& AtlasUvInput = AtlasUv->Inputs.AddDefaulted_GetRef();
    AtlasUvInput.InputName = TEXT("UV");
    AtlasUvInput.Input.Expression = TexCoord;
    FCustomInput& AtlasObjectInput = AtlasUv->Inputs.AddDefaulted_GetRef();
    AtlasObjectInput.InputName = TEXT("ObjectPos");
    AtlasObjectInput.Input.Expression = ObjectPosition;
    FCustomInput& AtlasCameraInput = AtlasUv->Inputs.AddDefaulted_GetRef();
    AtlasCameraInput.InputName = TEXT("CameraPos");
    AtlasCameraInput.Input.Expression = CameraPosition;
    FCustomInput& AtlasAzimuthOffsetInput = AtlasUv->Inputs.AddDefaulted_GetRef();
    AtlasAzimuthOffsetInput.InputName = TEXT("AzimuthOffsetTurns");
    AtlasAzimuthOffsetInput.Input.Expression = AtlasAzimuthOffsetTurns;
    FCustomInput& AtlasFrameOverrideInput = AtlasUv->Inputs.AddDefaulted_GetRef();
    AtlasFrameOverrideInput.InputName = TEXT("FrameOverride");
    AtlasFrameOverrideInput.Input.Expression = AtlasFrameOverride;

    UMaterialExpressionTextureSampleParameter2D* DepthSample = nullptr;
    UMaterialExpressionScalarParameter* DepthScale = nullptr;
    if (bUseDepthParallax)
    {
        DepthSample = AddExpression(
            NewObject<UMaterialExpressionTextureSampleParameter2D>(Material),
            -860,
            360);
        DepthSample->ParameterName = TEXT("AtlasDepth");
        DepthSample->Texture = DepthTexture;
        DepthSample->SamplerType = SAMPLERTYPE_LinearGrayscale;
        DepthSample->Coordinates.Expression = AtlasUv;
        DepthSample->MipValueMode = TMVM_MipLevel;
        DepthSample->ConstMipValue = 0;
        DepthScale = AddExpression(
            NewObject<UMaterialExpressionScalarParameter>(Material),
            -860,
            500);
        DepthScale->ParameterName = TEXT("AtlasDepthParallaxScaleCm");
        DepthScale->DefaultValue = DepthParallaxScaleCm;
    }

    UMaterialExpressionCustom* BillboardOffset =
        AddExpression(NewObject<UMaterialExpressionCustom>(Material), -900, 620);
    BillboardOffset->Description = TEXT("Rotate the source XY plane toward the active camera");
    BillboardOffset->OutputType = CMOT_Float3;
    BillboardOffset->Code = bUseDepthParallax
        ? TEXT("float3 ViewToCamera = normalize((float3)(CameraPos - ObjectPos));\n")
          TEXT("float3 Forward = -ViewToCamera;\n")
          TEXT("float3 Right = normalize(cross(float3(0.0, 0.0, 1.0), Forward));\n")
          TEXT("float3 Up = normalize(cross(Forward, Right));\n")
          TEXT("float3 LocalDelta = (float3)(WorldPos - ObjectPos);\n")
          TEXT("float DepthCentered = saturate(Depth.r) - 0.5;\n")
          TEXT("float3 BillboardPos = (float3)ObjectPos + Right * LocalDelta.x + Up * LocalDelta.y - Forward * DepthCentered * DepthScaleCm;\n")
          TEXT("return BillboardPos - (float3)WorldPos;")
        : TEXT("float3 ViewToCamera = normalize((float3)(CameraPos - ObjectPos));\n")
          TEXT("float3 Forward = -ViewToCamera;\n")
          TEXT("float3 Right = normalize(cross(float3(0.0, 0.0, 1.0), Forward));\n")
          TEXT("float3 Up = normalize(cross(Forward, Right));\n")
          TEXT("float3 LocalDelta = (float3)(WorldPos - ObjectPos);\n")
          TEXT("float3 BillboardPos = (float3)ObjectPos + Right * LocalDelta.x + Up * LocalDelta.y;\n")
          TEXT("return BillboardPos - (float3)WorldPos;");
    FCustomInput& BillboardWorldInput = BillboardOffset->Inputs.AddDefaulted_GetRef();
    BillboardWorldInput.InputName = TEXT("WorldPos");
    BillboardWorldInput.Input.Expression = WorldPosition;
    FCustomInput& BillboardObjectInput = BillboardOffset->Inputs.AddDefaulted_GetRef();
    BillboardObjectInput.InputName = TEXT("ObjectPos");
    BillboardObjectInput.Input.Expression = ObjectPosition;
    FCustomInput& BillboardCameraInput = BillboardOffset->Inputs.AddDefaulted_GetRef();
    BillboardCameraInput.InputName = TEXT("CameraPos");
    BillboardCameraInput.Input.Expression = CameraPosition;
    if (bUseDepthParallax)
    {
        FCustomInput& BillboardDepthInput = BillboardOffset->Inputs.AddDefaulted_GetRef();
        BillboardDepthInput.InputName = TEXT("Depth");
        BillboardDepthInput.Input.Expression = DepthSample;
        FCustomInput& BillboardDepthScaleInput = BillboardOffset->Inputs.AddDefaulted_GetRef();
        BillboardDepthScaleInput.InputName = TEXT("DepthScaleCm");
        BillboardDepthScaleInput.Input.Expression = DepthScale;
    }

    UMaterialExpressionTextureSampleParameter2D* BaseColorSample =
        AddExpression(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -620, -520);
    BaseColorSample->ParameterName = TEXT("AtlasBaseColorOpacity");
    BaseColorSample->Texture = BaseColorTexture;
    BaseColorSample->SamplerType = SAMPLERTYPE_Color;
    BaseColorSample->Coordinates.Expression = AtlasUv;
    UMaterialExpressionTextureSampleParameter2D* OpacitySample =
        AddExpression(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -620, -320);
    OpacitySample->ParameterName = TEXT("AtlasOpacity");
    OpacitySample->Texture = OpacityTexture;
    OpacitySample->SamplerType = SAMPLERTYPE_LinearGrayscale;
    OpacitySample->Coordinates.Expression = AtlasUv;
    UMaterialExpressionTextureSampleParameter2D* MaterialIdentitySample =
        AddExpression(
            NewObject<UMaterialExpressionTextureSampleParameter2D>(Material),
            -620,
            -200);
    MaterialIdentitySample->ParameterName = TEXT("AtlasMaterialIdentity");
    MaterialIdentitySample->Texture = MaterialIdentityTexture;
    MaterialIdentitySample->SamplerType = SAMPLERTYPE_LinearGrayscale;
    MaterialIdentitySample->Coordinates.Expression = AtlasUv;
    UMaterialExpressionComponentMask* AtlasFoliageMask =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), -420, -180);
    AtlasFoliageMask->Input.Expression = MaterialIdentitySample;
    AtlasFoliageMask->R = true;
    UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData();
    UMaterialExpression* ConditionedColor = BaseColorSample;
    if (bUseColorCorrectShading)
    {
        UMaterialExpressionVectorParameter* AtlasColorGain =
            AddExpression(NewObject<UMaterialExpressionVectorParameter>(Material), -300, -520);
        AtlasColorGain->ParameterName = TEXT("AtlasColorGain");
        AtlasColorGain->DefaultValue = AtlasColorGainDefault;
        UMaterialExpressionMultiply* BaseGainColor =
            AddExpression(NewObject<UMaterialExpressionMultiply>(Material), -60, -540);
        BaseGainColor->A.Expression = BaseColorSample;
        BaseGainColor->B.Expression = AtlasColorGain;
        UMaterialExpressionScalarParameter* AtlasTrunkGainMultiplier =
            AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), -300, -720);
        AtlasTrunkGainMultiplier->ParameterName = TEXT("AtlasTrunkGainMultiplier");
        AtlasTrunkGainMultiplier->DefaultValue = 1.0f;
        AtlasTrunkGainMultiplier->SliderMin = 0.5f;
        AtlasTrunkGainMultiplier->SliderMax = 2.5f;
        UMaterialExpressionScalarParameter* AtlasFoliageGainMultiplier =
            AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), -300, -640);
        AtlasFoliageGainMultiplier->ParameterName = TEXT("AtlasFoliageGainMultiplier");
        AtlasFoliageGainMultiplier->DefaultValue = 1.0f;
        AtlasFoliageGainMultiplier->SliderMin = 0.5f;
        AtlasFoliageGainMultiplier->SliderMax = 2.5f;
        UMaterialExpressionLinearInterpolate* MaterialGainMultiplier =
            AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), -20, -660);
        MaterialGainMultiplier->A.Expression = AtlasTrunkGainMultiplier;
        MaterialGainMultiplier->B.Expression = AtlasFoliageGainMultiplier;
        MaterialGainMultiplier->Alpha.Expression = AtlasFoliageMask;
        UMaterialExpressionMultiply* ConditionedAtlasColor =
            AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 180, -520);
        ConditionedAtlasColor->A.Expression = BaseGainColor;
        ConditionedAtlasColor->B.Expression = MaterialGainMultiplier;
        ConditionedColor = ConditionedAtlasColor;
    }
    if (bUseLitShading)
    {
        ConnectPreviewMaterialColorInput(EditorOnlyData->BaseColor, ConditionedColor);
        UMaterialExpressionTextureSampleParameter2D* WorldNormalSample =
            AddExpression(
                NewObject<UMaterialExpressionTextureSampleParameter2D>(Material),
                -620,
                -80);
        WorldNormalSample->ParameterName = TEXT("AtlasWorldNormal");
        WorldNormalSample->Texture = NormalTexture;
        WorldNormalSample->SamplerType = SAMPLERTYPE_LinearColor;
        WorldNormalSample->Coordinates.Expression = AtlasUv;
        UMaterialExpressionCustom* DecodedWorldNormal =
            AddExpression(NewObject<UMaterialExpressionCustom>(Material), -300, -40);
        DecodedWorldNormal->Description = TEXT(
            "Decode the captured world-space source normal for relighting");
        DecodedWorldNormal->OutputType = CMOT_Float3;
        DecodedWorldNormal->Code =
            TEXT("return normalize(WorldNormal.rgb * 2.0 - 1.0);");
        FCustomInput& WorldNormalInput =
            DecodedWorldNormal->Inputs.AddDefaulted_GetRef();
        WorldNormalInput.InputName = TEXT("WorldNormal");
        WorldNormalInput.Input.Expression = WorldNormalSample;
        ConnectPreviewMaterialVectorInput(EditorOnlyData->Normal, DecodedWorldNormal);
        if (bFoliageLayer)
        {
            UMaterialExpressionVectorParameter* AtlasFoliageTransmissionTint =
                AddExpression(
                    NewObject<UMaterialExpressionVectorParameter>(Material),
                    180,
                    20);
            AtlasFoliageTransmissionTint->ParameterName =
                TEXT("AtlasFoliageTransmissionTint");
            AtlasFoliageTransmissionTint->DefaultValue =
                FLinearColor(0.78f, 1.0f, 0.58f, 1.0f);
            UMaterialExpressionMultiply* AtlasFoliageSubsurfaceColor =
                AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 420, 20);
            AtlasFoliageSubsurfaceColor->A.Expression = ConditionedColor;
            AtlasFoliageSubsurfaceColor->B.Expression =
                AtlasFoliageTransmissionTint;
            ConnectPreviewMaterialColorInput(
                EditorOnlyData->SubsurfaceColor,
                AtlasFoliageSubsurfaceColor);
        }

        UMaterialExpressionScalarParameter* AtlasTrunkRoughness =
            AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), -60, 180);
        AtlasTrunkRoughness->ParameterName = TEXT("AtlasTrunkRoughness");
        AtlasTrunkRoughness->DefaultValue = bTrunkLayer ? 0.62f : 0.68f;
        AtlasTrunkRoughness->SliderMin = 0.0f;

        AtlasTrunkRoughness->SliderMax = 1.0f;
        UMaterialExpressionScalarParameter* AtlasFoliageRoughness =
            AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), -60, 260);
        AtlasFoliageRoughness->ParameterName = TEXT("AtlasFoliageRoughness");
        AtlasFoliageRoughness->DefaultValue = bFoliageLayer ? 0.72f : 0.68f;
        AtlasFoliageRoughness->SliderMin = 0.0f;
        AtlasFoliageRoughness->SliderMax = 1.0f;
        UMaterialExpressionLinearInterpolate* Roughness =
            AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 180, 180);
        Roughness->A.Expression = AtlasTrunkRoughness;
        Roughness->B.Expression = AtlasFoliageRoughness;
        Roughness->Alpha.Expression = AtlasFoliageMask;
        UMaterialExpressionScalarParameter* AtlasTrunkSpecular =
            AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), -60, 340);
        AtlasTrunkSpecular->ParameterName = TEXT("AtlasTrunkSpecular");
        AtlasTrunkSpecular->DefaultValue = bTrunkLayer ? 0.12f : 0.18f;
        AtlasTrunkSpecular->SliderMin = 0.0f;
        AtlasTrunkSpecular->SliderMax = 1.0f;
        UMaterialExpressionScalarParameter* AtlasFoliageSpecular =
            AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), -60, 420);
        AtlasFoliageSpecular->ParameterName = TEXT("AtlasFoliageSpecular");
        AtlasFoliageSpecular->DefaultValue = 0.18f;
        AtlasFoliageSpecular->SliderMin = 0.0f;
        AtlasFoliageSpecular->SliderMax = 1.0f;
        UMaterialExpressionLinearInterpolate* Specular =
            AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 180, 300);
        Specular->A.Expression = AtlasTrunkSpecular;
        Specular->B.Expression = AtlasFoliageSpecular;
        Specular->Alpha.Expression = AtlasFoliageMask;
        UMaterialExpressionConstant* AmbientOcclusion =
            AddExpression(NewObject<UMaterialExpressionConstant>(Material), 180, 340);
        AmbientOcclusion->R = 1.0f;
        ConnectPreviewMaterialScalarInput(EditorOnlyData->Roughness, Roughness);
        ConnectPreviewMaterialScalarInput(EditorOnlyData->Specular, Specular);
        ConnectPreviewMaterialScalarInput(
            EditorOnlyData->AmbientOcclusion,
            AmbientOcclusion);
    }
    else
    {
        ConnectPreviewMaterialColorInput(EditorOnlyData->EmissiveColor, ConditionedColor);
    }
    UMaterialExpression* FinalOpacity = OpacitySample;
    if (bTrunkLayer || bFoliageLayer)
    {
        UMaterialExpression* LayerIdentity = AtlasFoliageMask;
        if (bTrunkLayer)
        {
            UMaterialExpressionOneMinus* AtlasTrunkMask = AddExpression(
                NewObject<UMaterialExpressionOneMinus>(Material),
                -180,
                -260);
            AtlasTrunkMask->Input.Expression = AtlasFoliageMask;
            LayerIdentity = AtlasTrunkMask;
        }
        UMaterialExpressionMultiply* LayerOpacity =
            AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 40, -280);
        LayerOpacity->A.Expression = OpacitySample;
        LayerOpacity->B.Expression = LayerIdentity;
        FinalOpacity = LayerOpacity;
    }
    if (bEnableComplementaryTransition)
    {
        FinalOpacity = AddComplementaryScreenDitherOpacity(
            Material,
            FinalOpacity,
            0,
            false,
            0.0f,
            -120,
            -300);
    }
    ConnectPreviewMaterialScalarInput(EditorOnlyData->OpacityMask, FinalOpacity);
    ConnectPreviewMaterialVectorInput(EditorOnlyData->WorldPositionOffset, BillboardOffset);

    Material->PostEditChange();
    Material->MarkPackageDirty();
    Package->MarkPackageDirty();
    Material->ForceRecompileForRendering();
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (GShaderCompilingManager)
    {
        GShaderCompilingManager->FinishAllCompilation();
    }
    FMaterialResource* MaterialResource = Material->GetMaterialResource(GMaxRHIShaderPlatform);
    if (MaterialResource && !MaterialResource->IsGameThreadShaderMapComplete())
    {
        MaterialResource->SubmitCompileJobs_GameThread(EShaderCompileJobPriority::High);
        MaterialResource->FinishCompilation();
        if (GShaderCompilingManager)
        {
            GShaderCompilingManager->ProcessAsyncResults(false, true);
        }
        MaterialResource->IsCompilationFinished();
    }
    MaterialResource = Material->GetMaterialResource(GMaxRHIShaderPlatform);
    if (!MaterialResource ||
        Material->IsCompilingOrHadCompileError(GMaxRHIShaderPlatform) ||
        !MaterialResource->GetCompileErrors().IsEmpty())
    {
        UE_LOG(
            LogRaftSimEditor,
            Warning,
            TEXT("Local PVE atlas material shader gate failed for %s (resource=%s, compiling_or_error=%s, valid_shader_map=%s, errors=%d)."),
            *ObjectPath,
            MaterialResource ? TEXT("true") : TEXT("false"),
            Material->IsCompilingOrHadCompileError(GMaxRHIShaderPlatform) ? TEXT("true") : TEXT("false"),
            MaterialResource && MaterialResource->HasValidGameThreadShaderMap() ? TEXT("true") : TEXT("false"),
            MaterialResource ? MaterialResource->GetCompileErrors().Num() : -1);
        OutSummary += FString::Printf(
            TEXT("Local PVE atlas material failed shader validation for %s: %s\n"),
            *ObjectPath,
            MaterialResource
                ? *FString::Join(MaterialResource->GetCompileErrors(), TEXT(" | "))
                : TEXT("no material resource"));
        return nullptr;
    }
    const FString Filename = FPackageName::LongPackageNameToFilename(
        PackagePath,
        FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Material, *Filename, SaveArgs))
    {
        OutSummary += FString::Printf(TEXT("Could not save local PVE atlas material %s.\n"), *ObjectPath);
        return nullptr;
    }
    OutSummary += FString::Printf(TEXT("Saved local PVE atlas material %s.\n"), *ObjectPath);
    return Material;
}

bool BakeFutaleufuCypressMultiViewAtlas(
    UWorld* World,
    AActor* TrunkActor,
    AActor* FoliageActor,
    const FString& VariantId,
    const FString& AssetToken,
    const FString& LocalSavedNamespace,
    const FString& LocalReviewNamespace,
    bool bUseColorCorrectHlod,
    const FLinearColor& AtlasColorGain,
    bool bDeterministicValidationCapture,
    float AzimuthOffsetDegrees,
    bool bUsePerspectiveCapture,
    float RequestedPerspectiveCaptureRadiusCm,
    bool bUseDepthParallax,
    bool bEnableComplementaryTransition,
    int32 RequestedTileResolution,
    FRaftSimPveMultiViewAtlasBakeResult& OutResult,
    FString& OutSummary)
{
    OutResult = FRaftSimPveMultiViewAtlasBakeResult();
    if (!World || !TrunkActor || !FoliageActor)
    {
        OutSummary += TEXT("Multi-view atlas bake requires the live trunk and foliage actors.\n");
        return false;
    }
    if (RequestedTileResolution != 512 && RequestedTileResolution != 1024)
    {
        OutSummary += TEXT("Multi-view atlas tile resolution must be 512 or 1024.\n");
        return false;
    }
    if (!FMath::IsFinite(AzimuthOffsetDegrees) ||
        FMath::Abs(AzimuthOffsetDegrees) > 22.5f)
    {
        OutSummary += TEXT("Multi-view atlas azimuth offset must be finite and within half a frame.\n");
        return false;
    }
    if (bUsePerspectiveCapture &&
        (!FMath::IsFinite(RequestedPerspectiveCaptureRadiusCm) ||
         RequestedPerspectiveCaptureRadiusCm < 100.0f))
    {
        OutSummary += TEXT("Perspective multi-view capture radius must be finite and positive.\n");
        return false;
    }
    if (bUseDepthParallax && !bUsePerspectiveCapture)
    {
        OutSummary += TEXT("Depth-aware multi-view proxy requires perspective capture.\n");
        return false;
    }
    const int32 TileResolution = RequestedTileResolution;
    constexpr int32 AtlasGrid = 4;
    const int32 AtlasResolution = TileResolution * AtlasGrid;
    constexpr int32 AzimuthViewCount = 8;
    constexpr int32 ElevationViewCount = 2;
    constexpr int32 ViewCount = AzimuthViewCount * ElevationViewCount;
    static const float ElevationDegrees[ElevationViewCount] = {0.0f, 25.0f};
    OutResult.TileResolution = TileResolution;
    OutResult.AtlasResolution = AtlasResolution;
    OutResult.ViewCount = ViewCount;
    OutResult.ColorGain = AtlasColorGain;
    OutResult.AzimuthOffsetDegrees = AzimuthOffsetDegrees;

    FBox SourceBounds(EForceInit::ForceInit);
    SourceBounds += TrunkActor->GetComponentsBoundingBox(true);
    SourceBounds += FoliageActor->GetComponentsBoundingBox(true);
    if (!SourceBounds.IsValid)
    {
        OutSummary += TEXT("Multi-view atlas source bounds are invalid.\n");
        return false;
    }
    const FVector Target = SourceBounds.GetCenter();
    const FVector SourceSize = SourceBounds.GetSize();
    const float OrthoWidth = FMath::Max3(SourceSize.X, SourceSize.Y, SourceSize.Z) * 1.12f;
    const float CaptureRadius = bUsePerspectiveCapture
        ? RequestedPerspectiveCaptureRadiusCm
        : FMath::Max(OrthoWidth * 2.25f, 5000.0f);
    const float PerspectiveHorizontalFovDegrees = bUsePerspectiveCapture
        ? FMath::RadiansToDegrees(2.0f * FMath::Atan(OrthoWidth / (2.0f * CaptureRadius)))
        : 0.0f;
    const float DepthParallaxScaleCm = bUseDepthParallax
        ? FMath::Max(SourceSize.X, SourceSize.Y)
        : 0.0f;
    OutResult.OrthoWidthCm = OrthoWidth;
    OutResult.bPerspectiveCapture = bUsePerspectiveCapture;
    OutResult.CaptureRadiusCm = CaptureRadius;
    OutResult.PerspectiveHorizontalFovDegrees = PerspectiveHorizontalFovDegrees;
    OutResult.bDepthParallaxEnabled = bUseDepthParallax;
    OutResult.DepthParallaxScaleCm = DepthParallaxScaleCm;
    OutResult.bComplementaryTransitionEnabled = bEnableComplementaryTransition;

    FAssetCompilingManager::Get().FinishAllCompilation();
    if (GShaderCompilingManager)
    {
        GShaderCompilingManager->FinishAllCompilation();
    }
    World->SendAllEndOfFrameUpdates();
    FlushRenderingCommands();

    UTextureRenderTarget2D* RenderTarget = NewObject<UTextureRenderTarget2D>(
        GetTransientPackage(), NAME_None, RF_Transient);
    UTextureRenderTarget2D* ColorRenderTarget = NewObject<UTextureRenderTarget2D>(
        GetTransientPackage(), NAME_None, RF_Transient);
    ASceneCapture2D* SceneCapture = World->SpawnActor<ASceneCapture2D>(
        ASceneCapture2D::StaticClass(), Target, FRotator::ZeroRotator);
    if (!RenderTarget || !ColorRenderTarget || !SceneCapture ||
        !SceneCapture->GetCaptureComponent2D())
    {
        OutSummary += TEXT("Could not allocate multi-view atlas scene capture.\n");
        if (SceneCapture)
        {
            SceneCapture->Destroy();
        }
        return false;
    }
    RenderTarget->RenderTargetFormat = RTF_RGBA16f;
    RenderTarget->ClearColor = FLinearColor(0.0f, 0.0f, 0.0f, 1.0f);
    RenderTarget->InitAutoFormat(TileResolution, TileResolution);
    RenderTarget->UpdateResourceImmediate(true);
    ColorRenderTarget->RenderTargetFormat = RTF_RGBA8_SRGB;
    ColorRenderTarget->ClearColor = FLinearColor::Transparent;
    ColorRenderTarget->InitAutoFormat(TileResolution, TileResolution);
    ColorRenderTarget->UpdateResourceImmediate(true);

    USceneCaptureComponent2D* CaptureComponent = SceneCapture->GetCaptureComponent2D();
    CaptureComponent->TextureTarget = RenderTarget;
    CaptureComponent->ProjectionType = bUsePerspectiveCapture
        ? ECameraProjectionMode::Perspective
        : ECameraProjectionMode::Orthographic;
    CaptureComponent->OrthoWidth = OrthoWidth;
    if (bUsePerspectiveCapture)
    {
        CaptureComponent->FOVAngle = PerspectiveHorizontalFovDegrees;
    }
    CaptureComponent->PrimitiveRenderMode =
        ESceneCapturePrimitiveRenderMode::PRM_RenderScenePrimitives;
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* Actor = *It;
        if (Actor && Actor != TrunkActor && Actor != FoliageActor &&
            Actor->FindComponentByClass<UMeshComponent>())
        {
            CaptureComponent->HiddenActors.Add(Actor);
        }
    }
    CaptureComponent->bCaptureEveryFrame = false;
    CaptureComponent->bCaptureOnMovement = false;
    CaptureComponent->bAlwaysPersistRenderingState = true;
    CaptureComponent->bExcludeFromSceneTextureExtents = true;
    CaptureComponent->ShowFlags.SetSelection(false);
    CaptureComponent->ShowFlags.SetModeWidgets(false);
    CaptureComponent->ShowFlags.SetCompositeEditorPrimitives(false);
    CaptureComponent->ShowFlags.SetAtmosphere(false);
    CaptureComponent->ShowFlags.SetFog(false);
    if (bDeterministicValidationCapture)
    {
        CaptureComponent->ShowFlags.SetLighting(false);
        CaptureComponent->ShowFlags.SetPostProcessing(false);
        CaptureComponent->ShowFlags.SetAntiAliasing(false);
        CaptureComponent->ShowFlags.SetTemporalAA(false);
        CaptureComponent->ShowFlags.SetMotionBlur(false);
        CaptureComponent->ShowFlags.SetEyeAdaptation(false);
        CaptureComponent->ShowFlags.SetAmbientOcclusion(false);
        CaptureComponent->ShowFlags.SetGlobalIllumination(false);
        CaptureComponent->ShowFlags.SetLumenGlobalIllumination(false);
        CaptureComponent->ShowFlags.SetLumenReflections(false);
        CaptureComponent->ShowFlags.SetScreenSpaceReflections(false);
        CaptureComponent->ShowFlags.SetReflectionEnvironment(false);
    }
    const FRaftSimPhotographicCaptureSettings AtlasCaptureSettings =
        GetPhotographicCaptureSettings(TEXT("futaleufu_terminator"));
    CaptureComponent->PostProcessSettings.bOverride_AutoExposureMethod = true;
    CaptureComponent->PostProcessSettings.AutoExposureMethod = AEM_Manual;
    CaptureComponent->PostProcessSettings.bOverride_AutoExposureBias = true;
    CaptureComponent->PostProcessSettings.AutoExposureBias = AtlasCaptureSettings.ExposureBias;
    CaptureComponent->PostProcessSettings.bOverride_AutoExposureApplyPhysicalCameraExposure = true;
    CaptureComponent->PostProcessSettings.AutoExposureApplyPhysicalCameraExposure = 0;
    CaptureComponent->PostProcessSettings.bOverride_ColorSaturation = true;
    CaptureComponent->PostProcessSettings.ColorSaturation = FVector4(
        AtlasCaptureSettings.Saturation,
        AtlasCaptureSettings.Saturation,
        AtlasCaptureSettings.Saturation,
        1.0f);
    CaptureComponent->PostProcessSettings.bOverride_ColorContrast = true;
    CaptureComponent->PostProcessSettings.ColorContrast = FVector4(
        AtlasCaptureSettings.Contrast,
        AtlasCaptureSettings.Contrast,
        AtlasCaptureSettings.Contrast,

        1.0f);
    CaptureComponent->PostProcessBlendWeight = 1.0f;

    TArray<FColor> BaseColorAtlas;
    TArray<FColor> AlbedoAtlas;
    TArray<FColor> NormalAtlas;
    TArray<FColor> OpacityAtlas;
    TArray<FColor> DepthAtlas;
    TArray<FColor> MaterialIdentityAtlas;
    BaseColorAtlas.Init(FColor(0, 0, 0, 0), AtlasResolution * AtlasResolution);
    AlbedoAtlas.Init(FColor(0, 0, 0, 0), AtlasResolution * AtlasResolution);
    NormalAtlas.Init(FColor(128, 128, 255, 0), AtlasResolution * AtlasResolution);
    OpacityAtlas.Init(FColor::Black, AtlasResolution * AtlasResolution);
    DepthAtlas.Init(FColor(0, 0, 0, 0), AtlasResolution * AtlasResolution);
    MaterialIdentityAtlas.Init(FColor(0, 0, 0, 0), AtlasResolution * AtlasResolution);
    bool bUsedInverseOpacity = true;
    bool bAllPassesCaptured = true;

    auto CapturePass = [CaptureComponent, RenderTarget, TileResolution](
                           ESceneCaptureSource Source,
                           TArray<FLinearColor>& OutPixels)
    {
        CaptureComponent->CaptureSource = Source;
        CaptureComponent->CaptureScene();
        FlushRenderingCommands();
        FTextureRenderTargetResource* Resource = RenderTarget->GameThread_GetRenderTargetResource();
        return Resource && Resource->ReadLinearColorPixels(
            OutPixels,
            FReadSurfaceDataFlags(RCM_MinMax, CubeFace_MAX)) &&
            OutPixels.Num() == TileResolution * TileResolution;
    };
    auto CaptureColorPass = [
                                CaptureComponent,
                                ColorRenderTarget,
                                RenderTarget,
                                TileResolution](
                                TArray<FColor>& OutPixels)
    {
        CaptureComponent->TextureTarget = ColorRenderTarget;
        CaptureComponent->CaptureSource = SCS_FinalColorLDR;
        CaptureComponent->CaptureScene();
        FlushRenderingCommands();
        FTextureRenderTargetResource* Resource =
            ColorRenderTarget->GameThread_GetRenderTargetResource();
        const bool bRead = Resource && Resource->ReadPixels(
            OutPixels,
            FReadSurfaceDataFlags(RCM_UNorm, CubeFace_MAX)) &&
            OutPixels.Num() == TileResolution * TileResolution;
        CaptureComponent->TextureTarget = RenderTarget;
        return bRead;
    };

    TrunkActor->SetActorHiddenInGame(false);
    FoliageActor->SetActorHiddenInGame(false);
    for (int32 ElevationIndex = 0; ElevationIndex < ElevationViewCount; ++ElevationIndex)
    {
        const float ElevationRadians = FMath::DegreesToRadians(ElevationDegrees[ElevationIndex]);
        for (int32 AzimuthIndex = 0; AzimuthIndex < AzimuthViewCount; ++AzimuthIndex)
        {
            const int32 ViewIndex = ElevationIndex * AzimuthViewCount + AzimuthIndex;
            const float AzimuthRadians =
                FMath::DegreesToRadians(AzimuthOffsetDegrees) +
                2.0f * PI * static_cast<float>(AzimuthIndex) /
                    static_cast<float>(AzimuthViewCount);
            const FVector CameraDirection(
                FMath::Cos(AzimuthRadians) * FMath::Cos(ElevationRadians),
                FMath::Sin(AzimuthRadians) * FMath::Cos(ElevationRadians),
                FMath::Sin(ElevationRadians));
            const FVector CameraLocation = Target + CameraDirection * CaptureRadius;
            SceneCapture->SetActorLocationAndRotation(
                CameraLocation,
                (Target - CameraLocation).Rotation());

            TArray<FLinearColor> SceneColorPixels;
            TArray<FLinearColor> BaseColorPixels;
            TArray<FLinearColor> NormalPixels;
            TArray<FLinearColor> DepthPixels;
            TArray<FLinearColor> TrunkSceneColorPixels;
            TArray<FLinearColor> TrunkDepthPixels;
            TArray<FLinearColor> FoliageSceneColorPixels;
            TArray<FLinearColor> FoliageDepthPixels;
            TArray<FColor> FinalColorPixels;
            bool bViewCaptured =
                CapturePass(SCS_SceneColorHDR, SceneColorPixels) &&
                CapturePass(SCS_BaseColor, BaseColorPixels) &&
                CapturePass(SCS_Normal, NormalPixels) &&
                CapturePass(SCS_SceneDepth, DepthPixels) &&
                CaptureColorPass(FinalColorPixels);
            FoliageActor->SetActorHiddenInGame(true);
            World->SendAllEndOfFrameUpdates();
            FlushRenderingCommands();
            bViewCaptured &=
                CapturePass(SCS_SceneColorHDR, TrunkSceneColorPixels) &&
                CapturePass(SCS_SceneDepth, TrunkDepthPixels);
            FoliageActor->SetActorHiddenInGame(false);
            TrunkActor->SetActorHiddenInGame(true);
            World->SendAllEndOfFrameUpdates();
            FlushRenderingCommands();
            bViewCaptured &=
                CapturePass(SCS_SceneColorHDR, FoliageSceneColorPixels) &&
                CapturePass(SCS_SceneDepth, FoliageDepthPixels);
            TrunkActor->SetActorHiddenInGame(false);
            World->SendAllEndOfFrameUpdates();
            FlushRenderingCommands();
            bAllPassesCaptured &= bViewCaptured;
            if (!bViewCaptured)
            {
                continue;
            }

            TArray<float> Opacity;
            TArray<float> TrunkOpacity;
            TArray<float> FoliageOpacity;
            Opacity.SetNumUninitialized(TileResolution * TileResolution);
            TrunkOpacity.SetNumUninitialized(TileResolution * TileResolution);
            FoliageOpacity.SetNumUninitialized(TileResolution * TileResolution);
            int32 InverseOpacityCoveredPixels = 0;
            for (int32 PixelIndex = 0; PixelIndex < Opacity.Num(); ++PixelIndex)
            {
                Opacity[PixelIndex] = FMath::Clamp(1.0f - SceneColorPixels[PixelIndex].A, 0.0f, 1.0f);
                TrunkOpacity[PixelIndex] = FMath::Clamp(
                    1.0f - TrunkSceneColorPixels[PixelIndex].A,
                    0.0f,
                    1.0f);
                FoliageOpacity[PixelIndex] = FMath::Clamp(
                    1.0f - FoliageSceneColorPixels[PixelIndex].A,
                    0.0f,
                    1.0f);
                InverseOpacityCoveredPixels += Opacity[PixelIndex] > 0.02f ? 1 : 0;
            }
            float Coverage = static_cast<float>(InverseOpacityCoveredPixels) /
                static_cast<float>(Opacity.Num());
            if (Coverage < 0.002f || Coverage > 0.85f)
            {
                bUsedInverseOpacity = false;
                int32 BaseColorCoveredPixels = 0;
                for (int32 PixelIndex = 0; PixelIndex < Opacity.Num(); ++PixelIndex)
                {
                    const FLinearColor& Base = BaseColorPixels[PixelIndex];
                    const float BaseMagnitude = FMath::Abs(Base.R) + FMath::Abs(Base.G) + FMath::Abs(Base.B);
                    Opacity[PixelIndex] = BaseMagnitude > 0.002f ? 1.0f : 0.0f;
                    BaseColorCoveredPixels += Opacity[PixelIndex] > 0.02f ? 1 : 0;
                }
                Coverage = static_cast<float>(BaseColorCoveredPixels) /
                    static_cast<float>(Opacity.Num());
            }
            OutResult.MinimumCoverage = FMath::Min(OutResult.MinimumCoverage, Coverage);
            OutResult.MaximumCoverage = FMath::Max(OutResult.MaximumCoverage, Coverage);

            float MinimumDepth = TNumericLimits<float>::Max();
            float MaximumDepth = TNumericLimits<float>::Lowest();
            for (int32 PixelIndex = 0; PixelIndex < Opacity.Num(); ++PixelIndex)
            {
                const float Depth = DepthPixels[PixelIndex].R;
                if (Opacity[PixelIndex] > 0.02f && FMath::IsFinite(Depth) && Depth > 0.0f)
                {
                    MinimumDepth = FMath::Min(MinimumDepth, Depth);
                    MaximumDepth = FMath::Max(MaximumDepth, Depth);
                }
            }
            const float DepthRange = MaximumDepth > MinimumDepth
                ? MaximumDepth - MinimumDepth
                : 1.0f;
            const int32 TileOriginX = (ViewIndex % AtlasGrid) * TileResolution;
            const int32 TileOriginY = (ViewIndex / AtlasGrid) * TileResolution;
            for (int32 Y = 0; Y < TileResolution; ++Y)
            {
                for (int32 X = 0; X < TileResolution; ++X)
                {
                    const int32 TileIndex = Y * TileResolution + X;
                    const int32 AtlasIndex =
                        (TileOriginY + Y) * AtlasResolution + TileOriginX + X;
                    const uint8 Alpha = static_cast<uint8>(
                        FMath::RoundToInt(Opacity[TileIndex] * 255.0f));
                    FColor BaseColor = FinalColorPixels[TileIndex];
                    BaseColor.A = Alpha;
                    BaseColorAtlas[AtlasIndex] = BaseColor;
                    FColor AlbedoColor =
                        BaseColorPixels[TileIndex].GetClamped().ToFColor(true);
                    AlbedoColor.A = Alpha;
                    AlbedoAtlas[AtlasIndex] = AlbedoColor;
                    FColor NormalColor = NormalPixels[TileIndex].GetClamped().ToFColor(false);
                    NormalColor.A = Alpha;
                    NormalAtlas[AtlasIndex] = NormalColor;
                    OpacityAtlas[AtlasIndex] = FColor(Alpha, Alpha, Alpha, 255);
                    const float NormalizedDepth = FMath::Clamp(
                        1.0f - ((DepthPixels[TileIndex].R - MinimumDepth) / DepthRange),
                        0.0f,
                        1.0f);
                    const uint8 DepthValue = static_cast<uint8>(
                        FMath::RoundToInt(NormalizedDepth * 255.0f));
                    DepthAtlas[AtlasIndex] = FColor(DepthValue, DepthValue, DepthValue, Alpha);
                    const bool bTrunkCovered = TrunkOpacity[TileIndex] > 0.02f;
                    const bool bFoliageCovered = FoliageOpacity[TileIndex] > 0.02f;
                    bool bFoliageOwnsPixel = bFoliageCovered &&
                        (!bTrunkCovered ||
                         FoliageDepthPixels[TileIndex].R <=
                             TrunkDepthPixels[TileIndex].R + 0.5f);
                    if (Opacity[TileIndex] > 0.02f &&
                        !bTrunkCovered && !bFoliageCovered)
                    {
                        const FLinearColor& Base = BaseColorPixels[TileIndex];
                        bFoliageOwnsPixel = Base.G > FMath::Max(Base.R, Base.B);
                        ++OutResult.MaterialIdentityFallbackPixelCount;
                    }
                    const uint8 MaterialIdentity = bFoliageOwnsPixel ? 255 : 0;
                    MaterialIdentityAtlas[AtlasIndex] = FColor(
                        MaterialIdentity,
                        MaterialIdentity,
                        MaterialIdentity,
                        Alpha);
                }
            }
            DilatePveAtlasTileRgb(
                BaseColorAtlas, AtlasResolution, TileOriginX, TileOriginY, TileResolution, 12);
            DilatePveAtlasTileRgb(
                AlbedoAtlas, AtlasResolution, TileOriginX, TileOriginY, TileResolution, 12);
            DilatePveAtlasTileRgb(
                NormalAtlas, AtlasResolution, TileOriginX, TileOriginY, TileResolution, 12);
            DilatePveAtlasTileRgb(
                DepthAtlas, AtlasResolution, TileOriginX, TileOriginY, TileResolution, 12);
            DilatePveAtlasTileRgb(
                MaterialIdentityAtlas,
                AtlasResolution,
                TileOriginX,
                TileOriginY,
                TileResolution,
                12);
        }
    }
    SceneCapture->Destroy();
    RenderTarget->ReleaseResource();
    ColorRenderTarget->ReleaseResource();
    OutResult.OpacitySource = bUsedInverseOpacity
        ? TEXT("SceneColorHDR inverse opacity alpha")
        : TEXT("SceneColorHDR inverse opacity with BaseColor occupancy fallback");
    if (!bAllPassesCaptured || OutResult.MinimumCoverage < 0.002f ||
        OutResult.MaximumCoverage > 0.85f)
    {
        OutSummary += FString::Printf(
            TEXT("Multi-view atlas capture failed pass or coverage checks (%.6f to %.6f).\n"),
            OutResult.MinimumCoverage,
            OutResult.MaximumCoverage);
        return false;
    }

    const FString VariantLower = VariantId.ToLower();
    const FString OutputDirectory = FPaths::Combine(
        FPaths::ProjectSavedDir(), TEXT("RaftSimPveReview"), LocalSavedNamespace);
    const FString RelativeOutputRoot = FString::Printf(
        TEXT("unreal/Saved/RaftSimPveReview/%s/%s_multiview_atlas"),
        *LocalSavedNamespace,
        *VariantLower);
    OutResult.BaseColorRelativePath = RelativeOutputRoot + TEXT("_base_color_opacity.png");
    OutResult.AlbedoRelativePath = RelativeOutputRoot + TEXT("_albedo_opacity.png");
    OutResult.NormalRelativePath = RelativeOutputRoot + TEXT("_world_normal.png");
    OutResult.OpacityRelativePath = RelativeOutputRoot + TEXT("_opacity.png");
    OutResult.DepthRelativePath = RelativeOutputRoot + TEXT("_depth.png");
    OutResult.MaterialIdentityRelativePath =
        RelativeOutputRoot + TEXT("_material_identity.png");
    const FString BaseColorAbsolutePath = FPaths::Combine(
        OutputDirectory, VariantLower + TEXT("_multiview_atlas_base_color_opacity.png"));
    const FString AlbedoAbsolutePath = FPaths::Combine(
        OutputDirectory, VariantLower + TEXT("_multiview_atlas_albedo_opacity.png"));
    const FString NormalAbsolutePath = FPaths::Combine(
        OutputDirectory, VariantLower + TEXT("_multiview_atlas_world_normal.png"));
    const FString OpacityAbsolutePath = FPaths::Combine(
        OutputDirectory, VariantLower + TEXT("_multiview_atlas_opacity.png"));
    const FString DepthAbsolutePath = FPaths::Combine(
        OutputDirectory, VariantLower + TEXT("_multiview_atlas_depth.png"));
    const FString MaterialIdentityAbsolutePath = FPaths::Combine(
        OutputDirectory,
        VariantLower + TEXT("_multiview_atlas_material_identity.png"));
    OutResult.bAtlasFilesSaved =
        SavePveAtlasPng(BaseColorAbsolutePath, AtlasResolution, AtlasResolution, BaseColorAtlas) &&
        SavePveAtlasPng(AlbedoAbsolutePath, AtlasResolution, AtlasResolution, AlbedoAtlas) &&
        SavePveAtlasPng(NormalAbsolutePath, AtlasResolution, AtlasResolution, NormalAtlas) &&
        SavePveAtlasPng(OpacityAbsolutePath, AtlasResolution, AtlasResolution, OpacityAtlas) &&
        SavePveAtlasPng(DepthAbsolutePath, AtlasResolution, AtlasResolution, DepthAtlas) &&
        SavePveAtlasPng(
            MaterialIdentityAbsolutePath,
            AtlasResolution,
            AtlasResolution,
            MaterialIdentityAtlas);
    if (!OutResult.bAtlasFilesSaved)
    {
        OutSummary += TEXT("One or more multi-view atlas PNG files failed to save.\n");
        return false;
    }
    OutResult.BaseColorDigest = LexToString(FMD5Hash::HashFile(*BaseColorAbsolutePath));
    OutResult.AlbedoDigest = LexToString(FMD5Hash::HashFile(*AlbedoAbsolutePath));
    OutResult.NormalDigest = LexToString(FMD5Hash::HashFile(*NormalAbsolutePath));
    OutResult.OpacityDigest = LexToString(FMD5Hash::HashFile(*OpacityAbsolutePath));
    OutResult.DepthDigest = LexToString(FMD5Hash::HashFile(*DepthAbsolutePath));
    OutResult.MaterialIdentityDigest =
        LexToString(FMD5Hash::HashFile(*MaterialIdentityAbsolutePath));

    const FString AtlasPackageRoot = FString::Printf(
        TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/%s/MultiViewAtlas"),
        *LocalReviewNamespace);
    OutResult.BaseColorAssetPath = FString::Printf(
        TEXT("%s/T_%s_%s_MultiViewBaseColorOpacity"),
        *AtlasPackageRoot, *AssetToken, *VariantLower);
    OutResult.AlbedoAssetPath = FString::Printf(
        TEXT("%s/T_%s_%s_MultiViewAlbedoOpacity"),
        *AtlasPackageRoot, *AssetToken, *VariantLower);
    OutResult.NormalAssetPath = FString::Printf(
        TEXT("%s/T_%s_%s_MultiViewWorldNormal"),
        *AtlasPackageRoot, *AssetToken, *VariantLower);
    OutResult.OpacityAssetPath = FString::Printf(
        TEXT("%s/T_%s_%s_MultiViewOpacity"),
        *AtlasPackageRoot, *AssetToken, *VariantLower);
    OutResult.DepthAssetPath = FString::Printf(
        TEXT("%s/T_%s_%s_MultiViewDepth"),
        *AtlasPackageRoot, *AssetToken, *VariantLower);
    OutResult.MaterialIdentityAssetPath = FString::Printf(
        TEXT("%s/T_%s_%s_MultiViewMaterialIdentity"),
        *AtlasPackageRoot, *AssetToken, *VariantLower);
    UTexture2D* BaseColorTexture = CreateOrUpdateLocalPveAtlasTexture(
        OutResult.BaseColorAssetPath,

        BaseColorAtlas,
        AtlasResolution,
        TC_Default,
        true,
        true,
        OutSummary);
    UTexture2D* AlbedoTexture = CreateOrUpdateLocalPveAtlasTexture(
        OutResult.AlbedoAssetPath,
        AlbedoAtlas,
        AtlasResolution,
        TC_Default,
        true,
        true,
        OutSummary);
    UTexture2D* NormalTexture = CreateOrUpdateLocalPveAtlasTexture(
        OutResult.NormalAssetPath,
        NormalAtlas,
        AtlasResolution,
        TC_VectorDisplacementmap,
        false,
        false,
        OutSummary);
    UTexture2D* OpacityTexture = CreateOrUpdateLocalPveAtlasTexture(
        OutResult.OpacityAssetPath,
        OpacityAtlas,
        AtlasResolution,
        TC_Grayscale,
        false,
        false,
        OutSummary);
    UTexture2D* DepthTexture = CreateOrUpdateLocalPveAtlasTexture(
        OutResult.DepthAssetPath,
        DepthAtlas,
        AtlasResolution,
        TC_Grayscale,
        false,
        false,
        OutSummary);
    UTexture2D* MaterialIdentityTexture = CreateOrUpdateLocalPveAtlasTexture(
        OutResult.MaterialIdentityAssetPath,
        MaterialIdentityAtlas,
        AtlasResolution,
        TC_Grayscale,
        false,
        false,
        OutSummary);
    OutResult.bTextureAssetsSaved =
        BaseColorTexture && AlbedoTexture && NormalTexture && OpacityTexture &&
        DepthTexture && MaterialIdentityTexture;
    if (!OutResult.bTextureAssetsSaved)
    {
        return false;
    }
    TArray<UTexture*> AtlasTextures = {
        BaseColorTexture,
        AlbedoTexture,
        NormalTexture,
        OpacityTexture,
        DepthTexture,
        MaterialIdentityTexture};
    FTextureCompilingManager::Get().FinishCompilation(AtlasTextures);
    for (UTexture* Texture : AtlasTextures)
    {
        Texture->UpdateResource();
    }
    FlushRenderingCommands();

    OutResult.MaterialAssetPath = FString::Printf(
        TEXT("%s/M_%s_%s_MultiViewHlodV2"),
        *AtlasPackageRoot, *AssetToken, *VariantLower);
    OutResult.Material = CreateOrUpdateLocalPveAtlasMaterial(
        OutResult.MaterialAssetPath,
        BaseColorTexture,
        NormalTexture,
        OpacityTexture,
        DepthTexture,
        MaterialIdentityTexture,
        bUseColorCorrectHlod,
        AtlasColorGain,
        AzimuthOffsetDegrees,
        bUseDepthParallax,
        DepthParallaxScaleCm,
        bEnableComplementaryTransition,
        false,
        EPveAtlasMaterialLayer::Combined,
        OutSummary);
    OutResult.bMaterialSaved = OutResult.Material != nullptr;
    OutResult.RelightableMaterialAssetPath = FString::Printf(
        TEXT("%s/M_%s_%s_MultiViewHlodV3Lit"),
        *AtlasPackageRoot,
        *AssetToken,
        *VariantLower);
    OutResult.RelightableMaterial = CreateOrUpdateLocalPveAtlasMaterial(
        OutResult.RelightableMaterialAssetPath,
        AlbedoTexture,
        NormalTexture,
        OpacityTexture,
        DepthTexture,
        MaterialIdentityTexture,
        true,
        FLinearColor(1.55f, 1.55f, 1.55f, 1.0f),
        AzimuthOffsetDegrees,
        bUseDepthParallax,
        DepthParallaxScaleCm,
        bEnableComplementaryTransition,
        true,
        EPveAtlasMaterialLayer::Combined,
        OutSummary);
    OutResult.bRelightableMaterialSaved =
        OutResult.RelightableMaterial != nullptr;
    OutResult.RelightableTrunkMaterialAssetPath = FString::Printf(
        TEXT("%s/M_%s_%s_MultiViewHlodV4LitTrunk"),
        *AtlasPackageRoot,
        *AssetToken,
        *VariantLower);
    OutResult.RelightableTrunkMaterial = CreateOrUpdateLocalPveAtlasMaterial(
        OutResult.RelightableTrunkMaterialAssetPath,
        AlbedoTexture,
        NormalTexture,
        OpacityTexture,
        DepthTexture,
        MaterialIdentityTexture,
        true,
        FLinearColor(1.55f, 1.55f, 1.55f, 1.0f),
        AzimuthOffsetDegrees,
        bUseDepthParallax,
        DepthParallaxScaleCm,
        bEnableComplementaryTransition,
        true,
        EPveAtlasMaterialLayer::Trunk,
        OutSummary);
    OutResult.bRelightableTrunkMaterialSaved =
        OutResult.RelightableTrunkMaterial != nullptr;
    OutResult.RelightableFoliageMaterialAssetPath = FString::Printf(
        TEXT("%s/M_%s_%s_MultiViewHlodV4LitFoliage"),
        *AtlasPackageRoot,
        *AssetToken,
        *VariantLower);
    OutResult.RelightableFoliageMaterial = CreateOrUpdateLocalPveAtlasMaterial(
        OutResult.RelightableFoliageMaterialAssetPath,
        AlbedoTexture,
        NormalTexture,
        OpacityTexture,
        DepthTexture,
        MaterialIdentityTexture,
        true,
        FLinearColor(1.55f, 1.55f, 1.55f, 1.0f),
        AzimuthOffsetDegrees,
        bUseDepthParallax,
        DepthParallaxScaleCm,
        bEnableComplementaryTransition,
        true,
        EPveAtlasMaterialLayer::Foliage,
        OutSummary);
    OutResult.bRelightableFoliageMaterialSaved =
        OutResult.RelightableFoliageMaterial != nullptr;
    UStaticMesh* ProxyMesh = LoadPreviewMesh(TEXT("/Engine/BasicShapes/Plane.Plane"));
    if (bUseDepthParallax && OutResult.Material)
    {
        constexpr int32 GridSegments = 32;
        constexpr int32 GridVerticesPerSide = GridSegments + 1;
        TArray<FVector> GridVertices;
        TArray<int32> GridTriangles;
        TArray<FVector> GridNormals;
        TArray<FVector2D> GridUVs;
        GridVertices.Reserve(GridVerticesPerSide * GridVerticesPerSide);
        GridNormals.Reserve(GridVerticesPerSide * GridVerticesPerSide);
        GridUVs.Reserve(GridVerticesPerSide * GridVerticesPerSide);
        GridTriangles.Reserve(GridSegments * GridSegments * 6);
        for (int32 Y = 0; Y <= GridSegments; ++Y)
        {
            const float V = static_cast<float>(Y) / static_cast<float>(GridSegments);
            for (int32 X = 0; X <= GridSegments; ++X)
            {
                const float U = static_cast<float>(X) / static_cast<float>(GridSegments);
                GridVertices.Add(FVector((U - 0.5f) * 100.0f, (V - 0.5f) * 100.0f, 0.0f));
                GridNormals.Add(FVector::UpVector);
                GridUVs.Add(FVector2D(U, V));
            }
        }
        for (int32 Y = 0; Y < GridSegments; ++Y)
        {
            for (int32 X = 0; X < GridSegments; ++X)
            {
                const int32 A = Y * GridVerticesPerSide + X;
                const int32 B = A + 1;
                const int32 C = A + GridVerticesPerSide;
                const int32 D = C + 1;
                GridTriangles.Append({A, C, B, B, C, D});
            }
        }
        AActor* GridSourceActor = AddPreviewProceduralMeshActor(
            World,
            TEXT("RaftSim_PveCypressDepthGridProxy_Source"),
            GridVertices,
            GridTriangles,
            GridNormals,
            GridUVs,
            FLinearColor::White,
            OutResult.Material,
            nullptr,
            false);
        const FString GridAssetPath = FString::Printf(
            TEXT("%s/SM_RaftSim_PveDepthGrid32"),
            *AtlasPackageRoot);
        ProxyMesh = ConvertNativeCanopyProceduralActorToStaticMesh(
            GridSourceActor,
            GridAssetPath,
            OutResult.Material,
            false,
            ENaniteShapePreservation::None,
            OutSummary);
        if (GridSourceActor)
        {
            GridSourceActor->Destroy();
        }
    }
    OutResult.ProxyVertexCount = ProxyMesh ? ProxyMesh->GetNumVertices(0) : 0;
    OutResult.ProxyTriangleCount = ProxyMesh ? ProxyMesh->GetNumTriangles(0) : 0;
    OutResult.ProxyActor = ProxyMesh && OutResult.Material
        ? World->SpawnActor<AStaticMeshActor>(
              AStaticMeshActor::StaticClass(),
              FTransform(
                  FRotator::ZeroRotator,
                  Target,
                  FVector(OrthoWidth / 100.0f, OrthoWidth / 100.0f, 1.0f)))
        : nullptr;
    if (OutResult.ProxyActor && OutResult.ProxyActor->GetStaticMeshComponent())
    {
        OutResult.ProxyActor->SetActorLabel(TEXT("RaftSim_PveCypressMultiViewAtlasHlod"));
        UStaticMeshComponent* Component = OutResult.ProxyActor->GetStaticMeshComponent();
        Component->SetStaticMesh(ProxyMesh);
        Component->SetMaterial(0, OutResult.Material);
        Component->SetMobility(EComponentMobility::Static);
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->SetCastShadow(false);
        Component->BoundsScale = 2.5f;
        OutResult.ProxyActor->SetActorHiddenInGame(true);
        OutResult.bProxyActorCreated = true;
    }

    OutResult.ManifestRelativePath = FString::Printf(
        TEXT("unreal/Saved/RaftSimPveReview/%s/%s_multiview_atlas_manifest.json"),
        *LocalSavedNamespace,
        *VariantLower);
    const FString ManifestAbsolutePath = FPaths::Combine(
        OutputDirectory,
        VariantLower + TEXT("_multiview_atlas_manifest.json"));
    const FString Manifest = FString::Printf(
        TEXT("{\n")
        TEXT("  \"schema\": \"raftsim.unreal.pve_multiview_atlas.v1\",\n")
        TEXT("  \"variant\": \"%s\",\n")
        TEXT("  \"status\": \"%s\",\n")
        TEXT("  \"view_contract\": {\"type\": \"bounded_upper_hemisphere\", \"azimuth_offset_degrees\": %.6f, \"azimuth_degrees\": [%.6f, %.6f, %.6f, %.6f, %.6f, %.6f, %.6f, %.6f], \"elevation_degrees\": [0, 25], \"view_count\": 16},\n")
        TEXT("  \"atlas_contract\": {\"grid\": [4, 4], \"tile_resolution\": %d, \"atlas_resolution\": %d, \"padding_pixels\": 12, \"orthographic_width_cm\": %.6f},\n")
        TEXT("  \"projection_contract\": {\"type\": \"%s\", \"capture_radius_cm\": %.6f, \"perspective_horizontal_fov_degrees\": %.6f, \"proxy_plane_width_cm\": %.6f},\n")
        TEXT("  \"representation_shape_contract\": {\"type\": \"%s\", \"depth_parallax_enabled\": %s, \"depth_parallax_scale_cm\": %.6f, \"proxy_vertex_count\": %d, \"proxy_triangle_count\": %d},\n")
        TEXT("  \"capture_contract\": {\"source_lit_color\": \"%s\", \"relightable_albedo\": \"SCS_BaseColor linear converted to sRGB atlas texels\", \"normal\": \"SCS_Normal world space\", \"opacity\": \"%s\", \"depth\": \"SCS_SceneDepth normalized per view, near white\", \"material_identity\": \"frontmost owner from separate trunk and foliage opacity plus scene-depth passes; black trunk and white foliage\", \"material_identity_fallback_pixels\": %lld, \"primitive_filter\": \"all non-source mesh actors hidden while retaining the review light rig\"},\n")
        TEXT("  \"coverage_fraction_range\": [%.9f, %.9f],\n")
        TEXT("  \"outputs\": {\n")
        TEXT("    \"base_color_opacity\": {\"path\": \"%s\", \"md5\": \"%s\"},\n")
        TEXT("    \"albedo_opacity\": {\"path\": \"%s\", \"md5\": \"%s\"},\n")
        TEXT("    \"world_normal\": {\"path\": \"%s\", \"md5\": \"%s\"},\n")
        TEXT("    \"opacity\": {\"path\": \"%s\", \"md5\": \"%s\"},\n")
        TEXT("    \"depth\": {\"path\": \"%s\", \"md5\": \"%s\"},\n")
        TEXT("    \"material_identity\": {\"path\": \"%s\", \"md5\": \"%s\"}\n")
        TEXT("  },\n")
        TEXT("  \"assets\": {\"base_color_opacity\": \"%s\", \"albedo_opacity\": \"%s\", \"world_normal\": \"%s\", \"opacity\": \"%s\", \"depth\": \"%s\", \"material_identity\": \"%s\", \"legacy_unlit_material\": \"%s\", \"relightable_lit_material\": \"%s\", \"relightable_trunk_material\": \"%s\", \"relightable_foliage_material\": \"%s\"},\n")
        TEXT("  \"runtime_contract\": {\"geometry\": \"%s\", \"frame_selection\": \"nearest 45-degree azimuth plus 0/25-degree elevation row\", \"shading\": \"%s\", \"atlas_color_gain\": [%.6f, %.6f, %.6f], \"material_inputs\": [\"base_color_opacity\", \"opacity\", \"material_identity\"%s], \"captured_but_not_sampled\": [%s], \"texture_residency_for_immediate_exact_camera_review\": \"never_stream\", \"world_normal_relighting_enabled\": %s, \"depth_reserved_for_future_parallax\": %s, \"complementary_screen_dither_enabled\": %s, \"complementary_source_coverage_parameter\": \"ComplementarySourceCoverage\"},\n")
        TEXT("  \"relightable_runtime_contract\": {\"ready\": %s, \"split_layer_ready\": %s, \"shading\": \"masked DefaultLit combined control plus disjoint DefaultLit trunk and TwoSidedFoliage layers using captured world normal and frontmost material identity\", \"base_color_gain\": [1.55, 1.55, 1.55], \"emissive_connected\": false, \"world_normal_relighting_enabled\": true, \"material_identity_parameter\": \"AtlasMaterialIdentity\", \"layer_opacity\": {\"trunk\": \"opacity_times_one_minus_material_identity\", \"foliage\": \"opacity_times_material_identity\"}, \"layer_transition_order\": \"material_identity_layer_opacity_then_complementary_temporal_mask\", \"trunk_shading_model\": \"DefaultLit\", \"foliage_shading_model\": \"TwoSidedFoliage\", \"foliage_transmission_parameter\": \"AtlasFoliageTransmissionTint\", \"foliage_transmission_default\": [0.78, 1.0, 0.58], \"trunk_parameters\": [\"AtlasTrunkGainMultiplier\", \"AtlasTrunkRoughness\", \"AtlasTrunkSpecular\"], \"foliage_parameters\": [\"AtlasFoliageGainMultiplier\", \"AtlasFoliageRoughness\", \"AtlasFoliageSpecular\"], \"combined_default_roughness\": [0.68, 0.68], \"split_default_roughness\": [0.62, 0.72], \"combined_default_specular\": [0.18, 0.18], \"split_default_specular\": [0.12, 0.18], \"default_gain_multipliers\": [1.0, 1.0], \"transition_mode_parameter\": \"ComplementaryTransitionMode\", \"production_candidate_mode\": \"engine_DitherTemporalAA_with_exact_inverse_hlod_ownership\", \"legacy_ordered_control_retained\": true, \"atlas_frame_override_parameter\": \"AtlasFrameOverride\", \"automatic_frame_override_value\": -1.0},\n")
        TEXT("  \"git_policy\": \"generated atlases and assets are local and ignored\"\n")
        TEXT("}\n"),
        *EscapeRaftSimJsonString(VariantId),
        OutResult.IsReady() ? TEXT("generated_and_proxy_ready_for_exact_camera_review") : TEXT("generation_failed"),
        AzimuthOffsetDegrees,
        AzimuthOffsetDegrees,
        AzimuthOffsetDegrees + 45.0f,
        AzimuthOffsetDegrees + 90.0f,
        AzimuthOffsetDegrees + 135.0f,
        AzimuthOffsetDegrees + 180.0f,
        AzimuthOffsetDegrees + 225.0f,
        AzimuthOffsetDegrees + 270.0f,
        AzimuthOffsetDegrees + 315.0f,
        TileResolution,
        AtlasResolution,
        OrthoWidth,
        bUsePerspectiveCapture ? TEXT("perspective") : TEXT("orthographic"),
        CaptureRadius,
        PerspectiveHorizontalFovDegrees,
        OrthoWidth,
        bUseDepthParallax ? TEXT("32x32_tessellated_depth_displaced_billboard") : TEXT("flat_billboard"),
        bUseDepthParallax ? TEXT("true") : TEXT("false"),
        DepthParallaxScaleCm,
        OutResult.ProxyVertexCount,
        OutResult.ProxyTriangleCount,
        bUseColorCorrectHlod
            ? TEXT("SCS_FinalColorLDR source-lit RGB with inverse-opacity silhouette")
            : TEXT("SCS_FinalColorLDR lit RGB with Futaleufu photographic post process"),
        *EscapeRaftSimJsonString(OutResult.OpacitySource),
        static_cast<long long>(OutResult.MaterialIdentityFallbackPixelCount),
        OutResult.MinimumCoverage,
        OutResult.MaximumCoverage,
        *EscapeRaftSimJsonString(OutResult.BaseColorRelativePath),
        *OutResult.BaseColorDigest,
        *EscapeRaftSimJsonString(OutResult.AlbedoRelativePath),
        *OutResult.AlbedoDigest,
        *EscapeRaftSimJsonString(OutResult.NormalRelativePath),
        *OutResult.NormalDigest,
        *EscapeRaftSimJsonString(OutResult.OpacityRelativePath),
        *OutResult.OpacityDigest,
        *EscapeRaftSimJsonString(OutResult.DepthRelativePath),
        *OutResult.DepthDigest,
        *EscapeRaftSimJsonString(OutResult.MaterialIdentityRelativePath),
        *OutResult.MaterialIdentityDigest,
        *EscapeRaftSimJsonString(OutResult.BaseColorAssetPath),
        *EscapeRaftSimJsonString(OutResult.AlbedoAssetPath),
        *EscapeRaftSimJsonString(OutResult.NormalAssetPath),
        *EscapeRaftSimJsonString(OutResult.OpacityAssetPath),
        *EscapeRaftSimJsonString(OutResult.DepthAssetPath),
        *EscapeRaftSimJsonString(OutResult.MaterialIdentityAssetPath),

        *EscapeRaftSimJsonString(OutResult.MaterialAssetPath),
        *EscapeRaftSimJsonString(OutResult.RelightableMaterialAssetPath),
        *EscapeRaftSimJsonString(OutResult.RelightableTrunkMaterialAssetPath),
        *EscapeRaftSimJsonString(OutResult.RelightableFoliageMaterialAssetPath),
        bUseDepthParallax
            ? TEXT("camera-facing 32x32 tessellated XY grid with depth-atlas vertex displacement")
            : TEXT("camera-facing XY plane through world-position offset"),
        bUseColorCorrectHlod
            ? TEXT("masked unlit source-lit RGB with bounded color gain")
            : TEXT("masked unlit baked FinalColorLDR"),
        AtlasColorGain.R,
        AtlasColorGain.G,
        AtlasColorGain.B,
        bUseDepthParallax ? TEXT(", \"depth\"") : TEXT(""),
        bUseDepthParallax ? TEXT("\"world_normal\"") : TEXT("\"world_normal\", \"depth\""),
        TEXT("false"),
        bUseDepthParallax ? TEXT("false") : TEXT("true"),
        bEnableComplementaryTransition ? TEXT("true") : TEXT("false"),
        OutResult.IsRelightableReady() ? TEXT("true") : TEXT("false"),
        OutResult.IsSplitRelightableReady() ? TEXT("true") : TEXT("false"));
    const bool bManifestSaved = FFileHelper::SaveStringToFile(Manifest, *ManifestAbsolutePath);
    if (!bManifestSaved)
    {
        OutSummary += TEXT("Multi-view atlas manifest failed to save.\n");
    }
    OutSummary += FString::Printf(
        TEXT("Multi-view atlas generated 16 views at %d px into %d px outputs; coverage %.6f to %.6f.\n"),
        TileResolution,
        AtlasResolution,
        OutResult.MinimumCoverage,
        OutResult.MaximumCoverage);
    return bManifestSaved && OutResult.IsSplitRelightableReady();
}
} // namespace

void FRaftSimEditorModule::HandleEvaluateFutaleufuCordilleraCypressPveCandidateCommand(
    const TArray<FString>& Args)
{
    if (ProceduralBeechExecutionSource)
    {
        UE_LOG(LogRaftSimEditor, Warning, TEXT("A PVE candidate evaluation is already running."));
        return;
    }

    const FString Variant = Args.IsEmpty() ? TEXT("open_grown_conical") : Args[0];
    const FString PaletteMode = Args.Num() > 1
        ? Args[1].ToLower()
        : TEXT("flat_cards");
    if (PaletteMode != TEXT("flat_cards") && PaletteMode != TEXT("curved_shells") &&
        PaletteMode != TEXT("twig_hierarchy") &&
        PaletteMode != TEXT("connected_twig_hierarchy") &&
        PaletteMode != TEXT("compact_connected_twig_hierarchy") &&
        PaletteMode != TEXT("authored_scale_leaf_hierarchy") &&
        PaletteMode != TEXT("dense_authored_scale_leaf_hierarchy") &&
        PaletteMode != TEXT("botanical_flattened_spray_hierarchy") &&
        PaletteMode != TEXT("dense_botanical_flattened_spray_hierarchy") &&
        PaletteMode != TEXT("branchlet_mass_botanical_flattened_spray_hierarchy") &&
        PaletteMode != TEXT("hierarchical_botanical_shoot_cluster") &&
        PaletteMode != TEXT("terminal_cluster_botanical_shoot") &&
        PaletteMode != TEXT("compound_branchlet_atlas") &&
        PaletteMode != TEXT("detiered_compound_branchlet_atlas") &&
        PaletteMode != TEXT("async_secondary_compound_branchlet_atlas") &&
        PaletteMode != TEXT("irregular_crown_mass_compound_branchlet_atlas") &&
        PaletteMode !=
            TEXT("hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas") &&
        PaletteMode != TEXT(
            "high_detail_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas") &&
        PaletteMode != TEXT(
            "frozen_wpo_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas") &&
        PaletteMode != TEXT(
            "frozen_wpo_high_detail_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas") &&
        PaletteMode != TEXT(
            "frozen_wpo_azimuth_registered_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas") &&
        PaletteMode != TEXT(
            "frozen_wpo_azimuth_registered_perspective_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas") &&
        PaletteMode != TEXT(
            "frozen_wpo_azimuth_registered_perspective_depth_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas") &&
        PaletteMode != TEXT(
            "frozen_wpo_azimuth_registered_perspective_complementary_transition_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas"))
    {
        UE_LOG(
            LogRaftSimEditor,
            Error,
            TEXT("Unsupported cypress palette mode %s; use flat_cards, curved_shells, twig_hierarchy, connected_twig_hierarchy, compact_connected_twig_hierarchy, authored_scale_leaf_hierarchy, dense_authored_scale_leaf_hierarchy, botanical_flattened_spray_hierarchy, dense_botanical_flattened_spray_hierarchy, branchlet_mass_botanical_flattened_spray_hierarchy, hierarchical_botanical_shoot_cluster, terminal_cluster_botanical_shoot, compound_branchlet_atlas, detiered_compound_branchlet_atlas, async_secondary_compound_branchlet_atlas, irregular_crown_mass_compound_branchlet_atlas, hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas, high_detail_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas, frozen_wpo_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas, frozen_wpo_high_detail_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas, frozen_wpo_azimuth_registered_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas, frozen_wpo_azimuth_registered_perspective_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas, frozen_wpo_azimuth_registered_perspective_depth_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas, or frozen_wpo_azimuth_registered_perspective_complementary_transition_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas."),
            *PaletteMode);
        return;
    }
    const FFutaleufuCypressPveFormSpec* Spec = FindFutaleufuCypressPveFormSpec(Variant);
    if (!Spec)
    {
        UE_LOG(
            LogRaftSimEditor,
            Error,
            TEXT("Unsupported V17 cypress PVE form %s; use one of the eight ids in the authoring manifest."),
            *Variant);
        return;
    }
    const bool bIrregularCrownMass =
        PaletteMode == TEXT("irregular_crown_mass_compound_branchlet_atlas") ||
        PaletteMode ==
            TEXT("hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas") ||
        PaletteMode == TEXT(
            "high_detail_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas") ||
        PaletteMode == TEXT(
            "frozen_wpo_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas") ||
        PaletteMode == TEXT(
            "frozen_wpo_high_detail_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas") ||
        PaletteMode == TEXT(
            "frozen_wpo_azimuth_registered_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas") ||
        PaletteMode == TEXT(
            "frozen_wpo_azimuth_registered_perspective_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas") ||
        PaletteMode == TEXT(
            "frozen_wpo_azimuth_registered_perspective_depth_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas") ||
        PaletteMode == TEXT(
            "frozen_wpo_azimuth_registered_perspective_complementary_transition_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas");
    const bool bAsyncSecondaryCrown =
        PaletteMode == TEXT("async_secondary_compound_branchlet_atlas") ||
        bIrregularCrownMass;
    const bool bDeTieredCrown =
        PaletteMode == TEXT("detiered_compound_branchlet_atlas") ||
        bAsyncSecondaryCrown;

    UWorld* PaletteWorld = UEditorLoadingAndSavingUtils::NewBlankMap(false);
    TArray<FString> LiveTwigPaths;
    FString DeadTwigPath;
    FString PaletteSummary;
    if (!CreateFutaleufuCypressPvePalette(
            PaletteWorld,
            PaletteMode,
            LiveTwigPaths,
            DeadTwigPath,
            PaletteSummary))
    {
        UE_LOG(
            LogRaftSimEditor,
            Error,
            TEXT("Could not create the retained project-owned PVE palette.\n%s"),
            *PaletteSummary);
        return;
    }

    const FString SamplePath =
        TEXT("/ProceduralVegetationEditor/SampleAssets/StarterContent/ConiferTree_01/"
             "PVE_Sample_Conifer_Tree_01.PVE_Sample_Conifer_Tree_01");
    UProceduralVegetation* Sample = LoadObject<UProceduralVegetation>(nullptr, *SamplePath);
    if (!Sample)
    {
        UE_LOG(LogRaftSimEditor, Error, TEXT("Could not load the installed UE 5.8 conifer PVE graph."));
        return;
    }

    UPCGGraph* SampleGraph = Cast<UPCGGraph>(Sample->GetGraph());
    UPCGSettings* SampleMesherSettings = FindPveSettingsByClassName(
        SampleGraph, TEXT("PVMeshBuilderSettings"));
    UPCGSettings* SampleProfileSettings = FindPveSettingsByClassName(
        SampleGraph, TEXT("PVPlantProfileLoaderSettings"));
    if (!SampleGraph || !SampleMesherSettings || !SampleProfileSettings)
    {
        UE_LOG(
            LogRaftSimEditor,
            Error,
            TEXT("The installed PVE sample no longer exposes the bounded mesher/profile donor contract."));
        return;
    }

    ProceduralBeechCandidateAsset = NewObject<UProceduralVegetation>(
        GetTransientPackage(),
        UProceduralVegetation::StaticClass(),
        TEXT("RaftSimFutaleufuCordilleraCypressPveCandidate"),
        RF_Transient);
    if (!ProceduralBeechCandidateAsset)
    {
        UE_LOG(LogRaftSimEditor, Error, TEXT("Could not create the project-owned cypress PVE asset."));
        return;
    }
    ProceduralBeechCandidateAsset->CreateGraph();
    ProceduralBeechCandidateAsset->AddToRoot();
    ProceduralBeechVariant = Spec->Id;
    ProceduralCypressPaletteMode = PaletteMode;
    bProceduralCypressPveCandidate = true;
    UPCGGraph* Graph = Cast<UPCGGraph>(ProceduralBeechCandidateAsset->GetGraph());
    if (!Graph || !Graph->GetOutputNode())
    {
        FinishProceduralBeechCandidate(false, TEXT("project-owned V17 PVE graph was not created"));
        return;
    }

    UPCGSettings* BranchGrowerSettings = nullptr;
    UPCGSettings* AsyncBranchGrowerSettingsB = nullptr;
    UPCGSettings* AsyncBranchGrowerSettingsC = nullptr;
    UPCGSettings* MainGrowerSettings = nullptr;
    UPCGSettings* GraftPaletteSettings = nullptr;
    UPCGSettings* GraftDistributorSettings = nullptr;
    UPCGSettings* ScaleSettings = nullptr;
    UPCGSettings* GravitySettings = nullptr;
    UPCGSettings* MesherSettings = nullptr;
    UPCGSettings* ProfileSettings = nullptr;
    UPCGSettings* BoneReductionSettings = nullptr;
    UPCGSettings* DeadPaletteSettings = nullptr;
    UPCGSettings* DeadDistributorSettings = nullptr;
    UPCGSettings* LivePaletteSettings = nullptr;
    UPCGSettings* LiveDistributorSettings = nullptr;

    UPCGNode* BranchGrowerNode = AddProjectPveNode(
        Graph, TEXT("PVGrowerSettings"), BranchGrowerSettings);
    UPCGNode* AsyncBranchGrowerNodeB = bAsyncSecondaryCrown
        ? AddProjectPveNode(
              Graph, TEXT("PVGrowerSettings"), AsyncBranchGrowerSettingsB)
        : nullptr;
    UPCGNode* AsyncBranchGrowerNodeC = bAsyncSecondaryCrown
        ? AddProjectPveNode(
              Graph, TEXT("PVGrowerSettings"), AsyncBranchGrowerSettingsC)
        : nullptr;
    UPCGNode* GraftPaletteNode = AddProjectPveNode(
        Graph, TEXT("PVGraftPaletteSettings"), GraftPaletteSettings);
    UPCGNode* MainGrowerNode = AddProjectPveNode(
        Graph, TEXT("PVGrowerSettings"), MainGrowerSettings);
    UPCGNode* GraftDistributorNode = AddProjectPveNode(
        Graph, TEXT("PVGraftDistributorSettings"), GraftDistributorSettings);
    UPCGNode* ScaleNode = AddProjectPveNode(
        Graph, TEXT("PVScaleSettings"), ScaleSettings);
    UPCGNode* GravityNode = AddProjectPveNode(
        Graph, TEXT("PVGravitySettings"), GravitySettings);
    UPCGNode* MesherNode = Graph->AddNodeCopy(SampleMesherSettings, MesherSettings);
    UPCGNode* ProfileNode = Graph->AddNodeCopy(SampleProfileSettings, ProfileSettings);
    UPCGNode* BoneReductionNode = AddProjectPveNode(
        Graph, TEXT("PVBoneReductionSettings"), BoneReductionSettings);
    UPCGNode* DeadPaletteNode = AddProjectPveNode(
        Graph, TEXT("PVFoliagePaletteSettings"), DeadPaletteSettings);
    UPCGNode* DeadDistributorNode = AddProjectPveNode(
        Graph, TEXT("PVFoliageDistributorSettings"), DeadDistributorSettings);
    UPCGNode* LivePaletteNode = AddProjectPveNode(
        Graph, TEXT("PVFoliagePaletteSettings"), LivePaletteSettings);
    UPCGNode* LiveDistributorNode = AddProjectPveNode(
        Graph, TEXT("PVFoliageDistributorSettings"), LiveDistributorSettings);

    const bool bAsyncBranchNodesCreated = !bAsyncSecondaryCrown ||
        (AsyncBranchGrowerNodeB && AsyncBranchGrowerNodeC);
    const bool bNodesCreated = BranchGrowerNode && bAsyncBranchNodesCreated &&
        GraftPaletteNode && MainGrowerNode &&
        GraftDistributorNode && ScaleNode && GravityNode && MesherNode && ProfileNode &&
        BoneReductionNode && DeadPaletteNode && DeadDistributorNode && LivePaletteNode &&
        LiveDistributorNode;
    bool bConfigured = bNodesCreated;
    bConfigured &= ConfigureFutaleufuCypressPveGrower(
        BranchGrowerSettings, *Spec, true, bDeTieredCrown, 0);
    if (bAsyncSecondaryCrown)
    {
        bConfigured &= ConfigureFutaleufuCypressPveGrower(
            AsyncBranchGrowerSettingsB, *Spec, true, bDeTieredCrown, 1);
        bConfigured &= ConfigureFutaleufuCypressPveGrower(
            AsyncBranchGrowerSettingsC, *Spec, true, bDeTieredCrown, 2);
    }
    bConfigured &= ConfigureFutaleufuCypressPveGrower(
        MainGrowerSettings, *Spec, false, bDeTieredCrown, 0);
    bConfigured &= SetPveGraftPaletteEntryCount(
        GraftPaletteSettings, bAsyncSecondaryCrown ? 3 : 1);
    bConfigured &= SetPveFoliagePaletteMeshes(
        DeadPaletteSettings, TArray<FString>{DeadTwigPath});
    bConfigured &= SetPveFoliagePaletteMeshes(LivePaletteSettings, LiveTwigPaths);
    bConfigured &= SetPvePropertyText(
        ScaleSettings, TEXT("Scale"), FString::Printf(TEXT("%.6f"), Spec->WholeTreeScale));
    bConfigured &= SetPveStructFloat(
        GravitySettings,
        TEXT("GravitySettings"),
        TEXT("Gravity"),
        Spec->GravityStrength * (Spec->bAllowSenescence ? 0.55f : 0.05f));
    bConfigured &= SetPveStructFloat(
        GravitySettings,
        TEXT("GravitySettings"),
        TEXT("AngleCorrection"),
        Spec->bAllowSenescence
            ? FMath::Max(Spec->GravityAngleCorrection, 0.52f)
            : FMath::Max(Spec->GravityAngleCorrection, 0.92f));
    bConfigured &= SetPvePropertyText(
        BoneReductionSettings, TEXT("Strength"), TEXT("0.720000"));
    bConfigured &= SetPveNestedFloat(
        MesherSettings,
        TEXT("MesherSettings"),
        TEXT("BranchRadius"),
        TEXT("MinRadius"),
        0.0008f);

    bConfigured &= SetPvePropertyText(
        GraftDistributorSettings, TEXT("Mode"), TEXT("ParametricSettings"));
    bConfigured &= SetPvePropertyText(
        GraftDistributorSettings,
        TEXT("RandomSeed"),
        FString::FromInt(Spec->Seed + 700001));
    bConfigured &= SetPvePropertyText(
        GraftDistributorSettings, TEXT("bRecomputeLight"), TEXT("True"));
    bConfigured &= SetPveNestedInt(
        GraftDistributorSettings,
        TEXT("ParametricSettings"),
        TEXT("SpacingSettings"),
        TEXT("BranchDensity"),
        FMath::Clamp(Spec->GraftDensity, 18, 36));
    bConfigured &= SetPveNestedFloat(
        GraftDistributorSettings,
        TEXT("ParametricSettings"),
        TEXT("SpacingSettings"),
        TEXT("RelativeStart"),
        Spec->GraftRelativeStart);
    bConfigured &= SetPveNestedFloat(
        GraftDistributorSettings,
        TEXT("ParametricSettings"),
        TEXT("SpacingSettings"),
        TEXT("RelativeEnd"),
        bDeTieredCrown ? 0.98f : 1.0f);
    bConfigured &= SetPveNestedBool(
        GraftDistributorSettings,
        TEXT("ParametricSettings"),
        TEXT("SpacingSettings"),
        TEXT("LimitStartGeneration"),
        true);
    bConfigured &= SetPveNestedInt(
        GraftDistributorSettings,
        TEXT("ParametricSettings"),
        TEXT("SpacingSettings"),
        TEXT("StartGeneration"),

        2);
    bConfigured &= SetPveNestedBool(
        GraftDistributorSettings,
        TEXT("ParametricSettings"),
        TEXT("SpacingSettings"),
        TEXT("LimitEndGeneration"),
        true);
    bConfigured &= SetPveNestedInt(
        GraftDistributorSettings,
        TEXT("ParametricSettings"),
        TEXT("SpacingSettings"),
        TEXT("EndGeneration"),
        2);
    bConfigured &= SetPveNestedText(
        GraftDistributorSettings,
        TEXT("ParametricSettings"),
        TEXT("SpacingSettings"),
        TEXT("SpacingBasis"),
        TEXT("Branch"));
    bConfigured &= SetPveNestedBool(
        GraftDistributorSettings,
        TEXT("ParametricSettings"),
        TEXT("PhyllotaxySettings"),
        TEXT("ResetPhyllotaxy"),
        true);
    bConfigured &= SetPveNestedText(
        GraftDistributorSettings,
        TEXT("ParametricSettings"),
        TEXT("PhyllotaxySettings"),
        TEXT("PhyllotaxyType"),
        TEXT("Spiral"));
    bConfigured &= SetPveNestedFloat(
        GraftDistributorSettings,
        TEXT("ParametricSettings"),
        TEXT("PhyllotaxySettings"),
        TEXT("PhyllotaxyAdditionalAngle"),
        bDeTieredCrown ? 137.507764f : 17.5f);
    bConfigured &= SetPveNestedFloat(
        GraftDistributorSettings,
        TEXT("ParametricSettings"),
        TEXT("AngleSettings"),
        TEXT("AxilAngle"),
        bDeTieredCrown ? 66.0f : 72.0f);
    bConfigured &= SetPveNestedFloat(
        GraftDistributorSettings,
        TEXT("ParametricSettings"),
        TEXT("AngleSettings"),
        TEXT("RandomizeAxilAngleMinimum"),
        bDeTieredCrown ? -18.0f : -8.0f);
    bConfigured &= SetPveNestedFloat(
        GraftDistributorSettings,
        TEXT("ParametricSettings"),
        TEXT("AngleSettings"),
        TEXT("RandomizeAxilAngleMaximum"),
        bDeTieredCrown ? 18.0f : 8.0f);
    if (bIrregularCrownMass)
    {
        bConfigured &= SetPveNestedText(
            GraftDistributorSettings,
            TEXT("ParametricSettings"),
            TEXT("ScaleSettings"),
            TEXT("ScaleRampBasis"),
            TEXT("Plant"));
        bConfigured &= SetPveNestedFloat(
            GraftDistributorSettings,
            TEXT("ParametricSettings"),
            TEXT("ScaleSettings"),
            TEXT("BaseScale"),
            1.0f);
        bConfigured &= SetPveNestedFloat(
            GraftDistributorSettings,
            TEXT("ParametricSettings"),
            TEXT("ScaleSettings"),
            TEXT("RandomizeScaleMinimum"),
            0.88f);
        bConfigured &= SetPveNestedFloat(
            GraftDistributorSettings,
            TEXT("ParametricSettings"),
            TEXT("ScaleSettings"),
            TEXT("RandomizeScaleMaximum"),
            1.12f);
        bConfigured &= SetPveNestedRamp(
            GraftDistributorSettings,
            TEXT("ParametricSettings"),
            TEXT("ScaleSettings"),
            TEXT("ScaleRamp"),
            TArray<FVector2f>{
                {0.0f, 0.92f},
                {0.18f, 0.96f},
                {0.40f, 0.98f},
                {0.62f, 0.94f},
                {0.82f, 0.82f},
                {1.0f, 0.48f}});
    }

    bConfigured &= SetPvePropertyText(
        DeadDistributorSettings, TEXT("Mode"), TEXT("ParametricSettings"));
    bConfigured &= SetPvePropertyText(
        DeadDistributorSettings,
        TEXT("RandomSeed"),
        FString::FromInt(Spec->Seed + 101012));
    bConfigured &= SetPveNestedInt(
        DeadDistributorSettings,
        TEXT("ParametricSettings"),
        TEXT("SpacingSettings"),
        TEXT("BranchDensity"),
        Spec->bAllowSenescence ? 6 : 0);
    bConfigured &= SetPveNestedFloat(
        DeadDistributorSettings,
        TEXT("ParametricSettings"),
        TEXT("SpacingSettings"),
        TEXT("RelativeStart"),
        0.62f);
    bConfigured &= SetPveNestedFloat(
        DeadDistributorSettings,
        TEXT("ParametricSettings"),
        TEXT("ScaleSettings"),
        TEXT("BaseScale"),
        0.38f);
    bConfigured &= SetPveNestedBool(
        DeadDistributorSettings,
        TEXT("ParametricSettings"),
        TEXT("SpacingSettings"),
        TEXT("LimitStartGeneration"),
        true);
    bConfigured &= SetPveNestedInt(
        DeadDistributorSettings,
        TEXT("ParametricSettings"),
        TEXT("SpacingSettings"),
        TEXT("StartGeneration"),
        2);
    bConfigured &= SetPveNestedBool(
        DeadDistributorSettings,
        TEXT("ParametricSettings"),
        TEXT("SpacingSettings"),
        TEXT("LimitEndGeneration"),
        true);
    bConfigured &= SetPveNestedInt(
        DeadDistributorSettings,
        TEXT("ParametricSettings"),
        TEXT("SpacingSettings"),
        TEXT("EndGeneration"),
        2);

    bConfigured &= SetPvePropertyText(
        LiveDistributorSettings, TEXT("Mode"), TEXT("HormoneBasedSettings"));
    bConfigured &= SetPvePropertyText(
        LiveDistributorSettings,
        TEXT("RandomSeed"),
        FString::FromInt(Spec->Seed + 100003));
    bConfigured &= SetPveNestedFloat(
        LiveDistributorSettings,
        TEXT("HormoneBasedSettings"),
        TEXT("ScaleSettings"),
        TEXT("BaseScale"),
        Spec->LiveTwigScale * 1.50f);
    bConfigured &= SetPveNestedFloat(
        LiveDistributorSettings,
        TEXT("HormoneBasedSettings"),
        TEXT("ScaleSettings"),
        TEXT("MinScale"),
        0.80f);
    bConfigured &= SetPveNestedFloat(
        LiveDistributorSettings,
        TEXT("HormoneBasedSettings"),
        TEXT("ScaleSettings"),
        TEXT("MaxScale"),
        1.35f);
    bConfigured &= SetPveNestedFloat(
        LiveDistributorSettings,
        TEXT("HormoneBasedSettings"),
        TEXT("DistributionSettings"),
        TEXT("EthyleneThreshold"),
        0.72f);
    bConfigured &= SetPveNestedFloat(
        LiveDistributorSettings,
        TEXT("HormoneBasedSettings"),
        TEXT("DistributionSettings"),
        TEXT("InstanceSpacing"),
        bIrregularCrownMass ? 0.096f : 0.055f);
    bConfigured &= SetPveNestedFloat(
        LiveDistributorSettings,
        TEXT("HormoneBasedSettings"),
        TEXT("DistributionSettings"),
        TEXT("InstanceSpacingRampEffect"),
        0.45f);
    bConfigured &= SetPveNestedBool(
        LiveDistributorSettings,
        TEXT("HormoneBasedSettings"),
        TEXT("AngleSettings"),
        TEXT("OverrideAxilAngle"),
        true);
    bConfigured &= SetPveNestedFloat(
        LiveDistributorSettings,
        TEXT("HormoneBasedSettings"),
        TEXT("AngleSettings"),
        TEXT("AxilAngle"),
        18.0f);

    for (UPCGNode* Node : Graph->GetNodes())
    {
        if (Node)
        {
            Node->UpdateAfterSettingsChangeDuringCreation();
        }
    }

    auto AddRequiredEdge = [Graph](
                               UPCGNode* FromNode,
                               const FName& FromPin,
                               UPCGNode* ToNode,
                               const FName& ToPin)
    {
        return Graph->AddEdge(FromNode, FromPin, ToNode, ToPin) != nullptr;
    };
    bool bGraphWired = bConfigured;
    bGraphWired &= AddRequiredEdge(BranchGrowerNode, TEXT("Out"), GraftPaletteNode, TEXT("Graft 1"));
    if (bAsyncSecondaryCrown)
    {
        bGraphWired &= AddRequiredEdge(
            AsyncBranchGrowerNodeB, TEXT("Out"), GraftPaletteNode, TEXT("Graft 2"));
        bGraphWired &= AddRequiredEdge(
            AsyncBranchGrowerNodeC, TEXT("Out"), GraftPaletteNode, TEXT("Graft 3"));
    }
    bGraphWired &= AddRequiredEdge(MainGrowerNode, TEXT("Out"), GraftDistributorNode, TEXT("Skeleton"));
    bGraphWired &= AddRequiredEdge(GraftPaletteNode, TEXT("Out"), GraftDistributorNode, TEXT("Graft"));
    bGraphWired &= AddRequiredEdge(GraftDistributorNode, TEXT("Out"), ScaleNode, TEXT("In"));
    bGraphWired &= AddRequiredEdge(ScaleNode, TEXT("Out"), GravityNode, TEXT("In"));
    bGraphWired &= AddRequiredEdge(GravityNode, TEXT("Out"), MesherNode, TEXT("In"));
    bGraphWired &= AddRequiredEdge(ProfileNode, TEXT("plantProfile_10"), MesherNode, TEXT("Profile"));
    bGraphWired &= AddRequiredEdge(MesherNode, TEXT("Out"), BoneReductionNode, TEXT("In"));
    if (Spec->bAllowSenescence)
    {
        bGraphWired &= AddRequiredEdge(BoneReductionNode, TEXT("Out"), DeadDistributorNode, TEXT("In"));
        bGraphWired &= AddRequiredEdge(DeadPaletteNode, TEXT("Out"), DeadDistributorNode, TEXT("Foliage"));
        bGraphWired &= AddRequiredEdge(DeadDistributorNode, TEXT("Out"), LiveDistributorNode, TEXT("In"));
    }
    else
    {
        bGraphWired &= AddRequiredEdge(BoneReductionNode, TEXT("Out"), LiveDistributorNode, TEXT("In"));
    }
    bGraphWired &= AddRequiredEdge(LivePaletteNode, TEXT("Out"), LiveDistributorNode, TEXT("Foliage"));
    bGraphWired &= AddRequiredEdge(LiveDistributorNode, TEXT("Out"), Graph->GetOutputNode(), TEXT("Out"));
    if (!bGraphWired)
    {
        FinishProceduralBeechCandidate(
            false,
            TEXT("project-owned V17 cypress graph configuration or wiring failed"));
        return;
    }

    FPCGGenerationPostProcessCallback PostProcessCallback;
    PostProcessCallback.BindRaw(this, &FRaftSimEditorModule::HandleProceduralBeechPostProcess);
    FPCGDefaultExecutionSourceParams ExecutionParams;
    ExecutionParams.GraphInterface = Graph;
    ExecutionParams.Seed = Spec->Seed;
    ExecutionParams.PostProcessCallback = MoveTemp(PostProcessCallback);
    ProceduralBeechExecutionSource =
        IPCGBaseSubsystem::CreateExecutionSource<UPCGDefaultExecutionSource>(ExecutionParams);
    if (!ProceduralBeechExecutionSource)
    {
        FinishProceduralBeechCandidate(false, TEXT("could not create the V17 PCG execution source"));
        return;
    }
    ProceduralBeechExecutionSource->AddToRoot();
    ProceduralBeechOutputCollection.Reset();
    ProceduralBeechStartSeconds = FPlatformTime::Seconds();
    ProceduralBeechExecutionSource->Generate();
    ProceduralBeechCandidateTickerHandle = FTSTicker::GetCoreTicker().AddTicker(
        FTickerDelegate::CreateRaw(this, &FRaftSimEditorModule::TickProceduralBeechCandidate),
        0.25f);
    UE_LOG(
        LogRaftSimEditor,
        Display,
        TEXT("Started V17 project-graph PVE cypress generation for %s with project-owned live/dead twig palettes.\n%s"),
        *Spec->Id,
        *PaletteSummary);
}

void FRaftSimEditorModule::HandleEvaluateProceduralBeechCandidateCommand(const TArray<FString>& Args)
{
    if (ProceduralBeechExecutionSource)
    {
        UE_LOG(LogRaftSimEditor, Warning, TEXT("A PVE candidate evaluation is already running."));
        return;
    }

    bProceduralCypressPveCandidate = false;
    ProceduralBeechVariant = Args.IsEmpty() ? TEXT("Beech_01") : Args[0];
    const TSet<FString> AllowedVariants = {TEXT("Beech_01"), TEXT("Beech_02"), TEXT("Beech_03"), TEXT("Beech_04")};
    if (!AllowedVariants.Contains(ProceduralBeechVariant))
    {
        UE_LOG(
            LogRaftSimEditor,
            Error,
            TEXT("Unsupported PVE beech variant %s; expected Beech_01 through Beech_04."),
            *ProceduralBeechVariant);
        return;
    }

    const FString SamplePath =
        TEXT("/ProceduralVegetationEditor/SampleAssets/StarterContent/DeciduousTree_01/"
             "PVE_Sample_Deciduous_Tree_01.PVE_Sample_Deciduous_Tree_01");
    UProceduralVegetation* Sample = LoadObject<UProceduralVegetation>(nullptr, *SamplePath);
    UClass* GrowthAssetClass = FindObject<UClass>(
        nullptr,
        TEXT("/Script/ProceduralVegetation.ProceduralVegetationGrowthDataAsset"));
    UClass* GrowthLoaderClass = FindObject<UClass>(
        nullptr,
        TEXT("/Script/ProceduralVegetation.PVGrowthDataLoaderSettings"));
    if (!Sample || !GrowthAssetClass || !GrowthLoaderClass)
    {
        FinishProceduralBeechCandidate(false, TEXT("required PVE sample or reflected classes are unavailable"));
        return;
    }

    ProceduralBeechGrowthAsset = NewObject<UObject>(
        GetTransientPackage(),
        GrowthAssetClass,
        TEXT("RaftSimFutaleufuEuropeanBeechGrowthData"),

        RF_Transient);
    if (!ProceduralBeechGrowthAsset)
    {
        FinishProceduralBeechCandidate(false, TEXT("could not create transient PVE growth-data asset"));
        return;
    }
    ProceduralBeechGrowthAsset->AddToRoot();

    const FString GrowthJsonDirectory = FPaths::ConvertRelativePathToFull(FPaths::Combine(
        FPaths::EngineDir(),
        TEXT("Plugins/Experimental/ProceduralVegetationEditor/Content/SampleAssets/"
             "Tree_European_Beech_01/Instances")));
    FStructProperty* JsonDirectoryProperty = FindFProperty<FStructProperty>(
        GrowthAssetClass,
        TEXT("JsonDirectoryPath"));
    UFunction* UpdateDataFunction = GrowthAssetClass->FindFunctionByName(TEXT("UpdateDataAsset"));
    if (!JsonDirectoryProperty || !UpdateDataFunction)
    {
        FinishProceduralBeechCandidate(false, TEXT("PVE growth-data reflection contract changed"));
        return;
    }
    FDirectoryPath* JsonDirectory = JsonDirectoryProperty->ContainerPtrToValuePtr<FDirectoryPath>(
        ProceduralBeechGrowthAsset);
    JsonDirectory->Path = GrowthJsonDirectory;
    ProceduralBeechGrowthAsset->ProcessEvent(UpdateDataFunction, nullptr);

    FArrayProperty* VariationsProperty = FindFProperty<FArrayProperty>(
        GrowthAssetClass,
        TEXT("GrowthVariations"));
    const int32 LoadedVariationCount = VariationsProperty
        ? FScriptArrayHelper(
              VariationsProperty,
              VariationsProperty->ContainerPtrToValuePtr<void>(ProceduralBeechGrowthAsset)).Num()
        : 0;
    if (LoadedVariationCount != 4)
    {
        FinishProceduralBeechCandidate(
            false,
            FString::Printf(TEXT("PVE growth-data asset loaded %d/4 beech variants"), LoadedVariationCount));
        return;
    }

    ProceduralBeechCandidateAsset = DuplicateObject<UProceduralVegetation>(
        Sample,
        GetTransientPackage(),
        TEXT("RaftSimFutaleufuEuropeanBeechCandidate"));
    if (!ProceduralBeechCandidateAsset)
    {
        FinishProceduralBeechCandidate(false, TEXT("could not duplicate the PVE sample graph"));
        return;
    }
    ProceduralBeechCandidateAsset->AddToRoot();
    UPCGGraph* Graph = Cast<UPCGGraph>(ProceduralBeechCandidateAsset->GetGraph());
    if (!Graph)
    {
        FinishProceduralBeechCandidate(false, TEXT("duplicated PVE candidate has no PCG graph"));
        return;
    }

    UPCGNode* MesherNode = nullptr;
    UPCGNode* ExportNode = nullptr;
    for (UPCGNode* Node : Graph->GetNodes())
    {
        UPCGSettings* Settings = Node ? Node->GetSettings() : nullptr;
        if (!Settings)
        {
            continue;
        }
        const FString SettingsClassName = Settings->GetClass()->GetName();
        MesherNode = SettingsClassName == TEXT("PVMeshBuilderSettings") ? Node : MesherNode;
        ExportNode = SettingsClassName == TEXT("PVExportSettings") ? Node : ExportNode;
    }
    if (!MesherNode || !ExportNode || !Graph->GetOutputNode())
    {
        FinishProceduralBeechCandidate(false, TEXT("PVE sample graph no longer exposes mesher/export/output nodes"));
        return;
    }

    UPCGSettings* LoaderSettings = nullptr;
    UPCGNode* LoaderNode = Graph->AddNodeOfType(GrowthLoaderClass, LoaderSettings);
    FObjectPropertyBase* GrowthAssetProperty = LoaderSettings
        ? FindFProperty<FObjectPropertyBase>(LoaderSettings->GetClass(), TEXT("GrowthAsset"))
        : nullptr;
    if (!LoaderNode || !LoaderSettings || !GrowthAssetProperty)
    {
        FinishProceduralBeechCandidate(false, TEXT("could not create or configure the PVE growth loader"));
        return;
    }
    GrowthAssetProperty->SetObjectPropertyValue_InContainer(LoaderSettings, ProceduralBeechGrowthAsset);
    LoaderNode->UpdateAfterSettingsChangeDuringCreation();

    if (!LoaderNode->GetOutputPin(FName(*ProceduralBeechVariant)))
    {
        FinishProceduralBeechCandidate(
            false,
            FString::Printf(TEXT("growth loader did not expose output pin %s"), *ProceduralBeechVariant));
        return;
    }
    Graph->RemoveInboundEdges(MesherNode, TEXT("In"));
    Graph->AddEdge(LoaderNode, FName(*ProceduralBeechVariant), MesherNode, TEXT("In"));
    Graph->AddEdge(ExportNode, TEXT("Out"), Graph->GetOutputNode(), TEXT("Out"));

    FPCGGenerationPostProcessCallback PostProcessCallback;
    PostProcessCallback.BindRaw(this, &FRaftSimEditorModule::HandleProceduralBeechPostProcess);
    FPCGDefaultExecutionSourceParams ExecutionParams;
    ExecutionParams.GraphInterface = Graph;
    ExecutionParams.Seed = 7023;
    ExecutionParams.PostProcessCallback = MoveTemp(PostProcessCallback);
    ProceduralBeechExecutionSource =
        IPCGBaseSubsystem::CreateExecutionSource<UPCGDefaultExecutionSource>(ExecutionParams);
    if (!ProceduralBeechExecutionSource)
    {
        FinishProceduralBeechCandidate(false, TEXT("could not create a default PCG execution source"));
        return;
    }
    ProceduralBeechExecutionSource->AddToRoot();
    ProceduralBeechOutputCollection.Reset();
    ProceduralBeechStartSeconds = FPlatformTime::Seconds();
    ProceduralBeechExecutionSource->Generate();
    ProceduralBeechCandidateTickerHandle = FTSTicker::GetCoreTicker().AddTicker(
        FTickerDelegate::CreateRaw(this, &FRaftSimEditorModule::TickProceduralBeechCandidate),
        0.25f);
    UE_LOG(
        LogRaftSimEditor,
        Display,
        TEXT("Started headless PVE structural evaluation for %s from %s."),
        *ProceduralBeechVariant,
        *GrowthJsonDirectory);
}

void FRaftSimEditorModule::HandleProceduralBeechPostProcess(const FPCGDataCollection& OutputData)
{
    for (const FPCGTaggedData& TaggedData : OutputData.TaggedData)
    {
        const UPVMeshData* MeshData = Cast<UPVMeshData>(TaggedData.Data);
        if (!MeshData || !MeshData->GetSharedCollection().IsValid())
        {
            continue;
        }
        ProceduralBeechOutputCollection = MakeShared<FManagedArrayCollection>();
        MeshData->GetSharedCollection()->CopyTo(ProceduralBeechOutputCollection.Get());
        UE_LOG(
            LogRaftSimEditor,
            Display,
            TEXT("Received PVE mesh output for %s on pin %s."),
            *ProceduralBeechVariant,
            *TaggedData.Pin.ToString());
        break;
    }
}

bool FRaftSimEditorModule::TickProceduralBeechCandidate(float)
{
    if (!ProceduralBeechExecutionSource)
    {
        ProceduralBeechCandidateTickerHandle.Reset();
        return false;
    }
    if (ProceduralBeechExecutionSource->GetExecutionState().IsGenerating())
    {
        if (FPlatformTime::Seconds() - ProceduralBeechStartSeconds < 180.0)
        {
            return true;
        }
        ProceduralBeechCandidateTickerHandle.Reset();
        FinishProceduralBeechCandidate(false, TEXT("PVE graph execution timed out after 180 seconds"));
        return false;
    }
    ProceduralBeechCandidateTickerHandle.Reset();
    if (!ProceduralBeechOutputCollection.IsValid())
    {
        FinishProceduralBeechCandidate(false, TEXT("PVE graph completed without a mesh collection at graph output"));
        return false;
    }

    const FFutaleufuCypressPveFormSpec* CypressSpec = bProceduralCypressPveCandidate
        ? FindFutaleufuCypressPveFormSpec(ProceduralBeechVariant)
        : nullptr;
    if (bProceduralCypressPveCandidate && !CypressSpec)
    {
        FinishProceduralBeechCandidate(false, TEXT("V16 cypress form context was lost after graph execution"));
        return false;
    }
    const bool bCurvedCypressShellPalette =
        bProceduralCypressPveCandidate &&
        ProceduralCypressPaletteMode == TEXT("curved_shells");
    const bool bHighDetailHlodCalibratedIrregularCrownMassCypressPalette =
        bProceduralCypressPveCandidate &&
        ProceduralCypressPaletteMode == TEXT(
            "high_detail_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas");
    const bool bFrozenWpoHighDetailHlodCalibratedIrregularCrownMassCypressPalette =
        bProceduralCypressPveCandidate &&
        ProceduralCypressPaletteMode == TEXT(
            "frozen_wpo_high_detail_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas");
    const bool bFrozenWpoAzimuthRegisteredPerspectiveDepthHlodCalibratedIrregularCrownMassCypressPalette =
        bProceduralCypressPveCandidate &&
        ProceduralCypressPaletteMode == TEXT(
            "frozen_wpo_azimuth_registered_perspective_depth_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas");
    const bool bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette =
        bProceduralCypressPveCandidate &&
        ProceduralCypressPaletteMode == TEXT(
            "frozen_wpo_azimuth_registered_perspective_complementary_transition_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas");
    const bool bFrozenWpoAzimuthRegisteredPerspectiveHlodCalibratedIrregularCrownMassCypressPalette =
        bProceduralCypressPveCandidate &&
        (ProceduralCypressPaletteMode == TEXT(
             "frozen_wpo_azimuth_registered_perspective_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas") ||
         bFrozenWpoAzimuthRegisteredPerspectiveDepthHlodCalibratedIrregularCrownMassCypressPalette ||
         bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette);
    const bool bFrozenWpoAzimuthRegisteredHlodCalibratedIrregularCrownMassCypressPalette =
        bProceduralCypressPveCandidate &&
        (ProceduralCypressPaletteMode == TEXT(
             "frozen_wpo_azimuth_registered_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas") ||
         bFrozenWpoAzimuthRegisteredPerspectiveHlodCalibratedIrregularCrownMassCypressPalette);
    const bool bFrozenWpoHlodCalibratedIrregularCrownMassCypressPalette =
        bProceduralCypressPveCandidate &&
        (ProceduralCypressPaletteMode == TEXT(
             "frozen_wpo_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas") ||
         bFrozenWpoHighDetailHlodCalibratedIrregularCrownMassCypressPalette ||
         bFrozenWpoAzimuthRegisteredHlodCalibratedIrregularCrownMassCypressPalette);
    const bool bHlodCalibratedIrregularCrownMassCypressPalette =
        bProceduralCypressPveCandidate &&
        (ProceduralCypressPaletteMode ==
             TEXT("hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas") ||
         bHighDetailHlodCalibratedIrregularCrownMassCypressPalette ||
         bFrozenWpoHlodCalibratedIrregularCrownMassCypressPalette);
    const bool bIrregularCrownMassCompoundBranchletAtlasCypressPalette =
        bProceduralCypressPveCandidate &&
        (ProceduralCypressPaletteMode ==
             TEXT("irregular_crown_mass_compound_branchlet_atlas") ||
         bHlodCalibratedIrregularCrownMassCypressPalette);
    const bool bAsyncSecondaryCompoundBranchletAtlasCypressPalette =
        bProceduralCypressPveCandidate &&
        (ProceduralCypressPaletteMode ==
             TEXT("async_secondary_compound_branchlet_atlas") ||
         bIrregularCrownMassCompoundBranchletAtlasCypressPalette);
    const bool bDeTieredCompoundBranchletAtlasCypressPalette =
        bProceduralCypressPveCandidate &&
        (ProceduralCypressPaletteMode == TEXT("detiered_compound_branchlet_atlas") ||
         bAsyncSecondaryCompoundBranchletAtlasCypressPalette);
    const bool bCompoundBranchletAtlasCypressPalette =
        bProceduralCypressPveCandidate &&
        (ProceduralCypressPaletteMode == TEXT("compound_branchlet_atlas") ||
         bDeTieredCompoundBranchletAtlasCypressPalette);
    const bool bTerminalClusterBotanicalShootCypressPalette =
        bProceduralCypressPveCandidate &&
        ProceduralCypressPaletteMode == TEXT("terminal_cluster_botanical_shoot");
    const bool bHierarchicalBotanicalShootClusterCypressPalette =
        bProceduralCypressPveCandidate &&
        ProceduralCypressPaletteMode ==
            TEXT("hierarchical_botanical_shoot_cluster");
    const bool bBranchletMassBotanicalFlattenedSprayCypressHierarchyPalette =
        bProceduralCypressPveCandidate &&
        (ProceduralCypressPaletteMode ==
             TEXT("branchlet_mass_botanical_flattened_spray_hierarchy") ||
         bHierarchicalBotanicalShootClusterCypressPalette ||
         bTerminalClusterBotanicalShootCypressPalette ||
         bCompoundBranchletAtlasCypressPalette);
    const bool bDenseBotanicalFlattenedSprayCypressHierarchyPalette =
        bProceduralCypressPveCandidate &&
        (ProceduralCypressPaletteMode ==
             TEXT("dense_botanical_flattened_spray_hierarchy") ||
         bBranchletMassBotanicalFlattenedSprayCypressHierarchyPalette);
    const bool bBotanicalFlattenedSprayCypressHierarchyPalette =
        bProceduralCypressPveCandidate &&
        (ProceduralCypressPaletteMode == TEXT("botanical_flattened_spray_hierarchy") ||
         bDenseBotanicalFlattenedSprayCypressHierarchyPalette);
    const bool bAuthoredScaleLeafCypressHierarchyPalette =
        bProceduralCypressPveCandidate &&
        (ProceduralCypressPaletteMode == TEXT("authored_scale_leaf_hierarchy") ||
         ProceduralCypressPaletteMode == TEXT("dense_authored_scale_leaf_hierarchy"));
    const bool bDenseAuthoredScaleLeafCypressHierarchyPalette =
        bProceduralCypressPveCandidate &&
        ProceduralCypressPaletteMode == TEXT("dense_authored_scale_leaf_hierarchy");
    const bool bTraditionalRasterCypressFoliagePalette =
        bAuthoredScaleLeafCypressHierarchyPalette ||
        bBotanicalFlattenedSprayCypressHierarchyPalette;
    const bool bCompactConnectedCypressTwigHierarchyPalette =
        bProceduralCypressPveCandidate &&
        ProceduralCypressPaletteMode == TEXT("compact_connected_twig_hierarchy");
    const bool bConnectedCypressTwigHierarchyPalette =
        bProceduralCypressPveCandidate &&
        (ProceduralCypressPaletteMode == TEXT("connected_twig_hierarchy") ||
         bCompactConnectedCypressTwigHierarchyPalette ||
         bAuthoredScaleLeafCypressHierarchyPalette ||
         bBotanicalFlattenedSprayCypressHierarchyPalette);
    const bool bCypressTwigHierarchyPalette =
        bProceduralCypressPveCandidate &&
        (ProceduralCypressPaletteMode == TEXT("twig_hierarchy") ||
         bConnectedCypressTwigHierarchyPalette);
    const FString UnfrozenLocalReviewNamespace = bProceduralCypressPveCandidate
        ? (bBotanicalFlattenedSprayCypressHierarchyPalette
               ? (bCompoundBranchletAtlasCypressPalette
                    ? (bDeTieredCompoundBranchletAtlasCypressPalette
                        ? (bAsyncSecondaryCompoundBranchletAtlasCypressPalette
                            ? (bIrregularCrownMassCompoundBranchletAtlasCypressPalette
                                ? (bHlodCalibratedIrregularCrownMassCypressPalette
                                    ? (bHighDetailHlodCalibratedIrregularCrownMassCypressPalette
                                        ? TEXT("PVEFutaleufuCordilleraCypressHighDetailHlodCalibratedIrregularCrownMassCompoundBranchletAtlas")
                                        : TEXT("PVEFutaleufuCordilleraCypressHlodCalibratedIrregularCrownMassCompoundBranchletAtlas"))
                                    : TEXT("PVEFutaleufuCordilleraCypressIrregularCrownMassCompoundBranchletAtlas"))
                                : TEXT("PVEFutaleufuCordilleraCypressAsyncSecondaryCompoundBranchletAtlas"))
                            : TEXT("PVEFutaleufuCordilleraCypressDeTieredCompoundBranchletAtlas"))
                        : TEXT("PVEFutaleufuCordilleraCypressCompoundBranchletAtlas"))
                    : (bTerminalClusterBotanicalShootCypressPalette
                    ? TEXT("PVEFutaleufuCordilleraCypressTerminalClusterBotanicalShoot")
                    : (bHierarchicalBotanicalShootClusterCypressPalette
                    ? TEXT("PVEFutaleufuCordilleraCypressHierarchicalBotanicalShootCluster")
                    : (bBranchletMassBotanicalFlattenedSprayCypressHierarchyPalette
                    ? TEXT("PVEFutaleufuCordilleraCypressBranchletMassBotanicalFlattenedSprayHierarchy")
                    : (bDenseBotanicalFlattenedSprayCypressHierarchyPalette
                        ? TEXT("PVEFutaleufuCordilleraCypressDenseBotanicalFlattenedSprayHierarchy")
                        : TEXT("PVEFutaleufuCordilleraCypressBotanicalFlattenedSprayHierarchy"))))))
               : (bDenseAuthoredScaleLeafCypressHierarchyPalette
               ? TEXT("PVEFutaleufuCordilleraCypressDenseAuthoredScaleLeafHierarchy")
               : (bAuthoredScaleLeafCypressHierarchyPalette
               ? TEXT("PVEFutaleufuCordilleraCypressAuthoredScaleLeafHierarchy")
               : (bCompactConnectedCypressTwigHierarchyPalette
               ? TEXT("PVEFutaleufuCordilleraCypressCompactConnectedTwigHierarchy")
               : (bConnectedCypressTwigHierarchyPalette
               ? TEXT("PVEFutaleufuCordilleraCypressConnectedTwigHierarchy")

               : (bCypressTwigHierarchyPalette
               ? TEXT("PVEFutaleufuCordilleraCypressTwigHierarchy")
               : (bCurvedCypressShellPalette
                      ? TEXT("PVEFutaleufuCordilleraCypressCurvedShell")
                      : TEXT("PVEFutaleufuCordilleraCypress"))))))))
        : TEXT("PVEFutaleufuEuropeanBeech");
    const FString LocalReviewNamespace =
        bFrozenWpoHlodCalibratedIrregularCrownMassCypressPalette
        ? (bFrozenWpoAzimuthRegisteredHlodCalibratedIrregularCrownMassCypressPalette
            ? (bFrozenWpoAzimuthRegisteredPerspectiveHlodCalibratedIrregularCrownMassCypressPalette
                ? (bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette
                    ? TEXT("PVEFutaleufuCordilleraCypressFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCompoundBranchletAtlas")
                    : (bFrozenWpoAzimuthRegisteredPerspectiveDepthHlodCalibratedIrregularCrownMassCypressPalette
                        ? TEXT("PVEFutaleufuCordilleraCypressFrozenWpoAzimuthRegisteredPerspectiveDepthHlodCalibratedIrregularCrownMassCompoundBranchletAtlas")
                        : TEXT("PVEFutaleufuCordilleraCypressFrozenWpoAzimuthRegisteredPerspectiveHlodCalibratedIrregularCrownMassCompoundBranchletAtlas")))
                : TEXT("PVEFutaleufuCordilleraCypressFrozenWpoAzimuthRegisteredHlodCalibratedIrregularCrownMassCompoundBranchletAtlas"))
            : (bFrozenWpoHighDetailHlodCalibratedIrregularCrownMassCypressPalette
            ? TEXT("PVEFutaleufuCordilleraCypressFrozenWpoHighDetailHlodCalibratedIrregularCrownMassCompoundBranchletAtlas")
            : TEXT("PVEFutaleufuCordilleraCypressFrozenWpoHlodCalibratedIrregularCrownMassCompoundBranchletAtlas")))
        : UnfrozenLocalReviewNamespace;
    const FString UnfrozenLocalSavedNamespace = bProceduralCypressPveCandidate
        ? (bBotanicalFlattenedSprayCypressHierarchyPalette
               ? (bCompoundBranchletAtlasCypressPalette
                    ? (bDeTieredCompoundBranchletAtlasCypressPalette
                        ? (bAsyncSecondaryCompoundBranchletAtlasCypressPalette
                            ? (bIrregularCrownMassCompoundBranchletAtlasCypressPalette
                                ? (bHlodCalibratedIrregularCrownMassCypressPalette
                                    ? (bHighDetailHlodCalibratedIrregularCrownMassCypressPalette
                                        ? TEXT("FutaleufuCordilleraCypressHighDetailHlodCalibratedIrregularCrownMassCompoundBranchletAtlas")
                                        : TEXT("FutaleufuCordilleraCypressHlodCalibratedIrregularCrownMassCompoundBranchletAtlas"))
                                    : TEXT("FutaleufuCordilleraCypressIrregularCrownMassCompoundBranchletAtlas"))
                                : TEXT("FutaleufuCordilleraCypressAsyncSecondaryCompoundBranchletAtlas"))
                            : TEXT("FutaleufuCordilleraCypressDeTieredCompoundBranchletAtlas"))
                        : TEXT("FutaleufuCordilleraCypressCompoundBranchletAtlas"))
                    : (bTerminalClusterBotanicalShootCypressPalette
                    ? TEXT("FutaleufuCordilleraCypressTerminalClusterBotanicalShoot")
                    : (bHierarchicalBotanicalShootClusterCypressPalette
                    ? TEXT("FutaleufuCordilleraCypressHierarchicalBotanicalShootCluster")
                    : (bBranchletMassBotanicalFlattenedSprayCypressHierarchyPalette
                    ? TEXT("FutaleufuCordilleraCypressBranchletMassBotanicalFlattenedSprayHierarchy")
                    : (bDenseBotanicalFlattenedSprayCypressHierarchyPalette
                        ? TEXT("FutaleufuCordilleraCypressDenseBotanicalFlattenedSprayHierarchy")
                        : TEXT("FutaleufuCordilleraCypressBotanicalFlattenedSprayHierarchy"))))))
               : (bDenseAuthoredScaleLeafCypressHierarchyPalette
               ? TEXT("FutaleufuCordilleraCypressDenseAuthoredScaleLeafHierarchy")
               : (bAuthoredScaleLeafCypressHierarchyPalette
               ? TEXT("FutaleufuCordilleraCypressAuthoredScaleLeafHierarchy")
               : (bCompactConnectedCypressTwigHierarchyPalette
               ? TEXT("FutaleufuCordilleraCypressCompactConnectedTwigHierarchy")
               : (bConnectedCypressTwigHierarchyPalette
               ? TEXT("FutaleufuCordilleraCypressConnectedTwigHierarchy")
               : (bCypressTwigHierarchyPalette
               ? TEXT("FutaleufuCordilleraCypressTwigHierarchy")
               : (bCurvedCypressShellPalette
                      ? TEXT("FutaleufuCordilleraCypressCurvedShell")
                      : TEXT("FutaleufuCordilleraCypress"))))))))
        : TEXT("FutaleufuEuropeanBeech");
    const FString LocalSavedNamespace =
        bFrozenWpoHlodCalibratedIrregularCrownMassCypressPalette
        ? (bFrozenWpoAzimuthRegisteredHlodCalibratedIrregularCrownMassCypressPalette
            ? (bFrozenWpoAzimuthRegisteredPerspectiveHlodCalibratedIrregularCrownMassCypressPalette
                ? (bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette
                    ? TEXT("FutaleufuCordilleraCypressFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCompoundBranchletAtlas")
                    : (bFrozenWpoAzimuthRegisteredPerspectiveDepthHlodCalibratedIrregularCrownMassCypressPalette
                        ? TEXT("FutaleufuCordilleraCypressFrozenWpoAzimuthRegisteredPerspectiveDepthHlodCalibratedIrregularCrownMassCompoundBranchletAtlas")
                        : TEXT("FutaleufuCordilleraCypressFrozenWpoAzimuthRegisteredPerspectiveHlodCalibratedIrregularCrownMassCompoundBranchletAtlas")))
                : TEXT("FutaleufuCordilleraCypressFrozenWpoAzimuthRegisteredHlodCalibratedIrregularCrownMassCompoundBranchletAtlas"))
            : (bFrozenWpoHighDetailHlodCalibratedIrregularCrownMassCypressPalette
            ? TEXT("FutaleufuCordilleraCypressFrozenWpoHighDetailHlodCalibratedIrregularCrownMassCompoundBranchletAtlas")
            : TEXT("FutaleufuCordilleraCypressFrozenWpoHlodCalibratedIrregularCrownMassCompoundBranchletAtlas")))
        : UnfrozenLocalSavedNamespace;
    const FString CandidateAssetToken = bProceduralCypressPveCandidate
        ? CypressSpec->AssetToken
        : ProceduralBeechVariant;
    const FString UnfrozenCandidateAssetPrefix = bProceduralCypressPveCandidate
        ? (bBotanicalFlattenedSprayCypressHierarchyPalette
               ? (bCompoundBranchletAtlasCypressPalette
                    ? (bDeTieredCompoundBranchletAtlasCypressPalette
                        ? (bAsyncSecondaryCompoundBranchletAtlasCypressPalette
                            ? (bIrregularCrownMassCompoundBranchletAtlasCypressPalette
                                ? (bHlodCalibratedIrregularCrownMassCypressPalette
                                    ? (bHighDetailHlodCalibratedIrregularCrownMassCypressPalette
                                        ? TEXT("FutaleufuPveCordilleraCypressHighDetailHlodCalibratedIrregularCrownMassCompoundBranchletAtlas")
                                        : TEXT("FutaleufuPveCordilleraCypressHlodCalibratedIrregularCrownMassCompoundBranchletAtlas"))
                                    : TEXT("FutaleufuPveCordilleraCypressIrregularCrownMassCompoundBranchletAtlas"))
                                : TEXT("FutaleufuPveCordilleraCypressAsyncSecondaryCompoundBranchletAtlas"))
                            : TEXT("FutaleufuPveCordilleraCypressDeTieredCompoundBranchletAtlas"))
                        : TEXT("FutaleufuPveCordilleraCypressCompoundBranchletAtlas"))
                    : (bTerminalClusterBotanicalShootCypressPalette
                    ? TEXT("FutaleufuPveCordilleraCypressTerminalClusterBotanicalShoot")
                    : (bHierarchicalBotanicalShootClusterCypressPalette
                    ? TEXT("FutaleufuPveCordilleraCypressHierarchicalBotanicalShootCluster")
                    : (bBranchletMassBotanicalFlattenedSprayCypressHierarchyPalette
                    ? TEXT("FutaleufuPveCordilleraCypressBranchletMassBotanicalFlattenedSprayHierarchy")
                    : (bDenseBotanicalFlattenedSprayCypressHierarchyPalette
                        ? TEXT("FutaleufuPveCordilleraCypressDenseBotanicalFlattenedSprayHierarchy")
                        : TEXT("FutaleufuPveCordilleraCypressBotanicalFlattenedSprayHierarchy"))))))
               : (bDenseAuthoredScaleLeafCypressHierarchyPalette
               ? TEXT("FutaleufuPveCordilleraCypressDenseAuthoredScaleLeafHierarchy")
               : (bAuthoredScaleLeafCypressHierarchyPalette
               ? TEXT("FutaleufuPveCordilleraCypressAuthoredScaleLeafHierarchy")
               : (bCompactConnectedCypressTwigHierarchyPalette
               ? TEXT("FutaleufuPveCordilleraCypressCompactConnectedTwigHierarchy")
               : (bConnectedCypressTwigHierarchyPalette
               ? TEXT("FutaleufuPveCordilleraCypressConnectedTwigHierarchy")
               : (bCypressTwigHierarchyPalette
               ? TEXT("FutaleufuPveCordilleraCypressTwigHierarchy")
               : (bCurvedCypressShellPalette
                      ? TEXT("FutaleufuPveCordilleraCypressCurvedShell")
                      : TEXT("FutaleufuPveCordilleraCypress"))))))))
        : TEXT("FutaleufuPveEuropean");

    const FString CandidateAssetPrefix =
        bFrozenWpoHlodCalibratedIrregularCrownMassCypressPalette
        ? (bFrozenWpoAzimuthRegisteredHlodCalibratedIrregularCrownMassCypressPalette
            ? (bFrozenWpoAzimuthRegisteredPerspectiveHlodCalibratedIrregularCrownMassCypressPalette
                ? (bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette
                    ? TEXT("FutaleufuPveCordilleraCypressFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCompoundBranchletAtlas")
                    : (bFrozenWpoAzimuthRegisteredPerspectiveDepthHlodCalibratedIrregularCrownMassCypressPalette
                        ? TEXT("FutaleufuPveCordilleraCypressFrozenWpoAzimuthRegisteredPerspectiveDepthHlodCalibratedIrregularCrownMassCompoundBranchletAtlas")
                        : TEXT("FutaleufuPveCordilleraCypressFrozenWpoAzimuthRegisteredPerspectiveHlodCalibratedIrregularCrownMassCompoundBranchletAtlas")))
                : TEXT("FutaleufuPveCordilleraCypressFrozenWpoAzimuthRegisteredHlodCalibratedIrregularCrownMassCompoundBranchletAtlas"))
            : (bFrozenWpoHighDetailHlodCalibratedIrregularCrownMassCypressPalette
            ? TEXT("FutaleufuPveCordilleraCypressFrozenWpoHighDetailHlodCalibratedIrregularCrownMassCompoundBranchletAtlas")
            : TEXT("FutaleufuPveCordilleraCypressFrozenWpoHlodCalibratedIrregularCrownMassCompoundBranchletAtlas")))
        : UnfrozenCandidateAssetPrefix;

    const FManagedArrayCollection& Collection = *ProceduralBeechOutputCollection;
    const int32 TransformCount = Collection.NumElements(FGeometryCollection::TransformGroup);
    const int32 VertexCount = Collection.NumElements(FGeometryCollection::VerticesGroup);
    const int32 TriangleCount = Collection.NumElements(FGeometryCollection::FacesGroup);
    const PV::Facades::FFoliageFacade FoliageFacade(Collection);
    const int32 FoliageMeshCount = FoliageFacade.IsValid() ? FoliageFacade.NumFoliageInfo() : 0;
    const int32 FoliageInstanceCount = FoliageFacade.IsValid() ? FoliageFacade.NumFoliageEntries() : 0;
    FString FoliageMeshesJson;
    if (FoliageFacade.IsValid())
    {
        for (int32 Index = 0; Index < FoliageFacade.NumFoliageInfo(); ++Index)
        {
            const FString MeshPath = FoliageFacade.GetFoliageInfo(Index).Mesh.ToString();
            FoliageMeshesJson += FString::Printf(
                TEXT("%s\"%s\""),
                Index == 0 ? TEXT("") : TEXT(", "),
                *EscapeRaftSimJsonString(MeshPath));
        }
    }

    bool bLocalTrunkExported = false;
    bool bLocalTrunkValidated = false;
    bool bLocalTrunkNaniteEnabled = false;
    bool bLocalTrunkPreserveArea = false;
    int32 LocalTrunkVertexCount = 0;
    int32 LocalTrunkTriangleCount = 0;
    int32 LocalTrunkMaterialSlotCount = 0;
    int32 LocalTrunkNonNullMaterialCount = 0;
    FVector LocalTrunkBoundsSize = FVector::ZeroVector;
    const FString LocalTrunkAssetPath = FString::Printf(
        TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/%s/SM_%s_%s_Trunk"),
        *LocalReviewNamespace,
        *CandidateAssetPrefix,
        *CandidateAssetToken);
    const FString LocalTrunkPackagePath = LocalTrunkAssetPath;
    const FString TrunkAssetName = FPackageName::GetShortName(LocalTrunkPackagePath);
    const FString LocalTrunkObjectPath = FString::Printf(
        TEXT("%s.%s"),
        *LocalTrunkPackagePath,
        *TrunkAssetName);
    UStaticMesh* TrunkMesh = LoadObject<UStaticMesh>(nullptr, *LocalTrunkObjectPath);
    const bool bNewTrunkMesh = TrunkMesh == nullptr;
    UPackage* TrunkPackage = TrunkMesh
        ? TrunkMesh->GetOutermost()
        : CreatePackage(*LocalTrunkPackagePath);
    if (TrunkPackage && !TrunkMesh)
    {
        TrunkMesh = NewObject<UStaticMesh>(TrunkPackage, *TrunkAssetName, RF_Public | RF_Standalone);
    }
    if (TrunkMesh)
    {
        const TUniquePtr<FGeometryCollection> GeometryCollection(
            Collection.NewCopy<FGeometryCollection>());
        if (GeometryCollection.IsValid() && TransformCount > 0)
        {
            const TManagedArray<FTransform3f>& BoneTransforms = Collection.GetAttribute<FTransform3f>(
                TEXT("Transform"),
                FGeometryCollection::TransformGroup);
            TArray<int32> TransformIndices;
            TransformIndices.Reserve(BoneTransforms.Num());
            for (int32 Index = 0; Index < BoneTransforms.Num(); ++Index)
            {
                TransformIndices.Add(Index);
            }
            UE::Geometry::FDynamicMesh3 CombinedMesh;
            FTransform UnusedTransform;
            ConvertGeometryCollectionToDynamicMesh(
                CombinedMesh,
                UnusedTransform,
                false,
                *GeometryCollection,
                false,
                BoneTransforms.GetConstArray(),
                true,
                TransformIndices);
            UDynamicMesh* DynamicMesh = NewObject<UDynamicMesh>(GetTransientPackage());
            DynamicMesh->SetMesh(MoveTemp(CombinedMesh));

            TArray<TObjectPtr<UMaterialInterface>> Materials;
            const TCHAR* CypressBarkMaterialObjectPath =
                bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette
                ? TEXT("/Game/RaftSim/Environment/ProceduralVegetation/FutaleufuNativeCanopy/"
                       "Materials/M_RaftSim_FutaleufuCordilleraCypress_V32_ComplementaryTransitionBark."
                       "M_RaftSim_FutaleufuCordilleraCypress_V32_ComplementaryTransitionBark")
                : TEXT("/Game/RaftSim/Environment/ProceduralVegetation/FutaleufuNativeCanopy/"
                       "Materials/M_RaftSim_FutaleufuCordilleraCypress_Bark."
                       "M_RaftSim_FutaleufuCordilleraCypress_Bark");
            UMaterialInterface* CypressBarkMaterial = bProceduralCypressPveCandidate
                ? LoadObject<UMaterialInterface>(nullptr, CypressBarkMaterialObjectPath)
                : nullptr;
            if (Collection.HasAttribute(TEXT("MaterialPath"), FGeometryCollection::MaterialGroup))
            {
                const TManagedArray<FString>& MaterialPaths = Collection.GetAttribute<FString>(
                    TEXT("MaterialPath"),
                    FGeometryCollection::MaterialGroup);
                for (const FString& MaterialPath : MaterialPaths)
                {
                    Materials.Add(CypressBarkMaterial
                        ? CypressBarkMaterial
                        : LoadObject<UMaterialInterface>(nullptr, *MaterialPath));
                }
            }
            FGeometryScriptCopyMeshToAssetOptions CopyOptions;
            CopyOptions.bEmitTransaction = false;
            CopyOptions.bDeferMeshPostEditChange = false;
            CopyOptions.bEnableRecomputeTangents = false;
            CopyOptions.bReplaceMaterials = true;
            CopyOptions.NewMaterials = Materials;
            CopyOptions.bApplyNaniteSettings = true;
            CopyOptions.NewNaniteSettings = TrunkMesh->GetNaniteSettings();
            CopyOptions.NewNaniteSettings.bEnabled =
                !bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette;
            CopyOptions.NewNaniteSettings.ShapePreservation = bProceduralCypressPveCandidate
                ? ENaniteShapePreservation::None
                : ENaniteShapePreservation::PreserveArea;
            EGeometryScriptOutcomePins CopyOutcome = EGeometryScriptOutcomePins::Failure;
            UGeometryScriptLibrary_StaticMeshFunctions::CopyMeshToStaticMesh(
                DynamicMesh,
                TrunkMesh,
                CopyOptions,
                FGeometryScriptMeshWriteLOD(),
                CopyOutcome,
                true,
                nullptr);
            if (CopyOutcome == EGeometryScriptOutcomePins::Success)
            {
                TrunkMesh->Modify();
                TrunkMesh->MarkPackageDirty();
                if (bNewTrunkMesh)
                {
                    FAssetRegistryModule::AssetCreated(TrunkMesh);
                }
                FAssetCompilingManager::Get().FinishAllCompilation();
                const FString TrunkFilename = FPackageName::LongPackageNameToFilename(
                    LocalTrunkPackagePath,
                    FPackageName::GetAssetPackageExtension());
                FSavePackageArgs SaveArgs;
                SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
                SaveArgs.SaveFlags = SAVE_NoError;
                bLocalTrunkExported = UPackage::SavePackage(
                    TrunkPackage,
                    TrunkMesh,
                    *TrunkFilename,
                    SaveArgs);
                if (bLocalTrunkExported)
                {
                    LocalTrunkVertexCount = TrunkMesh->GetNumVertices(0);
                    LocalTrunkTriangleCount = TrunkMesh->GetNumTriangles(0);
                    LocalTrunkMaterialSlotCount = TrunkMesh->GetStaticMaterials().Num();
                    for (int32 MaterialIndex = 0; MaterialIndex < LocalTrunkMaterialSlotCount; ++MaterialIndex)
                    {
                        LocalTrunkNonNullMaterialCount += TrunkMesh->GetMaterial(MaterialIndex) ? 1 : 0;
                    }
                    LocalTrunkBoundsSize = TrunkMesh->GetBoundingBox().GetSize();
                    bLocalTrunkNaniteEnabled = TrunkMesh->IsNaniteEnabled();
                    bLocalTrunkPreserveArea =
                        TrunkMesh->GetNaniteSettings().ShapePreservation ==
                        ENaniteShapePreservation::PreserveArea;
                    const bool bShapePreservationValid = bProceduralCypressPveCandidate
                        ? !bLocalTrunkPreserveArea
                        : bLocalTrunkPreserveArea;
                    const bool bTrunkRendererValid =
                        bLocalTrunkNaniteEnabled ||
                        bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette;
                    bLocalTrunkValidated =
                        bTrunkRendererValid &&
                        bShapePreservationValid &&
                        LocalTrunkVertexCount > 0 &&
                        LocalTrunkTriangleCount > 0 &&
                        LocalTrunkMaterialSlotCount > 0 &&
                        LocalTrunkNonNullMaterialCount == LocalTrunkMaterialSlotCount &&
                        LocalTrunkBoundsSize.X > 0.0 &&
                        LocalTrunkBoundsSize.Y > 0.0 &&
                        LocalTrunkBoundsSize.Z > 0.0;
                }
            }
        }
    }

    auto GetLocalFoliageTransform = [
                                        &FoliageFacade,
                                        this,
                                        TrunkMesh](int32 EntryIndex)
    {
        FTransform Transform = FoliageFacade.GetFoliageTransform(EntryIndex);
        if (!bProceduralCypressPveCandidate || !TrunkMesh)
        {
            return Transform;
        }
        const FBox Bounds = TrunkMesh->GetBoundingBox();
        const float Height = Bounds.GetSize().Z;
        const float CrownT = Height > UE_SMALL_NUMBER
            ? (Transform.GetLocation().Z - Bounds.Min.Z) / Height

            : 0.0f;
        if (CrownT > 0.86f)
        {
            const float UpperCrownT = FMath::Clamp((CrownT - 0.86f) / 0.14f, 0.0f, 1.0f);
            Transform.SetScale3D(
                Transform.GetScale3D() * FMath::Lerp(0.92f, 0.68f, UpperCrownT));
        }
        return Transform;
    };

    FString FoliageInstancesJson;
    if (FoliageFacade.IsValid())
    {
        for (int32 Index = 0; Index < FoliageFacade.NumFoliageEntries(); ++Index)
        {
            const PV::Facades::FFoliageEntryData Entry = FoliageFacade.GetFoliageEntry(Index);
            const FTransform Transform = GetLocalFoliageTransform(Index);
            const FVector Location = Transform.GetLocation();
            const FQuat Rotation = Transform.GetRotation();
            const FVector Scale = Transform.GetScale3D();
            FoliageInstancesJson += FString::Printf(
                TEXT("%s    {\"mesh_index\": %d, \"location_cm\": [%.6f, %.6f, %.6f], "
                     "\"rotation_xyzw\": [%.9f, %.9f, %.9f, %.9f], \"scale\": [%.6f, %.6f, %.6f]}"),
                Index == 0 ? TEXT("") : TEXT(",\n"),
                Entry.NameId,
                Location.X,
                Location.Y,
                Location.Z,
                Rotation.X,
                Rotation.Y,
                Rotation.Z,
                Rotation.W,
                Scale.X,
                Scale.Y,
                Scale.Z);
        }
    }
    const FString LocalTemplateDirectory = FPaths::Combine(
        FPaths::ProjectSavedDir(),
        TEXT("RaftSimPveReview"),
        LocalSavedNamespace);
    IFileManager::Get().MakeDirectory(*LocalTemplateDirectory, true);
    const FString LocalTemplatePath = FPaths::Combine(
        LocalTemplateDirectory,
        ProceduralBeechVariant.ToLower() + TEXT("_foliage_template.json"));
    const FString LocalTemplate = FString::Printf(
        TEXT("{\n")
        TEXT("  \"schema\": \"raftsim.unreal.local_pve_foliage_template.v1\",\n")
        TEXT("  \"variant\": \"%s\",\n")
        TEXT("  \"source_trunk_asset\": \"%s\",\n")
        TEXT("  \"foliage_meshes\": [%s],\n")
        TEXT("  \"instances\": [\n%s\n  ]\n")
        TEXT("}\n"),
        *EscapeRaftSimJsonString(ProceduralBeechVariant),
        *EscapeRaftSimJsonString(LocalTrunkAssetPath),
        *FoliageMeshesJson,
        *FoliageInstancesJson);
    const bool bLocalTemplateSaved = FFileHelper::SaveStringToFile(LocalTemplate, *LocalTemplatePath);
    const FString LocalTemplateReportPath = FString::Printf(
        TEXT("unreal/Saved/RaftSimPveReview/%s/%s_foliage_template.json"),
        *LocalSavedNamespace,
        *ProceduralBeechVariant.ToLower());

    bool bLocalImpostorSourceExported = false;
    bool bLocalImpostorSourceValidated = false;
    int32 LocalImpostorSourceVertexCount = 0;
    int32 LocalImpostorSourceTriangleCount = 0;
    int32 LocalImpostorSourceMaterialSlotCount = 0;
    int32 LocalImpostorSourceBarkMaterialSlotCount = 0;
    int32 LocalImpostorSourceFoliageMaterialSlotCount = 0;
    int32 LocalImpostorSourceSectionCount = 0;
    FVector LocalImpostorSourceBoundsSize = FVector::ZeroVector;
    bool bLocalImpostorSourceNaniteEnabled = false;
    bool bLocalImpostorSourcePreserveArea = false;
    UStaticMesh* LocalImpostorSourceMesh = nullptr;
    const FString LocalImpostorSourceAssetPath = FString::Printf(
        TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/%s/Impostor/"
             "SM_%s_%s_ImpostorSource"),
        *LocalReviewNamespace,
        *CandidateAssetPrefix,
        *CandidateAssetToken);
    if (bProceduralCypressPveCandidate && bLocalTrunkValidated && FoliageFacade.IsValid())
    {
        UDynamicMesh* CombinedSourceMesh = NewObject<UDynamicMesh>(GetTransientPackage());
        EGeometryScriptOutcomePins TrunkCopyOutcome = EGeometryScriptOutcomePins::Failure;
        UGeometryScriptLibrary_StaticMeshFunctions::CopyMeshFromStaticMeshV2(
            TrunkMesh,
            CombinedSourceMesh,
            FGeometryScriptCopyMeshFromAssetOptions(),
            FGeometryScriptMeshReadLOD(),
            TrunkCopyOutcome,
            false,
            nullptr);

        TArray<UMaterialInterface*> CombinedSourceMaterials;
        TArray<FName> CombinedSourceMaterialNames;
        UGeometryScriptLibrary_StaticMeshFunctions::GetMaterialListFromStaticMesh(
            TrunkMesh,
            CombinedSourceMaterials,
            CombinedSourceMaterialNames,
            nullptr);

        TArray<TObjectPtr<UDynamicMesh>> FoliageSourceMeshes;
        TArray<TArray<UMaterialInterface*>> FoliageSourceMaterials;
        FoliageSourceMeshes.SetNum(FoliageFacade.NumFoliageInfo());
        FoliageSourceMaterials.SetNum(FoliageFacade.NumFoliageInfo());
        bool bFoliageSourcesValid = TrunkCopyOutcome == EGeometryScriptOutcomePins::Success;
        for (int32 MeshIndex = 0; MeshIndex < FoliageFacade.NumFoliageInfo(); ++MeshIndex)
        {
            const FString FoliageMeshPath = FoliageFacade.GetFoliageInfo(MeshIndex).Mesh.ToString();
            UStaticMesh* FoliageMesh = LoadObject<UStaticMesh>(nullptr, *FoliageMeshPath);
            UDynamicMesh* FoliageDynamicMesh = FoliageMesh
                ? NewObject<UDynamicMesh>(GetTransientPackage())
                : nullptr;
            EGeometryScriptOutcomePins FoliageCopyOutcome = EGeometryScriptOutcomePins::Failure;
            if (FoliageMesh && FoliageDynamicMesh)
            {
                UGeometryScriptLibrary_StaticMeshFunctions::CopyMeshFromStaticMeshV2(
                    FoliageMesh,
                    FoliageDynamicMesh,
                    FGeometryScriptCopyMeshFromAssetOptions(),
                    FGeometryScriptMeshReadLOD(),
                    FoliageCopyOutcome,
                    false,
                    nullptr);
                TArray<FName> FoliageMaterialNames;
                UGeometryScriptLibrary_StaticMeshFunctions::GetMaterialListFromStaticMesh(
                    FoliageMesh,
                    FoliageSourceMaterials[MeshIndex],
                    FoliageMaterialNames,
                    nullptr);
            }
            bFoliageSourcesValid &=
                FoliageCopyOutcome == EGeometryScriptOutcomePins::Success &&
                !FoliageSourceMaterials[MeshIndex].IsEmpty();
            FoliageSourceMeshes[MeshIndex] = FoliageDynamicMesh;
        }

        if (bFoliageSourcesValid)
        {
            FGeometryScriptAppendMeshOptions AppendOptions;
            AppendOptions.CombineMode = EGeometryScriptCombineAttributesMode::EnableAllMatching;
            for (int32 EntryIndex = 0; EntryIndex < FoliageFacade.NumFoliageEntries(); ++EntryIndex)
            {
                const PV::Facades::FFoliageEntryData Entry =
                    FoliageFacade.GetFoliageEntry(EntryIndex);
                if (!FoliageSourceMeshes.IsValidIndex(Entry.NameId) ||
                    !FoliageSourceMeshes[Entry.NameId])
                {
                    bFoliageSourcesValid = false;
                    break;
                }
                TArray<UMaterialInterface*> AppendedMaterials;
                UGeometryScriptLibrary_MeshBasicEditFunctions::AppendMeshWithMaterials(
                    CombinedSourceMesh,
                    CombinedSourceMaterials,
                    FoliageSourceMeshes[Entry.NameId],
                    FoliageSourceMaterials[Entry.NameId],
                    AppendedMaterials,
                    GetLocalFoliageTransform(EntryIndex),
                    true,
                    AppendOptions,
                    true,
                    nullptr);
                CombinedSourceMaterials = MoveTemp(AppendedMaterials);
            }
        }

        const FString ImpostorSourceAssetName =
            FPackageName::GetShortName(LocalImpostorSourceAssetPath);
        const FString ImpostorSourceObjectPath = FString::Printf(
            TEXT("%s.%s"),
            *LocalImpostorSourceAssetPath,
            *ImpostorSourceAssetName);
        UStaticMesh* ImpostorSourceMesh = LoadObject<UStaticMesh>(
            nullptr,
            *ImpostorSourceObjectPath);
        const bool bNewImpostorSourceMesh = ImpostorSourceMesh == nullptr;
        UPackage* ImpostorSourcePackage = ImpostorSourceMesh
            ? ImpostorSourceMesh->GetOutermost()
            : CreatePackage(*LocalImpostorSourceAssetPath);
        if (bFoliageSourcesValid && ImpostorSourcePackage && !ImpostorSourceMesh)
        {
            ImpostorSourceMesh = NewObject<UStaticMesh>(
                ImpostorSourcePackage,
                *ImpostorSourceAssetName,
                RF_Public | RF_Standalone);
        }
        if (bFoliageSourcesValid && ImpostorSourceMesh)
        {
            TArray<TObjectPtr<UMaterialInterface>> SourceMaterialObjects;
            SourceMaterialObjects.Reserve(CombinedSourceMaterials.Num());
            for (UMaterialInterface* Material : CombinedSourceMaterials)
            {
                SourceMaterialObjects.Add(Material);
            }
            FGeometryScriptCopyMeshToAssetOptions CopyOptions;
            CopyOptions.bEmitTransaction = false;
            CopyOptions.bDeferMeshPostEditChange = false;
            CopyOptions.bEnableRecomputeTangents = false;
            CopyOptions.bReplaceMaterials = true;
            CopyOptions.NewMaterials = MoveTemp(SourceMaterialObjects);
            CopyOptions.bApplyNaniteSettings = true;
            CopyOptions.NewNaniteSettings = ImpostorSourceMesh->GetNaniteSettings();
            CopyOptions.NewNaniteSettings.bEnabled =
                !bTraditionalRasterCypressFoliagePalette;
            CopyOptions.NewNaniteSettings.ShapePreservation =
                ENaniteShapePreservation::None;
            EGeometryScriptOutcomePins SourceCopyOutcome = EGeometryScriptOutcomePins::Failure;
            UGeometryScriptLibrary_StaticMeshFunctions::CopyMeshToStaticMesh(
                CombinedSourceMesh,
                ImpostorSourceMesh,
                CopyOptions,
                FGeometryScriptMeshWriteLOD(),
                SourceCopyOutcome,
                false,
                nullptr);
            if (SourceCopyOutcome == EGeometryScriptOutcomePins::Success)
            {
                ImpostorSourceMesh->Modify();
                ImpostorSourceMesh->MarkPackageDirty();
                if (bNewImpostorSourceMesh)
                {
                    FAssetRegistryModule::AssetCreated(ImpostorSourceMesh);
                }
                FAssetCompilingManager::Get().FinishAllCompilation();
                const FString ImpostorSourceFilename = FPackageName::LongPackageNameToFilename(
                    LocalImpostorSourceAssetPath,
                    FPackageName::GetAssetPackageExtension());
                FSavePackageArgs SaveArgs;
                SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
                SaveArgs.SaveFlags = SAVE_NoError;
                bLocalImpostorSourceExported = UPackage::SavePackage(
                    ImpostorSourcePackage,
                    ImpostorSourceMesh,
                    *ImpostorSourceFilename,
                    SaveArgs);
                if (bLocalImpostorSourceExported)
                {
                    LocalImpostorSourceMesh = ImpostorSourceMesh;
                    LocalImpostorSourceVertexCount = ImpostorSourceMesh->GetNumVertices(0);
                    LocalImpostorSourceTriangleCount = ImpostorSourceMesh->GetNumTriangles(0);
                    LocalImpostorSourceMaterialSlotCount =
                        ImpostorSourceMesh->GetStaticMaterials().Num();
                    LocalImpostorSourceSectionCount =
                        ImpostorSourceMesh->GetNumSections(0);
                    for (const FStaticMaterial& Material :
                         ImpostorSourceMesh->GetStaticMaterials())
                    {
                        const FString MaterialIdentity = Material.MaterialInterface
                            ? Material.MaterialInterface->GetPathName()
                            : Material.MaterialSlotName.ToString();
                        if (MaterialIdentity.Contains(
                                TEXT("Bark"),
                                ESearchCase::IgnoreCase))
                        {
                            ++LocalImpostorSourceBarkMaterialSlotCount;
                        }
                        else
                        {
                            ++LocalImpostorSourceFoliageMaterialSlotCount;
                        }
                    }
                    LocalImpostorSourceBoundsSize =
                        ImpostorSourceMesh->GetBoundingBox().GetSize();
                    bLocalImpostorSourceNaniteEnabled = ImpostorSourceMesh->IsNaniteEnabled();
                    bLocalImpostorSourcePreserveArea =
                        ImpostorSourceMesh->GetNaniteSettings().ShapePreservation ==
                        ENaniteShapePreservation::PreserveArea;
                    const bool bExpectedWholeTreeRenderer =
                        bTraditionalRasterCypressFoliagePalette
                        ? !bLocalImpostorSourceNaniteEnabled
                        : bLocalImpostorSourceNaniteEnabled;
                    bLocalImpostorSourceValidated =
                        bExpectedWholeTreeRenderer &&
                        !bLocalImpostorSourcePreserveArea &&
                        LocalImpostorSourceVertexCount > LocalTrunkVertexCount &&
                        LocalImpostorSourceTriangleCount > LocalTrunkTriangleCount &&
                        LocalImpostorSourceMaterialSlotCount >= 2 &&
                        LocalImpostorSourceBarkMaterialSlotCount == 1 &&
                        LocalImpostorSourceFoliageMaterialSlotCount >= 1 &&
                        LocalImpostorSourceSectionCount >= 2 &&
                        LocalImpostorSourceBoundsSize.X >= LocalTrunkBoundsSize.X * 0.90f &&
                        LocalImpostorSourceBoundsSize.X <= LocalTrunkBoundsSize.X * 1.25f &&
                        LocalImpostorSourceBoundsSize.Y >= LocalTrunkBoundsSize.Y * 0.90f &&
                        LocalImpostorSourceBoundsSize.Y <= LocalTrunkBoundsSize.Y * 1.25f &&
                        LocalImpostorSourceBoundsSize.Z >= LocalTrunkBoundsSize.Z * 0.95f &&
                        LocalImpostorSourceBoundsSize.Z <= LocalTrunkBoundsSize.Z * 1.10f;
                }
            }
        }
    }

    bool bLocalFarProxyExported = false;
    bool bLocalFarProxyValidated = false;
    int32 LocalFarProxySourceFoliageCount = 0;
    int32 LocalFarProxyClusterCount = 0;
    int32 LocalFarProxyVertexCount = 0;
    int32 LocalFarProxyTriangleCount = 0;
    FVector LocalFarProxyBoundsSize = FVector::ZeroVector;
    FString LocalFarProxySummary;
    UStaticMesh* LocalFarProxyMesh = nullptr;
    const FString LocalFarProxyAssetPath = FString::Printf(
        TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/%s/FarProxy/"
             "SM_%s_%s_VolumetricFarProxy"),
        *LocalReviewNamespace,
        *CandidateAssetPrefix,
        *CandidateAssetToken);
    if (bProceduralCypressPveCandidate && bLocalTrunkValidated &&
        FoliageFacade.IsValid() && GEditor)
    {
        UWorld* BuildWorld = GEditor->GetEditorWorldContext().World();
        UMaterialInterface* FarProxyMaterial =
            CreateOrUpdateFutaleufuCypressFarProxyMaterial(LocalFarProxySummary);
        TArray<FVector> FarProxyVertices;
        TArray<int32> FarProxyTriangles;
        TArray<FVector2D> FarProxyUVs;
        TArray<FLinearColor> FarProxyVertexColors;

        auto AppendFarScaleSpray = [&FarProxyVertices,

                                    &FarProxyTriangles,
                                    &FarProxyUVs,
                                    &FarProxyVertexColors](
                                       const FVector& Center,
                                       const FVector& Axis,
                                       const FVector& Side,
                                       const FVector& Binormal,
                                       float AverageScale,
                                       int32 Seed)
        {
            constexpr int32 RingCount = 3;
            constexpr int32 SegmentCount = 4;
            static const float RingAxialUnits[RingCount] = {-0.52f, 0.02f, 0.72f};
            static const float RingRadiusScales[RingCount] = {0.18f, 1.0f, 0.24f};
            const float ScaleRoot = FMath::Sqrt(AverageScale);
            const float AxialRadiusCm = FMath::Clamp(
                43.0f * AverageScale, 30.0f, 80.0f);
            const float SideRadiusCm = FMath::Clamp(
                16.0f * ScaleRoot, 10.0f, 28.0f);
            const float BinormalRadiusCm = FMath::Clamp(
                5.2f * ScaleRoot, 4.0f, 9.0f);
            const int32 BaseIndex = FarProxyVertices.Num();
            const float ClusterTone = 0.88f + 0.10f * FMath::Sin(Seed * 0.019f);
            const FLinearColor CrownColor(
                0.036f * ClusterTone,
                0.128f * (0.94f + 0.06f * FMath::Sin(Seed * 0.031f)),
                0.019f * ClusterTone,
                1.0f);
            for (int32 RingIndex = 0; RingIndex < RingCount; ++RingIndex)
            {
                const float RingT = static_cast<float>(RingIndex) /
                    static_cast<float>(RingCount - 1);
                const float AxialUnit = RingAxialUnits[RingIndex];
                const float RingRadius = RingRadiusScales[RingIndex];
                for (int32 SegmentIndex = 0; SegmentIndex < SegmentCount; ++SegmentIndex)
                {
                    const float SegmentT = static_cast<float>(SegmentIndex) /
                        static_cast<float>(SegmentCount);
                    const float Angle = SegmentT * 2.0f * PI + PI * 0.25f;
                    const float Lobe = 0.88f + 0.12f * FMath::Sin(
                        static_cast<float>(Seed) * 0.017f + RingIndex * 1.31f +
                        SegmentIndex * 1.77f);
                    const FVector Radial =
                        Side * FMath::Cos(Angle) * SideRadiusCm +
                        Binormal * FMath::Sin(Angle) * BinormalRadiusCm;
                    FarProxyVertices.Add(
                        Center + Axis * AxialUnit * AxialRadiusCm +
                        Radial * RingRadius * Lobe);
                    FarProxyUVs.Add(FVector2D(SegmentT, RingT));
                    const float ColorNoise = 0.82f + 0.16f * FMath::Sin(
                        static_cast<float>(Seed) * 0.031f + RingIndex * 0.73f +
                        SegmentIndex * 1.19f);
                    FarProxyVertexColors.Add(ScalePreviewColor(
                        CrownColor,
                        ColorNoise * FMath::Lerp(0.88f, 1.04f, RingT)));
                }
            }
            for (int32 RingIndex = 0; RingIndex < RingCount - 1; ++RingIndex)
            {
                const int32 CurrentRing = BaseIndex + RingIndex * SegmentCount;
                const int32 NextRing = CurrentRing + SegmentCount;
                for (int32 SegmentIndex = 0; SegmentIndex < SegmentCount; ++SegmentIndex)
                {
                    const int32 NextSegment = (SegmentIndex + 1) % SegmentCount;
                    const int32 A = CurrentRing + SegmentIndex;
                    const int32 B = CurrentRing + NextSegment;
                    const int32 C = NextRing + SegmentIndex;
                    const int32 D = NextRing + NextSegment;
                    FarProxyTriangles.Append({A, C, B, B, C, D});
                }
            }
            const int32 FirstRing = BaseIndex;
            const int32 LastRing = BaseIndex + (RingCount - 1) * SegmentCount;
            const int32 TopIndex = FarProxyVertices.Num();
            FarProxyVertices.Add(Center + Axis * AxialRadiusCm * 0.92f);
            FarProxyUVs.Add(FVector2D(0.5f, 1.0f));
            FarProxyVertexColors.Add(ScalePreviewColor(CrownColor, 0.98f));
            const int32 BottomIndex = FarProxyVertices.Num();
            FarProxyVertices.Add(Center - Axis * AxialRadiusCm * 0.68f);
            FarProxyUVs.Add(FVector2D(0.5f, 0.0f));
            FarProxyVertexColors.Add(ScalePreviewColor(CrownColor, 0.70f));
            for (int32 SegmentIndex = 0; SegmentIndex < SegmentCount; ++SegmentIndex)
            {
                const int32 NextSegment = (SegmentIndex + 1) % SegmentCount;
                FarProxyTriangles.Append({
                    LastRing + SegmentIndex,
                    TopIndex,
                    LastRing + NextSegment,
                    BottomIndex,
                    FirstRing + NextSegment,
                    FirstRing + SegmentIndex});
            }
            return true;
        };
        constexpr int32 FarProxyFoliageStride = 4;
        LocalFarProxySourceFoliageCount = FoliageFacade.NumFoliageEntries();
        for (int32 EntryIndex = 0;
             EntryIndex < FoliageFacade.NumFoliageEntries();
             EntryIndex += FarProxyFoliageStride)
        {
            const FTransform Transform = GetLocalFoliageTransform(EntryIndex);
            const FVector Scale = Transform.GetScale3D();
            FVector Axis = Transform.TransformVectorNoScale(FVector::ForwardVector).GetSafeNormal();
            FVector Side = Transform.TransformVectorNoScale(FVector::RightVector).GetSafeNormal();
            FVector Binormal = FVector::CrossProduct(Axis, Side).GetSafeNormal();
            if (Axis.IsNearlyZero() || Side.IsNearlyZero() || Binormal.IsNearlyZero())
            {
                continue;
            }
            const float Roll = 0.28f * FMath::Sin((EntryIndex + 17011) * 0.037f);
            const FVector RolledSide = Side * FMath::Cos(Roll) + Binormal * FMath::Sin(Roll);
            const FVector RolledBinormal =
                FVector::CrossProduct(Axis, RolledSide).GetSafeNormal();
            const float AverageScale = FMath::Max(
                0.20f,
                (FMath::Abs(Scale.X) + FMath::Abs(Scale.Y) + FMath::Abs(Scale.Z)) / 3.0f);
            const FVector Center = Transform.GetLocation();
            if (AppendFarScaleSpray(
                    Center,
                    Axis,
                    RolledSide,
                    RolledBinormal,
                    AverageScale,
                    EntryIndex + 17011))
            {
                ++LocalFarProxyClusterCount;
            }
            const float FanJitter = 0.10f * FMath::Sin((EntryIndex + 17011) * 0.071f);
            for (int32 FanSide = -1; FanSide <= 1; FanSide += 2)
            {
                const FVector LateralAxis = (
                    Axis * 0.80f + RolledSide * (0.52f * static_cast<float>(FanSide)) +
                    RolledBinormal * FanJitter).GetSafeNormal();
                FVector LateralSide = RolledSide -
                    LateralAxis * FVector::DotProduct(RolledSide, LateralAxis);
                LateralSide.Normalize();
                const FVector LateralBinormal =
                    FVector::CrossProduct(LateralAxis, LateralSide).GetSafeNormal();
                if (LateralAxis.IsNearlyZero() || LateralSide.IsNearlyZero() ||
                    LateralBinormal.IsNearlyZero())
                {
                    continue;
                }
                if (AppendFarScaleSpray(
                        Center + Axis * (10.0f * AverageScale),
                        LateralAxis,
                        LateralSide,
                        LateralBinormal,
                        AverageScale * 0.78f,
                        EntryIndex + 17011 + FanSide * 97))
                {
                    ++LocalFarProxyClusterCount;
                }
            }
        }

        const TArray<FVector> FarProxyNormals = ComputePreviewMeshNormals(
            FarProxyVertices,
            FarProxyTriangles);

        AActor* FarProxySourceActor =
            BuildWorld && FarProxyMaterial && LocalFarProxyClusterCount > 0
            ? AddPreviewProceduralMeshActor(
                  BuildWorld,
                  TEXT("RaftSim_PveCypressVolumetricFarProxy_Source"),
                  FarProxyVertices,
                  FarProxyTriangles,
                  FarProxyNormals,
                  FarProxyUVs,
                  FLinearColor::White,
                  FarProxyMaterial,
                  &FarProxyVertexColors,
                  false)
            : nullptr;
        LocalFarProxyMesh = ConvertNativeCanopyProceduralActorToStaticMesh(
            FarProxySourceActor,
            LocalFarProxyAssetPath,
            FarProxyMaterial,
            false,
            ENaniteShapePreservation::None,
            LocalFarProxySummary);
        if (FarProxySourceActor)
        {
            FarProxySourceActor->Destroy();
        }
        if (LocalFarProxyMesh)
        {
            LocalFarProxyVertexCount = LocalFarProxyMesh->GetNumVertices(0);
            LocalFarProxyTriangleCount = LocalFarProxyMesh->GetNumTriangles(0);
            LocalFarProxyBoundsSize = LocalFarProxyMesh->GetBoundingBox().GetSize();
            bLocalFarProxyExported = true;
            bLocalFarProxyValidated =
                bLocalFarProxyExported &&
                LocalFarProxySourceFoliageCount == FoliageFacade.NumFoliageEntries() &&
                LocalFarProxyClusterCount >= 2000 &&
                LocalFarProxyTriangleCount >= 8000 &&
                LocalFarProxyTriangleCount <= 100000 &&
                LocalFarProxyTriangleCount < TriangleCount &&
                LocalFarProxyBoundsSize.X >= LocalTrunkBoundsSize.X * 0.85f &&
                LocalFarProxyBoundsSize.Y >= LocalTrunkBoundsSize.Y * 0.85f &&
                LocalFarProxyBoundsSize.Z >= LocalTrunkBoundsSize.Z * 0.70f &&
                LocalFarProxyBoundsSize.Z <= LocalTrunkBoundsSize.Z * 1.10f;
        }
    }

    bool bLocalVisualMapSaved = false;
    bool bLocalVisualReviewCaptured = false;
    bool bLocalFarProxyReviewCaptured = false;
    bool bLocalNaniteWholeTreeReviewCaptured = false;
    bool bLocalMultiViewAtlasReviewCaptured = false;
    bool bLocalHandoffReviewCaptured =
        !bHlodCalibratedIrregularCrownMassCypressPalette;
    bool bLocalComplementaryTransitionReviewCaptured =
        !bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette;
    bool bLocalTemporalTransitionReviewCaptured =
        !bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette;
    bool bLocalPersistentMotionTransitionReviewCaptured =
        !bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette;
    bool bLocalFinePersistentMotionTransitionReviewCaptured =
        !bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette;
    bool bLocalLitRiverViewMotionTransitionReviewCaptured =
        !bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette;
    bool bLocalTemporalLitRiverViewMotionTransitionReviewCaptured =
        !bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette;
    bool bLocalHlodFrameSearchReviewCaptured =
        !bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette;
    bool bLocalHlodSplitShadingSearchReviewCaptured =
        !bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette;
    bool bLocalHlodDualLayerReviewCaptured =
        !bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette;
    bool bLocalHlodTransmissionLightBracketReviewCaptured =
        !bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette;
    bool bLocalHlodMergedGeometryShapeBracketReviewCaptured =
        !bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette;
    bool bLocalHlodMergedComponentParityReviewCaptured =
        !bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette;
    FRaftSimPveMultiViewAtlasBakeResult LocalMultiViewAtlas;
    UStaticMesh* LocalMultiViewHlodMesh = nullptr;
    FTransform LocalMultiViewHlodTransform = FTransform::Identity;
    int32 LocalVisualFoliageMeshCount = 0;
    int32 LocalVisualFoliageInstanceCount = 0;
    const FString LocalVisualMapPackagePath = FString::Printf(
        TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/%s/"
             "L_%s_%s_IsolatedReview"),
        *LocalReviewNamespace,
        *CandidateAssetPrefix,
        *CandidateAssetToken);
    const FString LocalVisualCaptureBase = FString::Printf(
        TEXT("unreal/Saved/RaftSimPveReview/%s/%s"),
        *LocalSavedNamespace,
        *ProceduralBeechVariant.ToLower());
    FString LocalMultiViewAtlasCapturePath =
        LocalVisualCaptureBase + TEXT("_multiview_atlas_hlod_60m.png");
    FString LocalVisualSummary;
    LocalVisualSummary += LocalFarProxySummary;
    TArray<FString> LocalVisualCapturePaths = {
        LocalVisualCaptureBase + TEXT("_turntable_azimuth_035.png"),
        LocalVisualCaptureBase + TEXT("_turntable_azimuth_145.png"),
        LocalVisualCaptureBase + TEXT("_river_distance_60m.png"),
        LocalVisualCaptureBase + TEXT("_branch_spray_closeup.png"),
        LocalVisualCaptureBase +
            (bProceduralCypressPveCandidate
                 ? TEXT("_volumetric_far_proxy_60m.png")
                 : TEXT("_river_distance_60m.png")),
        LocalVisualCaptureBase +
            (bTraditionalRasterCypressFoliagePalette
                 ? TEXT("_merged_raster_whole_tree_60m.png")
                 : TEXT("_nanite_whole_tree_60m.png"))};
    static const TCHAR* HandoffDistanceTokens[] = {
        TEXT("20m"), TEXT("28m"), TEXT("36m")};
    static const TCHAR* HandoffAuthorityTokens[] = {
        TEXT("source_only"), TEXT("hlod_only"), TEXT("combined")};
    static const TCHAR* ComplementaryTransitionDistanceTokens[] = {
        TEXT("24m"), TEXT("25m"), TEXT("26m")};
    static const float ComplementaryTransitionRadiiCm[] = {
        2400.0f, 2500.0f, 2600.0f};
    static const float ComplementaryTransitionSourceCoverage[] = {
        0.75f, 0.50f, 0.25f};
    TArray<FString> LocalHandoffCapturePaths;
    FString LocalHandoffCapturesJson;
    TArray<FString> LocalComplementaryTransitionCapturePaths;
    FString LocalComplementaryTransitionCapturesJson;
    TArray<FString> LocalTemporalTransitionTokens;
    TArray<float> LocalTemporalTransitionRadiiCm;
    TArray<float> LocalTemporalTransitionSourceCoverage;
    TArray<FString> LocalTemporalTransitionCapturePaths;
    FString LocalTemporalTransitionCapturesJson;
    TArray<FString> LocalPersistentMotionTransitionCapturePaths;
    FString LocalPersistentMotionTransitionCapturesJson;
    TArray<FString> LocalFinePersistentMotionTransitionCapturePaths;
    FString LocalFinePersistentMotionTransitionCapturesJson;
    TArray<FString> LocalLitRiverViewMotionTransitionCapturePaths;
    FString LocalLitRiverViewMotionTransitionCapturesJson;
    TArray<FString> LocalTemporalLitRiverViewMotionTransitionCapturePaths;
    FString LocalTemporalLitRiverViewMotionTransitionCapturesJson;
    TArray<FString> LocalHlodFrameSearchCapturePaths;
    FString LocalHlodFrameSearchCapturesJson;
    int32 LocalHlodFrameSearchAutomaticFrame = -1;
    TArray<FString> LocalHlodSplitShadingSearchCapturePaths;
    FString LocalHlodSplitShadingSearchCapturesJson;
    TArray<FString> LocalHlodDualLayerCapturePaths;
    FString LocalHlodDualLayerCapturesJson;
    TArray<FString> LocalHlodTransmissionLightBracketCapturePaths;
    FString LocalHlodTransmissionLightBracketCapturesJson;
    TArray<FString> LocalHlodMergedGeometryShapeBracketCapturePaths;
    FString LocalHlodMergedGeometryShapeBracketCapturesJson;
    TArray<FString> LocalHlodMergedComponentParityCapturePaths;
    FString LocalHlodMergedComponentParityCapturesJson;
    if (bHlodCalibratedIrregularCrownMassCypressPalette)
    {
        for (const TCHAR* DistanceToken : HandoffDistanceTokens)
        {
            for (const TCHAR* AuthorityToken : HandoffAuthorityTokens)
            {
                const FString CapturePath = FString::Printf(
                    TEXT("%s_handoff_%s_%s.png"),
                    *LocalVisualCaptureBase,
                    DistanceToken,
                    AuthorityToken);
                LocalHandoffCapturePaths.Add(CapturePath);

                LocalHandoffCapturesJson += FString::Printf(
                    TEXT("%s\"%s\""),
                    LocalHandoffCapturesJson.IsEmpty() ? TEXT("") : TEXT(", "),
                    *EscapeRaftSimJsonString(CapturePath));
            }
        }
    }
    if (bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette)
    {
        for (const TCHAR* DistanceToken : ComplementaryTransitionDistanceTokens)
        {
            for (const TCHAR* AuthorityToken : HandoffAuthorityTokens)
            {
                const FString CapturePath = FString::Printf(
                    TEXT("%s_transition_%s_%s.png"),
                    *LocalVisualCaptureBase,
                    DistanceToken,
                    AuthorityToken);
                LocalComplementaryTransitionCapturePaths.Add(CapturePath);
                LocalComplementaryTransitionCapturesJson += FString::Printf(
                    TEXT("%s\"%s\""),
                    LocalComplementaryTransitionCapturesJson.IsEmpty()
                        ? TEXT("")
                        : TEXT(", "),
                    *EscapeRaftSimJsonString(CapturePath));
            }
        }
        constexpr int32 TemporalSampleCount = 17;
        for (int32 SampleIndex = 0; SampleIndex < TemporalSampleCount; ++SampleIndex)
        {
            const int32 RadiusCm = 2300 + SampleIndex * 25;
            const int32 RadiusMeters = RadiusCm / 100;
            const int32 RadiusCentimeters = RadiusCm % 100;
            const FString DistanceToken = FString::Printf(
                TEXT("%02dm%02d"),
                RadiusMeters,
                RadiusCentimeters);
            LocalTemporalTransitionTokens.Add(DistanceToken);
            LocalTemporalTransitionRadiiCm.Add(static_cast<float>(RadiusCm));
            LocalTemporalTransitionSourceCoverage.Add(
                1.0f - static_cast<float>(SampleIndex) / 16.0f);
            for (const TCHAR* AuthorityToken : HandoffAuthorityTokens)
            {
                const FString CapturePath = FString::Printf(
                    TEXT("%s_temporal_%s_%s.png"),
                    *LocalVisualCaptureBase,
                    *DistanceToken,
                    AuthorityToken);
                LocalTemporalTransitionCapturePaths.Add(CapturePath);
                LocalTemporalTransitionCapturesJson += FString::Printf(
                    TEXT("%s\"%s\""),
                    LocalTemporalTransitionCapturesJson.IsEmpty()
                        ? TEXT("")
                        : TEXT(", "),
                    *EscapeRaftSimJsonString(CapturePath));
            }
        }
    }
    if (bLocalTrunkValidated && bLocalTemplateSaved && GEditor && FoliageFacade.IsValid())
    {
        UWorld* ReviewWorld = UEditorLoadingAndSavingUtils::NewBlankMap(false);
        if (ReviewWorld)
        {
            AStaticMeshActor* TrunkActor = ReviewWorld->SpawnActor<AStaticMeshActor>(
                AStaticMeshActor::StaticClass(),
                FTransform::Identity);
            if (TrunkActor && TrunkActor->GetStaticMeshComponent())
            {
                TrunkActor->SetActorLabel(TEXT("RaftSim_PveReview_Trunk"));
                TrunkActor->GetStaticMeshComponent()->SetStaticMesh(TrunkMesh);
                TrunkActor->GetStaticMeshComponent()->SetMobility(EComponentMobility::Static);
                TrunkActor->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            }

            AStaticMeshActor* FarProxyActor =
                bProceduralCypressPveCandidate && LocalFarProxyMesh
                ? ReviewWorld->SpawnActor<AStaticMeshActor>(
                      AStaticMeshActor::StaticClass(),
                      FTransform::Identity)
                : nullptr;
            if (FarProxyActor && FarProxyActor->GetStaticMeshComponent())
            {
                FarProxyActor->SetActorLabel(TEXT("RaftSim_PveCypressVolumetricFarProxy"));
                FarProxyActor->GetStaticMeshComponent()->SetStaticMesh(LocalFarProxyMesh);
                FarProxyActor->GetStaticMeshComponent()->SetMobility(EComponentMobility::Static);
                FarProxyActor->GetStaticMeshComponent()->SetCollisionEnabled(
                    ECollisionEnabled::NoCollision);
                FarProxyActor->GetStaticMeshComponent()->SetCastShadow(false);
                FarProxyActor->SetActorHiddenInGame(true);
            }

            AStaticMeshActor* NaniteWholeTreeActor =
                bProceduralCypressPveCandidate && LocalImpostorSourceMesh
                ? ReviewWorld->SpawnActor<AStaticMeshActor>(
                      AStaticMeshActor::StaticClass(),
                      FTransform::Identity)
                : nullptr;
            if (NaniteWholeTreeActor && NaniteWholeTreeActor->GetStaticMeshComponent())
            {
                NaniteWholeTreeActor->SetActorLabel(TEXT("RaftSim_PveCypressNaniteWholeTree"));
                NaniteWholeTreeActor->GetStaticMeshComponent()->SetStaticMesh(
                    LocalImpostorSourceMesh);
                NaniteWholeTreeActor->GetStaticMeshComponent()->SetMobility(
                    EComponentMobility::Static);
                NaniteWholeTreeActor->GetStaticMeshComponent()->SetCollisionEnabled(
                    ECollisionEnabled::NoCollision);
                NaniteWholeTreeActor->GetStaticMeshComponent()->SetCastShadow(true);
                NaniteWholeTreeActor->SetActorHiddenInGame(true);
            }

            AActor* FoliageActor = ReviewWorld->SpawnActor<AActor>();
            TArray<UHierarchicalInstancedStaticMeshComponent*> FoliageComponents;
            if (FoliageActor)
            {
                FoliageActor->SetActorLabel(TEXT("RaftSim_PveReview_Foliage"));
                USceneComponent* Root = NewObject<USceneComponent>(FoliageActor, TEXT("Root"));
                FoliageActor->AddInstanceComponent(Root);
                FoliageActor->SetRootComponent(Root);
                Root->SetMobility(EComponentMobility::Static);
                Root->RegisterComponent();
                for (int32 MeshIndex = 0; MeshIndex < FoliageFacade.NumFoliageInfo(); ++MeshIndex)
                {
                    const FString MeshPath = FoliageFacade.GetFoliageInfo(MeshIndex).Mesh.ToString();
                    UStaticMesh* FoliageMesh = LoadObject<UStaticMesh>(nullptr, *MeshPath);
                    if (!FoliageMesh)
                    {
                        FoliageComponents.Add(nullptr);
                        continue;
                    }
                    UHierarchicalInstancedStaticMeshComponent* Component =
                        NewObject<UHierarchicalInstancedStaticMeshComponent>(
                            FoliageActor,
                            *FString::Printf(TEXT("PveFoliage_%02d"), MeshIndex));
                    FoliageActor->AddInstanceComponent(Component);
                    Component->SetupAttachment(Root);
                    Component->SetStaticMesh(FoliageMesh);
                    Component->SetMobility(EComponentMobility::Static);
                    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
                    if (bProceduralCypressPveCandidate)
                    {
                        Component->SetCastShadow(false);
                        Component->bCastStaticShadow = false;
                        Component->bCastDynamicShadow = false;
                        Component->SetCastContactShadow(false);
                        Component->SetAffectDistanceFieldLighting(false);
                        Component->SetAffectDynamicIndirectLighting(false);
                    }
                    Component->RegisterComponent();
                    FoliageComponents.Add(Component);
                    ++LocalVisualFoliageMeshCount;
                }
                for (int32 EntryIndex = 0; EntryIndex < FoliageFacade.NumFoliageEntries(); ++EntryIndex)
                {
                    const PV::Facades::FFoliageEntryData Entry = FoliageFacade.GetFoliageEntry(EntryIndex);
                    if (!FoliageComponents.IsValidIndex(Entry.NameId) || !FoliageComponents[Entry.NameId])
                    {
                        continue;
                    }
                    FoliageComponents[Entry.NameId]->AddInstance(
                        GetLocalFoliageTransform(EntryIndex));
                    ++LocalVisualFoliageInstanceCount;
                }
            }

            UStaticMesh* PlaneMesh = LoadPreviewMesh(TEXT("/Engine/BasicShapes/Plane.Plane"));
            AStaticMeshActor* GroundActor = ReviewWorld->SpawnActor<AStaticMeshActor>(
                AStaticMeshActor::StaticClass(),
                FTransform(FRotator::ZeroRotator, FVector(0.0f, 0.0f, 40.0f), FVector(100.0f, 100.0f, 1.0f)));
            if (GroundActor && GroundActor->GetStaticMeshComponent())
            {
                GroundActor->SetActorLabel(TEXT("RaftSim_PveReview_NeutralGround"));
                GroundActor->GetStaticMeshComponent()->SetStaticMesh(PlaneMesh);
                GroundActor->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
                if (UMaterialInterface* GroundMaterial = LoadObject<UMaterialInterface>(
                        nullptr,
                        TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial")))
                {
                    GroundActor->GetStaticMeshComponent()->SetMaterial(0, GroundMaterial);
                }
            }

            FRaftSimEnvironmentPreviewSpec ReviewSpec;
            ReviewSpec.RiverId = TEXT("futaleufu_terminator");
            ReviewSpec.DisplayName = bProceduralCypressPveCandidate
                ? CypressSpec->DisplayName + TEXT(" V17 project-graph PVE review")
                : ProceduralBeechVariant + TEXT(" isolated PVE review");
            ReviewSpec.MapPackagePath = LocalVisualMapPackagePath;
            ReviewSpec.FoliageColor = FLinearColor(0.15f, 0.32f, 0.12f);
            ReviewSpec.RockColor = FLinearColor(0.38f, 0.36f, 0.31f);
            ReviewSpec.bDeterministicValidationCapture =
                bFrozenWpoHlodCalibratedIrregularCrownMassCypressPalette;
            AddPreviewLightRig(ReviewWorld, ReviewSpec);

            const FBox TrunkBounds = TrunkMesh->GetBoundingBox();
            const FVector Target = TrunkBounds.GetCenter();
            UStaticMesh* LiveSprayReviewMesh = nullptr;
            for (int32 MeshIndex = 0; MeshIndex < FoliageFacade.NumFoliageInfo(); ++MeshIndex)
            {
                const FString MeshPath = FoliageFacade.GetFoliageInfo(MeshIndex).Mesh.ToString();
                if (MeshPath.Contains(TEXT("PveLiveTwig"), ESearchCase::CaseSensitive))
                {
                    LiveSprayReviewMesh = LoadObject<UStaticMesh>(nullptr, *MeshPath);
                    if (LiveSprayReviewMesh)
                    {
                        break;
                    }
                }
            }
            const FVector SprayReviewLocation = Target + FVector(10000.0f, 0.0f, 180.0f);
            AStaticMeshActor* SprayReviewActor = LiveSprayReviewMesh
                ? ReviewWorld->SpawnActor<AStaticMeshActor>(
                      AStaticMeshActor::StaticClass(),
                      FTransform(FRotator::ZeroRotator, SprayReviewLocation, FVector(3.0f)))
                : nullptr;
            if (SprayReviewActor && SprayReviewActor->GetStaticMeshComponent())
            {
                SprayReviewActor->SetActorLabel(TEXT("RaftSim_PveBranchSprayCloseup"));
                SprayReviewActor->GetStaticMeshComponent()->SetStaticMesh(LiveSprayReviewMesh);
                SprayReviewActor->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
                SprayReviewActor->GetStaticMeshComponent()->SetCastShadow(false);
            }
            const float ReviewDistance = FMath::Max(
                TrunkBounds.GetSize().Z * 2.40f,
                FMath::Max(TrunkBounds.GetSize().X, TrunkBounds.GetSize().Y) * 2.25f);
            const FRaftSimPhotographicCaptureSettings CaptureSettings =
                GetPhotographicCaptureSettings(ReviewSpec.RiverId);
            auto AddReviewCamera = [ReviewWorld, Target, CaptureSettings](
                                       const TCHAR* Label,
                                       const FVector& Location,
                                       float FieldOfView)
            {
                ACameraActor* Camera = ReviewWorld->SpawnActor<ACameraActor>(
                    ACameraActor::StaticClass(),
                    FTransform((Target - Location).Rotation(), Location));
                if (!Camera || !Camera->GetCameraComponent())
                {
                    return false;
                }
                Camera->SetActorLabel(Label);
                Camera->GetCameraComponent()->FieldOfView = FieldOfView;
                FPostProcessSettings& Settings = Camera->GetCameraComponent()->PostProcessSettings;
                Settings.bOverride_AutoExposureMethod = true;
                Settings.AutoExposureMethod = AEM_Manual;
                Settings.bOverride_AutoExposureBias = true;
                Settings.AutoExposureBias = CaptureSettings.ExposureBias;
                Settings.bOverride_AutoExposureApplyPhysicalCameraExposure = true;
                Settings.AutoExposureApplyPhysicalCameraExposure = 0;
                Settings.bOverride_ColorSaturation = true;
                Settings.ColorSaturation = FVector4(
                    CaptureSettings.Saturation,
                    CaptureSettings.Saturation,
                    CaptureSettings.Saturation,
                    1.0f);
                Settings.bOverride_ColorContrast = true;
                Settings.ColorContrast = FVector4(
                    CaptureSettings.Contrast,
                    CaptureSettings.Contrast,
                    CaptureSettings.Contrast,
                    1.0f);
                Settings.bOverride_Sharpen = true;
                Settings.Sharpen = CaptureSettings.Sharpen;
                Settings.bOverride_FilmGrainIntensity = true;
                Settings.FilmGrainIntensity = 0.0f;
                return true;
            };
            const float CameraHeight = Target.Z + TrunkBounds.GetSize().Z * 0.08f;
            const bool bCameraA = AddReviewCamera(
                TEXT("RaftSim_PveTurntable_Azimuth035"),
                FVector(
                    Target.X - ReviewDistance * FMath::Cos(FMath::DegreesToRadians(35.0f)),
                    Target.Y - ReviewDistance * FMath::Sin(FMath::DegreesToRadians(35.0f)),
                    CameraHeight),
                46.0f);
            const bool bCameraB = AddReviewCamera(
                TEXT("RaftSim_PveTurntable_Azimuth145"),
                FVector(
                    Target.X - ReviewDistance * FMath::Cos(FMath::DegreesToRadians(145.0f)),
                    Target.Y - ReviewDistance * FMath::Sin(FMath::DegreesToRadians(145.0f)),
                    CameraHeight),
                46.0f);
            const bool bCameraDistance = AddReviewCamera(
                TEXT("RaftSim_PveRiverDistance60m"),
                FVector(Target.X - 6000.0f, Target.Y - 800.0f, CameraHeight),
                50.0f);
            bool bHandoffCamerasComplete = true;
            if (bHlodCalibratedIrregularCrownMassCypressPalette)
            {
                static const float HandoffDistancesCm[] = {
                    2000.0f, 2800.0f, 3600.0f};
                for (int32 HandoffIndex = 0; HandoffIndex < 3; ++HandoffIndex)
                {
                    const FString CameraLabel = FString::Printf(
                        TEXT("RaftSim_PveHandoff_%s"),
                        HandoffDistanceTokens[HandoffIndex]);
                    bHandoffCamerasComplete &= AddReviewCamera(
                        *CameraLabel,
                        FVector(
                            Target.X - HandoffDistancesCm[HandoffIndex],
                            Target.Y - 800.0f,
                            CameraHeight),
                        50.0f);
                }
                if (bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette)
                {
                    for (int32 TransitionIndex = 0; TransitionIndex < 3; ++TransitionIndex)
                    {
                        const float RadialDistanceCm =
                            ComplementaryTransitionRadiiCm[TransitionIndex];
                        const float AxialDistanceCm = FMath::Sqrt(
                            FMath::Square(RadialDistanceCm) - FMath::Square(800.0f));
                        const FString CameraLabel = FString::Printf(
                            TEXT("RaftSim_PveTransition_%s"),
                            ComplementaryTransitionDistanceTokens[TransitionIndex]);
                        bHandoffCamerasComplete &= AddReviewCamera(
                            *CameraLabel,
                            FVector(
                                Target.X - AxialDistanceCm,
                                Target.Y - 800.0f,
                                CameraHeight),
                            50.0f);

                    }
                    for (int32 SampleIndex = 0;
                         SampleIndex < LocalTemporalTransitionTokens.Num();
                         ++SampleIndex)
                    {
                        const float RadialDistanceCm =
                            LocalTemporalTransitionRadiiCm[SampleIndex];
                        const float AxialDistanceCm = FMath::Sqrt(
                            FMath::Square(RadialDistanceCm) - FMath::Square(800.0f));
                        const FString CameraLabel = FString::Printf(
                            TEXT("RaftSim_PveTemporal_%s"),
                            *LocalTemporalTransitionTokens[SampleIndex]);
                        bHandoffCamerasComplete &= AddReviewCamera(
                            *CameraLabel,
                            FVector(
                                Target.X - AxialDistanceCm,
                                Target.Y - 800.0f,
                                CameraHeight),
                            50.0f);
                    }
                }
            }
            const FVector SprayCameraTarget = SprayReviewLocation + FVector(70.0f, 0.0f, 0.0f);
            ACameraActor* SprayCamera = ReviewWorld->SpawnActor<ACameraActor>(
                ACameraActor::StaticClass(),
                FTransform(
                    (SprayCameraTarget - (SprayReviewLocation + FVector(-240.0f, -180.0f, 280.0f))).Rotation(),
                    SprayReviewLocation + FVector(-240.0f, -180.0f, 280.0f)));
            const bool bCameraSpray = SprayCamera && SprayCamera->GetCameraComponent();
            if (bCameraSpray)
            {
                SprayCamera->SetActorLabel(TEXT("RaftSim_PveBranchSprayCloseupCamera"));
                SprayCamera->GetCameraComponent()->FieldOfView = 42.0f;
            }

            const bool bMultiViewAtlasReady = !bProceduralCypressPveCandidate ||
                BakeFutaleufuCypressMultiViewAtlas(
                    ReviewWorld,
                    TrunkActor,
                    FoliageActor,
                    ProceduralBeechVariant,
                    CandidateAssetToken,
                    LocalSavedNamespace,
                    LocalReviewNamespace,
                    bDenseBotanicalFlattenedSprayCypressHierarchyPalette,
                    bHlodCalibratedIrregularCrownMassCypressPalette
                        ? FLinearColor(2.60f, 1.63f, 1.60f, 1.0f)
                        : FLinearColor(1.10f, 1.38f, 0.90f, 1.0f),
                    bFrozenWpoHlodCalibratedIrregularCrownMassCypressPalette,
                    bFrozenWpoAzimuthRegisteredHlodCalibratedIrregularCrownMassCypressPalette
                        ? 16.0f
                        : 0.0f,
                    bFrozenWpoAzimuthRegisteredPerspectiveHlodCalibratedIrregularCrownMassCypressPalette,
                    bFrozenWpoAzimuthRegisteredPerspectiveHlodCalibratedIrregularCrownMassCypressPalette
                        ? 2912.0439f
                        : 0.0f,
                    bFrozenWpoAzimuthRegisteredPerspectiveDepthHlodCalibratedIrregularCrownMassCypressPalette,
                    bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette,
                    bHighDetailHlodCalibratedIrregularCrownMassCypressPalette ||
                        bFrozenWpoHighDetailHlodCalibratedIrregularCrownMassCypressPalette
                        ? 1024
                        : 512,
                    LocalMultiViewAtlas,
                    LocalVisualSummary);
            if (LocalMultiViewAtlas.ProxyActor &&
                LocalMultiViewAtlas.ProxyActor->GetStaticMeshComponent())
            {
                LocalMultiViewHlodMesh =
                    LocalMultiViewAtlas.ProxyActor->GetStaticMeshComponent()->GetStaticMesh();
                LocalMultiViewHlodTransform =
                    LocalMultiViewAtlas.ProxyActor->GetActorTransform();
            }

            const bool bSceneComplete =
                TrunkActor && TrunkActor->GetStaticMeshComponent() &&
                LocalVisualFoliageMeshCount == FoliageMeshCount &&
                LocalVisualFoliageInstanceCount == FoliageInstanceCount &&
                PlaneMesh && GroundActor && SprayReviewActor &&
                bCameraA && bCameraB && bCameraDistance && bCameraSpray &&
                bHandoffCamerasComplete &&
                (!bProceduralCypressPveCandidate ||
                 (bLocalFarProxyValidated && FarProxyActor &&
                  FarProxyActor->GetStaticMeshComponent() &&
                  bLocalImpostorSourceValidated && NaniteWholeTreeActor &&
                  NaniteWholeTreeActor->GetStaticMeshComponent() &&
                  bMultiViewAtlasReady && LocalMultiViewAtlas.ProxyActor &&
                  LocalMultiViewAtlas.ProxyActor->GetStaticMeshComponent()));
            bLocalVisualMapSaved = bSceneComplete &&
                SavePreviewWorld(ReviewWorld, LocalVisualMapPackagePath, LocalVisualSummary);
            if (bLocalVisualMapSaved)
            {
                FAssetCompilingManager::Get().FinishAllCompilation();
                if (GShaderCompilingManager)
                {
                    GShaderCompilingManager->FinishAllCompilation();
                }
                const FString LocalCaptureRoot = FPaths::Combine(
                    FPaths::ProjectSavedDir(),
                    TEXT("RaftSimPveReview"),
                    LocalSavedNamespace);
                bool bCaptureA = CapturePreviewImageForSpec(
                    ReviewSpec,
                    LocalCaptureRoot,
                    LocalVisualCapturePaths[0],
                    TEXT("RaftSim_PveTurntable_Azimuth035"),
                    TEXT("turntable_azimuth_035"),
                    TEXT("PVE turntable azimuth 35"),
                    false,
                    LocalVisualSummary);
                bool bCaptureB = CapturePreviewImageForSpec(
                    ReviewSpec,
                    LocalCaptureRoot,
                    LocalVisualCapturePaths[1],
                    TEXT("RaftSim_PveTurntable_Azimuth145"),
                    TEXT("turntable_azimuth_145"),
                    TEXT("PVE turntable azimuth 145"),
                    false,
                    LocalVisualSummary);
                bool bCaptureDistance = CapturePreviewImageForSpec(
                    ReviewSpec,
                    LocalCaptureRoot,
                    LocalVisualCapturePaths[2],
                    TEXT("RaftSim_PveRiverDistance60m"),
                    TEXT("river_distance_60m"),
                    TEXT("PVE 60 m river-distance proxy"),
                    false,
                    LocalVisualSummary);
                bool bCaptureSpray = CapturePreviewImageForSpec(
                    ReviewSpec,
                    LocalCaptureRoot,
                    LocalVisualCapturePaths[3],
                    TEXT("RaftSim_PveBranchSprayCloseupCamera"),
                    TEXT("branch_spray_closeup"),
                    TEXT("PVE branch-spray material and alpha closeup"),
                    false,
                    LocalVisualSummary);
                bool bCaptureFarProxy = !bProceduralCypressPveCandidate;
                if (bProceduralCypressPveCandidate)
                {
                    bCaptureFarProxy = CapturePreviewImageForSpec(
                        ReviewSpec,
                        LocalCaptureRoot,
                        LocalVisualCapturePaths[4],
                        TEXT("RaftSim_PveRiverDistance60m"),
                        TEXT("volumetric_far_proxy_60m"),
                        TEXT("PVE volumetric far proxy at the exact source 60 m camera"),
                        false,
                        LocalVisualSummary,
                        [](UWorld* LoadedWorld, ACameraActor*, FString& SetupSummary)
                        {
                            AActor* SourceFoliageActor = nullptr;
                            AActor* LoadedFarProxyActor = nullptr;
                            for (TActorIterator<AActor> It(LoadedWorld); It; ++It)
                            {
                                AActor* Actor = *It;
                                if (!Actor)
                                {
                                    continue;
                                }
                                if (Actor->GetActorLabel() == TEXT("RaftSim_PveReview_Foliage"))
                                {
                                    SourceFoliageActor = Actor;
                                }
                                else if (Actor->GetActorLabel() ==
                                         TEXT("RaftSim_PveCypressVolumetricFarProxy"))
                                {
                                    LoadedFarProxyActor = Actor;
                                }
                            }
                            if (!SourceFoliageActor || !LoadedFarProxyActor)
                            {
                                SetupSummary += TEXT(
                                    "Exact-camera far-proxy setup could not resolve source and proxy actors.\n");
                                return false;
                            }
                            SourceFoliageActor->SetActorHiddenInGame(true);
                            LoadedFarProxyActor->SetActorHiddenInGame(false);
                            return true;
                        });
                }
                bool bCaptureNaniteWholeTree = !bProceduralCypressPveCandidate;
                if (bProceduralCypressPveCandidate)
                {
                    bCaptureNaniteWholeTree = CapturePreviewImageForSpec(
                        ReviewSpec,
                        LocalCaptureRoot,
                        LocalVisualCapturePaths[5],
                        TEXT("RaftSim_PveRiverDistance60m"),
                        TEXT("nanite_whole_tree_60m"),
                        TEXT("PVE merged Nanite whole tree at the exact source 60 m camera"),
                        false,
                        LocalVisualSummary,
                        [](UWorld* LoadedWorld, ACameraActor*, FString& SetupSummary)
                        {
                            AActor* SourceTrunkActor = nullptr;
                            AActor* SourceFoliageActor = nullptr;
                            AActor* LoadedNaniteWholeTreeActor = nullptr;
                            for (TActorIterator<AActor> It(LoadedWorld); It; ++It)
                            {
                                AActor* Actor = *It;
                                if (!Actor)
                                {
                                    continue;
                                }
                                if (Actor->GetActorLabel() == TEXT("RaftSim_PveReview_Trunk"))
                                {
                                    SourceTrunkActor = Actor;
                                }
                                else if (Actor->GetActorLabel() == TEXT("RaftSim_PveReview_Foliage"))
                                {
                                    SourceFoliageActor = Actor;
                                }
                                else if (Actor->GetActorLabel() ==
                                         TEXT("RaftSim_PveCypressNaniteWholeTree"))
                                {
                                    LoadedNaniteWholeTreeActor = Actor;
                                }
                            }
                            if (!SourceTrunkActor || !SourceFoliageActor ||
                                !LoadedNaniteWholeTreeActor)
                            {
                                SetupSummary += TEXT(
                                    "Exact-camera Nanite whole-tree setup could not resolve source and candidate actors.\n");
                                return false;
                            }
                            SourceTrunkActor->SetActorHiddenInGame(true);
                            SourceFoliageActor->SetActorHiddenInGame(true);
                            LoadedNaniteWholeTreeActor->SetActorHiddenInGame(false);
                            return true;
                        });
                }
                bool bCaptureMultiViewAtlas = !bProceduralCypressPveCandidate;
                if (bProceduralCypressPveCandidate)
                {
                    bCaptureMultiViewAtlas = CapturePreviewImageForSpec(
                        ReviewSpec,
                        LocalCaptureRoot,
                        LocalMultiViewAtlasCapturePath,
                        TEXT("RaftSim_PveRiverDistance60m"),
                        TEXT("multiview_atlas_hlod_60m"),
                        TEXT("PVE project-owned multi-view atlas HLOD at the exact source 60 m camera"),
                        false,
                        LocalVisualSummary,
                        [](UWorld* LoadedWorld, ACameraActor*, FString& SetupSummary)
                        {
                            AActor* SourceTrunkActor = nullptr;
                            AActor* SourceFoliageActor = nullptr;
                            AActor* LoadedAtlasActor = nullptr;
                            for (TActorIterator<AActor> It(LoadedWorld); It; ++It)
                            {
                                AActor* Actor = *It;
                                if (!Actor)
                                {
                                    continue;
                                }
                                const FString Label = Actor->GetActorLabel();
                                if (Label == TEXT("RaftSim_PveReview_Trunk"))
                                {
                                    SourceTrunkActor = Actor;
                                }
                                else if (Label == TEXT("RaftSim_PveReview_Foliage"))
                                {
                                    SourceFoliageActor = Actor;
                                }
                                else if (Label == TEXT("RaftSim_PveCypressMultiViewAtlasHlod"))
                                {
                                    LoadedAtlasActor = Actor;
                                }
                                else if (Label == TEXT("RaftSim_PveCypressVolumetricFarProxy") ||
                                         Label == TEXT("RaftSim_PveCypressNaniteWholeTree"))
                                {
                                    Actor->SetActorHiddenInGame(true);
                                }
                            }
                            if (!SourceTrunkActor || !SourceFoliageActor || !LoadedAtlasActor)
                            {
                                SetupSummary += TEXT(
                                    "Exact-camera multi-view atlas setup could not resolve source and HLOD actors.\n");
                                return false;
                            }
                            SourceTrunkActor->SetActorHiddenInGame(true);
                            SourceFoliageActor->SetActorHiddenInGame(true);
                            LoadedAtlasActor->SetActorHiddenInGame(false);
                            return true;
                        });
                }
                if (bHlodCalibratedIrregularCrownMassCypressPalette)
                {
                    bool bAllHandoffsCaptured = true;
                    for (int32 DistanceIndex = 0; DistanceIndex < 3; ++DistanceIndex)
                    {
                        for (int32 AuthorityIndex = 0; AuthorityIndex < 3; ++AuthorityIndex)
                        {
                            const FString AuthorityMode =
                                HandoffAuthorityTokens[AuthorityIndex];
                            const FString CameraLabel = FString::Printf(
                                TEXT("RaftSim_PveHandoff_%s"),
                                HandoffDistanceTokens[DistanceIndex]);
                            const FString CaptureId = FString::Printf(
                                TEXT("handoff_%s_%s"),
                                HandoffDistanceTokens[DistanceIndex],
                                HandoffAuthorityTokens[AuthorityIndex]);
                            const FString Description = FString::Printf(
                                TEXT("V25 exact %s cypress source/HLOD authority mode %s"),
                                HandoffDistanceTokens[DistanceIndex],
                                HandoffAuthorityTokens[AuthorityIndex]);
                            bAllHandoffsCaptured &= CapturePreviewImageForSpec(
                                ReviewSpec,
                                LocalCaptureRoot,
                                LocalHandoffCapturePaths[
                                    DistanceIndex * 3 + AuthorityIndex],
                                CameraLabel,
                                CaptureId,
                                Description,
                                false,
                                LocalVisualSummary,
                                [AuthorityMode](
                                    UWorld* LoadedWorld,
                                    ACameraActor* CaptureCamera,
                                    FString& SetupSummary)

                                {
                                    AActor* SourceTrunkActor = nullptr;
                                    AActor* SourceFoliageActor = nullptr;
                                    AActor* LoadedAtlasActor = nullptr;
                                    for (TActorIterator<AActor> It(LoadedWorld); It; ++It)
                                    {
                                        AActor* Actor = *It;
                                        if (!Actor)
                                        {
                                            continue;
                                        }
                                        const FString Label = Actor->GetActorLabel();
                                        if (Label == TEXT("RaftSim_PveReview_Trunk"))
                                        {
                                            SourceTrunkActor = Actor;
                                        }
                                        else if (Label == TEXT("RaftSim_PveReview_Foliage"))
                                        {
                                            SourceFoliageActor = Actor;
                                        }
                                        else if (Label ==
                                                 TEXT("RaftSim_PveCypressMultiViewAtlasHlod"))
                                        {
                                            LoadedAtlasActor = Actor;
                                        }
                                        else if (
                                            Label ==
                                                TEXT("RaftSim_PveCypressVolumetricFarProxy") ||
                                            Label ==
                                                TEXT("RaftSim_PveCypressNaniteWholeTree"))
                                        {
                                            Actor->SetActorHiddenInGame(true);
                                        }
                                    }
                                    if (!SourceTrunkActor || !SourceFoliageActor ||
                                        !LoadedAtlasActor || !CaptureCamera)
                                    {
                                        SetupSummary += TEXT(
                                            "Handoff setup could not resolve source, HLOD, and camera actors.\n");
                                        return false;
                                    }
                                    constexpr float SourceSelectionDistanceCm = 2500.0f;
                                    const float HorizontalDistanceCm = FVector::Dist2D(
                                        CaptureCamera->GetActorLocation(),
                                        LoadedAtlasActor->GetActorLocation());
                                    const bool bSourceOnly =
                                        AuthorityMode == TEXT("source_only");
                                    const bool bHlodOnly =
                                        AuthorityMode == TEXT("hlod_only");
                                    const bool bCombined =
                                        AuthorityMode == TEXT("combined");
                                    const bool bCombinedSelectsSource =
                                        bCombined &&
                                        HorizontalDistanceCm < SourceSelectionDistanceCm;
                                    const bool bShowSource =
                                        bSourceOnly || bCombinedSelectsSource;
                                    const bool bShowHlod =
                                        bHlodOnly ||
                                        (bCombined && !bCombinedSelectsSource);
                                    SourceTrunkActor->SetActorHiddenInGame(!bShowSource);
                                    SourceFoliageActor->SetActorHiddenInGame(!bShowSource);
                                    LoadedAtlasActor->SetActorHiddenInGame(!bShowHlod);
                                    SetupSummary += FString::Printf(
                                        TEXT("V25 handoff %s at %.3f m horizontal distance selects source=%s HLOD=%s.\n"),
                                        *AuthorityMode,
                                        HorizontalDistanceCm / 100.0f,
                                        bShowSource ? TEXT("true") : TEXT("false"),
                                        bShowHlod ? TEXT("true") : TEXT("false"));
                                    return (bShowSource != bShowHlod) &&
                                        (bSourceOnly || bHlodOnly || bCombined);
                                });
                        }
                    }
                    bLocalHandoffReviewCaptured = bAllHandoffsCaptured;
                }
                if (bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette)
                {
                    bool bAllTransitionCapturesProduced = true;
                    for (int32 DistanceIndex = 0; DistanceIndex < 3; ++DistanceIndex)
                    {
                        for (int32 AuthorityIndex = 0; AuthorityIndex < 3; ++AuthorityIndex)
                        {
                            const FString AuthorityMode =
                                HandoffAuthorityTokens[AuthorityIndex];
                            const float ExpectedSourceCoverage =
                                ComplementaryTransitionSourceCoverage[DistanceIndex];
                            const FString CameraLabel = FString::Printf(
                                TEXT("RaftSim_PveTransition_%s"),
                                ComplementaryTransitionDistanceTokens[DistanceIndex]);
                            const FString CaptureId = FString::Printf(
                                TEXT("transition_%s_%s"),
                                ComplementaryTransitionDistanceTokens[DistanceIndex],
                                HandoffAuthorityTokens[AuthorityIndex]);
                            const FString Description = FString::Printf(
                                TEXT("V32 exact radial %s complementary transition mode %s at %.2f source coverage"),
                                ComplementaryTransitionDistanceTokens[DistanceIndex],
                                *AuthorityMode,
                                ExpectedSourceCoverage);
                            bAllTransitionCapturesProduced &= CapturePreviewImageForSpec(
                                ReviewSpec,
                                LocalCaptureRoot,
                                LocalComplementaryTransitionCapturePaths[
                                    DistanceIndex * 3 + AuthorityIndex],
                                CameraLabel,
                                CaptureId,
                                Description,
                                false,
                                LocalVisualSummary,
                                [AuthorityMode, ExpectedSourceCoverage](
                                    UWorld* LoadedWorld,
                                    ACameraActor* CaptureCamera,
                                    FString& SetupSummary)
                                {
                                    AActor* SourceTrunkActor = nullptr;
                                    AActor* SourceFoliageActor = nullptr;
                                    AActor* LoadedAtlasActor = nullptr;
                                    for (TActorIterator<AActor> It(LoadedWorld); It; ++It)
                                    {
                                        AActor* Actor = *It;
                                        if (!Actor)
                                        {
                                            continue;
                                        }
                                        const FString Label = Actor->GetActorLabel();
                                        if (Label == TEXT("RaftSim_PveReview_Trunk"))
                                        {
                                            SourceTrunkActor = Actor;
                                        }
                                        else if (Label == TEXT("RaftSim_PveReview_Foliage"))
                                        {
                                            SourceFoliageActor = Actor;
                                        }
                                        else if (Label ==
                                                 TEXT("RaftSim_PveCypressMultiViewAtlasHlod"))
                                        {
                                            LoadedAtlasActor = Actor;
                                        }
                                        else if (
                                            Label ==
                                                TEXT("RaftSim_PveCypressVolumetricFarProxy") ||
                                            Label ==
                                                TEXT("RaftSim_PveCypressNaniteWholeTree"))
                                        {
                                            Actor->SetActorHiddenInGame(true);
                                        }
                                    }
                                    if (!SourceTrunkActor || !SourceFoliageActor ||
                                        !LoadedAtlasActor || !CaptureCamera)
                                    {
                                        SetupSummary += TEXT(
                                            "Complementary transition setup could not resolve source, HLOD, and camera actors.\n");
                                        return false;
                                    }
                                    const bool bSourceOnly =
                                        AuthorityMode == TEXT("source_only");
                                    const bool bHlodOnly =
                                        AuthorityMode == TEXT("hlod_only");
                                    const bool bCombined =
                                        AuthorityMode == TEXT("combined");
                                    const bool bShowSource = bSourceOnly || bCombined;
                                    const bool bShowHlod = bHlodOnly || bCombined;
                                    const float SourceCoverage = bSourceOnly
                                        ? 1.0f
                                        : (bHlodOnly ? 0.0f : ExpectedSourceCoverage);
                                    auto SetCoverage = [SourceCoverage](AActor* Actor)
                                    {
                                        TInlineComponentArray<UMeshComponent*> MeshComponents;
                                        Actor->GetComponents(MeshComponents);
                                        bool bUpdated = false;
                                        for (UMeshComponent* Component : MeshComponents)
                                        {
                                            if (!Component)
                                            {
                                                continue;
                                            }
                                            for (int32 MaterialIndex = 0;
                                                 MaterialIndex < Component->GetNumMaterials();
                                                 ++MaterialIndex)
                                            {
                                                UMaterialInstanceDynamic* DynamicMaterial =
                                                    Component->CreateDynamicMaterialInstance(
                                                        MaterialIndex);
                                                if (DynamicMaterial)
                                                {
                                                    DynamicMaterial->SetScalarParameterValue(
                                                        TEXT("ComplementarySourceCoverage"),
                                                        SourceCoverage);
                                                    bUpdated = true;
                                                }
                                            }
                                        }
                                        return bUpdated;
                                    };
                                    const bool bSourceMaterialsUpdated =
                                        SetCoverage(SourceTrunkActor) &&
                                        SetCoverage(SourceFoliageActor);
                                    const bool bHlodMaterialUpdated =
                                        SetCoverage(LoadedAtlasActor);
                                    SourceTrunkActor->SetActorHiddenInGame(!bShowSource);
                                    SourceFoliageActor->SetActorHiddenInGame(!bShowSource);
                                    LoadedAtlasActor->SetActorHiddenInGame(!bShowHlod);
                                    const float HorizontalDistanceCm = FVector::Dist2D(
                                        CaptureCamera->GetActorLocation(),
                                        LoadedAtlasActor->GetActorLocation());
                                    SetupSummary += FString::Printf(
                                        TEXT("V32 transition %s at %.3f m radial distance sets source coverage %.2f and visibility source=%s HLOD=%s.\n"),
                                        *AuthorityMode,
                                        HorizontalDistanceCm / 100.0f,
                                        SourceCoverage,
                                        bShowSource ? TEXT("true") : TEXT("false"),
                                        bShowHlod ? TEXT("true") : TEXT("false"));
                                    return bSourceMaterialsUpdated && bHlodMaterialUpdated &&
                                        (bSourceOnly || bHlodOnly || bCombined);
                                });
                        }
                    }
                    bLocalComplementaryTransitionReviewCaptured =
                        bAllTransitionCapturesProduced;
                    bool bAllTemporalTransitionCapturesProduced = true;
                    for (int32 SampleIndex = 0;
                         SampleIndex < LocalTemporalTransitionTokens.Num();
                         ++SampleIndex)
                    {
                        for (int32 AuthorityIndex = 0; AuthorityIndex < 3; ++AuthorityIndex)
                        {
                            const FString AuthorityMode =
                                HandoffAuthorityTokens[AuthorityIndex];
                            const float SourceCoverage =
                                LocalTemporalTransitionSourceCoverage[SampleIndex];
                            const FString CameraLabel = FString::Printf(
                                TEXT("RaftSim_PveTemporal_%s"),
                                *LocalTemporalTransitionTokens[SampleIndex]);
                            const FString CaptureId = FString::Printf(
                                TEXT("temporal_%s_%s"),
                                *LocalTemporalTransitionTokens[SampleIndex],
                                *AuthorityMode);
                            const FString Description = FString::Printf(
                                TEXT("V33 temporal-path sample %s mode %s at %.4f source coverage"),
                                *LocalTemporalTransitionTokens[SampleIndex],
                                *AuthorityMode,
                                SourceCoverage);
                            bAllTemporalTransitionCapturesProduced &=
                                CapturePreviewImageForSpec(
                                    ReviewSpec,
                                    LocalCaptureRoot,
                                    LocalTemporalTransitionCapturePaths[
                                        SampleIndex * 3 + AuthorityIndex],
                                    CameraLabel,
                                    CaptureId,
                                    Description,
                                    false,
                                    LocalVisualSummary,
                                    [AuthorityMode, SourceCoverage](
                                        UWorld* LoadedWorld,
                                        ACameraActor* CaptureCamera,
                                        FString& SetupSummary)
                                    {
                                        return ConfigureFutaleufuComplementaryTransitionCapture(
                                            LoadedWorld,
                                            CaptureCamera,
                                            AuthorityMode,
                                            SourceCoverage,
                                            SetupSummary);
                                    });
                        }
                    }
                    bLocalTemporalTransitionReviewCaptured =
                        bAllTemporalTransitionCapturesProduced;
                    bool bAllPersistentMotionTransitionCapturesProduced = true;
                    for (const TCHAR* AuthorityToken : HandoffAuthorityTokens)
                    {
                        bAllPersistentMotionTransitionCapturesProduced &=
                            CaptureFutaleufuComplementaryTransitionMotionSequence(
                                ReviewSpec,
                                LocalVisualCaptureBase,
                                AuthorityToken,
                                4,
                                LocalPersistentMotionTransitionCapturePaths,
                                LocalVisualSummary);
                    }
                    bLocalPersistentMotionTransitionReviewCaptured =
                        bAllPersistentMotionTransitionCapturesProduced &&
                        LocalPersistentMotionTransitionCapturePaths.Num() == 147;
                    for (const FString& CapturePath :
                         LocalPersistentMotionTransitionCapturePaths)
                    {
                        LocalPersistentMotionTransitionCapturesJson += FString::Printf(
                            TEXT("%s\"%s\""),
                            LocalPersistentMotionTransitionCapturesJson.IsEmpty()
                                ? TEXT("")
                                : TEXT(", "),
                            *EscapeRaftSimJsonString(CapturePath));
                    }
                    bool bAllFinePersistentMotionTransitionCapturesProduced = true;
                    for (const TCHAR* AuthorityToken : HandoffAuthorityTokens)
                    {
                        bAllFinePersistentMotionTransitionCapturesProduced &=
                            CaptureFutaleufuComplementaryTransitionMotionSequence(
                                ReviewSpec,
                                LocalVisualCaptureBase,
                                AuthorityToken,
                                8,
                                LocalFinePersistentMotionTransitionCapturePaths,
                                LocalVisualSummary);
                    }
                    bLocalFinePersistentMotionTransitionReviewCaptured =
                        bAllFinePersistentMotionTransitionCapturesProduced &&
                        LocalFinePersistentMotionTransitionCapturePaths.Num() == 147;
                    for (const FString& CapturePath :
                         LocalFinePersistentMotionTransitionCapturePaths)
                    {
                        LocalFinePersistentMotionTransitionCapturesJson += FString::Printf(
                            TEXT("%s\"%s\""),
                            LocalFinePersistentMotionTransitionCapturesJson.IsEmpty()
                                ? TEXT("")
                                : TEXT(", "),
                            *EscapeRaftSimJsonString(CapturePath));
                    }

                    FRaftSimEnvironmentPreviewSpec LitRiverReviewSpec = ReviewSpec;

                    LitRiverReviewSpec.DisplayName =
                        TEXT("Futaleufu V35 cypress handoff in the physical corridor");
                    LitRiverReviewSpec.MapPackagePath =
                        TEXT("/Game/RaftSim/Maps/EnvironmentPreviews/LandscapeCandidates/"
                             "L_FutaleufuTerminator_PhysicalCorridorCandidate");
                    LitRiverReviewSpec.bDeterministicValidationCapture = false;
                    UMaterialInterface* ActiveLitRiverHlodMaterial =
                        LocalMultiViewAtlas.Material;
                    UMaterialInterface* ActiveLitRiverHlodTrunkMaterial = nullptr;
                    UMaterialInterface* ActiveLitRiverHlodFoliageMaterial = nullptr;
                    bool bSpawnMergedGeometryHlodForCurrentCapture = false;
                    const auto SetupLitRiverView = [
                        TrunkMesh,
                        LocalHlodMesh = LocalMultiViewHlodMesh,
                        MergedGeometryMesh = LocalImpostorSourceMesh,
                        &ActiveLitRiverHlodMaterial,
                        &ActiveLitRiverHlodTrunkMaterial,
                        &ActiveLitRiverHlodFoliageMaterial,
                        &bSpawnMergedGeometryHlodForCurrentCapture,
                        LocalHlodTransform = LocalMultiViewHlodTransform,
                        &FoliageFacade,
                        GetLocalFoliageTransform](
                            UWorld* World,
                            ACameraActor*& ReferenceCamera,
                            AActor*& HlodActor,
                            FVector& MotionForward,
                            FVector& MotionRight,
                            FVector& ViewTargetOffset,
                            FString& SetupSummary)
                    {
                        if (!World || !TrunkMesh || !LocalHlodMesh ||
                            (bSpawnMergedGeometryHlodForCurrentCapture &&
                             !MergedGeometryMesh) ||
                            !ActiveLitRiverHlodMaterial ||
                            ((ActiveLitRiverHlodTrunkMaterial != nullptr) !=
                             (ActiveLitRiverHlodFoliageMaterial != nullptr)) ||
                            !FoliageFacade.IsValid())
                        {
                            SetupSummary += TEXT(
                                "V36 lit river-view setup is missing the corridor world, source, or HLOD assets.\n");
                            return false;
                        }

                        ACameraActor* RiverEyeCamera = FindPreviewCaptureCamera(
                            World,
                            TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"));
                        TActorIterator<ALandscape> LandscapeIt(World);
                        ALandscape* Landscape = LandscapeIt ? *LandscapeIt : nullptr;
                        if (!RiverEyeCamera || !RiverEyeCamera->GetCameraComponent() || !Landscape)
                        {
                            SetupSummary += TEXT(
                                "V36 lit river-view setup could not resolve the river-eye camera and Landscape.\n");
                            return false;
                        }

                        FVector RiverForward = RiverEyeCamera->GetActorForwardVector();
                        RiverForward.Z = 0.0f;
                        RiverForward.Normalize();
                        const FVector RiverRight(-RiverForward.Y, RiverForward.X, 0.0f);
                        if (RiverForward.IsNearlyZero())
                        {
                            SetupSummary += TEXT(
                                "V36 lit river-view setup found a degenerate river-eye camera basis.\n");
                            return false;
                        }

                        constexpr float TreeForwardOffsetCm = 3000.0f;
                        constexpr float StartRadiusCm = 2300.0f;
                        constexpr float LateralOffsetCm = 800.0f;
                        constexpr float RiverEyeClearanceAboveWaterCm = 130.0f;
                        const float StartAxialDistanceCm = FMath::Sqrt(
                            FMath::Square(StartRadiusCm) - FMath::Square(LateralOffsetCm));
                        const FVector RiverEyeLocation = RiverEyeCamera->GetActorLocation();
                        const float WaterSurfaceZ =
                            RiverEyeLocation.Z - RiverEyeClearanceAboveWaterCm;
                        UProceduralMeshComponent* RiverRibbonComponent = nullptr;
                        for (TActorIterator<AActor> It(World); It; ++It)
                        {
                            if (*It && It->GetActorLabel() ==
                                    TEXT("RaftSim_PhysicalCorridorRiverRibbon_futaleufu_terminator"))
                            {
                                RiverRibbonComponent =
                                    It->FindComponentByClass<UProceduralMeshComponent>();
                                break;
                            }
                        }
                        const FProcMeshSection* RiverRibbonSection =
                            RiverRibbonComponent
                            ? RiverRibbonComponent->GetProcMeshSection(0)
                            : nullptr;
                        if (!RiverRibbonSection)
                        {
                            SetupSummary += TEXT(
                                "V36 lit river-view setup could not resolve the physical river-ribbon section.\n");
                            return false;
                        }

                        const FVector DesiredCrossSection =
                            RiverEyeLocation + RiverForward * TreeForwardOffsetCm;
                        FVector RiverEdgeWorld[2] = {
                            FVector::ZeroVector,
                            FVector::ZeroVector};
                        float RiverEdgeDistanceSquared[2] = {
                            TNumericLimits<float>::Max(),
                            TNumericLimits<float>::Max()};
                        for (const FProcMeshVertex& Vertex :
                             RiverRibbonSection->ProcVertexBuffer)
                        {
                            const int32 EdgeIndex = Vertex.UV0.Y <= 0.01f
                                ? 0
                                : (Vertex.UV0.Y >= 0.99f ? 1 : -1);
                            if (EdgeIndex < 0)
                            {
                                continue;
                            }
                            const FVector WorldPosition =
                                RiverRibbonComponent->GetComponentTransform().TransformPosition(
                                    Vertex.Position);
                            const float DistanceSquared = FVector::DistSquared2D(
                                WorldPosition,
                                DesiredCrossSection);
                            if (DistanceSquared < RiverEdgeDistanceSquared[EdgeIndex])
                            {
                                RiverEdgeDistanceSquared[EdgeIndex] = DistanceSquared;
                                RiverEdgeWorld[EdgeIndex] = WorldPosition;
                            }
                        }
                        if (!FMath::IsFinite(RiverEdgeDistanceSquared[0]) ||
                            !FMath::IsFinite(RiverEdgeDistanceSquared[1]))
                        {
                            SetupSummary += TEXT(
                                "V36 lit river-view setup could not resolve both physical ribbon edges.\n");
                            return false;
                        }

                        float BestScore = TNumericLimits<float>::Max();
                        float BestBankSign = 1.0f;
                        float BestBankOffsetCm = 0.0f;
                        FVector BestTreeXY = FVector::ZeroVector;
                        float BestTreeGroundZ = TNumericLimits<float>::Lowest();
                        float BestCameraGroundZ = TNumericLimits<float>::Lowest();
                        for (int32 EdgeIndex = 0; EdgeIndex < 2; ++EdgeIndex)
                        {
                            FVector Outward = RiverEdgeWorld[EdgeIndex] - DesiredCrossSection;
                            Outward.Z = 0.0f;
                            Outward.Normalize();
                            if (Outward.IsNearlyZero())
                            {
                                continue;
                            }
                            constexpr float TreeOutsideRibbonCm = 150.0f;
                            const FVector CandidateTreeXY =
                                RiverEdgeWorld[EdgeIndex] + Outward * TreeOutsideRibbonCm;
                            const FVector CandidateCameraXY =
                                CandidateTreeXY - Outward * StartAxialDistanceCm -
                                RiverForward * LateralOffsetCm;
                            const float TreeGroundZ = Landscape->GetHeightAtLocation(
                                FVector(CandidateTreeXY.X, CandidateTreeXY.Y, 0.0f),
                                EHeightfieldSource::Editor).Get(
                                    TNumericLimits<float>::Lowest());
                            const float CameraGroundZ = Landscape->GetHeightAtLocation(
                                FVector(CandidateCameraXY.X, CandidateCameraXY.Y, 0.0f),
                                EHeightfieldSource::Editor).Get(
                                    TNumericLimits<float>::Lowest());
                            if (!FMath::IsFinite(TreeGroundZ) ||
                                !FMath::IsFinite(CameraGroundZ))
                            {
                                continue;
                            }
                            const float BankElevationPenalty = FMath::Abs(
                                TreeGroundZ - RiverEdgeWorld[EdgeIndex].Z);
                            const float CameraRibbonPenalty = FMath::Max(
                                0.0f,
                                CameraGroundZ - WaterSurfaceZ) * 4.0f;
                            const float Score =
                                BankElevationPenalty + CameraRibbonPenalty;
                            if (Score < BestScore)
                            {
                                BestScore = Score;
                                BestBankSign = FVector::DotProduct(Outward, RiverRight) < 0.0f
                                    ? -1.0f
                                    : 1.0f;
                                BestBankOffsetCm = FVector::Dist2D(
                                    CandidateTreeXY,
                                    DesiredCrossSection);
                                BestTreeXY = CandidateTreeXY;
                                BestTreeGroundZ = TreeGroundZ;
                                BestCameraGroundZ = CameraGroundZ;
                            }
                        }
                        if (!FMath::IsFinite(BestTreeGroundZ) ||
                            !FMath::IsFinite(BestCameraGroundZ))
                        {
                            SetupSummary += TEXT(
                                "V36 lit river-view setup could not find a finite near-bank placement.\n");
                            return false;
                        }

                        const FBox TrunkBounds = TrunkMesh->GetBoundingBox();
                        const FVector TreeRootLocation(
                            BestTreeXY.X,
                            BestTreeXY.Y,
                            BestTreeGroundZ - TrunkBounds.Min.Z + 2.0f);
                        const FTransform TreeRootTransform(
                            FRotator::ZeroRotator,
                            TreeRootLocation);
                        FActorSpawnParameters SpawnParameters;
                        SpawnParameters.ObjectFlags = RF_Transient;
                        AStaticMeshActor* SourceTrunkActor = World->SpawnActor<AStaticMeshActor>(
                            AStaticMeshActor::StaticClass(),
                            TreeRootTransform,
                            SpawnParameters);
                        AActor* SourceFoliageActor = World->SpawnActor<AActor>(
                            AActor::StaticClass(),
                            TreeRootTransform,
                            SpawnParameters);
                        AStaticMeshActor* AtlasActor = World->SpawnActor<AStaticMeshActor>(
                            AStaticMeshActor::StaticClass(),
                            LocalHlodTransform * TreeRootTransform,
                            SpawnParameters);
                        AStaticMeshActor* MergedGeometryActor =
                            bSpawnMergedGeometryHlodForCurrentCapture
                            ? World->SpawnActor<AStaticMeshActor>(
                                AStaticMeshActor::StaticClass(),
                                TreeRootTransform,
                                SpawnParameters)
                            : nullptr;
                        AActor* MergedGeometrySplitActor =
                            bSpawnMergedGeometryHlodForCurrentCapture
                            ? World->SpawnActor<AActor>(
                                AActor::StaticClass(),
                                TreeRootTransform,
                                SpawnParameters)
                            : nullptr;
                        if (!SourceTrunkActor || !SourceTrunkActor->GetStaticMeshComponent() ||
                            !SourceFoliageActor || !AtlasActor ||
                            !AtlasActor->GetStaticMeshComponent() ||
                            (bSpawnMergedGeometryHlodForCurrentCapture &&
                             (!MergedGeometryActor ||
                              !MergedGeometryActor->GetStaticMeshComponent() ||
                              !MergedGeometrySplitActor)))
                        {
                            SetupSummary += TEXT(
                                "V36 lit river-view setup could not spawn the transient transition actors.\n");
                            return false;
                        }

                        SourceTrunkActor->SetActorLabel(TEXT("RaftSim_PveReview_Trunk"));
                        SourceTrunkActor->Tags.Add(TEXT("RaftSim_VisualReviewOnly"));
                        UStaticMeshComponent* TrunkComponent =
                            SourceTrunkActor->GetStaticMeshComponent();
                        TrunkComponent->SetStaticMesh(TrunkMesh);
                        TrunkComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
                        TrunkComponent->SetGenerateOverlapEvents(false);
                        TrunkComponent->SetCastShadow(true);

                        SourceFoliageActor->SetActorLabel(TEXT("RaftSim_PveReview_Foliage"));
                        SourceFoliageActor->Tags.Add(TEXT("RaftSim_VisualReviewOnly"));
                        USceneComponent* Root = NewObject<USceneComponent>(
                            SourceFoliageActor,
                            TEXT("V36LitRiverViewRoot"));
                        SourceFoliageActor->AddInstanceComponent(Root);
                        SourceFoliageActor->SetRootComponent(Root);
                        Root->SetMobility(EComponentMobility::Static);
                        Root->RegisterComponent();
                        SourceFoliageActor->SetActorTransform(TreeRootTransform);
                        TArray<UHierarchicalInstancedStaticMeshComponent*> FoliageComponents;
                        FoliageComponents.SetNum(FoliageFacade.NumFoliageInfo());
                        for (int32 MeshIndex = 0;
                             MeshIndex < FoliageFacade.NumFoliageInfo();
                             ++MeshIndex)
                        {
                            UStaticMesh* FoliageMesh = LoadObject<UStaticMesh>(
                                nullptr,
                                *FoliageFacade.GetFoliageInfo(MeshIndex).Mesh.ToString());
                            if (!FoliageMesh)
                            {
                                continue;
                            }
                            UHierarchicalInstancedStaticMeshComponent* Component =
                                NewObject<UHierarchicalInstancedStaticMeshComponent>(
                                    SourceFoliageActor,
                                    *FString::Printf(TEXT("V36PveFoliage_%02d"), MeshIndex));
                            SourceFoliageActor->AddInstanceComponent(Component);
                            Component->SetupAttachment(Root);
                            Component->SetStaticMesh(FoliageMesh);
                            Component->SetMobility(EComponentMobility::Static);
                            Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
                            Component->SetGenerateOverlapEvents(false);
                            Component->SetCastShadow(false);
                            Component->bCastStaticShadow = false;
                            Component->bCastDynamicShadow = false;
                            Component->SetCastContactShadow(false);
                            Component->SetAffectDistanceFieldLighting(false);
                            Component->SetAffectDynamicIndirectLighting(false);
                            Component->RegisterComponent();
                            FoliageComponents[MeshIndex] = Component;
                        }
                        int32 AddedFoliageInstanceCount = 0;
                        for (int32 EntryIndex = 0;
                             EntryIndex < FoliageFacade.NumFoliageEntries();
                             ++EntryIndex)
                        {
                            const PV::Facades::FFoliageEntryData Entry =
                                FoliageFacade.GetFoliageEntry(EntryIndex);
                            if (!FoliageComponents.IsValidIndex(Entry.NameId) ||
                                !FoliageComponents[Entry.NameId])
                            {
                                continue;
                            }
                            FoliageComponents[Entry.NameId]->AddInstance(
                                GetLocalFoliageTransform(EntryIndex));
                            ++AddedFoliageInstanceCount;
                        }

                        AtlasActor->SetActorLabel(
                            TEXT("RaftSim_PveCypressMultiViewAtlasHlod"));
                        AtlasActor->Tags.Add(TEXT("RaftSim_VisualReviewOnly"));
                        UStaticMeshComponent* AtlasComponent =
                            AtlasActor->GetStaticMeshComponent();

                        AtlasComponent->SetStaticMesh(LocalHlodMesh);
                        AtlasComponent->SetMaterial(0, ActiveLitRiverHlodMaterial);
                        AtlasComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
                        AtlasComponent->SetGenerateOverlapEvents(false);
                        AtlasComponent->SetCastShadow(false);
                        AtlasComponent->SetAffectDistanceFieldLighting(false);
                        AtlasComponent->SetAffectDynamicIndirectLighting(false);
                        AtlasComponent->BoundsScale = 2.5f;
                        AtlasComponent->ComponentTags.Add(
                            TEXT("RaftSimHlodCombinedLayer"));
                        if (ActiveLitRiverHlodTrunkMaterial &&
                            ActiveLitRiverHlodFoliageMaterial)
                        {
                            const auto AddAtlasLayer = [
                                AtlasActor,
                                AtlasComponent,
                                LocalHlodMesh](
                                const TCHAR* ComponentName,
                                const TCHAR* ComponentTag,
                                UMaterialInterface* LayerMaterial)
                            {
                                UStaticMeshComponent* LayerComponent =
                                    NewObject<UStaticMeshComponent>(
                                        AtlasActor,
                                        ComponentName);
                                AtlasActor->AddInstanceComponent(LayerComponent);
                                LayerComponent->SetupAttachment(AtlasComponent);
                                LayerComponent->SetStaticMesh(LocalHlodMesh);
                                LayerComponent->SetMaterial(0, LayerMaterial);
                                LayerComponent->SetMobility(EComponentMobility::Static);
                                LayerComponent->SetCollisionEnabled(
                                    ECollisionEnabled::NoCollision);
                                LayerComponent->SetGenerateOverlapEvents(false);
                                LayerComponent->SetCastShadow(false);
                                LayerComponent->SetAffectDistanceFieldLighting(false);
                                LayerComponent->SetAffectDynamicIndirectLighting(false);
                                LayerComponent->BoundsScale = 2.5f;
                                LayerComponent->ComponentTags.Add(ComponentTag);
                                LayerComponent->SetVisibility(false, true);
                                LayerComponent->RegisterComponent();
                                return LayerComponent;
                            };
                            AddAtlasLayer(
                                TEXT("V40HlodTrunkLayer"),
                                TEXT("RaftSimHlodTrunkLayer"),
                                ActiveLitRiverHlodTrunkMaterial);
                            AddAtlasLayer(
                                TEXT("V40HlodFoliageLayer"),
                                TEXT("RaftSimHlodFoliageLayer"),
                                ActiveLitRiverHlodFoliageMaterial);
                        }

                        if (MergedGeometryActor)
                        {
                            MergedGeometryActor->SetActorLabel(
                                TEXT("RaftSim_PveCypressMergedGeometryHlod"));
                            MergedGeometryActor->Tags.Add(
                                TEXT("RaftSim_VisualReviewOnly"));
                            UStaticMeshComponent* MergedGeometryComponent =
                                MergedGeometryActor->GetStaticMeshComponent();
                            MergedGeometryComponent->SetStaticMesh(MergedGeometryMesh);
                            MergedGeometryComponent->SetMobility(
                                EComponentMobility::Static);
                            MergedGeometryComponent->SetCollisionEnabled(
                                ECollisionEnabled::NoCollision);
                            MergedGeometryComponent->SetGenerateOverlapEvents(false);
                            MergedGeometryComponent->SetCastShadow(false);
                            MergedGeometryComponent->bCastStaticShadow = false;
                            MergedGeometryComponent->bCastDynamicShadow = false;
                            MergedGeometryComponent->SetCastContactShadow(false);
                            MergedGeometryComponent->SetAffectDistanceFieldLighting(false);
                            MergedGeometryComponent->SetAffectDynamicIndirectLighting(false);
                            MergedGeometryActor->SetActorHiddenInGame(true);
                        }

                        if (MergedGeometrySplitActor)
                        {
                            TArray<int32> BarkMaterialIndices;
                            TArray<int32> FoliageMaterialIndices;
                            const TArray<FStaticMaterial>& SourceMaterials =
                                MergedGeometryMesh->GetStaticMaterials();
                            for (int32 MaterialIndex = 0;
                                 MaterialIndex < SourceMaterials.Num();
                                 ++MaterialIndex)
                            {
                                const UMaterialInterface* Material =
                                    SourceMaterials[MaterialIndex].MaterialInterface;
                                const FString MaterialIdentity = Material
                                    ? Material->GetPathName()
                                    : SourceMaterials[MaterialIndex]
                                          .MaterialSlotName.ToString();
                                if (MaterialIdentity.Contains(
                                        TEXT("Bark"),
                                        ESearchCase::IgnoreCase))
                                {
                                    BarkMaterialIndices.Add(MaterialIndex);
                                }
                                else
                                {
                                    FoliageMaterialIndices.Add(MaterialIndex);
                                }
                            }
                            if (BarkMaterialIndices.Num() != 1 ||
                                FoliageMaterialIndices.IsEmpty())
                            {
                                SetupSummary += FString::Printf(
                                    TEXT("V43 merged-component parity could not classify the merged source into one bark slot and at least one foliage slot (bark=%d foliage=%d).\n"),
                                    BarkMaterialIndices.Num(),
                                    FoliageMaterialIndices.Num());
                                return false;
                            }

                            MergedGeometrySplitActor->SetActorLabel(
                                TEXT("RaftSim_PveCypressMergedGeometrySplitHlod"));
                            MergedGeometrySplitActor->Tags.Add(
                                TEXT("RaftSim_VisualReviewOnly"));
                            USceneComponent* SplitRoot = NewObject<USceneComponent>(
                                MergedGeometrySplitActor,
                                TEXT("V43MergedGeometrySplitRoot"));
                            MergedGeometrySplitActor->AddInstanceComponent(SplitRoot);
                            MergedGeometrySplitActor->SetRootComponent(SplitRoot);
                            SplitRoot->SetMobility(EComponentMobility::Static);
                            SplitRoot->SetWorldTransform(TreeRootTransform);
                            SplitRoot->RegisterComponent();

                            UDynamicMeshComponent* SplitBarkComponent =
                                NewObject<UDynamicMeshComponent>(
                                    MergedGeometrySplitActor,
                                    TEXT("V43MergedGeometrySplitBark"));
                            UDynamicMeshComponent* SplitFoliageComponent =
                                NewObject<UDynamicMeshComponent>(
                                    MergedGeometrySplitActor,
                                    TEXT("V43MergedGeometrySplitFoliage"));
                            MergedGeometrySplitActor->AddInstanceComponent(
                                SplitBarkComponent);
                            MergedGeometrySplitActor->AddInstanceComponent(
                                SplitFoliageComponent);
                            SplitBarkComponent->SetupAttachment(SplitRoot);
                            SplitFoliageComponent->SetupAttachment(SplitRoot);

                            UDynamicMesh* SplitBarkMesh = NewObject<UDynamicMesh>(
                                SplitBarkComponent,
                                TEXT("V43MergedGeometrySplitBarkMesh"));
                            UDynamicMesh* SplitFoliageMesh = NewObject<UDynamicMesh>(
                                SplitFoliageComponent,
                                TEXT("V43MergedGeometrySplitFoliageMesh"));
                            EGeometryScriptOutcomePins BarkCopyOutcome =
                                EGeometryScriptOutcomePins::Failure;
                            EGeometryScriptOutcomePins FoliageCopyOutcome =
                                EGeometryScriptOutcomePins::Failure;
                            UGeometryScriptLibrary_StaticMeshFunctions::CopyMeshFromStaticMeshV2(
                                MergedGeometryMesh,
                                SplitBarkMesh,
                                FGeometryScriptCopyMeshFromAssetOptions(),
                                FGeometryScriptMeshReadLOD(),
                                BarkCopyOutcome,
                                false,
                                nullptr);
                            UGeometryScriptLibrary_StaticMeshFunctions::CopyMeshFromStaticMeshV2(
                                MergedGeometryMesh,
                                SplitFoliageMesh,
                                FGeometryScriptCopyMeshFromAssetOptions(),
                                FGeometryScriptMeshReadLOD(),
                                FoliageCopyOutcome,
                                false,
                                nullptr);
                            int32 DeletedBarkTriangleCount = 0;
                            int32 DeletedFoliageTriangleCount = 0;
                            for (int32 FoliageMaterialIndex : FoliageMaterialIndices)
                            {
                                int32 DeletedCount = 0;
                                UGeometryScriptLibrary_MeshMaterialFunctions::
                                    DeleteTrianglesByMaterialID(
                                        SplitBarkMesh,
                                        FoliageMaterialIndex,
                                        DeletedCount,
                                        true,
                                        nullptr);
                                DeletedBarkTriangleCount += DeletedCount;
                            }
                            for (int32 BarkMaterialIndex : BarkMaterialIndices)
                            {
                                int32 DeletedCount = 0;
                                UGeometryScriptLibrary_MeshMaterialFunctions::
                                    DeleteTrianglesByMaterialID(
                                        SplitFoliageMesh,
                                        BarkMaterialIndex,
                                        DeletedCount,
                                        true,
                                        nullptr);
                                DeletedFoliageTriangleCount += DeletedCount;
                            }
                            if (BarkCopyOutcome != EGeometryScriptOutcomePins::Success ||
                                FoliageCopyOutcome !=
                                    EGeometryScriptOutcomePins::Success ||
                                DeletedBarkTriangleCount <= 0 ||
                                DeletedFoliageTriangleCount <= 0)
                            {
                                SetupSummary += FString::Printf(
                                    TEXT("V43 merged-component parity could not split exact source triangles by material ID (bark copy=%d foliage copy=%d deleted from bark=%d deleted from foliage=%d).\n"),
                                    static_cast<int32>(BarkCopyOutcome),
                                    static_cast<int32>(FoliageCopyOutcome),
                                    DeletedBarkTriangleCount,
                                    DeletedFoliageTriangleCount);
                                return false;
                            }

                            SplitBarkComponent->SetDynamicMesh(SplitBarkMesh);
                            SplitFoliageComponent->SetDynamicMesh(SplitFoliageMesh);
                            for (int32 MaterialIndex = 0;
                                 MaterialIndex < SourceMaterials.Num();
                                 ++MaterialIndex)
                            {
                                SplitBarkComponent->SetMaterial(
                                    MaterialIndex,
                                    SourceMaterials[MaterialIndex].MaterialInterface);
                                SplitFoliageComponent->SetMaterial(
                                    MaterialIndex,
                                    SourceMaterials[MaterialIndex].MaterialInterface);
                            }
                            SplitBarkComponent->SetMobility(EComponentMobility::Static);
                            SplitBarkComponent->SetCollisionEnabled(
                                ECollisionEnabled::NoCollision);
                            SplitBarkComponent->SetGenerateOverlapEvents(false);
                            SplitBarkComponent->SetCastShadow(true);
                            SplitBarkComponent->ComponentTags.Add(
                                TEXT("RaftSimMergedGeometrySplitBark"));
                            SplitFoliageComponent->SetMobility(
                                EComponentMobility::Static);
                            SplitFoliageComponent->SetCollisionEnabled(
                                ECollisionEnabled::NoCollision);
                            SplitFoliageComponent->SetGenerateOverlapEvents(false);
                            SplitFoliageComponent->SetCastShadow(false);
                            SplitFoliageComponent->bCastStaticShadow = false;
                            SplitFoliageComponent->bCastDynamicShadow = false;
                            SplitFoliageComponent->SetCastContactShadow(false);
                            SplitFoliageComponent->SetAffectDistanceFieldLighting(
                                false);
                            SplitFoliageComponent->SetAffectDynamicIndirectLighting(
                                false);
                            SplitFoliageComponent->ComponentTags.Add(
                                TEXT("RaftSimMergedGeometrySplitFoliage"));
                            SplitBarkComponent->RegisterComponent();
                            SplitFoliageComponent->RegisterComponent();
                            MergedGeometrySplitActor->SetActorHiddenInGame(true);
                        }

                        const FVector HlodTarget = AtlasActor->GetActorLocation();
                        FVector BankOutward = BestTreeXY - DesiredCrossSection;
                        BankOutward.Z = 0.0f;
                        BankOutward.Normalize();
                        const FVector CameraStartXY =
                            HlodTarget - BankOutward * StartAxialDistanceCm -
                            RiverForward * LateralOffsetCm;
                        const FVector CameraStart(
                            CameraStartXY.X,
                            CameraStartXY.Y,
                            RiverEyeLocation.Z);
                        const FVector ViewTarget =
                            TreeRootLocation + FVector(0.0f, 0.0f, 500.0f);
                        RiverEyeCamera->SetActorLocationAndRotation(
                            CameraStart,
                            (ViewTarget - CameraStart).Rotation());
                        RiverEyeCamera->GetCameraComponent()->FieldOfView = 68.0f;

                        ReferenceCamera = RiverEyeCamera;
                        HlodActor = AtlasActor;
                        MotionForward = BankOutward;
                        MotionRight = RiverForward;
                        ViewTargetOffset = ViewTarget - HlodTarget;
                        World->SendAllEndOfFrameUpdates();
                        FlushRenderingCommands();
                        SetupSummary += FString::Printf(
                            TEXT("V36 placed one transient source/HLOD pair on the %.0f bank side "
                                 "at %.3f m offset, bank ground %.3f m, water-side ground %.3f m, "
                                 "and water surface %.3f m with %d/%d foliage instances; the source "
                                 "Landscape, water, collision, solver, and saved corridor remain unchanged.\n"),
                            BestBankSign,
                            BestBankOffsetCm / 100.0f,
                            BestTreeGroundZ / 100.0f,
                            BestCameraGroundZ / 100.0f,
                            WaterSurfaceZ / 100.0f,
                            AddedFoliageInstanceCount,
                            FoliageFacade.NumFoliageEntries());
                        return AddedFoliageInstanceCount ==
                            FoliageFacade.NumFoliageEntries();
                    };
                    bool bAllLitRiverViewMotionCapturesProduced = true;
                    for (const TCHAR* AuthorityToken : HandoffAuthorityTokens)
                    {
                        bAllLitRiverViewMotionCapturesProduced &=
                            CaptureFutaleufuComplementaryTransitionMotionSequence(
                                LitRiverReviewSpec,
                                LocalVisualCaptureBase,
                                AuthorityToken,
                                8,
                                LocalLitRiverViewMotionTransitionCapturePaths,
                                LocalVisualSummary,
                                true,
                                SetupLitRiverView);
                    }
                    bLocalLitRiverViewMotionTransitionReviewCaptured =
                        bAllLitRiverViewMotionCapturesProduced &&
                        LocalLitRiverViewMotionTransitionCapturePaths.Num() == 147;
                    for (const FString& CapturePath :
                         LocalLitRiverViewMotionTransitionCapturePaths)
                    {
                        LocalLitRiverViewMotionTransitionCapturesJson += FString::Printf(
                            TEXT("%s\"%s\""),
                            LocalLitRiverViewMotionTransitionCapturesJson.IsEmpty()
                                ? TEXT("")
                                : TEXT(", "),
                            *EscapeRaftSimJsonString(CapturePath));
                    }
                    ActiveLitRiverHlodMaterial =
                        LocalMultiViewAtlas.RelightableMaterial;
                    bool bAllTemporalLitRiverViewMotionCapturesProduced =
                        LocalMultiViewAtlas.IsRelightableReady();
                    for (const TCHAR* AuthorityToken : HandoffAuthorityTokens)
                    {

                        bAllTemporalLitRiverViewMotionCapturesProduced &=
                            CaptureFutaleufuComplementaryTransitionMotionSequence(
                                LitRiverReviewSpec,
                                LocalVisualCaptureBase,
                                AuthorityToken,
                                8,
                                LocalTemporalLitRiverViewMotionTransitionCapturePaths,
                                LocalVisualSummary,
                                true,
                                SetupLitRiverView,
                                1.0f);
                    }
                    bLocalTemporalLitRiverViewMotionTransitionReviewCaptured =
                        bAllTemporalLitRiverViewMotionCapturesProduced &&
                        LocalTemporalLitRiverViewMotionTransitionCapturePaths.Num() == 147;
                    for (const FString& CapturePath :
                         LocalTemporalLitRiverViewMotionTransitionCapturePaths)
                    {
                        LocalTemporalLitRiverViewMotionTransitionCapturesJson +=
                            FString::Printf(
                                TEXT("%s\"%s\""),
                                LocalTemporalLitRiverViewMotionTransitionCapturesJson.IsEmpty()
                                    ? TEXT("")
                                    : TEXT(", "),
                                *EscapeRaftSimJsonString(CapturePath));
                    }
                    const bool bAllHlodFrameSearchCapturesProduced =
                        LocalMultiViewAtlas.IsRelightableReady() &&
                        CaptureFutaleufuComplementaryTransitionMotionSequence(
                            LitRiverReviewSpec,
                            LocalVisualCaptureBase,
                            TEXT("hlod_frame_search"),
                            8,
                            LocalHlodFrameSearchCapturePaths,
                            LocalVisualSummary,
                            true,
                            SetupLitRiverView,
                            1.0f,
                            true,
                            &LocalHlodFrameSearchAutomaticFrame);
                    bLocalHlodFrameSearchReviewCaptured =
                        bAllHlodFrameSearchCapturesProduced &&
                        LocalHlodFrameSearchCapturePaths.Num() == 10;
                    for (const FString& CapturePath :
                         LocalHlodFrameSearchCapturePaths)
                    {
                        LocalHlodFrameSearchCapturesJson += FString::Printf(
                            TEXT("%s\"%s\""),
                            LocalHlodFrameSearchCapturesJson.IsEmpty()
                                ? TEXT("")
                                : TEXT(", "),
                            *EscapeRaftSimJsonString(CapturePath));
                    }
                    const bool bAllHlodSplitShadingSearchCapturesProduced =
                        LocalMultiViewAtlas.IsRelightableReady() &&
                        CaptureFutaleufuComplementaryTransitionMotionSequence(
                            LitRiverReviewSpec,
                            LocalVisualCaptureBase,
                            TEXT("hlod_split_shading_search"),
                            8,
                            LocalHlodSplitShadingSearchCapturePaths,
                            LocalVisualSummary,
                            true,
                            SetupLitRiverView,
                            1.0f,
                            false,
                            nullptr,
                            true);
                    bLocalHlodSplitShadingSearchReviewCaptured =
                        bAllHlodSplitShadingSearchCapturesProduced &&
                        LocalHlodSplitShadingSearchCapturePaths.Num() == 10;
                    for (const FString& CapturePath :
                         LocalHlodSplitShadingSearchCapturePaths)
                    {
                        LocalHlodSplitShadingSearchCapturesJson += FString::Printf(
                            TEXT("%s\"%s\""),
                            LocalHlodSplitShadingSearchCapturesJson.IsEmpty()
                                ? TEXT("")
                                : TEXT(", "),
                            *EscapeRaftSimJsonString(CapturePath));
                    }
                    ActiveLitRiverHlodTrunkMaterial =
                        LocalMultiViewAtlas.RelightableTrunkMaterial;
                    ActiveLitRiverHlodFoliageMaterial =
                        LocalMultiViewAtlas.RelightableFoliageMaterial;
                    const bool bAllHlodDualLayerCapturesProduced =
                        LocalMultiViewAtlas.IsSplitRelightableReady() &&
                        CaptureFutaleufuComplementaryTransitionMotionSequence(
                            LitRiverReviewSpec,
                            LocalVisualCaptureBase,
                            TEXT("hlod_dual_layer_review"),
                            8,
                            LocalHlodDualLayerCapturePaths,
                            LocalVisualSummary,
                            true,
                            SetupLitRiverView,
                            1.0f,
                            false,
                            nullptr,
                            false,
                            true);
                    bLocalHlodDualLayerReviewCaptured =
                        bAllHlodDualLayerCapturesProduced &&
                        LocalHlodDualLayerCapturePaths.Num() == 5;
                    for (const FString& CapturePath :
                         LocalHlodDualLayerCapturePaths)
                    {
                        LocalHlodDualLayerCapturesJson += FString::Printf(
                            TEXT("%s\"%s\""),
                            LocalHlodDualLayerCapturesJson.IsEmpty()
                                ? TEXT("")
                                : TEXT(", "),
                            *EscapeRaftSimJsonString(CapturePath));
                    }
                    const bool bAllHlodTransmissionLightBracketCapturesProduced =
                        LocalMultiViewAtlas.IsSplitRelightableReady() &&
                        CaptureFutaleufuComplementaryTransitionMotionSequence(
                            LitRiverReviewSpec,
                            LocalVisualCaptureBase,
                            TEXT("hlod_transmission_light_bracket_review"),
                            8,
                            LocalHlodTransmissionLightBracketCapturePaths,
                            LocalVisualSummary,
                            true,
                            SetupLitRiverView,
                            1.0f,
                            false,
                            nullptr,
                            false,
                            false,
                            true);
                    bLocalHlodTransmissionLightBracketReviewCaptured =
                        bAllHlodTransmissionLightBracketCapturesProduced &&
                        LocalHlodTransmissionLightBracketCapturePaths.Num() == 6;
                    for (const FString& CapturePath :
                         LocalHlodTransmissionLightBracketCapturePaths)
                    {
                        LocalHlodTransmissionLightBracketCapturesJson +=
                            FString::Printf(
                                TEXT("%s\"%s\""),
                                LocalHlodTransmissionLightBracketCapturesJson.IsEmpty()
                                    ? TEXT("")
                                : TEXT(", "),
                                *EscapeRaftSimJsonString(CapturePath));
                    }
                    bSpawnMergedGeometryHlodForCurrentCapture = true;
                    const bool bAllHlodMergedGeometryShapeBracketCapturesProduced =
                        LocalMultiViewAtlas.IsSplitRelightableReady() &&
                        bLocalImpostorSourceValidated && LocalImpostorSourceMesh &&
                        CaptureFutaleufuComplementaryTransitionMotionSequence(
                            LitRiverReviewSpec,
                            LocalVisualCaptureBase,
                            TEXT("hlod_merged_geometry_shape_bracket_review"),
                            8,
                            LocalHlodMergedGeometryShapeBracketCapturePaths,
                            LocalVisualSummary,
                            true,
                            SetupLitRiverView,
                            1.0f,
                            false,
                            nullptr,
                            false,
                            false,
                            false,
                            true);
                    bSpawnMergedGeometryHlodForCurrentCapture = false;
                    bLocalHlodMergedGeometryShapeBracketReviewCaptured =
                        bAllHlodMergedGeometryShapeBracketCapturesProduced &&
                        LocalHlodMergedGeometryShapeBracketCapturePaths.Num() == 6;
                    for (const FString& CapturePath :
                         LocalHlodMergedGeometryShapeBracketCapturePaths)
                    {
                        LocalHlodMergedGeometryShapeBracketCapturesJson +=
                            FString::Printf(
                                TEXT("%s\"%s\""),
                                LocalHlodMergedGeometryShapeBracketCapturesJson.IsEmpty()
                                    ? TEXT("")
                                    : TEXT(", "),
                                *EscapeRaftSimJsonString(CapturePath));
                    }
                    bSpawnMergedGeometryHlodForCurrentCapture = true;
                    const bool bAllHlodMergedComponentParityCapturesProduced =
                        bLocalImpostorSourceValidated && LocalImpostorSourceMesh &&
                        CaptureFutaleufuComplementaryTransitionMotionSequence(
                            LitRiverReviewSpec,
                            LocalVisualCaptureBase,
                            TEXT("hlod_merged_component_parity_review"),
                            8,
                            LocalHlodMergedComponentParityCapturePaths,
                            LocalVisualSummary,
                            true,
                            SetupLitRiverView,
                            1.0f,
                            false,
                            nullptr,
                            false,
                            false,
                            false,
                            false,
                            true);
                    bSpawnMergedGeometryHlodForCurrentCapture = false;
                    bLocalHlodMergedComponentParityReviewCaptured =
                        bAllHlodMergedComponentParityCapturesProduced &&
                        LocalHlodMergedComponentParityCapturePaths.Num() == 8;
                    for (const FString& CapturePath :
                         LocalHlodMergedComponentParityCapturePaths)
                    {
                        LocalHlodMergedComponentParityCapturesJson +=
                            FString::Printf(
                                TEXT("%s\"%s\""),
                                LocalHlodMergedComponentParityCapturesJson.IsEmpty()
                                    ? TEXT("")
                                    : TEXT(", "),
                                *EscapeRaftSimJsonString(CapturePath));
                    }
                    ActiveLitRiverHlodTrunkMaterial = nullptr;
                    ActiveLitRiverHlodFoliageMaterial = nullptr;
                }
                bLocalFarProxyReviewCaptured = bCaptureFarProxy;
                bLocalNaniteWholeTreeReviewCaptured = bCaptureNaniteWholeTree;
                bLocalMultiViewAtlasReviewCaptured = bCaptureMultiViewAtlas;
                bLocalVisualReviewCaptured =
                    bCaptureA && bCaptureB && bCaptureDistance && bCaptureSpray &&
                    bCaptureFarProxy && bCaptureNaniteWholeTree &&
                    bCaptureMultiViewAtlas && bLocalHandoffReviewCaptured &&
                    bLocalComplementaryTransitionReviewCaptured &&
                    bLocalTemporalTransitionReviewCaptured &&
                    bLocalPersistentMotionTransitionReviewCaptured &&
                    bLocalFinePersistentMotionTransitionReviewCaptured &&
                    bLocalLitRiverViewMotionTransitionReviewCaptured &&
                    bLocalTemporalLitRiverViewMotionTransitionReviewCaptured &&
                    bLocalHlodFrameSearchReviewCaptured &&
                    bLocalHlodSplitShadingSearchReviewCaptured &&
                    bLocalHlodDualLayerReviewCaptured &&
                    bLocalHlodTransmissionLightBracketReviewCaptured &&
                    bLocalHlodMergedGeometryShapeBracketReviewCaptured &&
                    bLocalHlodMergedComponentParityReviewCaptured;
            }
        }
    }
    const TCHAR* UnfrozenLocalMultiViewAtlasHumanAcceptance =
        bHighDetailHlodCalibratedIrregularCrownMassCypressPalette
        ? TEXT("V26 1024-pixel-per-view mid-distance atlas completed over the V25 color gain, hard authority, and hash-retained V24 source; no-pop and runtime-cost promotion remain pending committed comparison")
        : (bHlodCalibratedIrregularCrownMassCypressPalette
        ? TEXT("V25 calibrated HLOD color gain completed over the hash-retained V24 source geometry and exact 60 m camera; photometry and 20/28/36 m authority remain pending committed comparison")
        : (bIrregularCrownMassCompoundBranchletAtlasCypressPalette
        ? TEXT("V24 irregular plant-height graft-scale mass ramp completed over the V23 asynchronous secondary-shoot and V22 de-tiered golden-angle crown under fixed attachment-count, source-cost, and camera contracts; visual promotion remains pending committed comparison")
        : (bAsyncSecondaryCompoundBranchletAtlasCypressPalette
        ? TEXT("V23 asynchronous secondary-shoot graft variants and the V22 de-tiered golden-angle main crown completed under the fixed open-grown attachment-count, source-cost, and camera contract; crown topology and visual promotion remain pending committed comparison")
        : (bDeTieredCompoundBranchletAtlasCypressPalette
        ? TEXT("V22 de-tiered golden-angle crown and V21 compound branchlet source completed under the fixed open-grown source-cost and camera contract; crown topology and visual promotion remain pending committed comparison")
        : (bCompoundBranchletAtlasCypressPalette
        ? TEXT("V21 six-spray compound branchlet atlas and reduced-card source completed under the fixed V20.2 topology and camera contract; visual and cost promotion remain pending committed exact-camera comparison")
        : (bTerminalClusterBotanicalShootCypressPalette
        ? TEXT("V20.4 low-wood terminal-cluster source and clean first-run HLOD capture completed under the fixed V20.2 parent-spray and camera contract; visual promotion remains pending committed source-art comparison before handoff, temporal, and platform review")
        : (bHierarchicalBotanicalShootClusterCypressPalette
        ? TEXT("V20.3 hierarchical flattened shoot-cluster source and clean first-run HLOD capture completed under the fixed V20.2 material and camera contract; visual promotion remains pending committed source-art comparison before handoff, temporal, and platform review")
        : (bBranchletMassBotanicalFlattenedSprayCypressHierarchyPalette
        ? TEXT("V20.2 connected branchlet-mass source and retained source-lit color-correct HLOD capture completed under the fixed V20.1 spray and camera contract; visual promotion remains pending committed source-art comparison before handoff, temporal, and platform review")
        : (bDenseBotanicalFlattenedSprayCypressHierarchyPalette
        ? TEXT("V20.1 dense measured-spray source and source-lit color-correct HLOD capture completed after rejecting the raw-albedo world-normal relighting attempt; visual promotion remains pending the committed closeup, silhouette, handoff, temporal, and platform review")
        : (bBotanicalFlattenedSprayCypressHierarchyPalette
        ? TEXT("V20 botanical flattened-spray source and HLOD capture completed under the measured dimorphic-scale contract; visual promotion remains rejected pending the committed V20 closeup, silhouette, repetition, handoff, temporal, and platform review")
        : (bAuthoredScaleLeafCypressHierarchyPalette
        ? TEXT("authored scale-leaf source and HLOD capture completed without whole-spray crop boundaries; visual promotion remains rejected pending the committed V19 review because botanical scale-leaf read, silhouette, handoff, temporal, and platform gates remain open")
        : TEXT("representation path accepted at the exact 60 m camera: upright frame selection, branch-scale detail, alpha silhouette, and color survive the bake; production visual promotion remains rejected because source whole-spray card edges transfer into the atlas and handoff, temporal, and platform gates remain open"))))))))))));
    const TCHAR* LocalMultiViewAtlasHumanAcceptance =
        bFrozenWpoHlodCalibratedIrregularCrownMassCypressPalette
        ? (bFrozenWpoAzimuthRegisteredHlodCalibratedIrregularCrownMassCypressPalette
            ? (bFrozenWpoAzimuthRegisteredPerspectiveHlodCalibratedIrregularCrownMassCypressPalette
                ? (bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette
                    ? TEXT("V32 registered perspective flat proxy completed with deterministic complementary 4x4 source/HLOD transition captures, the V33 ordered reload-path precursor, the V34 persistent same-world 4x4 diagnostic, a V35 isolated 8x8 sequence, a V36 ordered lit physical-corridor sequence, a V37 temporal-AA plus relightable-albedo/world-normal sequence, a V38 fixed-camera automatic-versus-eight-frame atlas search, a V39 exact material-identity split-shading search, a V40 disjoint DefaultLit-bark/TwoSidedFoliage dual-layer review, a V41 fixed frontlit/backlit transmission bracket, a V42 merged-source-geometry fidelity upper bound, and a V43 exact merged-component material/shadow parity bracket; V33-V43 preserve woody geometry but use traditional raster for the dynamically masked source trunk after the Nanite path leaked wood into HLOD-owned pixels; V43 validates material-ID component partitioning but rejects material ID as source shadow provenance, so source-provenance splitting, reduced geometry, temporal handoff, source-card cleanup, named-hazard framing, and wall-clock performance remain pending")
                    : (bFrozenWpoAzimuthRegisteredPerspectiveDepthHlodCalibratedIrregularCrownMassCypressPalette
                        ? TEXT("V31 registered perspective 512-pixel atlas completed with a 32x32 depth-displaced proxy at the authored 28 m handoff radius; matched representation-shape comparison and any art decision remain pending")
                        : TEXT("V30 registered frozen-WPO 512-pixel atlas completed with perspective capture at the authored 28 m handoff radius; matched projection comparison and any art decision remain pending")))
                : TEXT("V29 frozen-WPO 512-pixel atlas completed with a 16-degree frame phase aligned to the authored handoff approach; matched angular-registration comparison and any art decision remain pending"))
            : (bFrozenWpoHighDetailHlodCalibratedIrregularCrownMassCypressPalette
            ? TEXT("V28 frozen-WPO 1024-pixel-per-view deterministic atlas completed under the V27 validation contract; matched resolution comparison and any art decision remain pending")
            : TEXT("V27 frozen-WPO 512-pixel-per-view deterministic atlas baseline completed over V24 source geometry and V25 photometry/authority; repeatability and no-pop promotion remain pending committed comparison")))
        : UnfrozenLocalMultiViewAtlasHumanAcceptance;
    const FString LocalMultiViewAtlasJson = FString::Printf(
        TEXT("{\n")
        TEXT("    \"status\": \"%s\",\n")
        TEXT("    \"manifest\": \"%s\",\n")
        TEXT("    \"view_contract\": {\"azimuth_count\": 8, \"elevation_count\": 2, \"view_count\": %d, \"azimuth_offset_degrees\": %.6f, \"tile_resolution\": %d, \"atlas_resolution\": %d},\n")
        TEXT("    \"orthographic_width_cm\": %.6f,\n")
        TEXT("    \"projection_contract\": {\"type\": \"%s\", \"capture_radius_cm\": %.6f, \"perspective_horizontal_fov_degrees\": %.6f, \"proxy_plane_width_cm\": %.6f},\n")
        TEXT("    \"representation_shape_contract\": {\"type\": \"%s\", \"depth_parallax_enabled\": %s, \"depth_parallax_scale_cm\": %.6f, \"proxy_vertex_count\": %d, \"proxy_triangle_count\": %d},\n")
        TEXT("    \"coverage_fraction_range\": [%.9f, %.9f],\n")
        TEXT("    \"opacity_source\": \"%s\",\n")
        TEXT("    \"outputs\": [\"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\"],\n")
        TEXT("    \"material_identity_contract\": {\"source\": \"frontmost owner from separate trunk and foliage opacity plus scene-depth passes\", \"encoding\": \"black_trunk_white_foliage\", \"fallback_pixels\": %lld},\n")
        TEXT("    \"material_asset\": \"%s\",\n")
        TEXT("    \"relightable_representation_contract\": {\"ready\": %s, \"split_layer_ready\": %s, \"albedo_source\": \"SCS_BaseColor linear converted to sRGB atlas texels\", \"albedo_output\": \"%s\", \"albedo_md5\": \"%s\", \"material_identity_output\": \"%s\", \"material_identity_md5\": \"%s\", \"material_asset\": \"%s\", \"trunk_material_asset\": \"%s\", \"foliage_material_asset\": \"%s\", \"shading_model\": \"DefaultLit\", \"split_shading_models\": {\"trunk\": \"DefaultLit\", \"foliage\": \"TwoSidedFoliage\"}, \"split_layer_opacity\": {\"trunk\": \"opacity_times_one_minus_material_identity\", \"foliage\": \"opacity_times_material_identity\"}, \"layer_transition_order\": \"material_identity_layer_opacity_then_complementary_temporal_mask\", \"foliage_transmission_parameter\": \"AtlasFoliageTransmissionTint\", \"foliage_transmission_default\": [0.78, 1.0, 0.58], \"base_color_gain\": [1.55, 1.55, 1.55], \"tangent_space_normal\": false, \"world_normal_sampled\": true, \"material_identity_sampled\": true, \"emissive_connected\": false, \"trunk_parameters\": [\"AtlasTrunkGainMultiplier\", \"AtlasTrunkRoughness\", \"AtlasTrunkSpecular\"], \"foliage_parameters\": [\"AtlasFoliageGainMultiplier\", \"AtlasFoliageRoughness\", \"AtlasFoliageSpecular\"], \"default_gain_multipliers\": [1.0, 1.0], \"default_roughness\": [0.68, 0.68], \"default_specular\": [0.18, 0.18], \"split_default_roughness\": [0.62, 0.72], \"split_default_specular\": [0.12, 0.18], \"transition_modes\": [\"legacy_ordered_control\", \"engine_temporal_aa_complementary\"], \"atlas_frame_override_parameter\": \"AtlasFrameOverride\", \"automatic_frame_override_value\": -1.0},\n")
        TEXT("    \"runtime_representation\": \"%s\",\n")
        TEXT("    \"atlas_color_gain\": [%.6f, %.6f, %.6f],\n")
        TEXT("    \"exact_source_camera_60m_capture\": \"%s\",\n")
        TEXT("    \"exact_source_camera_60m_capture_produced\": %s,\n")
        TEXT("    \"source_wpo_contract\": {\"frozen_for_deterministic_review\": %s, \"WindIntensity\": %.2f, \"WindWeight\": %.2f, \"WindSpeed\": %.2f},\n")
        TEXT("    \"deterministic_capture_contract\": {\"enabled\": %s, \"validation_only_not_art_review\": true, \"lighting\": false, \"post_processing\": false, \"atmosphere\": false, \"fog\": false, \"anti_aliasing\": false, \"temporal_aa\": false, \"motion_blur\": false, \"eye_adaptation\": false, \"ambient_occlusion\": false, \"global_illumination\": false, \"lumen_gi\": false, \"lumen_reflections\": false, \"screen_space_reflections\": false, \"reflection_environment\": false},\n")
        TEXT("    \"handoff_contract\": {\"enabled\": %s, \"distance_metric\": \"camera_to_hlod_actor_horizontal_distance\", \"source_selection_distance_cm\": 2500.0, \"source_authority_below_threshold\": true, \"single_representation_by_actor_visibility\": true, \"capture_count\": %d, \"captures\": [%s]},\n")
        TEXT("    \"complementary_transition_contract\": {\"enabled\": %s, \"pattern\": \"deterministic_4x4_screen_bayer\", \"parameter\": \"ComplementarySourceCoverage\", \"radial_band_cm\": [2300.0, 2700.0], \"sample_radii_cm\": [2400.0, 2500.0, 2600.0], \"source_coverage\": [0.75, 0.50, 0.25], \"source_and_hlod_visibility_overlap_inside_band\": true, \"pixel_ownership_complementary\": true, \"capture_count\": %d, \"captures\": [%s]},\n")
        TEXT("    \"temporal_transition_path_contract\": {\"enabled\": %s, \"sampling\": \"ordered_camera_path_precursor_without_same-world_temporal_history\", \"radial_band_cm\": [2300.0, 2700.0], \"radial_step_cm\": 25.0, \"sample_count\": 17, \"source_coverage_start\": 1.0, \"source_coverage_end\": 0.0, \"source_coverage_step\": -0.0625, \"authority_modes_per_sample\": [\"source_only\", \"hlod_only\", \"combined\"], \"source_woody_geometry\": \"unchanged_v24_v30_geometry\", \"source_woody_renderer\": \"traditional_raster_for_dynamic_screen_mask_compatibility\", \"nanite_source_woody_diagnostic\": \"rejected_wood_leaked_into_hlod_owned_pixels\", \"capture_count\": %d, \"captures\": [%s]},\n")
        TEXT("    \"persistent_motion_sequence_contract\": {\"enabled\": %s, \"sampling\": \"one_loaded_world_and_one_persistent_scene_capture_per_authority_mode\", \"pattern\": \"deterministic_4x4_screen_bayer\", \"pattern_rank_count\": 16, \"authority_modes\": [\"source_only\", \"hlod_only\", \"combined\"], \"radial_band_cm\": [2300.0, 2700.0], \"camera_step_cm\": 10.0, \"fixed_delta_seconds\": 0.016666667, \"target_simulation_fps\": 60.0, \"nominal_camera_speed_cm_per_second\": 600.0, \"warmup_frame_count\": 8, \"transition_frame_count\": 41, \"source_coverage_transition_frame_count\": 31, \"source_coverage_transition_end_radius_cm\": 2600.0, \"moving_hlod_only_tail_frame_count\": 10, \"endpoint_settle_frame_count\": 8, \"saved_frame_count_per_mode\": 49, \"source_coverage_start\": 1.0, \"source_coverage_end\": 0.0, \"source_coverage_step\": -0.033333333, \"persistent_view_state\": true, \"temporal_history\": true, \"anti_aliasing_method\": \"temporal_aa\", \"camera_motion_vectors\": \"camera_transform_advanced_before_each_capture_with_persistent_view_state\", \"target_pacing_scope\": \"fixed_simulation_delta_not_wall_clock_performance_measurement\", \"lighting\": false, \"motion_blur\": false, \"capture_count\": %d, \"captures\": [%s]},\n")
        TEXT("    \"fine_persistent_motion_sequence_contract\": {\"enabled\": %s, \"sampling\": \"one_loaded_world_and_one_persistent_scene_capture_per_authority_mode\", \"pattern\": \"deterministic_8x8_screen_bayer\", \"pattern_rank_count\": 64, \"base_pattern_retained_for_control\": \"deterministic_4x4_screen_bayer\", \"authority_modes\": [\"source_only\", \"hlod_only\", \"combined\"], \"radial_band_cm\": [2300.0, 2700.0], \"camera_step_cm\": 10.0, \"fixed_delta_seconds\": 0.016666667, \"target_simulation_fps\": 60.0, \"nominal_camera_speed_cm_per_second\": 600.0, \"warmup_frame_count\": 8, \"transition_frame_count\": 41, \"source_coverage_transition_frame_count\": 31, \"source_coverage_transition_end_radius_cm\": 2600.0, \"moving_hlod_only_tail_frame_count\": 10, \"endpoint_settle_frame_count\": 8, \"saved_frame_count_per_mode\": 49, \"source_coverage_start\": 1.0, \"source_coverage_end\": 0.0, \"source_coverage_step\": -0.033333333, \"persistent_view_state\": true, \"temporal_history\": true, \"anti_aliasing_method\": \"temporal_aa\", \"camera_motion_vectors\": \"camera_transform_advanced_before_each_capture_with_persistent_view_state\", \"target_pacing_scope\": \"fixed_simulation_delta_not_wall_clock_performance_measurement\", \"lighting\": false, \"motion_blur\": false, \"capture_count\": %d, \"captures\": [%s]},\n")
        TEXT("    \"lit_river_view_motion_sequence_contract\": {\"enabled\": %s, \"source_map\": \"/Game/RaftSim/Maps/EnvironmentPreviews/LandscapeCandidates/L_FutaleufuTerminator_PhysicalCorridorCandidate\", \"scene_setup\": \"one transient non-colliding source/HLOD pair placed on the finite lower-slope near bank from the existing river-eye basis\", \"saved_map_modified\": false, \"landscape_water_collision_solver_or_gameplay_authority_modified\": false, \"sampling\": \"one_loaded_physical_corridor_world_and_one_persistent_scene_capture_per_authority_mode\", \"pattern\": \"deterministic_8x8_screen_bayer\", \"pattern_rank_count\": 64, \"authority_modes\": [\"source_only\", \"hlod_only\", \"combined\"], \"radial_band_cm\": [2300.0, 2700.0], \"camera_step_cm\": 10.0, \"fixed_delta_seconds\": 0.016666667, \"target_simulation_fps\": 60.0, \"nominal_camera_speed_cm_per_second\": 600.0, \"warmup_frame_count\": 8, \"transition_frame_count\": 41, \"source_coverage_transition_frame_count\": 31, \"source_coverage_transition_end_radius_cm\": 2600.0, \"moving_hlod_only_tail_frame_count\": 10, \"endpoint_settle_frame_count\": 8, \"saved_frame_count_per_mode\": 49, \"persistent_view_state\": true, \"temporal_history\": true, \"anti_aliasing_method\": \"temporal_aa\", \"lighting\": true, \"atmosphere\": true, \"fog\": true, \"ambient_occlusion\": true, \"global_illumination\": true, \"lumen_gi\": true, \"lumen_reflections\": true, \"screen_space_reflections\": true, \"reflection_environment\": true, \"motion_blur\": false, \"target_pacing_scope\": \"fixed_simulation_delta_not_wall_clock_performance_measurement\", \"capture_count\": %d, \"captures\": [%s]},\n")
        TEXT("    \"temporal_lit_river_view_motion_sequence_contract\": {\"enabled\": %s, \"source_map\": \"/Game/RaftSim/Maps/EnvironmentPreviews/LandscapeCandidates/L_FutaleufuTerminator_PhysicalCorridorCandidate\", \"scene_setup\": \"same transient non-colliding river-edge placement as V36 with a separate relightable HLOD material\", \"saved_map_modified\": false, \"landscape_water_collision_solver_or_gameplay_authority_modified\": false, \"sampling\": \"one_loaded_physical_corridor_world_and_one_persistent_scene_capture_per_authority_mode\", \"transition\": \"engine_DitherTemporalAA_with_exact_inverse_hlod_ownership\", \"legacy_ordered_modes_retained\": true, \"source_material\": \"masked source bark and foliage with ComplementaryTransitionMode=1\", \"hlod_shading\": \"DefaultLit albedo plus captured world normal, no emissive connection\", \"authority_modes\": [\"source_only\", \"hlod_only\", \"combined\"], \"radial_band_cm\": [2300.0, 2700.0], \"camera_step_cm\": 10.0, \"fixed_delta_seconds\": 0.016666667, \"target_simulation_fps\": 60.0, \"warmup_frame_count\": 8, \"transition_frame_count\": 41, \"source_coverage_transition_frame_count\": 31, \"moving_hlod_only_tail_frame_count\": 10, \"endpoint_settle_frame_count\": 8, \"saved_frame_count_per_mode\": 49, \"persistent_view_state\": true, \"temporal_history\": true, \"anti_aliasing_method\": \"temporal_aa\", \"lighting\": true, \"atmosphere\": true, \"fog\": true, \"ambient_occlusion\": true, \"global_illumination\": true, \"lumen_gi\": true, \"lumen_reflections\": true, \"screen_space_reflections\": true, \"reflection_environment\": true, \"motion_blur\": false, \"target_pacing_scope\": \"fixed_simulation_delta_not_wall_clock_performance_measurement\", \"capture_count\": %d, \"captures\": [%s]},\n")
        TEXT("    \"hlod_frame_search_contract\": {\"enabled\": %s, \"source_map\": \"/Game/RaftSim/Maps/EnvironmentPreviews/LandscapeCandidates/L_FutaleufuTerminator_PhysicalCorridorCandidate\", \"scene_setup\": \"same transient non-colliding river-edge placement and relightable HLOD as V37\", \"saved_map_modified\": false, \"landscape_water_collision_solver_or_gameplay_authority_modified\": false, \"sampling\": \"one_loaded_physical_corridor_world_one_fixed_24_5m_camera_and_one_persistent_scene_capture\", \"camera_radius_cm\": 2450.0, \"warmup_frames_per_representation\": 8, \"lighting\": true, \"temporal_aa\": true, \"atlas_frame_override_parameter\": \"AtlasFrameOverride\", \"automatic_override_value\": -1.0, \"calculated_automatic_row_zero_frame\": %d, \"tested_row_zero_frames\": [0, 1, 2, 3, 4, 5, 6, 7], \"source_reference_count\": 1, \"automatic_selection_count\": 1, \"override_capture_count\": 8, \"capture_count\": %d, \"captures\": [%s]},\n")
        TEXT("    \"hlod_split_shading_search_contract\": {\"enabled\": %s, \"source_map\": \"/Game/RaftSim/Maps/EnvironmentPreviews/LandscapeCandidates/L_FutaleufuTerminator_PhysicalCorridorCandidate\", \"scene_setup\": \"same transient non-colliding river-edge placement, automatic frame, and relightable HLOD as V38\", \"saved_map_modified\": false, \"landscape_water_collision_solver_or_gameplay_authority_modified\": false, \"sampling\": \"one_loaded_physical_corridor_world_one_fixed_24_5m_camera_and_one_persistent_scene_capture\", \"camera_radius_cm\": 2450.0, \"warmup_frames_per_preset\": 8, \"temporal_history_reset_per_preset\": \"scene_capture_camera_cut_before_warmup\", \"lighting\": true, \"temporal_aa\": true, \"material_identity_parameter\": \"AtlasMaterialIdentity\", \"fixed_roughness\": [0.68, 0.68], \"fixed_specular\": [0.18, 0.18], \"gain_presets\": [{\"id\": \"baseline\", \"trunk\": 1.0, \"foliage\": 1.0}, {\"id\": \"foliage_gain_150\", \"trunk\": 1.0, \"foliage\": 1.5}, {\"id\": \"foliage_gain_200\", \"trunk\": 1.0, \"foliage\": 2.0}, {\"id\": \"foliage_gain_250\", \"trunk\": 1.0, \"foliage\": 2.5}, {\"id\": \"trunk_gain_150\", \"trunk\": 1.5, \"foliage\": 1.0}, {\"id\": \"trunk_gain_200\", \"trunk\": 2.0, \"foliage\": 1.0}, {\"id\": \"trunk_gain_250\", \"trunk\": 2.5, \"foliage\": 1.0}, {\"id\": \"balanced_gain_175\", \"trunk\": 1.75, \"foliage\": 1.75}, {\"id\": \"balanced_gain_200\", \"trunk\": 2.0, \"foliage\": 2.0}], \"source_reference_count\": 1, \"preset_capture_count\": 9, \"capture_count\": %d, \"captures\": [%s]},\n")
        TEXT("    \"hlod_dual_layer_review_contract\": {\"enabled\": %s, \"source_map\": \"/Game/RaftSim/Maps/EnvironmentPreviews/LandscapeCandidates/L_FutaleufuTerminator_PhysicalCorridorCandidate\", \"scene_setup\": \"same transient non-colliding river-edge placement with one combined control component plus disjoint trunk and foliage components sharing one proxy mesh\", \"saved_map_modified\": false, \"landscape_water_collision_solver_or_gameplay_authority_modified\": false, \"sampling\": \"one_loaded_physical_corridor_world_one_fixed_24_5m_camera_and_one_persistent_scene_capture\", \"camera_radius_cm\": 2450.0, \"warmup_frames_per_representation\": 8, \"temporal_history_reset_per_representation\": \"scene_capture_camera_cut_before_warmup\", \"lighting\": true, \"temporal_aa\": true, \"automatic_atlas_frame\": true, \"component_layers\": [\"combined_control\", \"trunk\", \"foliage\"], \"combined_control_shading_model\": \"DefaultLit\", \"trunk_shading_model\": \"DefaultLit\", \"foliage_shading_model\": \"TwoSidedFoliage\", \"layer_opacity\": {\"trunk\": \"opacity_times_one_minus_material_identity\", \"foliage\": \"opacity_times_material_identity\"}, \"source_transmission_tint\": [0.78, 1.0, 0.58], \"split_roughness\": [0.62, 0.72], \"split_specular\": [0.12, 0.18], \"variants\": [\"source_reference\", \"combined_default_lit_control\", \"two_sided_no_transmission\", \"two_sided_source_transmission\", \"two_sided_source_transmission_foliage_gain_150\"], \"capture_count\": %d, \"captures\": [%s]},\n")
        TEXT("    \"hlod_transmission_light_bracket_contract\": {\"enabled\": %s, \"source_map\": \"/Game/RaftSim/Maps/EnvironmentPreviews/LandscapeCandidates/L_FutaleufuTerminator_PhysicalCorridorCandidate\", \"scene_setup\": \"same transient non-colliding river-edge placement and dual-layer proxy as V40 with only the saved labeled sun rotated transiently\", \"saved_map_modified\": false, \"landscape_water_collision_solver_or_gameplay_authority_modified\": false, \"sampling\": \"one_loaded_physical_corridor_world_one_fixed_24_5m_camera_and_one_persistent_scene_capture\", \"camera_radius_cm\": 2450.0, \"warmup_frames_per_representation\": 8, \"temporal_history_reset_per_representation\": \"scene_capture_camera_cut_before_warmup\", \"lighting\": true, \"temporal_aa\": true, \"automatic_atlas_frame\": true, \"sun_actor_label\": \"RaftSim_Sun_LumenPreview\", \"sun_original_transform_restored\": true, \"light_direction_contract\": {\"frontlit_horizontal_travel\": \"camera_to_tree\", \"backlit_horizontal_travel\": \"tree_to_camera\", \"pre_normalized_downward_z\": -0.65}, \"light_modes\": [\"frontlit\", \"backlit\"], \"representations_per_light\": [\"source_reference\", \"two_sided_no_transmission\", \"two_sided_source_transmission\"], \"source_transmission_tint\": [0.78, 1.0, 0.58], \"split_roughness\": [0.62, 0.72], \"split_specular\": [0.12, 0.18], \"capture_count\": %d, \"captures\": [%s]},\n")
        TEXT("    \"hlod_merged_geometry_shape_bracket_contract\": {\"enabled\": %s, \"source_map\": \"/Game/RaftSim/Maps/EnvironmentPreviews/LandscapeCandidates/L_FutaleufuTerminator_PhysicalCorridorCandidate\", \"scene_setup\": \"same transient non-colliding river-edge placement as V41 with source, flat dual-layer atlas control, and merged source geometry compared in one loaded corridor world\", \"saved_map_modified\": false, \"landscape_water_collision_solver_or_gameplay_authority_modified\": false, \"sampling\": \"one_loaded_physical_corridor_world_one_fixed_24_5m_camera_and_one_persistent_scene_capture\", \"camera_radius_cm\": 2450.0, \"warmup_frames_per_representation\": 8, \"temporal_history_reset_per_representation\": \"scene_capture_camera_cut_before_warmup\", \"lighting\": true, \"temporal_aa\": true, \"sun_actor_label\": \"RaftSim_Sun_LumenPreview\", \"sun_original_transform_restored\": true, \"light_modes\": [\"frontlit\", \"backlit\"], \"representations_per_light\": [\"source_reference\", \"flat_hlod_control\", \"merged_geometry_hlod\"], \"flat_control\": \"V41 dual-layer atlas with source transmission tint\", \"merged_geometry_asset\": \"%s\", \"merged_geometry_vertex_count\": %d, \"merged_geometry_triangle_count\": %d, \"merged_geometry_material_slot_count\": %d, \"geometry_materials\": \"preserved_source_bark_and_foliage\", \"geometry_shadow_policy\": \"no_cast_shadow_for_bounded_shape_and_direct-light_upper-bound\", \"collision_and_overlap\": false, \"temporal_handoff_evaluated\": false, \"wall_clock_performance_evaluated\": false, \"capture_count\": %d, \"captures\": [%s]},\n")
        TEXT("    \"hlod_merged_component_parity_contract\": {\"enabled\": %s, \"source_map\": \"/Game/RaftSim/Maps/EnvironmentPreviews/LandscapeCandidates/L_FutaleufuTerminator_PhysicalCorridorCandidate\", \"scene_setup\": \"same transient source and exact merged geometry as V42, with a single-component control plus material-ID-split bark and foliage components\", \"saved_map_modified\": false, \"landscape_water_collision_solver_or_gameplay_authority_modified\": false, \"sampling\": \"one_loaded_physical_corridor_world_one_fixed_24_5m_camera_and_one_persistent_scene_capture\", \"camera_radius_cm\": 2450.0, \"warmup_frames_per_representation\": 8, \"temporal_history_reset_per_representation\": \"scene_capture_camera_cut_before_warmup\", \"lighting\": true, \"temporal_aa\": true, \"sun_actor_label\": \"RaftSim_Sun_LumenPreview\", \"sun_original_transform_restored\": true, \"light_modes\": [\"frontlit\", \"backlit\"], \"representations_per_light\": [\"source_reference\", \"merged_single_no_shadow\", \"merged_split_no_shadow\", \"merged_split_source_shadow\"], \"merged_geometry_asset\": \"%s\", \"merged_geometry_vertex_count\": %d, \"merged_geometry_triangle_count\": %d, \"merged_geometry_material_slot_count\": %d, \"merged_geometry_section_count\": %d, \"bark_material_slot_count\": %d, \"foliage_material_slot_count\": %d, \"component_partition\": \"exact static mesh copied twice and non-owner triangles deleted by source material ID\", \"material_identity\": \"source parent materials preserved\", \"material_state\": \"identical source-coverage temporal parameters on single and split controls\", \"shadow_partition_basis\": \"material ID\", \"source_component_shadow_provenance_preserved\": false, \"single_component_shadow_policy\": \"bark_and_foliage_no_cast_shadow\", \"split_no_shadow_policy\": \"bark_and_foliage_no_cast_shadow\", \"split_source_shadow_policy\": \"bark_casts_static_and_dynamic_shadow_foliage_casts_none\", \"collision_and_overlap\": false, \"temporal_handoff_evaluated\": false, \"wall_clock_performance_evaluated\": false, \"capture_count\": %d, \"captures\": [%s]},\n")
        TEXT("    \"human_visual_acceptance\": \"%s\",\n")
        TEXT("    \"depth_usage\": \"%s\",\n")
        TEXT("    \"git_policy\": \"generated atlases, assets, manifest, and comparison capture are local and ignored\"\n")
        TEXT("  }"),
        LocalMultiViewAtlas.IsReady() && bLocalMultiViewAtlasReviewCaptured
            ? TEXT("generated_and_exact_camera_representation_accepted_visual_promotion_rejected")
            : TEXT("generation_validation_or_exact_camera_capture_failed"),

        *EscapeRaftSimJsonString(LocalMultiViewAtlas.ManifestRelativePath),
        LocalMultiViewAtlas.ViewCount,
        LocalMultiViewAtlas.AzimuthOffsetDegrees,
        LocalMultiViewAtlas.TileResolution,
        LocalMultiViewAtlas.AtlasResolution,
        LocalMultiViewAtlas.OrthoWidthCm,
        LocalMultiViewAtlas.bPerspectiveCapture ? TEXT("perspective") : TEXT("orthographic"),
        LocalMultiViewAtlas.CaptureRadiusCm,
        LocalMultiViewAtlas.PerspectiveHorizontalFovDegrees,
        LocalMultiViewAtlas.OrthoWidthCm,
        LocalMultiViewAtlas.bDepthParallaxEnabled
            ? TEXT("32x32_tessellated_depth_displaced_billboard")
            : TEXT("flat_billboard"),
        LocalMultiViewAtlas.bDepthParallaxEnabled ? TEXT("true") : TEXT("false"),
        LocalMultiViewAtlas.DepthParallaxScaleCm,
        LocalMultiViewAtlas.ProxyVertexCount,
        LocalMultiViewAtlas.ProxyTriangleCount,
        LocalMultiViewAtlas.MinimumCoverage,
        LocalMultiViewAtlas.MaximumCoverage,
        *EscapeRaftSimJsonString(LocalMultiViewAtlas.OpacitySource),
        *EscapeRaftSimJsonString(LocalMultiViewAtlas.BaseColorRelativePath),
        *EscapeRaftSimJsonString(LocalMultiViewAtlas.AlbedoRelativePath),
        *EscapeRaftSimJsonString(LocalMultiViewAtlas.NormalRelativePath),
        *EscapeRaftSimJsonString(LocalMultiViewAtlas.OpacityRelativePath),
        *EscapeRaftSimJsonString(LocalMultiViewAtlas.DepthRelativePath),
        *EscapeRaftSimJsonString(LocalMultiViewAtlas.MaterialIdentityRelativePath),
        static_cast<long long>(LocalMultiViewAtlas.MaterialIdentityFallbackPixelCount),
        *EscapeRaftSimJsonString(LocalMultiViewAtlas.MaterialAssetPath),
        LocalMultiViewAtlas.IsRelightableReady() ? TEXT("true") : TEXT("false"),
        LocalMultiViewAtlas.IsSplitRelightableReady() ? TEXT("true") : TEXT("false"),
        *EscapeRaftSimJsonString(LocalMultiViewAtlas.AlbedoRelativePath),
        *LocalMultiViewAtlas.AlbedoDigest,
        *EscapeRaftSimJsonString(LocalMultiViewAtlas.MaterialIdentityRelativePath),
        *LocalMultiViewAtlas.MaterialIdentityDigest,
        *EscapeRaftSimJsonString(LocalMultiViewAtlas.RelightableMaterialAssetPath),
        *EscapeRaftSimJsonString(
            LocalMultiViewAtlas.RelightableTrunkMaterialAssetPath),
        *EscapeRaftSimJsonString(
            LocalMultiViewAtlas.RelightableFoliageMaterialAssetPath),
        LocalMultiViewAtlas.bDepthParallaxEnabled
            ? TEXT("camera-facing 32x32 tessellated grid with nearest-frame selection, inverse-opacity silhouette, bounded source-lit color gain, and depth-atlas vertex displacement; world normal retained but not sampled")
            : LocalMultiViewAtlas.bComplementaryTransitionEnabled
            ? TEXT("camera-facing flat registered-perspective proxy with nearest-frame selection, inverse-opacity silhouette, bounded source-lit color gain, and deterministic complementary 4x4 source/HLOD transition masking; world normal and depth retained but not sampled")
            : bDenseBotanicalFlattenedSprayCypressHierarchyPalette
            ? TEXT("camera-facing plane with nearest-frame selection, inverse-opacity silhouette, and bounded source-lit color gain; world normal and depth retained but not sampled")
            : TEXT("camera-facing plane with material-selected nearest azimuth/elevation frame and masked unlit baked color; world normal/depth retained for later relight/parallax work"),
        LocalMultiViewAtlas.ColorGain.R,
        LocalMultiViewAtlas.ColorGain.G,
        LocalMultiViewAtlas.ColorGain.B,
        *EscapeRaftSimJsonString(LocalMultiViewAtlasCapturePath),
        bLocalMultiViewAtlasReviewCaptured ? TEXT("true") : TEXT("false"),
        bFrozenWpoHlodCalibratedIrregularCrownMassCypressPalette
            ? TEXT("true")
            : TEXT("false"),
        bFrozenWpoHlodCalibratedIrregularCrownMassCypressPalette ? 0.0 : 0.16,
        bFrozenWpoHlodCalibratedIrregularCrownMassCypressPalette ? 0.0 : 0.28,
        bFrozenWpoHlodCalibratedIrregularCrownMassCypressPalette ? 0.0 : 0.42,
        bFrozenWpoHlodCalibratedIrregularCrownMassCypressPalette
            ? TEXT("true")
            : TEXT("false"),
        bHlodCalibratedIrregularCrownMassCypressPalette ? TEXT("true") : TEXT("false"),
        LocalHandoffCapturePaths.Num(),
        *LocalHandoffCapturesJson,
        LocalMultiViewAtlas.bComplementaryTransitionEnabled ? TEXT("true") : TEXT("false"),
        LocalComplementaryTransitionCapturePaths.Num(),
        *LocalComplementaryTransitionCapturesJson,
        LocalMultiViewAtlas.bComplementaryTransitionEnabled ? TEXT("true") : TEXT("false"),
        LocalTemporalTransitionCapturePaths.Num(),
        *LocalTemporalTransitionCapturesJson,
        LocalMultiViewAtlas.bComplementaryTransitionEnabled ? TEXT("true") : TEXT("false"),
        LocalPersistentMotionTransitionCapturePaths.Num(),
        *LocalPersistentMotionTransitionCapturesJson,
        LocalMultiViewAtlas.bComplementaryTransitionEnabled ? TEXT("true") : TEXT("false"),
        LocalFinePersistentMotionTransitionCapturePaths.Num(),
        *LocalFinePersistentMotionTransitionCapturesJson,
        LocalMultiViewAtlas.bComplementaryTransitionEnabled ? TEXT("true") : TEXT("false"),
        LocalLitRiverViewMotionTransitionCapturePaths.Num(),
        *LocalLitRiverViewMotionTransitionCapturesJson,
        LocalMultiViewAtlas.IsRelightableReady() ? TEXT("true") : TEXT("false"),
        LocalTemporalLitRiverViewMotionTransitionCapturePaths.Num(),
        *LocalTemporalLitRiverViewMotionTransitionCapturesJson,
        LocalMultiViewAtlas.IsRelightableReady() ? TEXT("true") : TEXT("false"),
        LocalHlodFrameSearchAutomaticFrame,
        LocalHlodFrameSearchCapturePaths.Num(),
        *LocalHlodFrameSearchCapturesJson,
        LocalMultiViewAtlas.IsRelightableReady() ? TEXT("true") : TEXT("false"),
        LocalHlodSplitShadingSearchCapturePaths.Num(),
        *LocalHlodSplitShadingSearchCapturesJson,
        LocalMultiViewAtlas.IsSplitRelightableReady() ? TEXT("true") : TEXT("false"),
        LocalHlodDualLayerCapturePaths.Num(),
        *LocalHlodDualLayerCapturesJson,
        LocalMultiViewAtlas.IsSplitRelightableReady() ? TEXT("true") : TEXT("false"),
        LocalHlodTransmissionLightBracketCapturePaths.Num(),
        *LocalHlodTransmissionLightBracketCapturesJson,
        bLocalHlodMergedGeometryShapeBracketReviewCaptured
            ? TEXT("true")
            : TEXT("false"),
        *EscapeRaftSimJsonString(LocalImpostorSourceAssetPath),
        LocalImpostorSourceVertexCount,
        LocalImpostorSourceTriangleCount,
        LocalImpostorSourceMaterialSlotCount,
        LocalHlodMergedGeometryShapeBracketCapturePaths.Num(),
        *LocalHlodMergedGeometryShapeBracketCapturesJson,
        bLocalHlodMergedComponentParityReviewCaptured
            ? TEXT("true")
            : TEXT("false"),
        *EscapeRaftSimJsonString(LocalImpostorSourceAssetPath),
        LocalImpostorSourceVertexCount,
        LocalImpostorSourceTriangleCount,
        LocalImpostorSourceMaterialSlotCount,
        LocalImpostorSourceSectionCount,
        LocalImpostorSourceBarkMaterialSlotCount,
        LocalImpostorSourceFoliageMaterialSlotCount,
        LocalHlodMergedComponentParityCapturePaths.Num(),
        *LocalHlodMergedComponentParityCapturesJson,
        LocalMultiViewAtlasHumanAcceptance,
        LocalMultiViewAtlas.bDepthParallaxEnabled
            ? TEXT("sampled at proxy vertices to displace the registered perspective billboard through the measured horizontal source depth")
            : TEXT("captured and reserved for later parallax/depth refinement; not sampled by this HLOD material"));
    const FString LocalVisualReviewJson = FString::Printf(
        TEXT("{\n")
        TEXT("    \"status\": \"%s\",\n")
        TEXT("    \"git_policy\": \"generated_map_and_captures_are_local_and_ignored\",\n")
        TEXT("    \"map_asset\": \"%s\",\n")
        TEXT("    \"foliage_mesh_count\": %d,\n")
        TEXT("    \"foliage_instance_count\": %d,\n")
        TEXT("    \"captures\": [\"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\"],\n")
        TEXT("    \"handoff_capture_count\": %d,\n")
        TEXT("    \"handoff_captures\": [%s],\n")
        TEXT("    \"complementary_transition_capture_count\": %d,\n")
        TEXT("    \"complementary_transition_captures\": [%s],\n")
        TEXT("    \"temporal_transition_capture_count\": %d,\n")
        TEXT("    \"temporal_transition_captures\": [%s],\n")
        TEXT("    \"persistent_motion_transition_capture_count\": %d,\n")
        TEXT("    \"persistent_motion_transition_captures\": [%s],\n")
        TEXT("    \"fine_persistent_motion_transition_capture_count\": %d,\n")
        TEXT("    \"fine_persistent_motion_transition_captures\": [%s],\n")
        TEXT("    \"lit_river_view_motion_transition_capture_count\": %d,\n")
        TEXT("    \"lit_river_view_motion_transition_captures\": [%s],\n")
        TEXT("    \"temporal_lit_river_view_motion_transition_capture_count\": %d,\n")
        TEXT("    \"temporal_lit_river_view_motion_transition_captures\": [%s],\n")
        TEXT("    \"hlod_frame_search_capture_count\": %d,\n")
        TEXT("    \"hlod_frame_search_captures\": [%s],\n")
        TEXT("    \"hlod_split_shading_search_capture_count\": %d,\n")
        TEXT("    \"hlod_split_shading_search_captures\": [%s],\n")
        TEXT("    \"hlod_dual_layer_capture_count\": %d,\n")
        TEXT("    \"hlod_dual_layer_captures\": [%s],\n")
        TEXT("    \"hlod_transmission_light_bracket_capture_count\": %d,\n")
        TEXT("    \"hlod_transmission_light_bracket_captures\": [%s],\n")
        TEXT("    \"hlod_merged_geometry_shape_bracket_capture_count\": %d,\n")
        TEXT("    \"hlod_merged_geometry_shape_bracket_captures\": [%s],\n")
        TEXT("    \"hlod_merged_component_parity_capture_count\": %d,\n")
        TEXT("    \"hlod_merged_component_parity_captures\": [%s],\n")
        TEXT("    \"multi_view_atlas_manifest\": \"%s\"\n")
        TEXT("  }"),
        bLocalVisualReviewCaptured
            ? (bTraditionalRasterCypressFoliagePalette
                ? TEXT("isolated_source_views_plus_exact_camera_far_proxy_merged_raster_and_multi_view_atlas_comparisons_ready_for_human_review")
                : TEXT("isolated_source_views_plus_exact_camera_far_proxy_nanite_and_multi_view_atlas_comparisons_ready_for_human_review"))
            : TEXT("isolated_visual_capture_failed"),
        *EscapeRaftSimJsonString(LocalVisualMapPackagePath),
        LocalVisualFoliageMeshCount,
        LocalVisualFoliageInstanceCount,
        *EscapeRaftSimJsonString(LocalVisualCapturePaths[0]),
        *EscapeRaftSimJsonString(LocalVisualCapturePaths[1]),
        *EscapeRaftSimJsonString(LocalVisualCapturePaths[2]),
        *EscapeRaftSimJsonString(LocalVisualCapturePaths[3]),
        *EscapeRaftSimJsonString(LocalVisualCapturePaths[4]),
        *EscapeRaftSimJsonString(LocalVisualCapturePaths[5]),
        *EscapeRaftSimJsonString(LocalMultiViewAtlasCapturePath),
        LocalHandoffCapturePaths.Num(),
        *LocalHandoffCapturesJson,
        LocalComplementaryTransitionCapturePaths.Num(),
        *LocalComplementaryTransitionCapturesJson,
        LocalTemporalTransitionCapturePaths.Num(),
        *LocalTemporalTransitionCapturesJson,
        LocalPersistentMotionTransitionCapturePaths.Num(),
        *LocalPersistentMotionTransitionCapturesJson,
        LocalFinePersistentMotionTransitionCapturePaths.Num(),
        *LocalFinePersistentMotionTransitionCapturesJson,
        LocalLitRiverViewMotionTransitionCapturePaths.Num(),
        *LocalLitRiverViewMotionTransitionCapturesJson,
        LocalTemporalLitRiverViewMotionTransitionCapturePaths.Num(),
        *LocalTemporalLitRiverViewMotionTransitionCapturesJson,
        LocalHlodFrameSearchCapturePaths.Num(),
        *LocalHlodFrameSearchCapturesJson,
        LocalHlodSplitShadingSearchCapturePaths.Num(),
        *LocalHlodSplitShadingSearchCapturesJson,
        LocalHlodDualLayerCapturePaths.Num(),
        *LocalHlodDualLayerCapturesJson,
        LocalHlodTransmissionLightBracketCapturePaths.Num(),
        *LocalHlodTransmissionLightBracketCapturesJson,
        LocalHlodMergedGeometryShapeBracketCapturePaths.Num(),
        *LocalHlodMergedGeometryShapeBracketCapturesJson,
        LocalHlodMergedComponentParityCapturePaths.Num(),
        *LocalHlodMergedComponentParityCapturesJson,
        *EscapeRaftSimJsonString(LocalMultiViewAtlas.ManifestRelativePath));

    const FString BeechReportRelativePath = FString::Printf(
        TEXT("docs/environment-captures/photoreal_river_previews/"
             "pve_futaleufu_european_beech_%s_structural_report.json"),
        *ProceduralBeechVariant.ToLower());
    const FString UnfrozenCypressPaletteReportSuffix =
        bBotanicalFlattenedSprayCypressHierarchyPalette
        ? (bCompoundBranchletAtlasCypressPalette
            ? (bDeTieredCompoundBranchletAtlasCypressPalette
                ? (bAsyncSecondaryCompoundBranchletAtlasCypressPalette
                    ? (bIrregularCrownMassCompoundBranchletAtlasCypressPalette
                        ? (bHlodCalibratedIrregularCrownMassCypressPalette
                            ? (bHighDetailHlodCalibratedIrregularCrownMassCypressPalette
                                ? TEXT("_high_detail_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas")
                                : TEXT("_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas"))
                            : TEXT("_irregular_crown_mass_compound_branchlet_atlas"))
                        : TEXT("_async_secondary_compound_branchlet_atlas"))
                    : TEXT("_detiered_compound_branchlet_atlas"))
                : TEXT("_compound_branchlet_atlas"))
            : (bTerminalClusterBotanicalShootCypressPalette
            ? TEXT("_terminal_cluster_botanical_shoot")
            : (bHierarchicalBotanicalShootClusterCypressPalette
            ? TEXT("_hierarchical_botanical_shoot_cluster")
            : (bBranchletMassBotanicalFlattenedSprayCypressHierarchyPalette
            ? TEXT("_branchlet_mass_botanical_flattened_spray_hierarchy")
            : (bDenseBotanicalFlattenedSprayCypressHierarchyPalette
                ? TEXT("_dense_botanical_flattened_spray_hierarchy")
                : TEXT("_botanical_flattened_spray_hierarchy"))))))
        : (bDenseAuthoredScaleLeafCypressHierarchyPalette
        ? TEXT("_dense_authored_scale_leaf_hierarchy")
        : (bAuthoredScaleLeafCypressHierarchyPalette
        ? TEXT("_authored_scale_leaf_hierarchy")
        : (bCompactConnectedCypressTwigHierarchyPalette
        ? TEXT("_compact_connected_twig_hierarchy")
        : (bConnectedCypressTwigHierarchyPalette
        ? TEXT("_connected_twig_hierarchy")
        : (bCypressTwigHierarchyPalette
               ? TEXT("_twig_hierarchy")
               : (bCurvedCypressShellPalette ? TEXT("_curved_shells") : TEXT("")))))));
    const FString CypressPaletteReportSuffix =
        bFrozenWpoHlodCalibratedIrregularCrownMassCypressPalette
        ? (bFrozenWpoAzimuthRegisteredHlodCalibratedIrregularCrownMassCypressPalette
            ? (bFrozenWpoAzimuthRegisteredPerspectiveHlodCalibratedIrregularCrownMassCypressPalette
                ? (bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette
                    ? TEXT("_frozen_wpo_azimuth_registered_perspective_complementary_transition_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas")
                    : (bFrozenWpoAzimuthRegisteredPerspectiveDepthHlodCalibratedIrregularCrownMassCypressPalette
                        ? TEXT("_frozen_wpo_azimuth_registered_perspective_depth_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas")
                        : TEXT("_frozen_wpo_azimuth_registered_perspective_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas")))
                : TEXT("_frozen_wpo_azimuth_registered_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas"))
            : (bFrozenWpoHighDetailHlodCalibratedIrregularCrownMassCypressPalette
            ? TEXT("_frozen_wpo_high_detail_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas")
            : TEXT("_frozen_wpo_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas")))
        : UnfrozenCypressPaletteReportSuffix;
    const FString UnfrozenCypressCandidateVersion =
        bBotanicalFlattenedSprayCypressHierarchyPalette
        ? (bCompoundBranchletAtlasCypressPalette
            ? (bDeTieredCompoundBranchletAtlasCypressPalette
                ? (bAsyncSecondaryCompoundBranchletAtlasCypressPalette
                    ? (bIrregularCrownMassCompoundBranchletAtlasCypressPalette
                        ? (bHlodCalibratedIrregularCrownMassCypressPalette
                            ? (bHighDetailHlodCalibratedIrregularCrownMassCypressPalette
                                ? TEXT("v26")
                                : TEXT("v25"))
                            : TEXT("v24"))
                        : TEXT("v23"))
                    : TEXT("v22"))
                : TEXT("v21"))
            : (bTerminalClusterBotanicalShootCypressPalette
            ? TEXT("v20_4")
            : (bHierarchicalBotanicalShootClusterCypressPalette
            ? TEXT("v20_3")
            : (bBranchletMassBotanicalFlattenedSprayCypressHierarchyPalette
            ? TEXT("v20_2")
            : (bDenseBotanicalFlattenedSprayCypressHierarchyPalette
                ? TEXT("v20_1")
                : TEXT("v20"))))))
        : (bDenseAuthoredScaleLeafCypressHierarchyPalette
        ? TEXT("v19_1")
        : (bAuthoredScaleLeafCypressHierarchyPalette
        ? TEXT("v19")
        : (bCompactConnectedCypressTwigHierarchyPalette
        ? TEXT("v18_2")
        : (bConnectedCypressTwigHierarchyPalette
        ? TEXT("v18_1")
        : (bCypressTwigHierarchyPalette
               ? TEXT("v18")
               : TEXT("v17"))))));
    const FString CypressCandidateVersion =
        bFrozenWpoHlodCalibratedIrregularCrownMassCypressPalette
        ? (bFrozenWpoAzimuthRegisteredHlodCalibratedIrregularCrownMassCypressPalette
            ? (bFrozenWpoAzimuthRegisteredPerspectiveHlodCalibratedIrregularCrownMassCypressPalette
                ? (bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette
                    ? TEXT("v32")
                    : (bFrozenWpoAzimuthRegisteredPerspectiveDepthHlodCalibratedIrregularCrownMassCypressPalette
                        ? TEXT("v31")
                        : TEXT("v30")))
                : TEXT("v29"))
            : (bFrozenWpoHighDetailHlodCalibratedIrregularCrownMassCypressPalette
            ? TEXT("v28")
            : TEXT("v27")))
        : UnfrozenCypressCandidateVersion;
    const FString ReportRelativePath = bProceduralCypressPveCandidate
        ? FString::Printf(
              TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates/"
                   "futaleufu_cordillera_cypress_%s_pve_%s%s_report.json"),
              *CypressCandidateVersion,
              *ProceduralBeechVariant.ToLower(),
              *CypressPaletteReportSuffix)
        : BeechReportRelativePath;
    const FString ReportPath = FPaths::Combine(GetRepoRoot(), ReportRelativePath);
    const FString BeechReport = FString::Printf(
        TEXT("{\n")
        TEXT("  \"schema\": \"raftsim.unreal.pve_growth_candidate_structural_review.v1\",\n")
        TEXT("  \"river_id\": \"futaleufu_terminator\",\n")
        TEXT("  \"candidate\": \"ue_5_8_pve_european_beech\",\n")
        TEXT("  \"variant\": \"%s\",\n")
        TEXT("  \"status\": \"structurally_generated_local_review_export_ready_not_visual_or_production_promoted\",\n")
        TEXT("  \"engine_version\": \"5.8\",\n")
        TEXT("  \"source_growth_json\": \"Engine/Plugins/Experimental/ProceduralVegetationEditor/Content/SampleAssets/Tree_European_Beech_01/Instances/%s.json\",\n")
        TEXT("  \"source_graph\": \"/ProceduralVegetationEditor/SampleAssets/StarterContent/DeciduousTree_01/PVE_Sample_Deciduous_Tree_01\",\n")
        TEXT("  \"generated_collection\": {\n")
        TEXT("    \"transform_count\": %d,\n")
        TEXT("    \"vertex_count\": %d,\n")

        TEXT("    \"triangle_count\": %d,\n")
        TEXT("    \"foliage_mesh_count\": %d,\n")
        TEXT("    \"foliage_instance_count\": %d,\n")
        TEXT("    \"foliage_meshes\": [%s]\n")
        TEXT("  },\n")
        TEXT("  \"local_review_export\": {\n")
        TEXT("    \"status\": \"%s\",\n")
        TEXT("    \"git_policy\": \"generated_files_are_ignored_and_must_not_be_open_source_redistributed\",\n")
        TEXT("    \"trunk_asset\": \"%s\",\n")
        TEXT("    \"foliage_template\": \"%s\",\n")
        TEXT("    \"asset_validation\": {\n")
        TEXT("      \"passed\": %s,\n")
        TEXT("      \"nanite_enabled\": %s,\n")
        TEXT("      \"nanite_shape_preservation\": \"%s\",\n")
        TEXT("      \"vertex_count_lod0\": %d,\n")
        TEXT("      \"triangle_count_lod0\": %d,\n")
        TEXT("      \"material_slot_count\": %d,\n")
        TEXT("      \"non_null_material_count\": %d,\n")
        TEXT("      \"bounds_size_cm\": [%.6f, %.6f, %.6f]\n")
        TEXT("    }\n")
        TEXT("  },\n")
        TEXT("  \"local_visual_review\": %s,\n")
        TEXT("  \"rights_boundary\": \"installed_unreal_engine_sample_evaluation_only_do_not_redistribute_as_open_source_asset\",\n")
        TEXT("  \"species_boundary\": \"fagus_sylvatica_structure_analog_not_native_nothofagus_or_patagonian_species_approval\",\n")
        TEXT("  \"promotion_gates\": [\"isolated_visual_material_validation\", \"river_view_comparison\", \"native_species_or_ecology_review\", \"open_source_redistribution_review\", \"desktop_and_vr_performance\"]\n")
        TEXT("}\n"),
        *EscapeRaftSimJsonString(ProceduralBeechVariant),
        *EscapeRaftSimJsonString(ProceduralBeechVariant),
        TransformCount,
        VertexCount,
        TriangleCount,
        FoliageMeshCount,
        FoliageInstanceCount,
        *FoliageMeshesJson,
        bLocalTrunkExported && bLocalTrunkValidated && bLocalTemplateSaved
            ? TEXT("trunk_nanite_asset_and_foliage_template_generated_locally")
            : TEXT("local_export_failed"),
        *EscapeRaftSimJsonString(LocalTrunkAssetPath),
        *EscapeRaftSimJsonString(LocalTemplateReportPath),
        bLocalTrunkValidated ? TEXT("true") : TEXT("false"),
        bLocalTrunkNaniteEnabled ? TEXT("true") : TEXT("false"),
        bLocalTrunkPreserveArea ? TEXT("preserve_area") : TEXT("other"),
        LocalTrunkVertexCount,
        LocalTrunkTriangleCount,
        LocalTrunkMaterialSlotCount,
        LocalTrunkNonNullMaterialCount,
        LocalTrunkBoundsSize.X,
        LocalTrunkBoundsSize.Y,
        LocalTrunkBoundsSize.Z,
        *LocalVisualReviewJson);
    const FString CypressReport = bProceduralCypressPveCandidate
        ? FString::Printf(
              TEXT("{\n")
              TEXT("  \"schema\": \"raftsim.unreal.futaleufu_cordillera_cypress_pve_review.v2\",\n")
              TEXT("  \"river_id\": \"futaleufu_terminator\",\n")
              TEXT("  \"candidate\": \"%s\",\n")
              TEXT("  \"variant\": \"%s\",\n")
              TEXT("  \"display_name\": \"%s\",\n")
              TEXT("  \"life_stage\": \"%s\",\n")
              TEXT("  \"status\": \"generated_local_isolated_review_not_visual_or_production_promoted\",\n")
              TEXT("  \"engine_version\": \"5.8\",\n")
              TEXT("  \"source_graph\": \"RaftSim-created transient UProceduralVegetationGraph\",\n")
              TEXT("  \"palette_mode\": \"%s\",\n")
              TEXT("  \"rendering_setting_donors\": [\"installed UE 5.8 conifer PVMeshBuilderSettings\", \"installed UE 5.8 conifer PVPlantProfileLoaderSettings\"],\n")
              TEXT("  \"workflow\": {\n")
              TEXT("    \"tree_level_authority\": \"project-authored PVE grower, grafting, gravity, bone reduction, and hormone-driven foliage topology\",\n")
              TEXT("    \"project_owned_palette\": %s,\n")
              TEXT("    \"botanical_spray_layering\": {\"main_layers\": %d, \"lateral_layers\": %d, \"measured_source_tiles_changed\": %s},\n")
              TEXT("    \"authored_branchlet_geometry\": {\"paired_laterals_per_twig\": %d, \"woody_support_length_fraction\": %.2f, \"attachment_rhythm\": \"%s\", \"tertiary_subshoots_per_lateral\": %d},\n")
              TEXT("    \"hlod_shading\": \"%s\",\n")
              TEXT("    \"whole_tree_scale\": %.6f,\n")
              TEXT("    \"authored_live_twig_scale\": %.6f,\n")
              TEXT("    \"effective_live_twig_scale\": %.6f,\n")
              TEXT("    \"branch_scale\": %.6f,\n")
              TEXT("    \"primary_axil_elevation_degrees\": %.6f,\n")
              TEXT("    \"axillary_parent_growth\": %.6f,\n")
              TEXT("    \"axillary_child_growth\": %.6f,\n")
              TEXT("    \"authored_graft_density\": %d,\n")
              TEXT("    \"effective_graft_density\": %d,\n")
              TEXT("    \"graft_relative_start\": %.6f,\n")
              TEXT("    \"senescence_enabled\": %s,\n")
              TEXT("    \"apical_random_angle_degrees\": %.6f,\n")
              TEXT("    \"axillary_random_angle_degrees\": %.6f,\n")
              TEXT("    \"effective_gravity_strength\": %.6f,\n")
              TEXT("    \"effective_gravity_angle_correction\": %.6f,\n")
              TEXT("    \"main_growth_cycles\": 44,\n")
              TEXT("    \"branchlet_growth_cycles\": 6,\n")
              TEXT("    \"branchlet_graft_template_count\": %d,\n")
              TEXT("    \"branchlet_template_seed_offsets\": %s,\n")
              TEXT("    \"branchlet_template_phyllotaxy_additional_angles_degrees\": %s,\n")
              TEXT("    \"branchlet_template_phyllotaxy_staggers\": %s,\n")
              TEXT("    \"graft_template_selection\": \"%s\",\n")
              TEXT("    \"graft_scale_ramp_basis\": \"%s\",\n")
              TEXT("    \"graft_scale_ramp\": %s,\n")
              TEXT("    \"graft_random_scale_range\": %s,\n")
              TEXT("    \"maximum_generation\": 2,\n")
              TEXT("    \"main_target_length_m\": 22.5,\n")
              TEXT("    \"branchlet_target_length_m\": 1.45,\n")
              TEXT("    \"mesher_minimum_radius_m\": 0.0008,\n")
              TEXT("    \"trunk_and_branch_bifurcation_enabled\": false,\n")
              TEXT("    \"sample_graph_topology_duplicated\": false,\n")
              TEXT("    \"manual_edit_or_export_nodes_present\": false,\n")
              TEXT("    \"live_foliage_shadows_enabled_in_isolated_review\": false,\n")
              TEXT("    \"live_foliage_material_defaults\": {\"base_color_scale\": 2.10, \"ao_influence\": 0.08, \"opacity_clip\": 0.42, \"diagnostic_emissive\": 0.0},\n")
              TEXT("    \"live_foliage_distribution\": {\"ethylene_threshold\": 0.72, \"instance_spacing\": %.6f, \"spacing_ramp_effect\": 0.45},\n")
              TEXT("    \"crown_topology_mode\": \"%s\",\n")
              TEXT("    \"main_phyllotaxy_additional_angle_degrees\": %.6f,\n")
              TEXT("    \"main_phyllotaxy_stagger\": %.6f,\n")
              TEXT("    \"graft_angle_jitter_degrees\": [%.6f, %.6f],\n")
              TEXT("    \"graft_phyllotaxy_additional_angle_degrees\": %.6f,\n")
              TEXT("    \"graft_axil_angle_degrees\": %.6f,\n")
              TEXT("    \"upper_crown_spray_taper\": {\"start_normalized_height\": 0.86, \"scale_range\": [0.92, 0.68]},\n")
              TEXT("    \"seed\": %d,\n")
              TEXT("    \"epic_sample_content_copied_into_repository\": false,\n")
              TEXT("    \"local_generated_assets_git_ignored\": true\n")
              TEXT("  },\n")
              TEXT("  \"generated_collection\": {\n")
              TEXT("    \"transform_count\": %d,\n")
              TEXT("    \"vertex_count\": %d,\n")
              TEXT("    \"triangle_count\": %d,\n")
              TEXT("    \"foliage_mesh_count\": %d,\n")
              TEXT("    \"foliage_instance_count\": %d,\n")
              TEXT("    \"foliage_meshes\": [%s]\n")
              TEXT("  },\n")
              TEXT("  \"local_review_export\": {\n")
              TEXT("    \"status\": \"%s\",\n")
              TEXT("    \"trunk_asset\": \"%s\",\n")
              TEXT("    \"foliage_template\": \"%s\",\n")
              TEXT("    \"nanite_woody_enabled\": %s,\n")
              TEXT("    \"woody_renderer_contract\": \"%s\",\n")
              TEXT("    \"nanite_shape_preservation\": \"none\",\n")
              TEXT("    \"bounds_size_cm\": [%.6f, %.6f, %.6f]\n")
              TEXT("  },\n")
              TEXT("  \"local_impostor_source\": {\n")
              TEXT("    \"status\": \"%s\",\n")
              TEXT("    \"asset\": \"%s\",\n")
              TEXT("    \"source_assembly\": \"V17 trunk plus all foliage instances merged through Geometry Script\",\n")
              TEXT("    \"vertex_count_lod0\": %d,\n")
              TEXT("    \"triangle_count_lod0\": %d,\n")
              TEXT("    \"material_slot_count\": %d,\n")
              TEXT("    \"bounds_size_cm\": [%.6f, %.6f, %.6f],\n")
              TEXT("    \"nanite_enabled\": %s,\n")
              TEXT("    \"renderer_contract\": \"%s\",\n")
              TEXT("    \"nanite_shape_preservation\": \"%s\",\n")
              TEXT("    \"preserve_area_evaluation\": \"%s\",\n")
              TEXT("    \"exact_camera_60m_capture_produced\": %s,\n")
              TEXT("    \"human_visual_acceptance\": \"%s\",\n")
              TEXT("    \"visual_role\": \"merged whole-tree near/mid representation candidate and source for any later HLOD or atlas bake\",\n")
              TEXT("    \"next_distance_representation\": \"project-owned multi-view atlas/HLOD baker or a separately rights-reviewed distance-stable native asset\",\n")
              TEXT("    \"git_policy\": \"local_generated_source_is_ignored\",\n")
              TEXT("    \"bake_contract\": {\"plugin\": \"ImpostorBaker\", \"type\": \"upper_hemisphere\", \"frames_xy\": 12, \"resolution\": 2048, \"capture\": \"GBuffer\", \"required_maps\": [\"base_color\", \"normal\", \"opacity_mask\", \"depth\"]}\n")
              TEXT("  },\n")
              TEXT("  \"local_far_proxy\": {\n")
              TEXT("    \"status\": \"%s\",\n")
              TEXT("    \"asset\": \"%s\",\n")
              TEXT("    \"representation\": \"closed three-wedge scale-spray fans aligned to every fourth authored PVE foliage transform; each fan has one axial and two lateral sprays and is paired with the original woody trunk\",\n")
              TEXT("    \"source_foliage_count\": %d,\n")
              TEXT("    \"sample_stride\": 4,\n")
              TEXT("    \"scale_spray_wedge_count\": %d,\n")
              TEXT("    \"material_response\": \"opaque DefaultLit vertex color; roughness 0.94, specular 0.035, ambient occlusion 0.82, no emissive\",\n")
              TEXT("    \"vertex_count_lod0\": %d,\n")
              TEXT("    \"triangle_count_lod0\": %d,\n")
              TEXT("    \"bounds_size_cm\": [%.6f, %.6f, %.6f],\n")
              TEXT("    \"nanite_enabled\": false,\n")
              TEXT("    \"planar_cards_present\": false,\n")
              TEXT("    \"exact_source_camera_60m_capture_produced\": %s,\n")
              TEXT("    \"human_visual_acceptance\": \"rejected; exact 60 m capture reads as detached geometric shards and cannot be promoted\",\n")
              TEXT("    \"built_in_impostor_baker_evaluation\": \"rejected for this merged source after both 12x12/2048 and 8x8/1024 profiles produced zero output assets at 600 seconds and the Epic utility widget crashed in DeleteLoadedAsset during shutdown\",\n")
              TEXT("    \"git_policy\": \"local generated proxy and comparison capture are ignored\"\n")
              TEXT("  },\n")
              TEXT("  \"local_multi_view_atlas_hlod\": %s,\n")
              TEXT("  \"local_visual_review\": %s,\n")
              TEXT("  \"rights_boundary\": \"only installed-engine mesher and plant-profile settings are copied into the transient local graph; no Epic graph topology, preset, twig geometry, materials, textures, or generated derivative is committed\",\n")
              TEXT("  \"species_boundary\": \"project-owned Austrocedrus-oriented topology and palette; exact-camera card-edge, all-form, ecology, temporal, and runtime gates remain required\",\n")
              TEXT("  \"promotion_gates\": [\"all_eight_v17_forms_generated\", \"V13_exact_camera_visual_review\", \"branch_spray_closeup\", \"card_edges_not_visible_at_60m\", \"V10_far_authority\", \"packaged_desktop_and_target_vr_profile\", \"ecology_and_rights_review\"]\n")
              TEXT("}\n"),
              bFrozenWpoHlodCalibratedIrregularCrownMassCypressPalette
                  ? (bFrozenWpoAzimuthRegisteredHlodCalibratedIrregularCrownMassCypressPalette
                      ? (bFrozenWpoAzimuthRegisteredPerspectiveHlodCalibratedIrregularCrownMassCypressPalette
                          ? (bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette
                              ? TEXT("ue_5_8_pve_cordillera_cypress_v32_frozen_wpo_azimuth_registered_perspective_complementary_transition_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas")
                              : (bFrozenWpoAzimuthRegisteredPerspectiveDepthHlodCalibratedIrregularCrownMassCypressPalette
                                  ? TEXT("ue_5_8_pve_cordillera_cypress_v31_frozen_wpo_azimuth_registered_perspective_depth_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas")
                                  : TEXT("ue_5_8_pve_cordillera_cypress_v30_frozen_wpo_azimuth_registered_perspective_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas")))
                          : TEXT("ue_5_8_pve_cordillera_cypress_v29_frozen_wpo_azimuth_registered_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas"))
                      : (bFrozenWpoHighDetailHlodCalibratedIrregularCrownMassCypressPalette
                      ? TEXT("ue_5_8_pve_cordillera_cypress_v28_frozen_wpo_high_detail_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas")
                      : TEXT("ue_5_8_pve_cordillera_cypress_v27_frozen_wpo_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas")))
                  : bBotanicalFlattenedSprayCypressHierarchyPalette
                  ? (bCompoundBranchletAtlasCypressPalette
                    ? (bDeTieredCompoundBranchletAtlasCypressPalette
                        ? (bAsyncSecondaryCompoundBranchletAtlasCypressPalette
                            ? (bIrregularCrownMassCompoundBranchletAtlasCypressPalette
                                ? (bHlodCalibratedIrregularCrownMassCypressPalette
                                    ? (bHighDetailHlodCalibratedIrregularCrownMassCypressPalette
                                        ? TEXT("ue_5_8_pve_cordillera_cypress_v26_high_detail_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas")
                                        : TEXT("ue_5_8_pve_cordillera_cypress_v25_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas"))
                                    : TEXT("ue_5_8_pve_cordillera_cypress_v24_irregular_crown_mass_compound_branchlet_atlas"))
                                : TEXT("ue_5_8_pve_cordillera_cypress_v23_async_secondary_compound_branchlet_atlas"))
                            : TEXT("ue_5_8_pve_cordillera_cypress_v22_detiered_compound_branchlet_atlas"))
                        : TEXT("ue_5_8_pve_cordillera_cypress_v21_compound_branchlet_atlas"))
                    : (bTerminalClusterBotanicalShootCypressPalette
                    ? TEXT("ue_5_8_pve_cordillera_cypress_v20_4_terminal_cluster_botanical_shoot")
                    : (bHierarchicalBotanicalShootClusterCypressPalette
                    ? TEXT("ue_5_8_pve_cordillera_cypress_v20_3_hierarchical_botanical_shoot_cluster")
                    : (bBranchletMassBotanicalFlattenedSprayCypressHierarchyPalette
                    ? TEXT("ue_5_8_pve_cordillera_cypress_v20_2_branchlet_mass_botanical_flattened_spray_hierarchy")
                    : (bDenseBotanicalFlattenedSprayCypressHierarchyPalette
                        ? TEXT("ue_5_8_pve_cordillera_cypress_v20_1_dense_botanical_flattened_spray_hierarchy")
                        : TEXT("ue_5_8_pve_cordillera_cypress_v20_botanical_flattened_spray_hierarchy"))))))
                  : (bDenseAuthoredScaleLeafCypressHierarchyPalette
                  ? TEXT("ue_5_8_pve_cordillera_cypress_v19_1_dense_authored_scale_leaf_hierarchy")
                  : (bAuthoredScaleLeafCypressHierarchyPalette
                  ? TEXT("ue_5_8_pve_cordillera_cypress_v19_authored_scale_leaf_hierarchy")
                  : (bCompactConnectedCypressTwigHierarchyPalette
                  ? TEXT("ue_5_8_pve_cordillera_cypress_v18_2_compact_connected_twig_hierarchy")
                  : (bConnectedCypressTwigHierarchyPalette
                  ? TEXT("ue_5_8_pve_cordillera_cypress_v18_1_connected_twig_hierarchy")
                  : (bCypressTwigHierarchyPalette
                  ? TEXT("ue_5_8_pve_cordillera_cypress_v18_twig_hierarchy")
                  : TEXT("ue_5_8_pve_cordillera_cypress_v17_project_graph")))))),
              *EscapeRaftSimJsonString(CypressSpec->Id),
              *EscapeRaftSimJsonString(CypressSpec->DisplayName),
              *EscapeRaftSimJsonString(CypressSpec->LifeStage),
              *EscapeRaftSimJsonString(ProceduralCypressPaletteMode),
              bBotanicalFlattenedSprayCypressHierarchyPalette
                  ? (bCompoundBranchletAtlasCypressPalette
                    ? (bDeTieredCompoundBranchletAtlasCypressPalette
                        ? (bAsyncSecondaryCompoundBranchletAtlasCypressPalette
                            ? (bIrregularCrownMassCompoundBranchletAtlasCypressPalette
                                ? TEXT("[\"V24 irregular crown-mass compound branchlet atlas live twig A\", \"V24 irregular crown-mass compound branchlet atlas live twig B\", \"V24 irregular crown-mass compound branchlet atlas live twig C\", \"V16 dead twig\"]")
                                : TEXT("[\"V23 asynchronous secondary-shoot compound branchlet atlas live twig A\", \"V23 asynchronous secondary-shoot compound branchlet atlas live twig B\", \"V23 asynchronous secondary-shoot compound branchlet atlas live twig C\", \"V16 dead twig\"]"))
                            : TEXT("[\"V22 de-tiered compound branchlet atlas live twig A\", \"V22 de-tiered compound branchlet atlas live twig B\", \"V22 de-tiered compound branchlet atlas live twig C\", \"V16 dead twig\"]"))
                        : TEXT("[\"V21 compound branchlet atlas live twig A\", \"V21 compound branchlet atlas live twig B\", \"V21 compound branchlet atlas live twig C\", \"V16 dead twig\"]"))
                    : (bTerminalClusterBotanicalShootCypressPalette
                    ? TEXT("[\"V20.4 terminal-cluster botanical shoot live twig A\", \"V20.4 terminal-cluster botanical shoot live twig B\", \"V20.4 terminal-cluster botanical shoot live twig C\", \"V16 dead twig\"]")
                    : (bHierarchicalBotanicalShootClusterCypressPalette
                    ? TEXT("[\"V20.3 hierarchical botanical shoot-cluster live twig A\", \"V20.3 hierarchical botanical shoot-cluster live twig B\", \"V20.3 hierarchical botanical shoot-cluster live twig C\", \"V16 dead twig\"]")
                    : (bBranchletMassBotanicalFlattenedSprayCypressHierarchyPalette
                    ? TEXT("[\"V20.2 branchlet-mass botanical flattened-spray hierarchy live twig A\", \"V20.2 branchlet-mass botanical flattened-spray hierarchy live twig B\", \"V20.2 branchlet-mass botanical flattened-spray hierarchy live twig C\", \"V16 dead twig\"]")
                    : (bDenseBotanicalFlattenedSprayCypressHierarchyPalette
                        ? TEXT("[\"V20.1 dense botanical flattened-spray hierarchy live twig A\", \"V20.1 dense botanical flattened-spray hierarchy live twig B\", \"V20.1 dense botanical flattened-spray hierarchy live twig C\", \"V16 dead twig\"]")
                        : TEXT("[\"V20 botanical flattened-spray hierarchy live twig A\", \"V20 botanical flattened-spray hierarchy live twig B\", \"V20 botanical flattened-spray hierarchy live twig C\", \"V16 dead twig\"]"))))))
                  : (bDenseAuthoredScaleLeafCypressHierarchyPalette
                  ? TEXT("[\"V19.1 dense authored scale-leaf hierarchy live twig A\", \"V19.1 dense authored scale-leaf hierarchy live twig B\", \"V19.1 dense authored scale-leaf hierarchy live twig C\", \"V16 dead twig\"]")
                  : (bAuthoredScaleLeafCypressHierarchyPalette
                  ? TEXT("[\"V19 authored scale-leaf hierarchy live twig A\", \"V19 authored scale-leaf hierarchy live twig B\", \"V19 authored scale-leaf hierarchy live twig C\", \"V16 dead twig\"]")
                  : (bCompactConnectedCypressTwigHierarchyPalette
                  ? TEXT("[\"V18.2 compact connected two-material twig hierarchy live twig A\", \"V18.2 compact connected two-material twig hierarchy live twig B\", \"V18.2 compact connected two-material twig hierarchy live twig C\", \"V16 dead twig\"]")
                  : (bConnectedCypressTwigHierarchyPalette
                  ? TEXT("[\"V18.1 connected two-material twig hierarchy live twig A\", \"V18.1 connected two-material twig hierarchy live twig B\", \"V18.1 connected two-material twig hierarchy live twig C\", \"V16 dead twig\"]")
                  : (bCypressTwigHierarchyPalette
                  ? TEXT("[\"V18 twig-hierarchy live twig A\", \"V18 twig-hierarchy live twig B\", \"V18 twig-hierarchy live twig C\", \"V16 dead twig\"]")
                  : (bCurvedCypressShellPalette
                         ? TEXT("[\"V17 curved-shell live twig A\", \"V17 curved-shell live twig B\", \"V17 curved-shell live twig C\", \"V16 dead twig\"]")
                         : TEXT("[\"V16 live twig A\", \"V16 live twig B\", \"V16 live twig C\", \"V16 dead twig\"]"))))))),
              bCompoundBranchletAtlasCypressPalette
                  ? 2
                  : (bDenseBotanicalFlattenedSprayCypressHierarchyPalette ? 3 : 1),
              bCompoundBranchletAtlasCypressPalette
                  ? 1
                  : (bDenseBotanicalFlattenedSprayCypressHierarchyPalette ? 2 : 1),
              bCompoundBranchletAtlasCypressPalette ? TEXT("true") : TEXT("false"),
              bBotanicalFlattenedSprayCypressHierarchyPalette
                  ? (bHierarchicalBotanicalShootClusterCypressPalette
                         ? 5
                         : (bBranchletMassBotanicalFlattenedSprayCypressHierarchyPalette
                                ? 6
                                : 4))
                  : 0,
              bBotanicalFlattenedSprayCypressHierarchyPalette
                  ? (bHierarchicalBotanicalShootClusterCypressPalette
                         ? 0.60f
                         : (bBranchletMassBotanicalFlattenedSprayCypressHierarchyPalette
                         ? 0.68f
                         : 0.82f))
                  : 0.0f,
              bBotanicalFlattenedSprayCypressHierarchyPalette
                  ? (bHierarchicalBotanicalShootClusterCypressPalette
                         ? TEXT("five side-offset connected pairs at 0.098-0.802 normalized main-axis positions with three-state vertical variation")
                         : (bBranchletMassBotanicalFlattenedSprayCypressHierarchyPalette
                         ? TEXT("six staggered connected pairs at 0.10-0.825 normalized main-axis positions with three-state vertical variation")
                         : TEXT("four regular connected pairs at 0.16-0.73 normalized main-axis positions")))
                  : TEXT("not_applicable"),
              (bHierarchicalBotanicalShootClusterCypressPalette ||
               bTerminalClusterBotanicalShootCypressPalette)
                  ? 2
                  : 0,
              bDenseBotanicalFlattenedSprayCypressHierarchyPalette
                  ? TEXT("masked unlit source-lit color bake with inverse-opacity silhouette and bounded color gain; raw-albedo world-normal relighting rejected")
                  : TEXT("masked unlit baked FinalColorLDR"),
              CypressSpec->WholeTreeScale,
              CypressSpec->LiveTwigScale,
              CypressSpec->LiveTwigScale * 1.50f,
              CypressSpec->BranchScale,
              CypressSpec->PrimaryAxilAngle,
              CypressSpec->AxillaryParentGrowth,
              CypressSpec->AxillaryChildGrowth,
              CypressSpec->GraftDensity,
              FMath::Clamp(CypressSpec->GraftDensity, 18, 36),
              CypressSpec->GraftRelativeStart,
              CypressSpec->bAllowSenescence ? TEXT("true") : TEXT("false"),
              bDeTieredCompoundBranchletAtlasCypressPalette
                  ? 1.5f
                  : CypressSpec->ApicalRandomAngle,
              bDeTieredCompoundBranchletAtlasCypressPalette
                  ? 12.0f
                  : CypressSpec->AxillaryRandomAngle,
              CypressSpec->GravityStrength * (CypressSpec->bAllowSenescence ? 0.55f : 0.05f),
              CypressSpec->bAllowSenescence
                  ? FMath::Max(CypressSpec->GravityAngleCorrection, 0.52f)
                  : FMath::Max(CypressSpec->GravityAngleCorrection, 0.92f),
              bAsyncSecondaryCompoundBranchletAtlasCypressPalette ? 3 : 1,
              bAsyncSecondaryCompoundBranchletAtlasCypressPalette
                  ? TEXT("[7919, 112648, 217377]")
                  : TEXT("[7919]"),
              bAsyncSecondaryCompoundBranchletAtlasCypressPalette
                  ? TEXT("[4.0, 71.0, 223.5]")
                  : TEXT("[4.0]"),
              bAsyncSecondaryCompoundBranchletAtlasCypressPalette

                  ? TEXT("[0.04, 0.07, 0.10]")
                  : TEXT("[0.04]"),
              bAsyncSecondaryCompoundBranchletAtlasCypressPalette
                  ? TEXT("uniform deterministic selection from connected palette entries; no active distribution condition")
                  : TEXT("single connected palette entry"),
              bIrregularCrownMassCompoundBranchletAtlasCypressPalette
                  ? TEXT("plant")
                  : TEXT("engine_default_plant"),
              bIrregularCrownMassCompoundBranchletAtlasCypressPalette
                  ? TEXT("[[0.0, 0.92], [0.18, 0.96], [0.40, 0.98], [0.62, 0.94], [0.82, 0.82], [1.0, 0.48]]")
                  : TEXT("[[0.0, 1.0], [1.0, 0.1]]"),
              bIrregularCrownMassCompoundBranchletAtlasCypressPalette
                  ? TEXT("[0.88, 1.12]")
                  : TEXT("[1.0, 1.0]"),
              bIrregularCrownMassCompoundBranchletAtlasCypressPalette
                  ? 0.096f
                  : 0.055f,
              bDeTieredCompoundBranchletAtlasCypressPalette
                  ? (bAsyncSecondaryCompoundBranchletAtlasCypressPalette
                      ? (bIrregularCrownMassCompoundBranchletAtlasCypressPalette
                          ? TEXT("golden_angle_detiered_async_secondary_irregular_crown_mass")
                          : TEXT("golden_angle_detiered_async_secondary"))
                      : TEXT("golden_angle_detiered"))
                  : TEXT("retained_ranked_spiral"),
              bDeTieredCompoundBranchletAtlasCypressPalette ? 137.507764f : 7.5f,
              bDeTieredCompoundBranchletAtlasCypressPalette ? 0.14f : 0.035f,
              bDeTieredCompoundBranchletAtlasCypressPalette ? -18.0f : -8.0f,
              bDeTieredCompoundBranchletAtlasCypressPalette ? 18.0f : 8.0f,
              bDeTieredCompoundBranchletAtlasCypressPalette ? 137.507764f : 17.5f,
              bDeTieredCompoundBranchletAtlasCypressPalette ? 66.0f : 72.0f,
              CypressSpec->Seed,
              TransformCount,
              VertexCount,
              TriangleCount,
              FoliageMeshCount,
              FoliageInstanceCount,
              *FoliageMeshesJson,
              bLocalTrunkExported && bLocalTrunkValidated && bLocalTemplateSaved
                  ? (bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette
                      ? TEXT("traditional_raster_transition_woody_asset_and_project_palette_template_generated_locally")
                      : TEXT("nanite_woody_asset_and_project_palette_template_generated_locally"))
                  : TEXT("local_export_failed"),
              *EscapeRaftSimJsonString(LocalTrunkAssetPath),
              *EscapeRaftSimJsonString(LocalTemplateReportPath),
              bLocalTrunkNaniteEnabled ? TEXT("true") : TEXT("false"),
              bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette
                  ? TEXT("traditional_raster_for_dynamic_screen_mask_compatibility")
                  : TEXT("nanite"),
              LocalTrunkBoundsSize.X,
              LocalTrunkBoundsSize.Y,
              LocalTrunkBoundsSize.Z,
              bLocalImpostorSourceValidated
                  ? TEXT("merged_source_validated_ready_for_upper_hemisphere_bake")
                  : TEXT("merged_source_generation_or_validation_failed"),
              *EscapeRaftSimJsonString(LocalImpostorSourceAssetPath),
              LocalImpostorSourceVertexCount,
              LocalImpostorSourceTriangleCount,
              LocalImpostorSourceMaterialSlotCount,
              LocalImpostorSourceBoundsSize.X,
              LocalImpostorSourceBoundsSize.Y,
              LocalImpostorSourceBoundsSize.Z,
              bLocalImpostorSourceNaniteEnabled ? TEXT("true") : TEXT("false"),
              bCompoundBranchletAtlasCypressPalette
                  ? (bDeTieredCompoundBranchletAtlasCypressPalette
                      ? (bAsyncSecondaryCompoundBranchletAtlasCypressPalette
                          ? (bIrregularCrownMassCompoundBranchletAtlasCypressPalette
                              ? (bFrozenWpoAzimuthRegisteredPerspectiveComplementaryTransitionHlodCalibratedIrregularCrownMassCypressPalette
                                  ? TEXT("traditional raster preserves V24 irregular-scale V23 asynchronous V21 compound branchlet alpha; transition source wood also uses traditional raster for dynamic screen-mask compatibility")
                                  : TEXT("traditional raster preserves V24 irregular-scale V23 asynchronous V21 compound branchlet alpha; woody source remains separately Nanite-enabled"))
                              : TEXT("traditional raster preserves V23 asynchronous V21 compound branchlet alpha; woody source remains separately Nanite-enabled"))
                          : TEXT("traditional raster preserves V22 de-tiered V21 compound branchlet alpha; woody source remains separately Nanite-enabled"))
                      : TEXT("traditional raster preserves V21 compound branchlet measured-spray alpha; woody source remains separately Nanite-enabled"))
                  : (bTerminalClusterBotanicalShootCypressPalette
                  ? TEXT("traditional raster preserves V20.4 low-wood terminal-cluster measured-spray alpha; woody source remains separately Nanite-enabled")
                  : (bHierarchicalBotanicalShootClusterCypressPalette
                  ? TEXT("traditional raster preserves V20.3 hierarchical measured-spray alpha; woody source remains separately Nanite-enabled")
                  : (bBranchletMassBotanicalFlattenedSprayCypressHierarchyPalette
                  ? TEXT("traditional raster preserves V20.2 connected branchlet-mass measured-spray alpha; woody source remains separately Nanite-enabled")
                  : (bDenseBotanicalFlattenedSprayCypressHierarchyPalette
                  ? TEXT("traditional raster preserves V20.1 overlapping measured-spray alpha; woody source remains separately Nanite-enabled")
                  : (bBotanicalFlattenedSprayCypressHierarchyPalette
                  ? TEXT("traditional raster preserves V20 botanical spray alpha; woody source remains separately Nanite-enabled")
                  : (bAuthoredScaleLeafCypressHierarchyPalette
                  ? TEXT("traditional raster preserves V19 micro-foliage; woody source remains separately Nanite-enabled")
                  : TEXT("Nanite merged-source diagnostic"))))))),
              bTraditionalRasterCypressFoliagePalette
                  ? TEXT("not_applicable_traditional_raster_micro_foliage")
                  : TEXT("none"),
              bCompoundBranchletAtlasCypressPalette
                  ? (bDeTieredCompoundBranchletAtlasCypressPalette
                      ? (bAsyncSecondaryCompoundBranchletAtlasCypressPalette
                          ? (bIrregularCrownMassCompoundBranchletAtlasCypressPalette
                              ? TEXT("Nanite is deliberately disabled for the merged V24 irregular-scale V23 asynchronous V21 compound source so measured alpha remains available to the exact source, source-cost, and source-lit HLOD crown-mass review")
                              : TEXT("Nanite is deliberately disabled for the merged V23 asynchronous V21 compound source so measured alpha remains available to the exact source, source-cost, and source-lit HLOD topology review"))
                          : TEXT("Nanite is deliberately disabled for the merged V22 de-tiered V21 compound source so measured alpha remains available to the exact source and source-lit HLOD topology review"))
                      : TEXT("Nanite is deliberately disabled for the merged V21 compound branchlet atlas so measured alpha remains available to the exact source and source-lit HLOD cost review"))
                  : (bTerminalClusterBotanicalShootCypressPalette
                  ? TEXT("Nanite is deliberately disabled for the merged V20.4 terminal-cluster measured sprays so millimetre-scale alpha detail remains available to the exact source and source-lit HLOD review")
                  : (bHierarchicalBotanicalShootClusterCypressPalette
                  ? TEXT("Nanite is deliberately disabled for the merged V20.3 hierarchical measured sprays so millimetre-scale alpha detail remains available to the exact source and source-lit HLOD review")
                  : (bBranchletMassBotanicalFlattenedSprayCypressHierarchyPalette
                  ? TEXT("Nanite is deliberately disabled for the merged V20.2 connected branchlet-mass measured sprays so millimetre-scale alpha detail remains available to the exact source and source-lit HLOD review")
                  : (bDenseBotanicalFlattenedSprayCypressHierarchyPalette
                  ? TEXT("Nanite is deliberately disabled for the merged V20.1 overlapping measured sprays so millimetre-scale alpha detail remains available to the exact source and source-lit HLOD review")
                  : (bBotanicalFlattenedSprayCypressHierarchyPalette
                  ? TEXT("Nanite is deliberately disabled for the merged V20 masked botanical sprays so the measured millimetre-scale alpha detail remains available to the exact source and HLOD review")
                  : (bAuthoredScaleLeafCypressHierarchyPalette
                  ? TEXT("Nanite is deliberately disabled for the merged V19 micro-foliage source because the first pass collapsed leaf-scale cards; exact source and HLOD review remain required")
                  : TEXT("rejected; exact 60 m capture over-expanded merged masked spray boundaries into a distorted dark crown mass"))))))),
              bLocalNaniteWholeTreeReviewCaptured ? TEXT("true") : TEXT("false"),
              bTraditionalRasterCypressFoliagePalette
                  ? TEXT("pending human review of the exact 60 m merged-raster capture; renderer validity does not imply art acceptance")
                  : TEXT("rejected; Nanite shape preservation None collapses masked sprays into a bare trunk with detached cards at the exact 60 m camera"),
              bLocalFarProxyValidated && bLocalFarProxyReviewCaptured
                  ? TEXT("structurally_valid_exact_camera_comparison_produced_visual_acceptance_pending")
                  : TEXT("generation_validation_or_exact_camera_capture_failed"),
              *EscapeRaftSimJsonString(LocalFarProxyAssetPath),
              LocalFarProxySourceFoliageCount,
              LocalFarProxyClusterCount,
              LocalFarProxyVertexCount,
              LocalFarProxyTriangleCount,
              LocalFarProxyBoundsSize.X,
              LocalFarProxyBoundsSize.Y,
              LocalFarProxyBoundsSize.Z,
              bLocalFarProxyReviewCaptured ? TEXT("true") : TEXT("false"),
              *LocalMultiViewAtlasJson,
              *LocalVisualReviewJson)
        : FString();
    const FString& Report = bProceduralCypressPveCandidate ? CypressReport : BeechReport;
    const bool bSaved = FFileHelper::SaveStringToFile(Report, *ReportPath);
    const bool bRequiredImpostorSourceValid =
        !bProceduralCypressPveCandidate ||
        (bLocalImpostorSourceValidated && bLocalNaniteWholeTreeReviewCaptured);
    const bool bRequiredFarProxyValid =
        !bProceduralCypressPveCandidate ||
        (bLocalFarProxyValidated && bLocalFarProxyReviewCaptured);
    const bool bRequiredMultiViewAtlasValid =
        !bProceduralCypressPveCandidate ||
        (LocalMultiViewAtlas.IsReady() && bLocalMultiViewAtlasReviewCaptured &&
         bLocalHandoffReviewCaptured);
    FinishProceduralBeechCandidate(
        bSaved && bLocalTrunkExported && bLocalTrunkValidated && bLocalTemplateSaved &&
            bRequiredImpostorSourceValid && bRequiredFarProxyValid &&
            bRequiredMultiViewAtlasValid,
        FString::Printf(
            TEXT("%s %s: %d vertices, %d triangles, %d foliage meshes, %d foliage instances, impostor source %s, volumetric far proxy %s -> %s"),
            bSaved ? TEXT("Recorded") : TEXT("Failed to record"),
            *ProceduralBeechVariant,
            VertexCount,
            TriangleCount,
            FoliageMeshCount,
            FoliageInstanceCount,
            bRequiredImpostorSourceValid ? TEXT("valid") : TEXT("invalid"),
            bRequiredFarProxyValid ? TEXT("valid") : TEXT("invalid"),
            *ReportRelativePath));
    return false;
}

void FRaftSimEditorModule::FinishProceduralBeechCandidate(bool bSuccess, const FString& Summary)
{
    const bool bWasCypressCandidate = bProceduralCypressPveCandidate;
    if (bSuccess)
    {
        UE_LOG(
            LogRaftSimEditor,
            Display,
            TEXT("PVE %s candidate evaluation finished: %s"),
            bWasCypressCandidate ? TEXT("cordilleran-cypress") : TEXT("beech"),
            *Summary);
    }
    else
    {
        UE_LOG(
            LogRaftSimEditor,
            Warning,
            TEXT("PVE %s candidate evaluation stopped: %s"),
            bWasCypressCandidate ? TEXT("cordilleran-cypress") : TEXT("beech"),
            *Summary);
    }
    ProceduralBeechOutputCollection.Reset();
    if (ProceduralBeechExecutionSource)
    {
        ProceduralBeechExecutionSource->Sunset();
        ProceduralBeechExecutionSource->RemoveFromRoot();
        ProceduralBeechExecutionSource = nullptr;
    }
    if (ProceduralBeechCandidateAsset)
    {
        ProceduralBeechCandidateAsset->RemoveFromRoot();
        ProceduralBeechCandidateAsset = nullptr;
    }
    if (ProceduralBeechGrowthAsset)
    {
        ProceduralBeechGrowthAsset->RemoveFromRoot();
        ProceduralBeechGrowthAsset = nullptr;
    }
    ProceduralCypressPaletteMode.Reset();
    bProceduralCypressPveCandidate = false;
    if (!IsEngineExitRequested() &&
        FParse::Param(FCommandLine::Get(), TEXT("RaftSimExitAfterPveGeneration")))
    {
        FPlatformMisc::RequestExit(
            !bSuccess,
            bWasCypressCandidate
                ? TEXT("RaftSim PVE cordilleran-cypress candidate evaluation finished")
                : TEXT("RaftSim PVE beech candidate evaluation finished"));
    }
}

#undef LOCTEXT_NAMESPACE
