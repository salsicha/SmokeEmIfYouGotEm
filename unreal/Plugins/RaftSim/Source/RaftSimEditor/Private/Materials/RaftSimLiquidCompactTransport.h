#pragma once

// Position transport only. Preserve native FLIP/PIC momentum and registered
// contact/inlet treatment. Four-point complete support, 32 vector loads per
// query. The continuous divergence is tent interpolation of centered grid D.
inline FString RaftSimLiquidCompactTransportHlsl(bool Unified=false)
{
    FString Code=TEXT(
        "// RiverCompactCompatibleTransport: averaged quadratic normal / tent transverse RK2.\n"
        "int tx,ty,tz;TransportFlow.GetNumCells(tx,ty,tz);int3 ts=int3(tx,ty,tz);\n"
        "float3 tu=mul(float4(PreviousPosition,1),TransportWorldToUnit).xyz;\n"
        "int3 ti=int3(round(tu*float3(ts)-0.5));float4 tb;\n"
        "TransportBoundary.GetPreviousVector4Value<Attribute=\"SolidVelocity_Boundary\">(ti.x,ti.y,ti.z,tb);\n"
        "bool tc=all(tu>0) && all(tu<1) && (round(tb.w)==0 || round(tb.w)==3);\n"
        "float3 tq=PreviousPosition,tv=0;\n"
        "for(int stage=0;stage<2 && tc;++stage) {\n"
        " float3 q=mul(float4(tq,1),TransportWorldToUnit).xyz*float3(ts)-0.5;int3 low=int3(floor(q))-1;\n"
        " if(any(low<0) || any(low+3>=ts)) {tc=false;break;}\n"
        " float3 sum=0;\n"
        " for(int z=0;z<4;++z) for(int y=0;y<4;++y) for(int x=0;x<4;++x) {\n"
        "  if(int(x==0 || x==3)+int(y==0 || y==3)+int(z==0 || z==3)>1) continue;\n"
        "  int3 i=low+int3(x,y,z);float3 r=float3(i)-q,w=max(1-abs(r),0),normal;\n"
        "  for(int axis=0;axis<3;++axis) {\n"
        "   float a=r[axis]-0.5,b=r[axis]+0.5;\n"
        "   float wa=abs(a)<0.5?0.75-a*a:0.5*pow(max(1.5-abs(a),0),2);\n"
        "   float wb=abs(b)<0.5?0.75-b*b:0.5*pow(max(1.5-abs(b),0),2);normal[axis]=0.5*(wa+wb);\n"
        "  }\n"
        "  float3 v;TransportFlow.GetPreviousVectorValue<Attribute=\"Velocity\">(i.x,i.y,i.z,v);\n"
        "  sum+=v*float3(normal.x*w.y*w.z,w.x*normal.y*w.z,w.x*w.y*normal.z);\n"
        " }\n"
        " tv=mul(float4(sum,0),TransportLocalToWorld).xyz;tq=PreviousPosition+0.5*DeltaTime*tv;\n"
        "}\n"
        "if(tc) Position=PreviousPosition+DeltaTime*tv;\n");
    if(Unified)
    {
        Code=TEXT("// RiverUnifiedTransport: shared basis and orthogonal cell frame.\n")+Code;
        Code.ReplaceInline(TEXT("float3 tu="),TEXT("precise float3 tu="));
        Code.ReplaceInline(TEXT("int3 ti=int3(round(tu*float3(ts)-0.5));"),TEXT("precise float3 phaseq=tu*float3(ts)-0.5;int3 ti=int3(round(phaseq));"));
        Code.ReplaceInline(TEXT("float3 q=mul"),TEXT("precise float3 q=mul"));
        Code.ReplaceInline(TEXT("mul(float4(PreviousPosition,1),TransportWorldToUnit).xyz"),TEXT("RaftSimLiquidOrthogonalUnit(PreviousPosition,TransportWorldToUnit)"));
        Code.ReplaceInline(TEXT("mul(float4(tq,1),TransportWorldToUnit).xyz"),TEXT("RaftSimLiquidOrthogonalUnit(tq,TransportWorldToUnit)"));
        // The existing input name is retained to avoid a second graph ABI;
        // unified installation binds UnitToWorld to this pin explicitly.
        const FString Start=TEXT("  int3 i=low+int3(x,y,z);float3 r=float3(i)-q,w=max(1-abs(r),0),normal;\n");
        const int32 First=Code.Find(Start),Last=Code.Find(TEXT("  float3 v;TransportFlow."));
        if(First>=0 && Last>First) Code=Code.Left(First)+TEXT("  int3 i=low+int3(x,y,z);float3 weights=RaftSimLiquidCompactWeights(float3(i)-q);\n")+Code.Mid(Last);
        Code.ReplaceInline(TEXT("float3(normal.x*w.y*w.z,w.x*normal.y*w.z,w.x*w.y*normal.z)"),TEXT("weights"));
    }
    return Code;
}
