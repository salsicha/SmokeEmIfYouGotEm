#include "RaftSimShorelineMeshComponent.h"
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
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Engine/World.h"
#include "ProfilingDebugging/CsvProfiler.h"

CSV_DEFINE_CATEGORY(RaftSimShoreline,true);

namespace
{
FDynamicMeshVertex RenderVertex(const FProcMeshVertex& V)
{
    FDynamicMeshVertex Out;
    Out.Position = FVector3f(V.Position);
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
    TArray<FDynamicMeshVertex> Vertices;
    TArray<uint32> Indices;
};

FShorelineRenderPacket MakeRenderPacket(const TArray<FProcMeshVertex>& Source,
    const TArray<uint32>& SourceIndices,bool bIncludeIndices,
    TArray<uint32>* DenseSources=nullptr,bool bReuseMapping=false)
{
    CSV_SCOPED_TIMING_STAT(RaftSimShoreline,RenderPacket);
    FShorelineRenderPacket Packet;
    if (bReuseMapping)
    {
        check(DenseSources && !bIncludeIndices);
        Packet.Vertices.Reserve(DenseSources->Num());
        for (uint32 I:*DenseSources) Packet.Vertices.Add(RenderVertex(Source[I]));
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
            Dense=Packet.Vertices.Add(RenderVertex(Source[I]));
            if (DenseSources) DenseSources->Add(I);
        }
        if (bIncludeIndices) Packet.Indices.Add(uint32(Dense));
    }
    // No coordinate welding, triangle removal or attribute interpolation.
    // Identical index order yields an identical remap when only values change.
    return Packet;
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
        , bStartupRenderAudit(FParse::Param(FCommandLine::Get(),TEXT("RaftSimStartupRenderAudit")))
    {
        if (!Material) Material = UMaterial::GetDefaultMaterial(MD_Surface);
        if (bStartupRenderAudit && GFrameCounter<8)
            UE_LOG(LogTemp,Display,TEXT("STARTUP_WATER_PROXY game_frame=%llu indices=%d visible=%d material=%s bounds=%s"),
                GFrameCounter,ActiveIndices,Component->IsVisible(),*Material->GetPathName(),*Component->Bounds.ToString());
        const auto Packet=MakeRenderPacket(Component->GetWaterVertices(),Component->GetWaterIndices(),true);
        TArray<FDynamicMeshVertex> Vertices;
        // Retain worst-case allocation and dry/rewet proxy stability, but draw
        // and subsequently upload only the exact referenced dense prefix.
        Vertices.Init(RenderVertex(Component->GetWaterVertices()[0]),Component->GetWaterVertices().Num());
        for (int32 I=0; I<Packet.Vertices.Num(); ++I) Vertices[I]=Packet.Vertices[I];
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
        const TArray<uint32>& Indices, bool bIndicesChanged)
    {
        check(IsInRenderingThread());
        check(uint32(Vertices.Num()) <= Buffers.PositionVertexBuffer.GetNumVertices());
        check(Indices.Num() <= IndexBuffer.Indices.Num());
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
                    if (Pair.Key.VFType==VertexFactory.GetType() && FString(Pair.Key.Type->GetName()).Contains(TEXT("BasePass")))
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
        Instance.InstanceTransforms.Add(GetLocalToWorld());
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
    const bool bShapeChanged = WaterVertices.Num()!=Vertices.Num() || WaterIndexCapacity!=IndexCapacity;
    WaterVertices = MoveTemp(Vertices);
    WaterIndices = MoveTemp(Indices);
    WaterIndexCapacity = IndexCapacity;
    TopologyCache.Reset();
    CrestRefinement.Reset();
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
    bool bTopologyRebuilt=false;
    auto& BaseVertices=Crests ? ClippedVertices : WaterVertices;
    auto& BaseIndices=Crests ? ClippedIndices : WaterIndices;
    auto& BaseOffsets=Crests ? ClippedCellOffsets : CellOffsets;
    {
        CSV_SCOPED_TIMING_STAT(RaftSimShoreline,Topology);
        static const bool bForceOppositeDryFan=FParse::Param(FCommandLine::Get(),TEXT("RaftSimOppositeDryBankFan"));
        static const bool bOriginalBankFan=FParse::Param(FCommandLine::Get(),TEXT("RaftSimOriginalBankFan"));
        // Qualified captured-cell and actual-contact correction for South Fork.
        // Other scenarios remain explicit until their own scene verification.
        const bool bReviewedSouthFork=GetWorld() && GetWorld()->GetMapName().EndsWith(TEXT("L_SouthForkAmerican_FullReach"));
        const bool bOppositeDryFan=!bOriginalBankFan && (bReviewedSouthFork || bForceOppositeDryFan);
        if (!TopologyCache.Update(Nx,Ny,MoveTemp(Source),Wet,Available,DepthM,BedM,
            BaseVertices,BaseIndices,BaseOffsets,bTopologyRebuilt,Crests!=nullptr,bOppositeDryFan)) return false;
    }
    if (Crests)
    {
        TArray<float> Coarse,Shore;
        {
            CSV_SCOPED_TIMING_STAT(RaftSimShoreline,CrestInput);
            Coarse.Init(0,BaseVertices.Num()); Shore.Init(0,BaseVertices.Num());
            for (int32 I=0; I<Nx*Ny; ++I)
            { Coarse[I]=Crests->SourceCrestCm[I]; Shore[I]=Crests->SourceShoreWeight[I]; }
            for (const auto& E:TopologyCache.GetEdges())
            { Coarse[E.Node]=Coarse[E.WetVertex]; Shore[E.Node]=Shore[E.WetVertex]; }
        }
        TArray<uint32> NewIndices;
        if (!CrestRefinement.Update(BaseVertices,BaseIndices,BaseOffsets,Coarse,Shore,*Crests,
            WaterVertices,NewIndices,CellOffsets)) return false;
        bTopologyRebuilt|=WaterIndices!=NewIndices;
        WaterIndices=MoveTemp(NewIndices);
        ActiveVertexCount=WaterVertices.Num();
        // Grow reserve only when required; never cap geometry to fit a budget.
        const int32 Capacity=ActiveVertexCount>BeforeVertices
            ? Align(ActiveVertexCount+ActiveVertexCount/8,4096) : BeforeVertices;
        WaterVertices.SetNum(Capacity);
        for (int32 I=ActiveVertexCount; I<Capacity; ++I) WaterVertices[I]=BaseVertices[0];
    }
    else ActiveVertexCount=WaterVertices.Num();
    WaterIndexCapacity=FMath::Max3(BeforeCapacity,(Nx-1)*(Ny-1)*12,
        FMath::DivideAndRoundUp(WaterIndices.Num(),12)*12);
    // Every referenced shore node lies within the XY hull of its two source
    // points and at its wet source's Z. Reserve nodes never contribute bounds.
    FBox SourceBounds(ForceInit);
    for (int32 I=0; I<Nx*Ny; ++I) SourceBounds+=BaseVertices[I].Position;
    WaterBounds=SourceBounds.ExpandBy(500.0);
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
        auto Packet=MakeRenderPacket(WaterVertices,WaterIndices,bIndicesChanged,
            &RenderVertexSources,!bOriginalRemap && bHasRenderVertexSources && !bIndicesChanged);
        bHasRenderVertexSources=true;
        static const bool bTiming=FParse::Param(FCommandLine::Get(),TEXT("RaftSimWaterStageTimings"));
        if (bTiming) UE_LOG(LogTemp,Display,TEXT("WaterUpload frame=%llu source_vertices=%d upload_vertices=%d indices=%d index_update=%d"),
            GFrameCounter,WaterVertices.Num(),Packet.Vertices.Num(),WaterIndices.Num(),bIndicesChanged ? 1 : 0);
        ENQUEUE_RENDER_COMMAND(RaftSimUpdateShoreline)(
            [Proxy, Vertices=MoveTemp(Packet.Vertices), Indices=MoveTemp(Packet.Indices), bIndicesChanged](FRHICommandListImmediate& RHICmdList)
            { Proxy->Update(RHICmdList, Vertices, Indices, bIndicesChanged); });
        bPendingIndexUpdate=false;
    }
}

#if WITH_AUTOMATION_TESTS
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
