using UnrealBuildTool;

public class RaftSimAudio : ModuleRules
{
    public RaftSimAudio(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "AudioMixer", "RaftSimCore" });
    }
}
