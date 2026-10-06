#pragma once
#include "RaftSimRaftMesh.h"

namespace RaftSimRaftMesh
{
// Deep-owned at import, not a view or a moved allocation that an importer can
// still mutate. Only const access is exposed; replacing an imported asset
// creates another owner. Retaining the owner prevents address-reuse aliasing.
class FImmutableProductionRestMesh final
{
    const TArray<FMeshData> Sections;
public:
    explicit FImmutableProductionRestMesh(const TArray<FMeshData>& Source):Sections(Source){}
    FImmutableProductionRestMesh(const FImmutableProductionRestMesh&)=delete;
    FImmutableProductionRestMesh& operator=(const FImmutableProductionRestMesh&)=delete;
    const TArray<FMeshData>& GetSections() const{return Sections;}
};
}
