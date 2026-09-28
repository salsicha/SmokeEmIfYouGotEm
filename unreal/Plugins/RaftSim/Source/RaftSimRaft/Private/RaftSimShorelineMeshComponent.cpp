#include "RaftSimShorelineMeshComponent.h"
#include "RaftSimWaterSourceBounds.h"
#include "RaftSimWaterRenderFrame.h"
#include "DynamicMeshBuilder.h"
#include "Materials/Material.h"
#include "Materials/MaterialRenderProxy.h"
#include "MaterialShared.h"
#include "MaterialDomain.h"
#include "PrimitiveSceneProxy.h"
#include "PrimitiveViewRelevance.h"
#include "PrimitiveUniformShaderParametersBuilder.h"
#include "StaticMeshResources.h"
#include "SceneInterface.h"
#include "SceneView.h"
#include "RayTracingInstance.h"
#include "Misc/AutomationTest.h"
#include "Misc/App.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Engine/World.h"
#include "ProfilingDebugging/CsvProfiler.h"
#include "Async/ParallelFor.h"
#include "RaftSimParallelBankAudit.h"

CSV_DEFINE_CATEGORY(RaftSimShoreline,true);

namespace
{
void PrepareStartupWaterShaders(URaftSimShorelineMeshComponent* Component)
{
#if WITH_EDITOR
    // Editor gameplay can load an incomplete on-demand shader map. Prepare the
    // actual water material before its first mesh publication, including its
    // depth/velocity passes; BasePass shaders alone still leave the river dry.
    // Cooked builds use cooked shaders and never enter this compilation path.
    // This is initialization work, not a per-frame wait or screenshot warmup.
    if (!FApp::CanEverRender() || !IsInGameThread() || !Component->GetWorld() ||
        !Component->GetWorld()->IsGameWorld() || !Component->GetWorld()->Scene) return;
    UMaterialInterface* Material=Component->GetMaterial(0);
    FMaterialResource* Resource=Material ? Material->GetMaterialResource(Component->GetWorld()->Scene->GetShaderPlatform()) : nullptr;
    if (!Resource || !Resource->GetShadingModels().HasShadingModel(MSM_SingleLayerWater) ||
        Resource->IsGameThreadShaderMapComplete()) return;
    const double Start=FPlatformTime::Seconds();
    Resource->CacheShaders(EMaterialShaderPrecompileMode::Synchronous);
    Resource->FinishCompilation();
    if (!Resource->IsGameThreadShaderMapComplete())
        UE_LOG(LogTemp,Error,TEXT("Startup water material shaders remain incomplete: %s"),*Material->GetPathName());
    UE_LOG(LogTemp,Display,TEXT("STARTUP_WATER_PREPARED game_frame=%llu seconds=%.6f material=%s"),
        GFrameCounter,FPlatformTime::Seconds()-Start,*Material->GetPathName());
#endif
}

FVector SelectWaterRenderOrigin(const FVector& GridOrigin)
{
    // One whole-grid GPU frame is the normal path after native and actual
    // motion qualification. CPU geometry and support never change frames.
    static const bool Legacy=FParse::Param(FCommandLine::Get(),TEXT("RaftSimLegacyShorelineCoordinates"));
    static const bool Rebased=!Legacy;
    static bool Logged=false;
    if(!Logged)
    {
        UE_LOG(LogTemp,Display,TEXT("WATER_RENDER_FRAME_MODE rebased=%d legacy_override=%d"),Rebased,Legacy);
        Logged=true;
    }
    return Rebased ? FVector(GridOrigin.X,GridOrigin.Y,0.) : FVector::ZeroVector;
}

FDynamicMeshVertex RenderVertex(const FProcMeshVertex& V,const FVector& RenderOrigin=FVector::ZeroVector)
{
    FDynamicMeshVertex Out;
    Out.Position = FRaftSimWaterRenderFrame{RenderOrigin}.Store(V.Position);
    Out.Color = V.Color;
    Out.TextureCoordinate[0] = FVector2f(V.UV0);
    Out.TextureCoordinate[1] = FVector2f(V.UV1);
    Out.TextureCoordinate[2] = FVector2f(V.UV2);
    Out.TextureCoordinate[3] = FVector2f(V.UV3);
    Out.TangentX = V.Tangent.TangentX;
    Out.TangentZ = V.Normal;
    Out.TangentZ.Vector.W = V.Tangent.bFlipTangentY ? -127 : 127;
    return Out;
}

struct FShorelineRenderPacket
{
    FVector RenderOrigin=FVector::ZeroVector;
    TArray<FDynamicMeshVertex> Vertices;
    TArray<uint32> Indices;
};

FShorelineRenderPacket MakeRenderPacket(const TArray<FProcMeshVertex>& Source,
    const TArray<uint32>& SourceIndices,bool bIncludeIndices,
    TArray<uint32>* DenseSources=nullptr,bool bReuseMapping=false,bool bParallelValues=false,
    const FVector& RenderOrigin=FVector::ZeroVector)
{
    CSV_SCOPED_TIMING_STAT(RaftSimShoreline,RenderPacket);
    FShorelineRenderPacket Packet;
    Packet.RenderOrigin=RenderOrigin;
    if (bReuseMapping)
    {
        check(DenseSources && !bIncludeIndices);
        if (bParallelValues)
        {
            // Membership is already exact; every current attribute is still
            // converted by RenderVertex. Workers own disjoint output ranges.
            Packet.Vertices.SetNumUninitialized(DenseSources->Num());
            constexpr int32 BatchSize=1024;
            ParallelFor(FMath::DivideAndRoundUp(DenseSources->Num(),BatchSize),[&](int32 Batch)
            {
                const int32 End=FMath::Min((Batch+1)*BatchSize,DenseSources->Num());
                for (int32 I=Batch*BatchSize;I<End;++I)
                    Packet.Vertices[I]=RenderVertex(Source[(*DenseSources)[I]],RenderOrigin);
            });
            return Packet;
        }
        Packet.Vertices.Reserve(DenseSources->Num());
        for (uint32 I:*DenseSources) Packet.Vertices.Add(RenderVertex(Source[I],RenderOrigin));
        return Packet;
    }
    if (DenseSources) DenseSources->Reset();
    TArray<int32> Remap; Remap.Init(INDEX_NONE,Source.Num());
    Packet.Vertices.Reserve(FMath::Min(Source.Num(),SourceIndices.Num()));
    if (bIncludeIndices) Packet.Indices.Reserve(SourceIndices.Num());
    for (uint32 I:SourceIndices)
    {
        int32& Dense=Remap[I];
        if (Dense==INDEX_NONE)
        {
            Dense=Packet.Vertices.Add(RenderVertex(Source[I],RenderOrigin));
            if (DenseSources) DenseSources->Add(I);
        }
        if (bIncludeIndices) Packet.Indices.Add(uint32(Dense));
    }
    // No coordinate welding, triangle removal or attribute interpolation.
    // Identical index order yields an identical remap when only values change.
    return Packet;
}

bool SameRenderPacket(const FShorelineRenderPacket& A,const FShorelineRenderPacket& B)
{
    if (A.RenderOrigin!=B.RenderOrigin || A.Indices!=B.Indices || A.Vertices.Num()!=B.Vertices.Num()) return false;
    for (int32 I=0;I<A.Vertices.Num();++I)
    {
        const auto& X=A.Vertices[I];const auto& Y=B.Vertices[I];
        if (X.Position!=Y.Position || X.Color!=Y.Color ||
            FMemory::Memcmp(&X.TangentX,&Y.TangentX,sizeof(X.TangentX)) ||
            FMemory::Memcmp(&X.TangentZ,&Y.TangentZ,sizeof(X.TangentZ))) return false;
        for (int32 UV=0;UV<4;++UV) if (X.TextureCoordinate[UV]!=Y.TextureCoordinate[UV]) return false;
    }
    return true;
}

class FShorelineSceneProxy final : public FPrimitiveSceneProxy
{
public:
    explicit FShorelineSceneProxy(URaftSimShorelineMeshComponent* Component)
        : FPrimitiveSceneProxy(Component)
        , VertexFactory(GetScene().GetFeatureLevel(), "RaftSimShoreline")
        , Material(Component->GetMaterial(0))
        , MaterialRelevance(Component->GetMaterialRelevance(GetScene().GetShaderPlatform()))
        , ActiveIndices(Component->GetWaterIndices().Num())
        , RenderFrame{Component->GetWaterRenderOrigin()}
        , bStartupRenderAudit(FParse::Param(FCommandLine::Get(),TEXT("RaftSimStartupRenderAudit")))
    {
        if (!Material) Material = UMaterial::GetDefaultMaterial(MD_Surface);
        if (bStartupRenderAudit && GFrameCounter<8)
            UE_LOG(LogTemp,Display,TEXT("STARTUP_WATER_PROXY game_frame=%llu indices=%d visible=%d material=%s bounds=%s"),
                GFrameCounter,ActiveIndices,Component->IsVisible(),*Material->GetPathName(),*Component->Bounds.ToString());
        const auto Packet=MakeRenderPacket(Component->GetWaterVertices(),Component->GetWaterIndices(),true,nullptr,false,false,RenderFrame.Origin);
        if(FParse::Param(FCommandLine::Get(),TEXT("RaftSimRenderFrameAudit")))
            UE_LOG(LogTemp,Display,TEXT("WATER_RENDER_FRAME_PROXY origin=(%.17g,%.17g,%.17g) vertices=%d indices=%d"),
                RenderFrame.Origin.X,RenderFrame.Origin.Y,RenderFrame.Origin.Z,Packet.Vertices.Num(),Packet.Indices.Num());
        TArray<FDynamicMeshVertex> Vertices;
        // Retain worst-case allocation and dry/rewet proxy stability, but draw
        // and subsequently upload only the exact referenced dense prefix.
        Vertices.Init(RenderVertex(Component->GetWaterVertices()[0],RenderFrame.Origin),Component->GetWaterVertices().Num());
        for (int32 I=0; I<Packet.Vertices.Num(); ++I) Vertices[I]=Packet.Vertices[I];
        // Isolated precision control, never inferred from a diagnostic pass.
        if(FParse::Param(FCommandLine::Get(),TEXT("RaftSimEphemeralProfile")) &&
            FParse::Param(FCommandLine::Get(),TEXT("RaftSimFullPrecisionWaterUVs")))
        {
            Buffers.StaticMeshVertexBuffer.SetUseFullPrecisionUVs(true);
            UE_LOG(LogTemp,Display,TEXT("Water UV precision review: four full-float UV channels; topology and normals unchanged"));
        }
        Buffers.InitFromDynamicVertex(&VertexFactory, Vertices, 4);
        IndexBuffer.Indices.Init(0, Component->GetIndexCapacity());
        FMemory::Memcpy(IndexBuffer.Indices.GetData(), Packet.Indices.GetData(), ActiveIndices*sizeof(uint32));
        BeginInitResource(&Buffers.PositionVertexBuffer);
        BeginInitResource(&Buffers.StaticMeshVertexBuffer);
        BeginInitResource(&Buffers.ColorVertexBuffer);
        BeginInitResource(&IndexBuffer);
        BeginInitResource(&VertexFactory);
#if RHI_RAYTRACING
        if (IsRayTracingEnabled())
        {
            ENQUEUE_RENDER_COMMAND(RaftSimInitShorelineRT)([this](FRHICommandListImmediate& RHICmdList)
            { RebuildRayTracing(RHICmdList); });
        }
#endif
    }

