using UnrealBuildTool;

public class RaftSimNetwork : ModuleRules
{
    public RaftSimNetwork(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[]
        {
            "Core",
            "CoreUObject",
            "Engine",
            "RaftSimCore",
            "RaftSimPhysics",
            "RaftSimAI",
            "RaftSimAudio"
        });
    }
}
