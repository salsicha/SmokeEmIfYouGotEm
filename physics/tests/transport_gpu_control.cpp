// Standalone execution of the production six-phase SM5 transport shader.
// Optional coupled mode also runs the original pressure/PCG40 pipeline.
// Neither mode is an RK step, engine integration, or scene-acceptance test.
// cl /EHsc /std:c++17 /O2 transport_gpu_control.cpp d3d11.lib d3dcompiler.lib dxguid.lib
// compile: EXE compile shader-directory exact-header output-directory version
// run: EXE run output-directory original-fixture.bin hardware|warp
#define NOMINMAX
#include <d3d11.h>
#include <d3dcompiler.h>
#include <d3d11shader.h>
#include <wrl/client.h>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>
using Microsoft::WRL::ComPtr;
using U=std::uint32_t;
namespace fs=std::filesystem;
void check(HRESULT h){if(FAILED(h))throw std::runtime_error("D3D failure "+std::to_string(h));}
std::vector<char> read(const fs::path& path)
{
    std::ifstream f(path,std::ios::binary);
    if(!f)throw std::runtime_error("Missing input: "+path.string());
    return {std::istreambuf_iterator<char>(f),{}};
}
template<class T>T word(std::istream& f)
{T value{};f.read(reinterpret_cast<char*>(&value),sizeof(T));if(!f)throw std::runtime_error("Truncated fixture");return value;}
template<class T>std::vector<T> array(std::istream& f,U count)
{std::vector<T> a(count);f.read(reinterpret_cast<char*>(a.data()),sizeof(T)*count);if(!f)throw std::runtime_error("Truncated array");return a;}
struct Includes:ID3DInclude
{
    fs::path root,exact;
    HRESULT __stdcall Open(D3D_INCLUDE_TYPE,LPCSTR name,LPCVOID,LPCVOID* data,UINT* size)override
    {
        try
        {
            // No UE platform macro is used by this shader. Do not substitute
            // any arithmetic implementation or preprocessor model selection.
            std::vector<char> bytes;
            if(std::string(name)!="/Engine/Public/Platform.ush")
                bytes=read(std::string(name)=="RaftSimExactHydrostatic.ush"?exact:root/name);
            auto* copy=new char[std::max(size_t(1),bytes.size())];
            if(!bytes.empty())std::memcpy(copy,bytes.data(),bytes.size());
            *data=copy;*size=UINT(bytes.size());return S_OK;
        }
        catch(const std::exception& e){std::cerr<<e.what()<<'\n';return E_FAIL;}
    }
    HRESULT __stdcall Close(LPCVOID data)override{delete[] static_cast<const char*>(data);return S_OK;}
};
struct Buffer
{
    ComPtr<ID3D11Buffer> data;
    ComPtr<ID3D11ShaderResourceView> srv;
    ComPtr<ID3D11UnorderedAccessView> uav;
    U bytes=0;
};
Buffer buffer(ID3D11Device* device,U stride,U count,const void* input=nullptr)
{
    Buffer b;b.bytes=stride*count;D3D11_BUFFER_DESC d{};
    d.ByteWidth=b.bytes;d.Usage=D3D11_USAGE_DEFAULT;
    d.BindFlags=D3D11_BIND_SHADER_RESOURCE|D3D11_BIND_UNORDERED_ACCESS;
    d.MiscFlags=D3D11_RESOURCE_MISC_BUFFER_STRUCTURED;d.StructureByteStride=stride;
    std::vector<char> zero(b.bytes,0);D3D11_SUBRESOURCE_DATA initial{};initial.pSysMem=input?input:zero.data();
    check(device->CreateBuffer(&d,&initial,&b.data));
    check(device->CreateShaderResourceView(b.data.Get(),nullptr,&b.srv));
    check(device->CreateUnorderedAccessView(b.data.Get(),nullptr,&b.uav));return b;
}
std::vector<U> download(ID3D11Device* device,ID3D11DeviceContext* context,const Buffer& b)
{
    D3D11_BUFFER_DESC d{};d.ByteWidth=b.bytes;d.Usage=D3D11_USAGE_STAGING;d.CPUAccessFlags=D3D11_CPU_ACCESS_READ;
    ComPtr<ID3D11Buffer> staging;check(device->CreateBuffer(&d,nullptr,&staging));
    context->CopyResource(staging.Get(),b.data.Get());D3D11_MAPPED_SUBRESOURCE m{};
    check(context->Map(staging.Get(),0,D3D11_MAP_READ,0,&m));
    std::vector<U> result(b.bytes/4);std::memcpy(result.data(),m.pData,b.bytes);context->Unmap(staging.Get(),0);return result;
}
float asfloat(U value){float result;std::memcpy(&result,&value,4);return result;}
bool compare(const std::vector<U>& bits,const std::vector<float>& expected,const char* name,U index)
{
    double e2=0,n2=0,maximum=0;bool finite=true;
    for(size_t i=0;i<bits.size();++i)
    {double a=asfloat(bits[i]),b=expected.at(i),e=a-b;finite&=std::isfinite(a);e2+=e*e;n2+=b*b;maximum=std::max(maximum,std::abs(e));}
    const double relative=std::sqrt(n2>0?e2/n2:e2);
    std::cout<<"case="<<index<<" field="<<name<<" relative="<<relative<<" max="<<maximum<<'\n';
    return finite && relative<2e-5 && maximum<1e-3; // Unchanged native fixture gate.
}
struct Shader
{
    ComPtr<ID3D11ComputeShader> code;
    ComPtr<ID3D11ShaderReflection> reflection;
};
Shader shader(ID3D11Device* device,const fs::path& path)
{
    auto bytes=read(path);Shader result;
    check(device->CreateComputeShader(bytes.data(),bytes.size(),nullptr,&result.code));
    check(D3DReflect(bytes.data(),bytes.size(),IID_ID3D11ShaderReflection,&result.reflection));
    return result;
}
using Buffers=std::map<std::string,Buffer>;
using Constants=std::map<std::string,std::vector<U>>;
void dispatch(ID3D11Device* device,ID3D11DeviceContext* context,const Shader& shader,
    Buffers& buffers,const Constants& values,U groups)
{
    ID3D11ShaderResourceView* srvs[128]={};ID3D11UnorderedAccessView* uavs[8]={};
    ID3D11Buffer* constants[14]={};std::vector<ComPtr<ID3D11Buffer>> retained;
    D3D11_SHADER_DESC sd{};check(shader.reflection->GetDesc(&sd));
    for(U binding=0;binding<sd.BoundResources;++binding)
    {
        D3D11_SHADER_INPUT_BIND_DESC d{};check(shader.reflection->GetResourceBindingDesc(binding,&d));
        if(d.Type==D3D_SIT_CBUFFER)
        {
            auto* cb=shader.reflection->GetConstantBufferByName(d.Name);D3D11_SHADER_BUFFER_DESC bd{};check(cb->GetDesc(&bd));
            std::vector<char> data((bd.Size+15)/16*16,0);
            for(U v=0;v<bd.Variables;++v)
            {
                D3D11_SHADER_VARIABLE_DESC vd{};check(cb->GetVariableByIndex(v)->GetDesc(&vd));
                if(!(vd.uFlags&D3D_SVF_USED))continue;
                const auto& value=values.at(vd.Name);if(vd.Size!=value.size()*4)throw std::runtime_error("Constant size mismatch");
                std::memcpy(data.data()+vd.StartOffset,value.data(),vd.Size);
            }
            D3D11_BUFFER_DESC desc{};desc.ByteWidth=U(data.size());desc.Usage=D3D11_USAGE_DEFAULT;desc.BindFlags=D3D11_BIND_CONSTANT_BUFFER;
            D3D11_SUBRESOURCE_DATA initial{};initial.pSysMem=data.data();ComPtr<ID3D11Buffer> b;
            check(device->CreateBuffer(&desc,&initial,&b));if(d.BindPoint>=14)throw std::runtime_error("Constant slot out of range");
            constants[d.BindPoint]=b.Get();retained.push_back(b);
        }
        else
        {
            std::string name=d.Name;const std::string suffix="Output";
            if(name.size()>suffix.size() && name.compare(name.size()-suffix.size(),suffix.size(),suffix)==0)name.resize(name.size()-suffix.size());
            auto& b=buffers.at(name);
            if(d.Type==D3D_SIT_STRUCTURED && d.BindPoint<128)srvs[d.BindPoint]=b.srv.Get();
            else if(d.Type==D3D_SIT_UAV_RWSTRUCTURED && d.BindPoint<8)uavs[d.BindPoint]=b.uav.Get();
            else throw std::runtime_error("Unexpected resource binding");
        }
    }
    context->CSSetShader(shader.code.Get(),nullptr,0);context->CSSetConstantBuffers(0,14,constants);
    context->CSSetShaderResources(0,128,srvs);context->CSSetUnorderedAccessViews(0,8,uavs,nullptr);
    context->Dispatch(groups,1,1);
    ID3D11ShaderResourceView* emptyS[128]={};ID3D11UnorderedAccessView* emptyU[8]={};
    context->CSSetShaderResources(0,128,emptyS);context->CSSetUnorderedAccessViews(0,8,emptyU,nullptr);
}