    ~FShorelineSceneProxy() override
    {
        Buffers.PositionVertexBuffer.ReleaseResource();
        Buffers.StaticMeshVertexBuffer.ReleaseResource();
        Buffers.ColorVertexBuffer.ReleaseResource();
        IndexBuffer.ReleaseResource();
        VertexFactory.ReleaseResource();
#if RHI_RAYTRACING
        RayTracingGeometry.ReleaseResource();
#endif
    }

    SIZE_T GetTypeHash() const override { static size_t Id; return reinterpret_cast<size_t>(&Id); }
    uint32 GetMemoryFootprint() const override { return sizeof(*this) + GetAllocatedSize(); }
    bool CanBeOccluded() const override { return !MaterialRelevance.bDisableDepthTest; }

    void Update(FRHICommandListBase& RHICmdList, const TArray<FDynamicMeshVertex>& Vertices,
        const TArray<uint32>& Indices, bool bIndicesChanged,const FVector& RenderOrigin)
    {
        check(IsInRenderingThread());
        check(uint32(Vertices.Num()) <= Buffers.PositionVertexBuffer.GetNumVertices());
        check(Indices.Num() <= IndexBuffer.Indices.Num());
        // The render-thread command owns both the new coordinate frame and
        // vertex payload. No draw can observe a frame from another packet.
        RenderFrame.Origin=RenderOrigin;
        for (int32 I=0; I<Vertices.Num(); ++I)
        {
            const FDynamicMeshVertex& V = Vertices[I];
            Buffers.PositionVertexBuffer.VertexPosition(I) = V.Position;
            Buffers.ColorVertexBuffer.VertexColor(I) = V.Color;
            Buffers.StaticMeshVertexBuffer.SetVertexTangents(I, V.TangentX.ToFVector3f(), V.GetTangentY(), V.TangentZ.ToFVector3f());
            for (int32 UV=0; UV<4; ++UV) Buffers.StaticMeshVertexBuffer.SetVertexUV(I, UV, V.TextureCoordinate[UV]);
        }
        const auto Upload = [&RHICmdList](FRHIBuffer* Buffer, const void* Data, uint32 Bytes)
        {
            if (!Bytes) return;
            void* Destination = RHICmdList.LockBuffer(Buffer, 0, Bytes, RLM_WriteOnly);
            FMemory::Memcpy(Destination, Data, Bytes);
            RHICmdList.UnlockBuffer(Buffer);
        };
        Upload(Buffers.PositionVertexBuffer.VertexBufferRHI, Buffers.PositionVertexBuffer.GetVertexData(),
            Vertices.Num()*Buffers.PositionVertexBuffer.GetStride());
        Upload(Buffers.ColorVertexBuffer.VertexBufferRHI, Buffers.ColorVertexBuffer.GetVertexData(),
            Vertices.Num()*Buffers.ColorVertexBuffer.GetStride());
        const uint32 Capacity=Buffers.StaticMeshVertexBuffer.GetNumVertices();
        Upload(Buffers.StaticMeshVertexBuffer.TangentsVertexBuffer.VertexBufferRHI,
            Buffers.StaticMeshVertexBuffer.GetTangentData(),
            (Buffers.StaticMeshVertexBuffer.GetTangentSize()/Capacity)*Vertices.Num());
        Upload(Buffers.StaticMeshVertexBuffer.TexCoordVertexBuffer.VertexBufferRHI,
            Buffers.StaticMeshVertexBuffer.GetTexCoordData(),
            (Buffers.StaticMeshVertexBuffer.GetTexCoordSize()/Capacity)*Vertices.Num());
        // The RHI allocation stays fixed. Only the active prefix is drawn; no
        // degenerate dry lattice, stale triangles, or section recreation.
        if (bIndicesChanged)
        {
            ActiveIndices=Indices.Num();
            Upload(IndexBuffer.IndexBufferRHI, Indices.GetData(), ActiveIndices*sizeof(uint32));
        }
#if RHI_RAYTRACING
        if (IsRayTracingEnabled()) RebuildRayTracing(RHICmdList);
#endif
    }

