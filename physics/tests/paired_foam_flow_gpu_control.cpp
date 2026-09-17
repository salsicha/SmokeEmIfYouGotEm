// Execute the exact production texture helper on hardware or WARP.
// Reuse only the D3D device/buffer/readback utilities, not an HLSL emulation.
#define main transport_control_unused_main
#include "transport_gpu_control.cpp"
#undef main
#include <limits>

struct FoamIncludes:Includes
{
    HRESULT __stdcall Open(D3D_INCLUDE_TYPE type,LPCSTR name,LPCVOID parent,LPCVOID* data,UINT* size)override
    {
        const std::string prefix="/Plugin/RaftSimWaterDetail/Private/";
        const std::string path=name;
        if(path.compare(0,prefix.size(),prefix)!=0)return E_FAIL;
        const auto leaf=path.substr(prefix.size());
        if(leaf!="RaftSimRegisteredFoamFlow.ush" && leaf!="RaftSimRegisteredDetailSample.ush")return E_FAIL;
        return Includes::Open(type,leaf.c_str(),parent,data,size);
    }
};

ComPtr<ID3D11ShaderResourceView> foam_texture(ID3D11Device* device,U width,U height,const std::vector<float>& values)
{
    D3D11_TEXTURE2D_DESC desc{};desc.Width=width;desc.Height=height;desc.MipLevels=1;desc.ArraySize=1;
    desc.Format=DXGI_FORMAT_R32G32B32A32_FLOAT;desc.SampleDesc.Count=1;desc.Usage=D3D11_USAGE_IMMUTABLE;
    desc.BindFlags=D3D11_BIND_SHADER_RESOURCE;
    D3D11_SUBRESOURCE_DATA data{};data.pSysMem=values.data();data.SysMemPitch=width*16;
    ComPtr<ID3D11Texture2D> texture;check(device->CreateTexture2D(&desc,&data,&texture));
    ComPtr<ID3D11ShaderResourceView> view;check(device->CreateShaderResourceView(texture.Get(),nullptr,&view));return view;
}

