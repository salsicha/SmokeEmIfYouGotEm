#include "RaftSimWaterModule.h"

#include "Modules/ModuleManager.h"
#if RAFTSIM_HAS_LIVE_SOLVER
#include "raftsim_water/solver.hpp"
#endif

void FRaftSimWaterModule::StartupModule()
{
#if RAFTSIM_HAS_LIVE_SOLVER
    UE_LOG(LogTemp, Display, TEXT("RaftSim live-water solver archive: %hs"), RAFTSIM_LIVE_SOLVER_BUILD_SHA256);
#endif
}

void FRaftSimWaterModule::ShutdownModule()
{
#if RAFTSIM_HAS_LIVE_SOLVER
    // Join outside DllMain: waiting for thread detach under the Windows loader
    // lock can deadlock module unloading even after the last water step.
    raftsim::shutdown_solver_workers();
    UE_LOG(LogTemp, Display, TEXT("RaftSim live-water solver workers joined before module unload"));
#endif
}

IMPLEMENT_MODULE(FRaftSimWaterModule, RaftSimWater)
