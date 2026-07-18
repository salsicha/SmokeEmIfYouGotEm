using UnrealBuildTool;

public class SmokeEmIfYouGotEm : ModuleRules
{
    public SmokeEmIfYouGotEm(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new[]
        {
            "Core",
            "CoreUObject",
            "Engine",
            "RaftSimCore",
            "RaftSimPhysics",
            "RaftSimRaft",
            "RaftSimUI",
            "RaftSimDebug",
            "RaftSimAudio",
            "RaftSimInput",
            "RaftSimWater",
            "UMG",
            "EnhancedInput",
            "RaftSimCrew",
            "RaftSimRiver",
            "Slate",
            "SlateCore"
        });
    }
}
