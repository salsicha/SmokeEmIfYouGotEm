using UnrealBuildTool;

public class RaftSimRaft : ModuleRules
{
    public RaftSimRaft(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "EnhancedInput", "Niagara", "RaftSimCore", "RaftSimPhysics", "RaftSimInput", "RaftSimWater", "RaftSimCrew", "ProceduralMeshComponent" });
        PrivateDependencyModuleNames.AddRange(new[] { "Json", "InputCore", "HairStrandsCore", "Slate", "SlateCore", "MovieSceneCapture" });
        if (Target.Platform == UnrealTargetPlatform.Win64)
        {
            // Debug screen recorder: Media Foundation H.264 sink writer.
            PublicSystemLibraries.AddRange(new[] { "mfplat.lib", "mfreadwrite.lib", "mfuuid.lib" });
        }
    }
}