    FPrimitiveViewRelevance GetViewRelevance(const FSceneView* View) const override
    {
        FPrimitiveViewRelevance Result;
        Result.bDrawRelevance = IsShown(View);
        Result.bShadowRelevance = IsShadowCast(View);
        Result.bDynamicRelevance = true;
        Result.bRenderInMainPass = ShouldRenderInMainPass();
        Result.bUsesLightingChannels = GetLightingChannelMask() != GetDefaultLightingChannelMask();
        Result.bRenderCustomDepth = ShouldRenderCustomDepth();
        MaterialRelevance.SetPrimitiveViewRelevance(Result);
        Result.bVelocityRelevance = DrawsVelocity() && Result.bOpaque && Result.bRenderInMainPass;
        if (bStartupRenderAudit && View->Family->FrameNumber<8)
            UE_LOG(LogTemp,Display,TEXT("STARTUP_WATER_RELEVANCE render_frame=%u draw=%d main=%d opaque=%d indices=%d"),
                View->Family->FrameNumber,Result.bDrawRelevance,Result.bRenderInMainPass,Result.bOpaque,ActiveIndices);
        return Result;
    }

    template<typename TCollector>
    void MakeBatch(FMeshBatch& Mesh, TCollector& Collector) const
    {
        Mesh.VertexFactory = &VertexFactory;
        Mesh.MaterialRenderProxy = Material->GetRenderProxy();
        Mesh.ReverseCulling = IsLocalToWorldDeterminantNegative();
        Mesh.Type = PT_TriangleList;
        Mesh.DepthPriorityGroup = SDPG_World;
        Mesh.bCanApplyViewModeOverrides = false;
        auto& Element = Mesh.Elements[0];
        Element.IndexBuffer = &IndexBuffer;
        Element.FirstIndex = 0;
        Element.NumPrimitives = ActiveIndices/3;
        Element.MinVertexIndex = 0;
        Element.MaxVertexIndex = Buffers.PositionVertexBuffer.GetNumVertices()-1;
        auto& Uniform = Collector.template AllocateOneFrameResource<FDynamicPrimitiveUniformBuffer>();
        FPrimitiveUniformShaderParametersBuilder Builder;
        BuildUniformShaderParameters(Builder);
        // This vertex factory has ONE current position stream, not a separate
        // previous-position buffer. Undo the CURRENT storage origin in both
        // matrices; using last packet's origin would invent velocity on rebase.
        if(RenderFrame.Origin!=FVector::ZeroVector)
        {
            FMatrix Previous;
            if(!GetScene().GetPreviousLocalToWorld(GetPrimitiveSceneInfo(),Previous))Previous=GetLocalToWorld();
            FBoxSphereBounds PreSkinned;
            GetPreSkinnedLocalBounds(PreSkinned);
            Builder.LocalToWorld(RenderFrame.Transform(GetLocalToWorld()))
                .PreviousLocalToWorld(RenderFrame.Transform(Previous))
                .LocalBounds(RenderFrame.Bounds(GetLocalBounds()))
                .PreSkinnedLocalBounds(RenderFrame.Bounds(PreSkinned));
        }
        Uniform.Set(Collector.GetRHICommandList(), Builder);
        Element.PrimitiveUniformBufferResource = &Uniform.UniformBuffer;
    }

    void GetDynamicMeshElements(const TArray<const FSceneView*>& Views,
        const FSceneViewFamily& Family, uint32 VisibilityMap, FMeshElementCollector& Collector) const override
    {
        if (bStartupRenderAudit && Family.FrameNumber<8)
        {
            const FMaterial* DrawMaterial=Material->GetRenderProxy()->GetMaterialNoFallback(GetScene().GetFeatureLevel());
            const FMaterialShaderMap* ShaderMap=DrawMaterial ? DrawMaterial->GetRenderingThreadShaderMap() : nullptr;
            UE_LOG(LogTemp,Display,TEXT("STARTUP_WATER_DRAW render_frame=%u mask=%u indices=%d buffers_ready=%d"),
                Family.FrameNumber,VisibilityMap,ActiveIndices,IndexBuffer.IsInitialized() && VertexFactory.IsInitialized());
            UE_LOG(LogTemp,Display,TEXT("STARTUP_WATER_MATERIAL render_frame=%u material_present=%d shader_map=%d complete=%d single_layer_water=%d material=%s"),
                Family.FrameNumber,DrawMaterial!=nullptr,ShaderMap!=nullptr,DrawMaterial && DrawMaterial->IsRenderingThreadShaderMapComplete(),
                DrawMaterial && DrawMaterial->GetShadingModels().HasShadingModel(MSM_SingleLayerWater),DrawMaterial ? *DrawMaterial->GetFriendlyName() : TEXT("none"));
            if (ShaderMap)
            {
                TMap<FShaderId,TShaderRef<FShader>> Shaders;
                ShaderMap->GetShaderList(Shaders);
                for (const auto& Pair:Shaders)
                    if (Pair.Key.VFType==VertexFactory.GetType())
                        UE_LOG(LogTemp,Display,TEXT("STARTUP_WATER_SHADER render_frame=%u type=%s permutation=%d"),
                            Family.FrameNumber,Pair.Key.Type->GetName(),Pair.Key.PermutationId);
            }
        }
        if (!ActiveIndices) return;
        for (int32 View=0; View<Views.Num(); ++View) if (VisibilityMap & (1<<View))
        {
            FMeshBatch& Mesh = Collector.AllocateMesh();
            MakeBatch(Mesh, Collector);
            Collector.AddMesh(View, Mesh);
        }
    }

#if RHI_RAYTRACING
    bool IsRayTracingRelevant() const override { return true; }
    bool HasRayTracingRepresentation() const override { return true; }
    void GetDynamicRayTracingInstances(FRayTracingInstanceCollector& Collector) override
    {
        const auto* Enabled = IConsoleManager::Get().FindTConsoleVariableDataInt(TEXT("r.RayTracing.Geometry.ProceduralMeshes"));
        if (!ActiveIndices || !RayTracingGeometry.IsValid() || (Enabled && !Enabled->GetValueOnRenderThread())) return;
        const auto Views = Collector.GetViews();
        const uint32 Mask = Collector.GetVisibilityMap();
        if (!Mask) return;
        FRayTracingInstance Instance;
        Instance.Geometry = &RayTracingGeometry;
        Instance.InstanceTransforms.Add(RenderFrame.Transform(GetLocalToWorld()));
        FMeshBatch Batch;
        MakeBatch(Batch, Collector);
        Batch.SegmentIndex = 0;
        Batch.CastRayTracedShadow = IsShadowCast(Views[FMath::CountTrailingZeros(Mask)]);
        Instance.Materials.Add(Batch);
        for (int32 View=0; View<Views.Num(); ++View)
            if (Mask & (1<<View)) Collector.AddRayTracingInstance(View, Instance);
    }

