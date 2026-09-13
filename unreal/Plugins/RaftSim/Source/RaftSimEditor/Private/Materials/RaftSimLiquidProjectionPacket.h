#pragma once
#include "RenderGraphUtils.h"
#include "RHIGPUReadback.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Dom/JsonObject.h"

// Optional, one-step diagnostic copies. Never reads a later tick's CurrentData
// as if it were paired with the selected native particle/transfer packet.
struct FRaftSimLiquidProjectionPacket
{
    bool AdvectionRequested=false;
    TRefCountPtr<IPooledRenderTarget> Fields[6];
    uint32 Steps[6]={0,0,0,0,0,0};
    static constexpr const TCHAR* Names[]={TEXT("projection_boundary"),TEXT("projection_velocity_before"),
        TEXT("projection_divergence"),TEXT("projection_pressure"),TEXT("projection_velocity_after"),TEXT("advection_velocity")};

    bool Capture(FRDGBuilder& Graph,FRDGTextureRef Source,int32 Field,uint32 Step,FString& Error)
    {
        if(!Source || Field<0 || Field>=(AdvectionRequested?6:5) || Fields[Field] || Steps[Field] || !Step)
        { Error=TEXT("Invalid or repeated same-step projection snapshot");return false; }
        const auto Format=Source->Desc.Format;
        const bool Vector=Field<2 || Field>=4;
        if((Vector && Format!=PF_FloatRGBA) || (!Vector && Format!=PF_R32_FLOAT && Format!=PF_R16F))
        { Error=TEXT("Unsupported native projection snapshot precision");return false; }
        auto Copy=Graph.CreateTexture(Source->Desc,TEXT("LiquidProjection.SameStepSnapshot"));
        AddCopyTexturePass(Graph,Source,Copy);Graph.QueueTextureExtraction(Copy,&Fields[Field]);
        Steps[Field]=Step;return true;
    }

    bool Save(FRHICommandListImmediate& Cmd,const FString& Directory,int32 Owner,FIntVector Cells,
        uint32 ExpectedStep,TSharedPtr<FJsonObject> Record,FString& Error) const
    {
        for(int32 I=0;I<(AdvectionRequested?6:5);++I)
        {
            if(!Fields[I] || Steps[I]!=ExpectedStep)
            { Error=TEXT("Projection packet missing a field from the selected native step");return false; }
            auto* Texture=Fields[I]->GetRHI();const auto& Desc=Texture->GetDesc();
            if(Desc.Extent!=FIntPoint(Cells.X,Cells.Y) || Desc.Depth!=Cells.Z)
            { Error=TEXT("Projection packet extent mismatch");return false; }
            const uint32 Stride=Desc.Format==PF_FloatRGBA?8:Desc.Format==PF_R16F?2:4;
            TArray<uint8> Bytes;Bytes.SetNumUninitialized(Cells.X*Cells.Y*Cells.Z*Stride);
            Cmd.Transition(FRHITransitionInfo(Texture,ERHIAccess::Unknown,ERHIAccess::CopySrc));
            for(int32 Z=0;Z<Cells.Z;++Z)
            {
                FRHIGPUTextureReadback Read(TEXT("LiquidProjection.SameStepRead"));
                Read.EnqueueCopy(Cmd,Texture,FIntVector(0,0,Z),0,FIntVector(Cells.X,Cells.Y,1));
                Cmd.SubmitAndBlockUntilGPUIdle();int32 Pitch=0;
                const auto* Data=static_cast<const uint8*>(Read.Lock(Pitch));
                if(!Data || Pitch<Cells.X)
                { if(Data) Read.Unlock();Error=TEXT("Projection packet readback unavailable");return false; }
                for(int32 Y=0;Y<Cells.Y;++Y)
                    FMemory::Memcpy(Bytes.GetData()+(Z*Cells.Y+Y)*Cells.X*Stride,Data+Y*Pitch*Stride,Cells.X*Stride);
                Read.Unlock();
            }
            const FString Name=FString::Printf(TEXT("p2g-%03d-%s.bin"),Owner,Names[I]);
            if(FPaths::FileExists(Directory/Name) || !FFileHelper::SaveArrayToFile(Bytes,*(Directory/Name)))
            { Error=TEXT("Could not save unique projection packet");return false; }
            Record->SetStringField(Names[I],Name);
            Record->SetStringField(FString(Names[I])+TEXT("_format"),Desc.Format==PF_FloatRGBA?TEXT("rgba16f"):Desc.Format==PF_R16F?TEXT("r16f"):TEXT("r32f"));
        }
        Record->SetNumberField(TEXT("projection_native_step"),ExpectedStep);
        Record->SetStringField(TEXT("projection_input_stage"),TEXT("Compute Divergence: after stage"));
        Record->SetStringField(TEXT("projection_pressure_stage"),TEXT("Solve Pressure: after final iteration and halo exchange"));
        Record->SetStringField(TEXT("projection_output_stage"),TEXT("Project Pressure: after stage"));
        if(AdvectionRequested) Record->SetStringField(TEXT("advection_velocity_stage"),TEXT("Extrapolate Velocities Again: after stage"));
        return true;
    }
};