#include "pressure_gpu_control.h"

int main(int argc,char** argv)
{
    try
    {
        if(argc==4 && std::string(argv[1])=="test-pressure-guard")
        {
            if(std::string(argv[3])!="hardware" && std::string(argv[3])!="warp")return 2;
            return test_pressure_activity_guard(argv[2],std::string(argv[3])=="warp")?0:1;
        }
        if((argc==4 || argc==5) && std::string(argv[1])=="compile-pressure")
        { compile_pressure(argv[2],argv[3],argc==5?argv[4]:"");return 0; }
        if(argc==6 && std::string(argv[1])=="compile")
        {
            const int version=std::stoi(argv[5]);if(version<1 || version>3)return 2;
            Includes includes;includes.root=fs::absolute(argv[2]);includes.exact=fs::absolute(argv[3]);
            const fs::path out=argv[4];if(fs::exists(out))throw std::runtime_error("Preserve previous compile evidence");
            fs::create_directory(out);
            auto bytes=read(includes.root/"RaftSimTotalDepthTransport.usf");
            // The original function body and all helpers are verbatim. Only its
            // entry attribute/name are wrapped to emit an independent phase tag.
            std::string source(bytes.begin(),bytes.end());
            const std::string attribute="[numthreads(256,1,1)]";
            const auto at=source.find(attribute);if(at==std::string::npos)throw std::runtime_error("Unknown entry layout");
            source.erase(at,attribute.size());
            source="#define MainCS ProductionMainCS\n"+source+
                "\n#undef MainCS\nRWStructuredBuffer<uint> HarnessTag;\n[numthreads(256,1,1)]\n"
                "void MainCS(uint3 id:SV_DispatchThreadID,uint3 group:SV_GroupID,uint lane:SV_GroupIndex) {"
                "ProductionMainCS(id,group,lane);if(id.x==0)HarnessTag[0]=0x52530000u+"
                "RAFTSIM_TRANSPORT_PHASE+16u*RAFTSIM_HARNESS_VERSION;}\n";
            for(int phase=0;phase<6;++phase)
            {
                std::string p=std::to_string(phase),v=std::to_string(version);
                D3D_SHADER_MACRO macros[]={{"RAFTSIM_TRANSPORT_PHASE",p.c_str()},
                    {"RAFTSIM_TRANSPORT_EXTERIOR","0"},{"RAFTSIM_TRANSPORT_CONTINUOUS",version==2?"1":"0"},
                    {"RAFTSIM_TRANSPORT_UNSCALED",version==3?"1":"0"},{"RAFTSIM_HARNESS_VERSION",v.c_str()},{nullptr,nullptr}};
                ComPtr<ID3DBlob> code,errors;
                std::cout<<"compiling version="<<version<<" phase="<<phase<<std::endl;
                HRESULT h=D3DCompile(source.data(),source.size(),"production-transport-wrapper",macros,&includes,"MainCS","cs_5_0",
                    D3DCOMPILE_OPTIMIZATION_LEVEL3|D3DCOMPILE_ENABLE_BACKWARDS_COMPATIBILITY|D3DCOMPILE_PACK_MATRIX_ROW_MAJOR,
                    0,&code,&errors);
                if(errors){std::ofstream log(out/(p+".log"),std::ios::binary);log.write(static_cast<const char*>(errors->GetBufferPointer()),errors->GetBufferSize());}
                check(h);std::ofstream f(out/(p+".cso"),std::ios::binary);f.write(static_cast<const char*>(code->GetBufferPointer()),code->GetBufferSize());
                if(!f)throw std::runtime_error("Cannot retain shader bytecode");
            }
            return 0;
        }
        const bool coupled=(argc==6 || argc==7) && std::string(argv[1])=="run-coupled";
        if((!coupled && (argc!=5 || std::string(argv[1])!="run")) ||
            (std::string(argv[4])!="hardware" && std::string(argv[4])!="warp"))return 2;
        std::ifstream fixture(argv[3],std::ios::binary);
        U magic=word<U>(fixture),version=word<U>(fixture),cases=word<U>(fixture);
        if(magic!=0x52534656u || version<1 || version>3 || cases<8 || cases>32)throw std::runtime_error("Invalid original transport fixture");
        ComPtr<ID3D11Device> device;ComPtr<ID3D11DeviceContext> context;D3D_FEATURE_LEVEL level=D3D_FEATURE_LEVEL_11_0,got;
        check(D3D11CreateDevice(nullptr,std::string(argv[4])=="warp"?D3D_DRIVER_TYPE_WARP:D3D_DRIVER_TYPE_HARDWARE,
            nullptr,0,&level,1,D3D11_SDK_VERSION,&device,&got,&context));
        Shader shaders[6];
        for(U phase=0;phase<6;++phase)
            shaders[phase]=shader(device.Get(),fs::path(argv[2])/(std::to_string(phase)+".cso"));
        std::vector<Shader> pressureShaders;
        if(coupled)for(const auto& spec:pressure_specs())pressureShaders.push_back(shader(device.Get(),fs::path(argv[5])/(spec.name+".cso")));
        bool passed=true,pressurePassed=true;
        for(U index=0;index<cases;++index)
        {
            U x=word<U>(fixture),y=word<U>(fixture),periodic=word<U>(fixture),second=word<U>(fixture);
            float dx=word<float>(fixture),cfl=word<float>(fixture);
            if(x<1 || y<1 || x>512 || y>512 || periodic>1 || second>1 || !std::isfinite(dx) || dx<=0 || !(cfl>0))throw std::runtime_error("Invalid case");
            U n=x*y,groups=(n+255)/256;
            auto bed=array<float>(fixture,n),state=array<float>(fixture,4*n),rate=array<float>(fixture,4*n);
            auto pairs=array<U>(fixture,n);auto slope=array<float>(fixture,2*n);
            auto pressure=array<float>(fixture,2*n),fraction=array<float>(fixture,n);
            std::map<std::string,Buffer> buffers;
            buffers.emplace("State",buffer(device.Get(),16,n,state.data()));buffers.emplace("Bed",buffer(device.Get(),4,n,bed.data()));
            for(auto name:{"Geometry","PhysicalBedSlope","Velocity","FoamFlux","CorrectionX","CorrectionY","ShorelineFactors"})buffers.emplace(name,buffer(device.Get(),8,n));
            for(auto name:{"RawX","RawY","SlopeX","SlopeY","FluxX","FluxY","HydroRate"})buffers.emplace(name,buffer(device.Get(),16,n));
            for(auto name:{"Pairs","Flattened"})buffers.emplace(name,buffer(device.Get(),4,n));
            buffers.emplace("Partial",buffer(device.Get(),8,groups));buffers.emplace("CFL",buffer(device.Get(),16,1));
            buffers.emplace("Diagnostics",buffer(device.Get(),4,4));buffers.emplace("HarnessTag",buffer(device.Get(),4,1));
            std::map<std::string,std::vector<U>> values={{"GridSize",{x,y}},{"Periodic",{periodic}},
                {"SecondOrder",{second}},{"PartialCount",{groups}},{"CellMeters",{0}}};std::memcpy(values["CellMeters"].data(),&dx,4);
            for(U phase=0;phase<6;++phase)
            {
                dispatch(device.Get(),context.Get(),shaders[phase],buffers,values,phase==5?1:groups);
                passed&=download(device.Get(),context.Get(),buffers.at("HarnessTag"))[0]==0x52530000u+phase+16*version;
            }
            const auto actual=download(device.Get(),context.Get(),buffers.at("HydroRate"));
            passed&=compare(actual,rate,"hydro_rate",index);
            passed&=compare(download(device.Get(),context.Get(),buffers.at("PhysicalBedSlope")),slope,"bed_slope",index);
            auto actualPairs=download(device.Get(),context.Get(),buffers.at("Pairs"));U mismatches=0;
            for(U i=0;i<n;++i)mismatches+=actualPairs[i]!=pairs[i];passed&=mismatches==0;
            const auto geo=download(device.Get(),context.Get(),buffers.at("Geometry"));
            double mass=0,magnitude=0;bool exactRest=std::all_of(rate.begin(),rate.end(),[](float v){return v==0;});
            for(U i=0;i<n;++i)
            {
                passed&=asfloat(geo[2*i])==state[4*i] && asfloat(geo[2*i+1])==bed[i];
                mass+=asfloat(actual[4*i]);magnitude+=std::abs(double(asfloat(actual[4*i])));passed&=asfloat(actual[4*i+3])==0;
            }
            passed&=std::abs(mass)<=2e-6*magnitude;
            if(index<2 || exactRest)for(U bits:actual)passed&=asfloat(bits)==0;
            const auto diagnostics=download(device.Get(),context.Get(),buffers.at("Diagnostics"));passed&=diagnostics[0]==0 && diagnostics[1]==0;
            const float actualCfl=asfloat(download(device.Get(),context.Get(),buffers.at("CFL"))[2]);
            passed&=std::isfinite(cfl)?std::isfinite(actualCfl) && std::abs(double(actualCfl)/cfl-1.)<2e-5:actualCfl==cfl;
            std::cout<<"case="<<index<<" pairs_mismatched="<<mismatches<<" mass="<<mass<<" diagnostics="<<diagnostics[0]<<'/'<<diagnostics[1]<<" cfl="<<actualCfl<<" cumulative_pass="<<passed<<std::endl;
            if(coupled)pressurePassed&=run_pressure(device.Get(),context.Get(),pressureShaders,buffers,values,n,groups,fraction,pressure,index,argc==7?fs::path(argv[6]):fs::path());
        }
        char extra;if(fixture.read(&extra,1))throw std::runtime_error("Trailing fixture bytes");
        std::cout<<"backend="<<argv[4]<<" cases="<<cases<<" transport_pass="<<passed;
        if(coupled)std::cout<<" coupled_pressure_fixture_pass="<<pressurePassed<<" step_accepted=0\n";
        else std::cout<<" pressure_or_step_accepted=0\n";
        return passed && pressurePassed?0:1;
    }
    catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 2;}
}