int main(int argc,char** argv)
{
    try
    {
        if(argc!=3 || (std::string(argv[2])!="hardware" && std::string(argv[2])!="warp"))return 2;
        FoamIncludes includes;includes.root=fs::absolute(argv[1]);
        const std::string source=R"(
#include "/Plugin/RaftSimWaterDetail/Private/RaftSimRegisteredFoamFlow.ush"
Texture2D<float4> Detail:register(t0);
Texture2D<float4> Flow:register(t1);
StructuredBuffer<float4> Query:register(t2);
RWStructuredBuffer<float4> Result:register(u0);
cbuffer Settings:register(b0) { float Enable; };
[numthreads(1,1,1)] void MainCS(uint3 id:SV_DispatchThreadID) {
    float4 q=Query[id.x];Result[id.x]=float4(RaftSimRegisteredFoamFlow(Detail,Flow,q.xy,q.zw,Enable),0,0);
})";
        ComPtr<ID3DBlob> code,errors;
        const auto compiled=D3DCompile(source.data(),source.size(),"production-paired-foam-flow",nullptr,&includes,
            "MainCS","cs_5_0",D3DCOMPILE_OPTIMIZATION_LEVEL3,0,&code,&errors);
        if(errors)std::cerr.write(static_cast<const char*>(errors->GetBufferPointer()),errors->GetBufferSize());
        check(compiled);
        ComPtr<ID3D11Device> device;ComPtr<ID3D11DeviceContext> context;
        const D3D_FEATURE_LEVEL level=D3D_FEATURE_LEVEL_11_0;D3D_FEATURE_LEVEL obtained;
        check(D3D11CreateDevice(nullptr,std::string(argv[2])=="warp"?D3D_DRIVER_TYPE_WARP:D3D_DRIVER_TYPE_HARDWARE,
            nullptr,0,&level,1,D3D11_SDK_VERSION,&device,&obtained,&context));
        ComPtr<ID3D11ComputeShader> shader;check(device->CreateComputeShader(code->GetBufferPointer(),code->GetBufferSize(),nullptr,&shader));
        constexpr U width=33,height=26;
        std::vector<float> original(width*height*4,0);
        for(U y=0;y<height-1;++y)for(U x=0;x<width;++x)
        {
            const auto i=4*(y*width+x);original[i]=2;original[i+1]=x*.125f-2;original[i+2]=y*.25f-3;
        }
        const U metadata=4*width*(height-1);
        original[metadata]=-5439;original[metadata+1]=3606;original[metadata+2]=.5f;original[metadata+3]=1;
        original[metadata+4]=1048576;original[metadata+5]=.03125f;original[metadata+7]=3;
        U checked=0,wrong=0;float maximum=0;
        for(U variant=0;variant<10;++variant)
        {
            auto flow=original;float enable=1;
            if(variant==1)flow[metadata]+=.5f;
            if(variant==2)flow[metadata+4]+=1;
            if(variant==3)flow[metadata+5]+=.03125f;
            if(variant==4)flow[metadata+7]=0;
            if(variant==5)enable=0;
            if(variant==6)enable=.5f;
            if(variant==7)for(U i=0;i<width*(height-1);++i)flow[4*i+1]=std::numeric_limits<float>::quiet_NaN();
            auto detail=original;
            if(variant==9){detail[metadata+7]=2;flow[metadata+7]=2;}
            auto detailSRV=foam_texture(device.Get(),width,height,detail);
            auto flowSRV=foam_texture(device.Get(),variant==8?width-1:width,height,flow);
            std::vector<float> queries,expected;
            for(float y:{-1.f,0.f,1.f,4.f,6.125f,8.f,11.f,12.f,13.f})
            for(float x:{-1.f,0.f,1.f,2.f,4.f,8.25f,12.f,15.f,16.f,17.f})
            {
                queries.insert(queries.end(),{-5439+x,3606+y,-7,5});
                const float edge=std::min(std::min(x,y),std::min(16-x,12-y));
                const float a=std::clamp(edge/4,0.f,1.f);
                const float weight=(variant==0 || variant==6 || variant==9)?a*a*(3-2*a)*enable:0;
                expected.insert(expected.end(),{-7+weight*(x*.25f-2+7),5+weight*(y*.5f-3-5),0,0});
            }
            auto input=buffer(device.Get(),16,U(queries.size()/4),queries.data());
            auto output=buffer(device.Get(),16,U(queries.size()/4));
            const float settings[4]={enable,0,0,0};
            D3D11_BUFFER_DESC bd{};bd.ByteWidth=16;bd.Usage=D3D11_USAGE_IMMUTABLE;bd.BindFlags=D3D11_BIND_CONSTANT_BUFFER;
            D3D11_SUBRESOURCE_DATA initial{};initial.pSysMem=settings;ComPtr<ID3D11Buffer> cb;check(device->CreateBuffer(&bd,&initial,&cb));
            ID3D11ShaderResourceView* srvs[]={detailSRV.Get(),flowSRV.Get(),input.srv.Get()};
            ID3D11UnorderedAccessView* uavs[]={output.uav.Get()};ID3D11Buffer* constants[]={cb.Get()};
            context->CSSetShader(shader.Get(),nullptr,0);context->CSSetShaderResources(0,3,srvs);
            context->CSSetUnorderedAccessViews(0,1,uavs,nullptr);context->CSSetConstantBuffers(0,1,constants);
            context->Dispatch(U(queries.size()/4),1,1);
            ID3D11UnorderedAccessView* empty[]={nullptr};context->CSSetUnorderedAccessViews(0,1,empty,nullptr);
            const auto actual=download(device.Get(),context.Get(),output);
            for(U i=0;i<actual.size();++i)
            {
                const float value=asfloat(actual[i]),error=std::abs(value-expected[i]);
                maximum=std::max(maximum,error);++checked;
                if(!std::isfinite(value) || error>1e-6f){++wrong;if(wrong<8)std::cerr<<"variant="<<variant<<" word="<<i<<" expected="<<expected[i]<<" actual="<<value<<'\n';}
            }
        }
        std::cout<<"backend="<<argv[2]<<" variants=10 checked_words="<<checked<<" wrong="<<wrong<<" max_error="<<maximum<<" visual_accepted=0\n";
        return wrong?1:0;
    }
    catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 2;}
}
