// Windows SM5 regression: execute FXC output, not a CPU translation of HLSL.
// Usage: portable_float_gpu_control shader.cso exact-scalar-fixture.bin [warp]
// Compile with cl /EHsc /std:c++17 ... d3d11.lib (Windows SDK required).
#include <d3d11.h>
#include <wrl/client.h>
#include <array>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <vector>
using Microsoft::WRL::ComPtr;
using Word = std::uint32_t;
using Vector = std::array<Word,4>;
void Check(HRESULT result)
{
    if(FAILED(result))throw std::runtime_error("D3D11 failed: "+std::to_string(result));
}
int main(int argc,char** argv)
{
    try
    {
        if(argc<3 || argc>4 || (argc==4 && std::string(argv[3])!="warp"))return 2;
        std::ifstream codeFile(argv[1],std::ios::binary),fixture(argv[2],std::ios::binary);
        std::vector<char> code{std::istreambuf_iterator<char>(codeFile),{}};
        Word header[3]={};fixture.read(reinterpret_cast<char*>(header),sizeof(header));
        if(code.empty() || !fixture || header[0]!=0x52534650 || header[1]<1 || header[1]>10 ||
            header[1]==5 || header[1]==9 || header[2]<32 || header[2]>65536)return 2;
        const Word operation=header[1]-1;
        const Word count=header[2],padded=(count+255u)/256u*256u;
        std::vector<Vector> input(padded);
        std::vector<Word> expected(count);
        for(Word i=0;i<count;++i)
        {
            fixture.read(reinterpret_cast<char*>(input[i].data()),operation==0?12:16);
            fixture.read(reinterpret_cast<char*>(&expected[i]),4);
            if(!fixture)return 2;
        }
        char extra;if(fixture.read(&extra,1))return 2;
        const bool warp=argc==4;
        ComPtr<ID3D11Device> device;ComPtr<ID3D11DeviceContext> context;
        const D3D_FEATURE_LEVEL requested=D3D_FEATURE_LEVEL_11_0;
        D3D_FEATURE_LEVEL obtained;
        Check(D3D11CreateDevice(nullptr,warp?D3D_DRIVER_TYPE_WARP:D3D_DRIVER_TYPE_HARDWARE,
            nullptr,0,&requested,1,D3D11_SDK_VERSION,&device,&obtained,&context));
        ComPtr<ID3D11ComputeShader> shader;
        Check(device->CreateComputeShader(code.data(),code.size(),nullptr,&shader));
        D3D11_BUFFER_DESC desc={};desc.ByteWidth=padded*sizeof(Vector);
        desc.Usage=D3D11_USAGE_DEFAULT;desc.BindFlags=D3D11_BIND_SHADER_RESOURCE;
        desc.MiscFlags=D3D11_RESOURCE_MISC_BUFFER_STRUCTURED;desc.StructureByteStride=sizeof(Vector);
        D3D11_SUBRESOURCE_DATA initial={};initial.pSysMem=input.data();
        ComPtr<ID3D11Buffer> in,out,read;
        Check(device->CreateBuffer(&desc,&initial,&in));
        desc.BindFlags=D3D11_BIND_UNORDERED_ACCESS;
        Check(device->CreateBuffer(&desc,nullptr,&out));
        desc.Usage=D3D11_USAGE_STAGING;desc.BindFlags=0;desc.CPUAccessFlags=D3D11_CPU_ACCESS_READ;
        desc.MiscFlags=0;desc.StructureByteStride=0;
        Check(device->CreateBuffer(&desc,nullptr,&read));
        ComPtr<ID3D11ShaderResourceView> srv;ComPtr<ID3D11UnorderedAccessView> uav;
        Check(device->CreateShaderResourceView(in.Get(),nullptr,&srv));
        Check(device->CreateUnorderedAccessView(out.Get(),nullptr,&uav));
        context->CSSetShader(shader.Get(),nullptr,0);
        ID3D11ShaderResourceView* srvs[]={srv.Get()};ID3D11UnorderedAccessView* uavs[]={uav.Get()};
        context->CSSetShaderResources(0,1,srvs);context->CSSetUnorderedAccessViews(0,1,uavs,nullptr);
        context->Dispatch(padded/256u,1,1);
        ID3D11UnorderedAccessView* emptyUav[]={nullptr};
        context->CSSetUnorderedAccessViews(0,1,emptyUav,nullptr);
        context->CopyResource(read.Get(),out.Get());
        D3D11_MAPPED_SUBRESOURCE mapped={};Check(context->Map(read.Get(),0,D3D11_MAP_READ,0,&mapped));
        const Vector* actual=static_cast<const Vector*>(mapped.pData);
        Word wrong=0,wideWrong=0,transportWrong=0,operationWrong=0;
        for(Word i=0;i<count;++i)
        {
            if(actual[i][0]!=expected[i])
            {
                if(wrong<16)std::cerr<<"case="<<i<<std::hex<<" expected="<<expected[i]
                    <<" actual="<<actual[i][0]<<" control="<<actual[i][2]<<std::dec<<'\n';
                ++wrong;
            }
            if(operation==9)wideWrong+=actual[i][2]!=expected[i];
            transportWrong+=actual[i][1]!=input[i][0];operationWrong+=actual[i][3]!=operation;
        }
        context->Unmap(read.Get(),0);
        std::cout<<"backend="<<(warp?"warp":"hardware")<<" operation="<<operation<<" cases="<<count
            <<" arithmetic_errors="<<wrong<<" wide_errors="<<wideWrong<<" transported_input_errors="
            <<transportWrong<<" operation_errors="<<operationWrong<<'\n';
        return wrong || wideWrong || transportWrong || operationWrong?1:0;
    }
    catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 2;}
}