    void RebuildRayTracing(FRHICommandListBase& RHICmdList)
    {
        RayTracingGeometry.ReleaseResource();
        if (!ActiveIndices) return;
        FRayTracingGeometryInitializer Init;
        Init.IndexBuffer = IndexBuffer.IndexBufferRHI;
        Init.TotalPrimitiveCount = ActiveIndices/3;
        Init.GeometryType = RTGT_Triangles;
        Init.bFastBuild = true;
        Init.bAllowUpdate = false;
        FRayTracingGeometrySegment Segment;
        Segment.VertexBuffer = Buffers.PositionVertexBuffer.VertexBufferRHI;
        Segment.MaxVertices = Buffers.PositionVertexBuffer.GetNumVertices();
        Segment.NumPrimitives = Init.TotalPrimitiveCount;
        Init.Segments.Add(Segment);
        RayTracingGeometry.SetInitializer(Init);
        RayTracingGeometry.InitResource(RHICmdList);
    }
    FRayTracingGeometry RayTracingGeometry;
#endif
private:
    FStaticMeshVertexBuffers Buffers;
    FDynamicMeshIndexBuffer32 IndexBuffer;
    FLocalVertexFactory VertexFactory;
    UMaterialInterface* Material;
    FMaterialRelevance MaterialRelevance;
    int32 ActiveIndices;
    FRaftSimWaterRenderFrame RenderFrame;
    bool bStartupRenderAudit;
};
}

URaftSimShorelineMeshComponent::URaftSimShorelineMeshComponent()
{
    SetCollisionEnabled(ECollisionEnabled::NoCollision);
    SetCastShadow(false);
    SetCanEverAffectNavigation(false);
    SetMobility(EComponentMobility::Movable);
}

bool URaftSimShorelineMeshComponent::SetWaterMesh(TArray<FProcMeshVertex>&& Vertices,
    TArray<uint32>&& Indices, int32 IndexCapacity)
{
    if (Vertices.IsEmpty() || IndexCapacity <= 0 || IndexCapacity%3 ||
        Indices.Num()%3 || Indices.Num()>IndexCapacity) return false;
    for (uint32 I : Indices) if (I >= uint32(Vertices.Num())) return false;
    FBox NewBounds(ForceInit);
    for (const auto& V : Vertices)
    {
        if (V.Position.ContainsNaN() || V.Normal.ContainsNaN()) return false;
        NewBounds += V.Position;
    }
    if (WaterVertices.IsEmpty()) PrepareStartupWaterShaders(this);
    const bool bShapeChanged = WaterVertices.Num()!=Vertices.Num() || WaterIndexCapacity!=IndexCapacity;
    WaterVertices = MoveTemp(Vertices);
    WaterRenderOrigin=SelectWaterRenderOrigin(WaterVertices[0].Position);
    WaterIndices = MoveTemp(Indices);
    WaterIndexCapacity = IndexCapacity;
    TopologyCache.Reset();
    CrestRefinement.Reset();
    AuditCrestRefinement.Reset();
    CrestSourceVertexCount=WaterVertices.Num();
    bCompactCrestSource=false;
    CellOffsets.Reset();
    bPendingIndexUpdate=true;
    WaterBounds = NewBounds.ExpandBy(500.0); // Conservative bounds for bounded material crests, not extra water.
    UpdateBounds();
    MarkRenderTransformDirty();
    if (bShapeChanged) MarkRenderStateDirty();
    else MarkRenderDynamicDataDirty();
    return true;
}

