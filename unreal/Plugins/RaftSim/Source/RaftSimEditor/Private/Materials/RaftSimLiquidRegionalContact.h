#pragma once
#include "CoreMinimal.h"
#include "Dom/JsonObject.h"
#include "RaftSimLiquidRegionalState.h"

class UNiagaraSystem;
namespace RaftSimLiquidParentExterior { class FProfile; }
// Install on an UNUSED transient regional clone after InstallArrays. Binds the
// exact canonical contact page to primary particle projection and pressure
// terrain classification, with grid-local P2G, centered gather, and an
// emitter-owned RGBA32F raw momentum/volume output before normalization. Does not
// activate water or transfer ownership. Optional validated parent-face table
// installs exterior flux/outlet classification, never internal reservoir faces.
bool RaftSimInstallRegionalLiquidContact(UNiagaraSystem* System,
    const RaftSimLiquidRegionalState::FState& Region,const TSharedPtr<FJsonObject>& Contact,FString& Error,
    const RaftSimLiquidParentExterior::FProfile* Exterior=nullptr);
