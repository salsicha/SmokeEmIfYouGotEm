#include "RaftSimCollisionGeometryBuilder.h"

FRaftSimCollisionBuildSummary URaftSimCollisionGeometryBuilder::BuildChronoCollisionSources(
    const TArray<FRaftSimCollisionFeature>& OrderedFeatures
) const
{
    FRaftSimCollisionBuildSummary Summary;
    Summary.TotalFeatures = OrderedFeatures.Num();

    for (const FRaftSimCollisionFeature& Feature : OrderedFeatures)
    {
        Summary.FeatureIds.Add(Feature.FeatureId);
        switch (Feature.FeatureType)
        {
            case ERaftSimCollisionFeatureType::Rock:
            case ERaftSimCollisionFeatureType::Bank:
            case ERaftSimCollisionFeatureType::Ledge:
            case ERaftSimCollisionFeatureType::Strainer:
                ++Summary.RockLikeFeatures;
                break;

            case ERaftSimCollisionFeatureType::Shallow:
            case ERaftSimCollisionFeatureType::Riverbed:
                ++Summary.BedLikeFeatures;
                break;
        }
    }

    return Summary;
}