bool URaftSimShorelineMeshComponent::SetClippedWaterMesh(int32 Nx, int32 Ny,
    TArray<FProcMeshVertex>&& Source, TConstArrayView<uint8> Wet, TConstArrayView<uint8> Available,
    TConstArrayView<float> DepthM, TConstArrayView<float> BedM,const FRaftSimShorelineCrestInput* Crests)
{
    CSV_SCOPED_TIMING_STAT(RaftSimShoreline,SetMesh);
    if (Crests && (Crests->SourceCrestCm.Num()!=Nx*Ny || Crests->SourceShoreWeight.Num()!=Nx*Ny)) return false;
    const int32 BeforeVertices=WaterVertices.Num(), BeforeCapacity=WaterIndexCapacity;
    if (!BeforeVertices) PrepareStartupWaterShaders(this);
    bool bTopologyRebuilt=false;
    auto& BaseVertices=Crests ? ClippedVertices : WaterVertices;
    auto& BaseIndices=Crests ? ClippedIndices : WaterIndices;
    auto& BaseOffsets=Crests ? ClippedCellOffsets : CellOffsets;
    const bool bReviewedSouthFork=GetWorld() && GetWorld()->GetMapName().EndsWith(TEXT("L_SouthForkAmerican_FullReach"));
    {
        CSV_SCOPED_TIMING_STAT(RaftSimShoreline,Topology);
        static const bool bForceOppositeDryFan=FParse::Param(FCommandLine::Get(),TEXT("RaftSimOppositeDryBankFan"));
        static const bool bOriginalBankFan=FParse::Param(FCommandLine::Get(),TEXT("RaftSimOriginalBankFan"));
        // Qualified captured-cell and actual-contact correction for South Fork.
        // Other scenarios remain explicit until their own scene verification.
        const bool bOppositeDryFan=!bOriginalBankFan && (bReviewedSouthFork || bForceOppositeDryFan);
        if(!RaftSimParallelBankAudit::Run(Nx,Ny,Source,Wet,Available,DepthM,BedM,
            Crests!=nullptr,bOppositeDryFan,bReviewedSouthFork))return false;
        if (!TopologyCache.Update(Nx,Ny,MoveTemp(Source),Wet,Available,DepthM,BedM,
            BaseVertices,BaseIndices,BaseOffsets,bTopologyRebuilt,Crests!=nullptr,bOppositeDryFan,bReviewedSouthFork)) return false;
    }
    if (Crests)
    {
        auto& Coarse=CrestWeights.Coarse;
        auto& Shore=CrestWeights.Shore;
        {
            CSV_SCOPED_TIMING_STAT(RaftSimShoreline,CrestInput);
            CrestWeights.Update(BaseVertices.Num(),Crests->SourceCrestCm,
                Crests->SourceShoreWeight,TopologyCache.GetEdges(),TopologyCache.GetCurvedBanks());
        }
        TArray<uint32> NewIndices;
        static const bool ForceCompactSource=FParse::Param(FCommandLine::Get(),TEXT("RaftSimCompactCrestSource"));
        static const bool ReferenceSource=FParse::Param(FCommandLine::Get(),TEXT("RaftSimReferenceCrestSource"));
        // Exact actual-input pairs and ordinary mean frame costs qualify this
        // representation only for South Fork. Other maps retain their source.
        const bool CompactSource=!ReferenceSource && (ForceCompactSource ||
            (GetWorld() && GetWorld()->GetMapName().EndsWith(TEXT("L_SouthForkAmerican_FullReach"))));
        static const bool AuditSource=FParse::Param(FCommandLine::Get(),TEXT("RaftSimCompactCrestSourceAudit"));
        static const bool LegacyDetailEdges=FParse::Param(FCommandLine::Get(),TEXT("RaftSimLegacyDetailEdges"));
        const bool SelectiveDetail=bReviewedSouthFork && !LegacyDetailEdges;
        if(!BeforeVertices)UE_LOG(LogTemp,Display,TEXT("Crest selective detail edges: enabled=%d legacy_override=%d; original shoreline points, profile tolerance and physics retained"),int32(SelectiveDetail),int32(LegacyDetailEdges));
        if(!BeforeVertices)UE_LOG(LogTemp,Display,TEXT("Crest source publication: compact=%d reference_override=%d"),int32(CompactSource),int32(ReferenceSource));
        const auto UpdateCrests=[&](bool Compact,FRaftSimShorelineCrests& State,
            TArray<FProcMeshVertex>& Out,TArray<uint32>& OutIndices,TArray<int32>& Offsets)
        {
            if(Compact)
            {
                {
                    CSV_SCOPED_TIMING_STAT(RaftSimShoreline,CrestSourceGather);
                    if(!ReferencedCrestSource.Update(BaseVertices,BaseIndices,Coarse,Shore))return false;
                }
                return State.Update(ReferencedCrestSource.Vertices,ReferencedCrestSource.Indices,
                    BaseOffsets,ReferencedCrestSource.Coarse,ReferencedCrestSource.Shore,*Crests,
                    Out,OutIndices,Offsets,SelectiveDetail);
            }
            return State.Update(BaseVertices,BaseIndices,BaseOffsets,Coarse,Shore,*Crests,
                Out,OutIndices,Offsets,SelectiveDetail);
        };
        if(AuditSource)
        {
            double Times[2]={};bool Valid=true;
            const auto Run=[&](bool Compact)
            {
                const bool Selected=Compact==CompactSource;
                const double Begin=FPlatformTime::Seconds();
                Valid &= UpdateCrests(Compact,Selected ? CrestRefinement : AuditCrestRefinement,
                    Selected ? WaterVertices : AuditCrestVertices,
                    Selected ? NewIndices : AuditCrestIndices,Selected ? CellOffsets : AuditCrestOffsets);
                Times[int32(Compact)]=(FPlatformTime::Seconds()-Begin)*1000.;
            };
            // Both evolving histories see every publication, from startup.
            const bool CandidateFirst=(GFrameCounter/2)%2!=0;
            Run(CandidateFirst);Run(!CandidateFirst);
            bool Exact=Valid && NewIndices.Num()==AuditCrestIndices.Num() && CellOffsets==AuditCrestOffsets;
            for(int32 I=0;Exact && I<NewIndices.Num();++I)
                Exact=FRaftSimCrestMidpointExpansion::EqualAttributes(
                    WaterVertices[NewIndices[I]],AuditCrestVertices[AuditCrestIndices[I]]);
            const auto& A=CrestRefinement.GetRenderedCorrectionsCm();
            const auto& B=AuditCrestRefinement.GetRenderedCorrectionsCm();
            for(int32 I=0;Exact && I<NewIndices.Num();++I)Exact=A[NewIndices[I]]==B[AuditCrestIndices[I]];
            const auto& TA=CrestRefinement.GetTargetCorrectionsCm();
            const auto& TB=AuditCrestRefinement.GetTargetCorrectionsCm();
            for(int32 I=0;Exact && I<NewIndices.Num();++I)Exact=TA[NewIndices[I]]==TB[AuditCrestIndices[I]];
            if(!Exact){UE_LOG(LogTemp,Error,TEXT("CompactCrestSource mismatch frame=%llu"),GFrameCounter);return false;}
            if(GFrameCounter>=120 && GFrameCounter<184)
                UE_LOG(LogTemp,Display,TEXT("CompactCrestSourcePair frame=%llu exact=%d candidate_first=%d source=%d compact=%d indices=%d reference_ms=%.9f candidate_ms=%.9f"),
                    GFrameCounter,int32(Exact),int32(CandidateFirst),BaseVertices.Num(),ReferencedCrestSource.Vertices.Num(),NewIndices.Num(),Times[0],Times[1]);
        }
        else if(!UpdateCrests(CompactSource,CrestRefinement,WaterVertices,NewIndices,CellOffsets))return false;
        {
        CSV_SCOPED_TIMING_STAT(RaftSimShoreline,OutputStorage);
        bCompactCrestSource=CompactSource;
        CrestSourceVertexCount=CompactSource ? ReferencedCrestSource.Vertices.Num() : BaseVertices.Num();
        bTopologyRebuilt|=WaterIndices!=NewIndices;
        WaterIndices=MoveTemp(NewIndices);
        ActiveVertexCount=WaterVertices.Num();
        // Grow reserve only when required; never cap geometry to fit a budget.
        const int32 Capacity=ActiveVertexCount>BeforeVertices
            ? Align(ActiveVertexCount+ActiveVertexCount/8,4096) : BeforeVertices;
        WaterVertices.SetNum(Capacity);
        for (int32 I=ActiveVertexCount; I<Capacity; ++I) WaterVertices[I]=BaseVertices[0];
        }
    }
    else
    {
        ActiveVertexCount=WaterVertices.Num();
        CrestSourceVertexCount=WaterVertices.Num();
        bCompactCrestSource=false;
    }
    CSV_SCOPED_TIMING_STAT(RaftSimShoreline,BoundsAndNotify);
    WaterIndexCapacity=FMath::Max3(BeforeCapacity,(Nx-1)*(Ny-1)*12,
        FMath::DivideAndRoundUp(WaterIndices.Num(),12)*12);
    // Every referenced shore node lies within the XY hull of its two source
    // points and at its wet source's Z. Reserve nodes never contribute bounds.
    const TConstArrayView<FProcMeshVertex> BoundsSource(BaseVertices.GetData(),Nx*Ny);
    static const bool bForceParallelBounds=FParse::Param(FCommandLine::Get(),TEXT("RaftSimParallelWaterBounds"));
    static const bool bSerialBounds=FParse::Param(FCommandLine::Get(),TEXT("RaftSimSerialWaterBounds"));
    // Exact native/live pairs and both orders of whole-frame controls qualify
    // the South Fork normal scene. Other scenes retain the original default.
    const bool bParallelBounds=!bSerialBounds && (bForceParallelBounds ||
        (GetWorld() && GetWorld()->GetMapName().EndsWith(TEXT("L_SouthForkAmerican_FullReach"))));
    if (!BeforeVertices) UE_LOG(LogTemp,Display,TEXT("WaterBoundsMode parallel=%d serial_override=%d"),
        int32(bParallelBounds),int32(bSerialBounds));
    static const bool bBoundsAudit=FParse::Param(FCommandLine::Get(),TEXT("RaftSimWaterBoundsAudit"));
    FBox SourceBounds(ForceInit);
    if (bBoundsAudit && GFrameCounter>=120 && GFrameCounter<184)
    {
        FBox Results[2]; double Times[2];
        const bool CandidateFirst=(GFrameCounter/2)%2!=0;
        for (int32 Order=0; Order<2; ++Order)
        {
            const int32 Kind=(Order+int32(CandidateFirst))%2;
            const double Start=FPlatformTime::Seconds();
            Results[Kind]=Kind ? RaftSimWaterSourceBounds::Parallel(BoundsSource)
                : RaftSimWaterSourceBounds::Reference(BoundsSource);
            Times[Kind]=(FPlatformTime::Seconds()-Start)*1000.;
        }
        const bool Exact=Results[0].IsValid==Results[1].IsValid &&
            Results[0].Min==Results[1].Min && Results[0].Max==Results[1].Max;
        UE_LOG(LogTemp,Display,TEXT("WaterBoundsPair frame=%llu exact=%d candidate_first=%d vertices=%d reference_ms=%.9f candidate_ms=%.9f"),
            GFrameCounter,int32(Exact),int32(CandidateFirst),BoundsSource.Num(),Times[0],Times[1]);
        if (!Exact) { UE_LOG(LogTemp,Error,TEXT("Water source bounds mismatch")); return false; }
        SourceBounds=Results[int32(bParallelBounds)];
    }
    else SourceBounds=bParallelBounds ? RaftSimWaterSourceBounds::Parallel(BoundsSource)
        : RaftSimWaterSourceBounds::Reference(BoundsSource);
    WaterBounds=SourceBounds.ExpandBy(500.0);
    WaterRenderOrigin=SelectWaterRenderOrigin(BaseVertices[0].Position);
    bPendingIndexUpdate|=bTopologyRebuilt;
    UpdateBounds();
    MarkRenderTransformDirty();
    if (BeforeVertices!=WaterVertices.Num() || BeforeCapacity!=WaterIndexCapacity) MarkRenderStateDirty();
    else MarkRenderDynamicDataDirty();
    return true;
}

