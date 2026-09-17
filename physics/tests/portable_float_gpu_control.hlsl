// FXC /T cs_5_0 /E MainCS /O3 /Gec /Zpr /D RAFTSIM_TEST_OPERATION=9.
// The runner pads inputs to 256 threads and checks the compiled operation tag.
// The compact helper and independent wide accumulator must both match the
// unchanged exact-rational fixture, including subnormals and signed zero.
#include "../../unreal/Plugins/RaftSim/Shaders/Private/RaftSimPortableFloat.ush"
#ifndef RAFTSIM_TEST_OPERATION
#error Select the scalar operation from the unchanged represented-float fixture.
#endif
StructuredBuffer<float4> Input : register(t0);
RWStructuredBuffer<uint4> Output : register(u0);
[numthreads(256,1,1)]
void MainCS(uint3 id:SV_DispatchThreadID)
{
    float4 v=Input[id.x];
#if RAFTSIM_TEST_OPERATION == 9
    uint result=asuint(RaftSimPortableAdd(v.x,v.y));
    uint control=asuint(RaftSimPortableEuler(v.x,1,v.y));
#else
    uint result=RAFTSIM_TEST_OPERATION==7?asuint(RaftSimPortableMul(v.x,v.y)):
        RAFTSIM_TEST_OPERATION==6?asuint(RaftSimPortableScale(v.x,int(v.y))):
        RAFTSIM_TEST_OPERATION==5?asuint(RaftSimPortableSqrt(v.x)):
        RAFTSIM_TEST_OPERATION==3?asuint(RaftSimPortableDivide(v.x,v.y)):
        RAFTSIM_TEST_OPERATION==2?uint(RaftSimPortableValidState(v)):
        RAFTSIM_TEST_OPERATION==1?asuint(RaftSimPortableRK2(v.x,v.y,v.z,v.w)):
        asuint(RaftSimPortableEuler(v.x,v.y,v.z));
    uint control=0;
#endif
    Output[id.x]=uint4(result,asuint(v.x),control,RAFTSIM_TEST_OPERATION);
}
