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
            "Engine"
        });
    }
}
