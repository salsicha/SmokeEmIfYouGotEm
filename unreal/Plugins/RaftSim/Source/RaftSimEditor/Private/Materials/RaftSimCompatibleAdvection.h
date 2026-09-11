#pragma once

// Advection only: averaged-face cubic/quadratic interpolation commutes with
// the existing centered divergence on complete support. APIC v/C are retained.
// The five-point support is not silently clamped at domain boundaries.
inline FString RaftSimCompatibleAdvectionHlsl()
{
    return TEXT(
        "// RiverCompatibleMidpointAdvection: continuous divergence matches interpolated centered grid divergence.\n"
        "AdvectedVelocity=NewVelocity;AdvectionStatus=0;\n"
        "if(round(boundary.w)!=1) {\n"
        " float3 start=Position,query=Position,transport=0;bool complete=true;\n"
        " for(int stage=0;stage<2;++stage) {\n"
        "  float3 uq=mul(float4(query,1),WorldToUnit).xyz;float3 rq=uq*float3(size)-0.5;\n"
        "  int3 base=int3(floor(rq-0.5))-1;\n"
        "  if(any(base<0) || any(base+4>=size)) { complete=false;break; }\n"
        "  float3 local=0;\n"
        "  for(int z=0;z<5;++z) for(int y=0;y<5;++y) for(int x=0;x<5;++x) {\n"
        "   if(int(x==0 || x==4)+int(y==0 || y==4)+int(z==0 || z==4)>1) continue;\n"
        "   int3 i=base+int3(x,y,z);float3 r=float3(i)-rq,a=abs(r),w,n;\n"
        "   for(int axis=0;axis<3;++axis) {\n"
        "    w[axis]=a[axis]<0.5?0.75-r[axis]*r[axis]:0.5*pow(max(1.5-a[axis],0),2);\n"
        "    float left=abs(r[axis]-0.5),right=abs(r[axis]+0.5);\n"
        "    float b=left<1?2.0/3-left*left+0.5*left*left*left:pow(max(2-left,0),3)/6;\n"
        "    float c=right<1?2.0/3-right*right+0.5*right*right*right:pow(max(2-right,0),3)/6;n[axis]=0.5*(b+c);\n"
        "   }\n"
        "   float3 weights=float3(n.x*w.y*w.z,w.x*n.y*w.z,w.x*w.y*n.z);\n"
        "   float3 v;Flow.GetPreviousVectorValue<Attribute=\"Velocity\">(i.x,i.y,i.z,v);local+=v*weights;\n"
        "  }\n"
        "  transport=local.x*normalize(UnitToWorld[0].xyz)+local.y*normalize(UnitToWorld[1].xyz)+local.z*normalize(UnitToWorld[2].xyz);\n"
        "  query=start+transport*(0.5*DeltaTime);\n"
        " }\n"
        " if(complete) {NewPosition=start+transport*DeltaTime;AdvectedVelocity=transport;AdvectionStatus=1;}\n"
        "}\n"
        "AdvectedPosition=NewPosition;\n");
}
