using UnrealBuildTool;
using System.IO;

public class RaftSimEditor : ModuleRules
{
    public RaftSimEditor(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        // The decomposed editor subsystems use private helper namespaces that must
        // remain isolated at translation-unit boundaries.
        bUseUnity = false;

        // Project-owned Niagara assets are authored from UE 5.8's stateless
        // emitter template data. These headers are editor-only implementation
        // surfaces; no packaged runtime module depends on this include path.
        PrivateIncludePaths.Add(Path.Combine(
            EngineDirectory,
            "Plugins/FX/Niagara/Source/Niagara/Internal"));
        PrivateIncludePaths.Add(Path.Combine(
            EngineDirectory,
            "Plugins/FX/Niagara/Source/NiagaraShader/Internal"));

        PublicDependencyModuleNames.AddRange(new[]
        {
            "Core",
            "CoreUObject",
            "Engine",
            "Slate",
            "SlateCore",
            "ToolMenus",
            "AssetRegistry",
            "RaftSimAutomation",
            "RaftSimCore",
            "RaftSimDebug",
            "RaftSimGeo",
            "RaftSimRiver",
            "RaftSimUI"
        });

        PrivateDependencyModuleNames.AddRange(new[]
        {
            "Landscape",
            "LandscapeEditor",
            "LevelEditor",
            "Chaos",
            "GeometryCollectionEngine",
            "GeometryCore",
            "GeometryFramework",
            "GeometryScriptingCore",
            "Json",
            "ImageWrapper",
            "InputCore",
            "MeshUtilities",
            "Niagara",
            "NiagaraCore",
            "NiagaraEditor",
            "NiagaraShader",
            "EnhancedInput",
            "RaftSimRaft",
            "RaftSimWater",
            "RaftSimWaterDetail",
            "Projects",
            "ProceduralMeshComponent",
            "ProceduralVegetation",
            "PCG",
            "PlanarCut",
            "RenderCore",
            "RHI",
            "UnrealEd"
        });
        // The generic platform SHA256 entry point is unimplemented on desktop.
        // Use the engine's bundled implementation for source-geometry provenance.
        AddEngineThirdPartyPrivateStaticDependencies(Target, "OpenSSL");
    }
}