FPrimitiveSceneProxy* URaftSimShorelineMeshComponent::CreateSceneProxy()
{
    return WaterVertices.IsEmpty() || WaterIndexCapacity<=0 ? nullptr : new FShorelineSceneProxy(this);
}

FBoxSphereBounds URaftSimShorelineMeshComponent::CalcBounds(const FTransform& Transform) const
{
    return WaterBounds.IsValid ? FBoxSphereBounds(WaterBounds).TransformBy(Transform)
        : FBoxSphereBounds(FVector::ZeroVector, FVector::ZeroVector, 0).TransformBy(Transform);
}

void URaftSimShorelineMeshComponent::SendRenderDynamicData_Concurrent()
{
    Super::SendRenderDynamicData_Concurrent();
    if (auto* Proxy = static_cast<FShorelineSceneProxy*>(SceneProxy))
    {
        const bool bIndicesChanged=bPendingIndexUpdate;
        static const bool bOriginalRemap=FParse::Param(FCommandLine::Get(),TEXT("RaftSimOriginalUploadRemap"));
        // Exact index-order equality is already checked by the topology owner.
        // Cache membership only; every active vertex attribute is rebuilt now.
        const bool bReuse=!bOriginalRemap && bHasRenderVertexSources && !bIndicesChanged;
        // Exact actual-game pairs qualify this in both execution orders.
        static const bool bParallelValues=!FParse::Param(FCommandLine::Get(),TEXT("RaftSimSerialRenderValues"));
        static const bool bPair=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRenderValuesAudit"));
        if (bPair && GFrameCounter>=120 && GFrameCounter<184)
        {
            FShorelineRenderPacket P[2];double Seconds[2];
            for (int32 Order=0;Order<2;++Order)
            {
                const int32 Kind=(Order+int32(GFrameCounter%2))%2;
                auto Mapping=RenderVertexSources;
                const double Start=FPlatformTime::Seconds();
                P[Kind]=MakeRenderPacket(WaterVertices,WaterIndices,bIndicesChanged,&Mapping,bReuse,Kind==1,WaterRenderOrigin);
                Seconds[Kind]=FPlatformTime::Seconds()-Start;
            }
            UE_LOG(LogTemp,Display,TEXT("RENDER_VALUES_PAIR frame=%llu original_first=%d reuse=%d vertices=%d exact=%d original_ms=%.9f candidate_ms=%.9f"),
                GFrameCounter,GFrameCounter%2==0,bReuse,P[0].Vertices.Num(),SameRenderPacket(P[0],P[1]),Seconds[0]*1000.,Seconds[1]*1000.);
        }
        auto Packet=MakeRenderPacket(WaterVertices,WaterIndices,bIndicesChanged,
            &RenderVertexSources,bReuse,bParallelValues,WaterRenderOrigin);
        static const bool bFrameAudit=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRenderFrameAudit"));
        if(bFrameAudit && GFrameCounter>=120 && GFrameCounter<184)
        {
            FRaftSimWaterRenderFrame Frame{Packet.RenderOrigin};double Error=0.,OriginalError=0.;
            for(int32 I=0;I<Packet.Vertices.Num();++I)
            {
                const auto& Source=WaterVertices[RenderVertexSources[I]].Position;
                const FVector Restored=Frame.Restore(Packet.Vertices[I].Position);
                const FVector Direct=FVector(FVector3f(Source));
                Error=FMath::Max(Error,FVector2D(Restored-Source).Size());
                OriginalError=FMath::Max(OriginalError,FVector2D(Direct-Source).Size());
            }
            UE_LOG(LogTemp,Display,TEXT("WATER_RENDER_FRAME_PACKET frame=%llu vertices=%d origin=(%.17g,%.17g,%.17g) xy_error_cm=%.17g direct_error_cm=%.17g"),
                GFrameCounter,Packet.Vertices.Num(),Frame.Origin.X,Frame.Origin.Y,Frame.Origin.Z,Error,OriginalError);
            if(Error>.005)UE_LOG(LogTemp,Error,TEXT("Rebased water buffer XY error exceeds0.005cm; candidate not accepted"));
        }
        bHasRenderVertexSources=true;
        static const bool bTiming=FParse::Param(FCommandLine::Get(),TEXT("RaftSimWaterStageTimings"));
        if (bTiming) UE_LOG(LogTemp,Display,TEXT("WaterUpload frame=%llu source_vertices=%d upload_vertices=%d indices=%d index_update=%d"),
            GFrameCounter,WaterVertices.Num(),Packet.Vertices.Num(),WaterIndices.Num(),bIndicesChanged ? 1 : 0);
        ENQUEUE_RENDER_COMMAND(RaftSimUpdateShoreline)(
            [Proxy, Vertices=MoveTemp(Packet.Vertices), Indices=MoveTemp(Packet.Indices), bIndicesChanged, Origin=Packet.RenderOrigin](FRHICommandListImmediate& RHICmdList)
            { Proxy->Update(RHICmdList, Vertices, Indices, bIndicesChanged,Origin); });
        bPendingIndexUpdate=false;
    }
}

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimShorelineRenderFrameTest,"RaftSim.M4.ShorelineRenderFrame",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimShorelineRenderFrameTest::RunTest(const FString&)
{
    const FVector ModeProbe(-551000.,-348600.,123.);
    const bool Legacy=FParse::Param(FCommandLine::Get(),TEXT("RaftSimLegacyShorelineCoordinates"));
    TestTrue(TEXT("normal frame enabled without candidate flag; legacy override explicit"),
        SelectWaterRenderOrigin(ModeProbe)==(Legacy ? FVector::ZeroVector : FVector(ModeProbe.X,ModeProbe.Y,0.)));
    TArray<FProcMeshVertex> Source;TArray<uint32> Indices,Mapping;
    for(int32 I=0;I<1025;++I)
    {
        FProcMeshVertex V;V.Position=FVector(-551000.+(I%33)*100.+.01234567,-348600.-(I/33)*100.-.02345678,812.345+I*.001);
        V.Normal=FVector(.2,.3,1.).GetSafeNormal();V.Color=FColor(I%251,83,147,217);
        V.Tangent=FProcMeshTangent(FVector(1.,.2,.1).GetSafeNormal(),I%2!=0);
        V.UV0=FVector2D(I*.007,1.);V.UV1=FVector2D(-2.7,3.1);V.UV2=FVector2D(.17,.91);V.UV3=FVector2D(.35,-.6);
        Source.Add(V);Indices.Add(I);if(I%7==0)Indices.Add(I);
    }
    const auto Original=MakeRenderPacket(Source,Indices,true,&Mapping);
    const FVector Origins[]={FVector(-551000.,-348600.,0.),FVector(-549976.,-349624.,0.),FVector(-550000.,-350000.,0.)};
    const FMatrix Transforms[]={FMatrix::Identity,
        FTransform(FRotator(0.,37.,0.),FVector(412345.,-271000.,15.),FVector(1.2,-.8,1.)).ToMatrixWithScale()};
    double Worst=0.,DirectWorst=0.;
    for(const auto& Origin:Origins)
    {
        const FRaftSimWaterRenderFrame Frame{Origin};
        const auto First=MakeRenderPacket(Source,Indices,true,nullptr,false,false,Origin);
        TestTrue(TEXT("rebasing preserves all index order"),First.Indices==Original.Indices);
        const auto Serial=MakeRenderPacket(Source,Indices,false,&Mapping,true,false,Origin);
        const auto Parallel=MakeRenderPacket(Source,Indices,false,&Mapping,true,true,Origin);
        TestTrue(TEXT("frame and packed attributes identical across scheduling"),SameRenderPacket(Serial,Parallel));
        for(int32 I=0;I<First.Vertices.Num();++I)
        {
            auto A=First.Vertices[I],B=Original.Vertices[I];
            const auto& P=Source[Mapping[I]].Position;const FVector Restored=Frame.Restore(A.Position);
            Worst=FMath::Max(Worst,FVector2D(Restored-P).Size());
            DirectWorst=FMath::Max(DirectWorst,FVector2D(FVector(B.Position)-P).Size());
            B.Position=A.Position;
            FShorelineRenderPacket PA,PB;PA.Vertices.Add(A);PB.Vertices.Add(B);
            if(!TestTrue(TEXT("rebasing changes no color, UV, tangent or normal bits"),SameRenderPacket(PA,PB)))return false;
            for(const auto& Transform:Transforms)
            {
                const FVector GPU=Frame.Transform(Transform).TransformPosition(FVector(A.Position));
                TestTrue(TEXT("raster/ray transform restores the original component frame"),GPU.Equals(Transform.TransformPosition(Restored),1.e-7));
                // Both previous and current matrices consume the same current
                // vertex stream, even when its storage origin changed.
                TestTrue(TEXT("origin change cannot invent component motion"),GPU.Equals(Transform.TransformPosition(P),.005));
            }
        }
        const FBoxSphereBounds Bounds(FVector(-550000.,-350000.,850.),FVector(3000.,3000.,100.),4300.);
        const auto Local=Frame.Bounds(Bounds);
        TestTrue(TEXT("local bounds are shifted without changing the world extent"),
            Local.Origin+Origin==Bounds.Origin && Local.BoxExtent==Bounds.BoxExtent && Local.SphereRadius==Bounds.SphereRadius);
        const auto Dry=MakeRenderPacket(Source,{},true,nullptr,false,false,Origin);
        TestTrue(TEXT("dry packets retain their frame but no stale geometry"),Dry.RenderOrigin==Origin && Dry.Vertices.IsEmpty() && Dry.Indices.IsEmpty());
    }
    TestTrue(TEXT("rebased buffer precision bound"),Worst<.005);
    TestTrue(TEXT("actual loss of precision reduced"),Worst<DirectWorst*.1);
    AddInfo(FString::Printf(TEXT("WaterRenderFrame max_xy_error_cm=%.17g direct_error_cm=%.17g"),Worst,DirectWorst));
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimShorelineParallelValuesTest,"RaftSim.M4.ShorelineParallelValues",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimShorelineParallelValuesTest::RunTest(const FString&)
{
    for (int32 Count:{0,1,1023,1024,1025,65536})
    {
        TArray<FProcMeshVertex> Source;Source.SetNum(Count);
        TArray<uint32> Indices;
        for (int32 I=Count-1;I>=0;--I)
        {
            auto& V=Source[I];V.Position=FVector(I*.37,-I*.19,I*.071);
            V.Normal=FVector(.2,.3,.9).GetSafeNormal();V.Color=FColor(I%251,83,147,217);
            V.Tangent=FProcMeshTangent(FVector(.9,-.2,.1).GetSafeNormal(),I%2!=0);
            V.UV0=FVector2D(I*.007,1.);V.UV1=FVector2D(-2.7,3.1);
            V.UV2=FVector2D(.17,.91);V.UV3=FVector2D(.35,-.6);
            Indices.Add(I);if (I%7==0) Indices.Add(I);
        }
        TArray<uint32> Mapping;
        MakeRenderPacket(Source,Indices,true,&Mapping);
        for (int32 Epoch=0;Epoch<3;++Epoch)
        {
            for (auto& V:Source) {V.Position.Z+=.031;V.UV3.X-=.015;V.Tangent.bFlipTangentY=!V.Tangent.bFlipTangentY;}
            const auto Serial=MakeRenderPacket(Source,Indices,false,&Mapping,true,false);
            const auto Parallel=MakeRenderPacket(Source,Indices,false,&Mapping,true,true);
            TestTrue(TEXT("all current packed attributes and source order match"),SameRenderPacket(Serial,Parallel));
        }
        MakeRenderPacket(Source,{},true,&Mapping);
        const auto Dry=MakeRenderPacket(Source,{},false,&Mapping,true,true);
        TestTrue(TEXT("dry cache emits no stale vertices"),Dry.Vertices.IsEmpty());
    }
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimShorelineCompactUploadTest,"RaftSim.M4.ShorelineCompactUpload",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimShorelineCompactUploadTest::RunTest(const FString&)
{
    TArray<FProcMeshVertex> Source; Source.SetNum(65536);
    const TArray<uint32> Original={65535,17,901,901,17,49000};
    for (uint32 I:Original)
    {
        auto& V=Source[I]; V.Position=FVector(I*.137,I*-.293,I*.013);
        V.Normal=FVector(.2,.3,.9).GetSafeNormal(); V.Color=FColor(I%251,83,147,217);
        V.Tangent=FProcMeshTangent(FVector(.9,-.2,.1).GetSafeNormal(),I%2!=0);
        V.UV0=FVector2D(I*.007,1.); V.UV1=FVector2D(-2.7,3.1);
        V.UV2=FVector2D(.17,.91); V.UV3=FVector2D(.35,-.6);
    }
    Source[49000].Position=Source[17].Position; // Coincident vertices keep distinct attributes.
    const auto Packet=MakeRenderPacket(Source,Original,true);
    TestEqual(TEXT("only referenced vertices are uploaded"),Packet.Vertices.Num(),4);
    TestTrue(TEXT("triangle and winding order is preserved"),Packet.Indices==TArray<uint32>({0,1,2,2,1,3}));
    const auto Equal=[](const FDynamicMeshVertex& A,const FDynamicMeshVertex& B)
    {
        bool Same=A.Position==B.Position && A.Color==B.Color &&
            A.TangentX.ToFVector3f()==B.TangentX.ToFVector3f() &&
            A.TangentZ.ToFVector3f()==B.TangentZ.ToFVector3f() && A.TangentZ.Vector.W==B.TangentZ.Vector.W;
        for (int32 UV=0; UV<4; ++UV) Same &= A.TextureCoordinate[UV]==B.TextureCoordinate[UV];
        return Same;
    };
    for (int32 I=0; I<Original.Num(); ++I)
        TestTrue(TEXT("every rendered corner preserves position, packed normals, color and four UV channels"),
            Equal(Packet.Vertices[Packet.Indices[I]],RenderVertex(Source[Original[I]])));
    Source[901].Position.Z+=.731; Source[901].UV1.X-=.91;
    const auto Dynamic=MakeRenderPacket(Source,Original,false);
    TestTrue(TEXT("value-only update does not require index upload"),Dynamic.Indices.IsEmpty());
    for (int32 I=0; I<Original.Num(); ++I)
        TestTrue(TEXT("value-only dense ordering matches retained GPU indices"),
            Equal(Dynamic.Vertices[Packet.Indices[I]],RenderVertex(Source[Original[I]])));
    const auto Dry=MakeRenderPacket(Source,{},true);
    TestTrue(TEXT("dry mesh uploads no stale vertices or indices"),Dry.Vertices.IsEmpty() && Dry.Indices.IsEmpty());
    const TArray<uint32> Rewet={901,49000,17,65535,901,17};
    const auto WetAgain=MakeRenderPacket(Source,Rewet,true);
    for (int32 I=0; I<Rewet.Num(); ++I)
        TestTrue(TEXT("rewet/reordered topology remaps each current corner exactly"),
            Equal(WetAgain.Vertices[WetAgain.Indices[I]],RenderVertex(Source[Rewet[I]])));
    TArray<uint32> DenseSources;
    const auto CachedInitial=MakeRenderPacket(Source,Original,true,&DenseSources);
    TestTrue(TEXT("cache retains exact first-occurrence source order"),
        DenseSources==TArray<uint32>({65535,17,901,49000}));
    Source[17].Color=FColor(17,49,71,103); Source[65535].UV3.Y+=.125;
    Source[49000].Position.Z+=.875;
    const auto CachedValues=MakeRenderPacket(Source,Original,false,&DenseSources,true);
    TestTrue(TEXT("cached membership does not upload unchanged indices"),CachedValues.Indices.IsEmpty());
    for (int32 I=0; I<Original.Num(); ++I)
        TestTrue(TEXT("cached value update refreshes every current attribute exactly"),
            Equal(CachedValues.Vertices[CachedInitial.Indices[I]],RenderVertex(Source[Original[I]])));
    const auto CachedDry=MakeRenderPacket(Source,{},true,&DenseSources);
    const auto StillDry=MakeRenderPacket(Source,{},false,&DenseSources,true);
    TestTrue(TEXT("dry topology clears cached membership and stays empty"),
        DenseSources.IsEmpty() && CachedDry.Vertices.IsEmpty() && StillDry.Vertices.IsEmpty());
    const auto CachedRewet=MakeRenderPacket(Source,Rewet,true,&DenseSources);
    const auto RewetValues=MakeRenderPacket(Source,Rewet,false,&DenseSources,true);
    TestTrue(TEXT("rewet cache rebuild preserves exact current indices"),CachedRewet.Indices==WetAgain.Indices);
    for (int32 I=0; I<Rewet.Num(); ++I)
        TestTrue(TEXT("rewet cached source ordering matches the rebuilt index buffer"),
            Equal(RewetValues.Vertices[CachedRewet.Indices[I]],RenderVertex(Source[Rewet[I]])));
    return !HasAnyErrors();
}
#endif
