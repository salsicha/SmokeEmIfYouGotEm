// Execute the candidate HLSL on hardware and WARP, not an HLSL emulation.
#define main transport_control_unused_main
#include "transport_gpu_control.cpp"
#undef main
#include <limits>

struct DepartureIncludes:Includes
{
    HRESULT __stdcall Open(D3D_INCLUDE_TYPE t,LPCSTR name,LPCVOID p,LPCVOID* data,UINT* size)override
    {
        const std::string prefix="/Plugin/RaftSimWaterDetail/Private/",path=name;
        if(path.compare(0,prefix.size(),prefix)!=0)return E_FAIL;
        const auto leaf=path.substr(prefix.size());
        if(leaf!="RaftSimFrothDeparture.ush" && leaf!="RaftSimRegisteredDetailSample.ush")return E_FAIL;
        return Includes::Open(t,leaf.c_str(),p,data,size);
    }
};
ComPtr<ID3D11ShaderResourceView> departure_texture(ID3D11Device* device,U width,U height,const std::vector<float>& values)
{
    D3D11_TEXTURE2D_DESC d{};d.Width=width;d.Height=height;d.MipLevels=1;d.ArraySize=1;
    d.Format=DXGI_FORMAT_R32G32B32A32_FLOAT;d.SampleDesc.Count=1;d.Usage=D3D11_USAGE_IMMUTABLE;
    d.BindFlags=D3D11_BIND_SHADER_RESOURCE;
    D3D11_SUBRESOURCE_DATA input{};input.pSysMem=values.data();input.SysMemPitch=width*16;
    ComPtr<ID3D11Texture2D> texture;check(device->CreateTexture2D(&d,&input,&texture));
    ComPtr<ID3D11ShaderResourceView> view;check(device->CreateShaderResourceView(texture.Get(),nullptr,&view));return view;
}
int main(int argc,char** argv)
{
    try
    {
        if(argc!=3 || (std::string(argv[2])!="hardware" && std::string(argv[2])!="warp"))return 2;
        DepartureIncludes includes;includes.root=fs::absolute(argv[1]);
        const std::string source=R"(
#include "/Plugin/RaftSimWaterDetail/Private/RaftSimFrothDeparture.ush"
Texture2D<float4> Detail:register(t0);Texture2D<float4> Flow:register(t1);
StructuredBuffer<float4> Query:register(t2);RWStructuredBuffer<float4> Result:register(u0);
cbuffer Settings:register(b0) { float Seconds;float Enable;uint Steps;float Pad; };
[numthreads(1,1,1)] void MainCS(uint3 id:SV_DispatchThreadID) {
 float4 q=Query[id.x];Result[id.x]=float4(RaftSimFrothDeparture(Detail,Flow,q.xy,q.zw,Seconds,Enable,Steps),0);
})";
        ComPtr<ID3DBlob> code,errors;
        auto compiled=D3DCompile(source.data(),source.size(),"froth-departure",nullptr,&includes,
            "MainCS","cs_5_0",D3DCOMPILE_OPTIMIZATION_LEVEL3,0,&code,&errors);
        if(errors)std::cerr.write(static_cast<const char*>(errors->GetBufferPointer()),errors->GetBufferSize());
        check(compiled);
        ComPtr<ID3D11Device> device;ComPtr<ID3D11DeviceContext> context;
        const D3D_FEATURE_LEVEL level=D3D_FEATURE_LEVEL_11_0;D3D_FEATURE_LEVEL obtained;
        check(D3D11CreateDevice(nullptr,std::string(argv[2])=="warp"?D3D_DRIVER_TYPE_WARP:D3D_DRIVER_TYPE_HARDWARE,
            nullptr,0,&level,1,D3D11_SDK_VERSION,&device,&obtained,&context));
        ComPtr<ID3D11ComputeShader> shader;check(device->CreateComputeShader(code->GetBufferPointer(),code->GetBufferSize(),nullptr,&shader));
        U checked=0,wrong=0;double maximum=0;std::vector<double> rotationErrors;
        constexpr U width=65,height=66,metadata=4*width*(height-1);
        for(U variant=0;variant<17;++variant)for(U steps:{2u,4u,8u,16u})
        {
            float enable=variant==5?0.f:variant==6?.5f:1.f;
            const float ox=variant==12?-5461.5f:-16.f,oy=variant==12?3575.f:-16.f;
            std::vector<float> detail(width*height*4,0);
            for(U y=0;y<height-1;++y)for(U x=0;x<width;++x)
            {
                const auto i=4*(y*width+x);const float px=x*.5f-16,py=y*.5f-16;
                detail[i]=variant==7 || (variant==13 && px>=0 && px<=2)?0.f:2.f;
                detail[i+1]=variant==1?.8f*py+1:variant==2?-.7f*py:variant==13?8.f:1.25f;
                detail[i+2]=variant==1?2.f:variant==2?.7f*px:-.75f;
                if(variant==8)detail[i+1]=std::numeric_limits<float>::quiet_NaN();
            }
            detail[metadata]=ox;detail[metadata+1]=oy;detail[metadata+2]=.5f;detail[metadata+3]=1;
            detail[metadata+4]=1048576;detail[metadata+5]=.03125f;detail[metadata+7]=3;
            auto flow=detail;
            if(variant==3)flow[metadata]+=.5f;
            if(variant==4)flow[metadata+5]+=.03125f;
            if(variant==9)flow[metadata+7]=0;
            if(variant==10){detail[metadata+7]=2;flow[metadata+7]=2;}
            auto d=departure_texture(device.Get(),width,height,detail);
            auto f=departure_texture(device.Get(),variant==11?width-1:width,height,flow);
            std::vector<float> queries;std::vector<double> expected;double analyticMax=0;
            for(float y:{-4.f,0.f,4.f})for(float x:{-4.f,0.f,4.f})
            {
                queries.insert(queries.end(),{ox+16+(variant==14?x+100:variant==15?-15:x),oy+16+y,-7,5});
                const bool valid=variant==0 || variant==1 || variant==2 || variant==6 || variant==10 || variant==12 ||
                    (variant==13 && x<0) || variant==15;
                double px=x,py=y,dt=.75/steps;
                for(U step=0;step<steps;++step)
                {
                    // Independent affine velocity formula, no texture or shader sampler.
                    auto velocity=[&](double a,double b){return std::pair<double,double>{
                        variant==1?.8*b+1:variant==2?-.7*b:variant==13?8.:1.25,
                        variant==1?2:variant==2?.7*a:-.75};};
                    const auto a=velocity(px,py),b=velocity(px-.5*dt*a.first,py-.5*dt*a.second);
                    px-=dt*b.first;py-=dt*b.second;
                }
                expected.insert(expected.end(),{valid?x-px:-7*.75,valid?y-py:5*.75,valid?(variant==15?.15625:double(enable)):0.,0.});
                if(variant==2)
                {
                    const double a=-.7*.75,ex=x*std::cos(a)-y*std::sin(a),ey=x*std::sin(a)+y*std::cos(a);
                    analyticMax=std::max(analyticMax,std::hypot(px-ex,py-ey));
                }
            }
            auto input=buffer(device.Get(),16,U(queries.size()/4),queries.data());auto output=buffer(device.Get(),16,U(queries.size()/4));
            struct Settings{float seconds,enable;U steps;float pad;} settings{.75f,enable,variant==16?0:steps,0};
            D3D11_BUFFER_DESC bd{};bd.ByteWidth=16;bd.Usage=D3D11_USAGE_IMMUTABLE;bd.BindFlags=D3D11_BIND_CONSTANT_BUFFER;
            D3D11_SUBRESOURCE_DATA initial{};initial.pSysMem=&settings;ComPtr<ID3D11Buffer> cb;check(device->CreateBuffer(&bd,&initial,&cb));
            ID3D11ShaderResourceView* srvs[]={d.Get(),f.Get(),input.srv.Get()};
            ID3D11UnorderedAccessView* uavs[]={output.uav.Get()};ID3D11Buffer* constants[]={cb.Get()};
            context->CSSetShader(shader.Get(),nullptr,0);context->CSSetShaderResources(0,3,srvs);
            context->CSSetUnorderedAccessViews(0,1,uavs,nullptr);context->CSSetConstantBuffers(0,1,constants);
            context->Dispatch(U(queries.size()/4),1,1);auto bits=download(device.Get(),context.Get(),output);
            for(U i=0;i<bits.size();++i){const double value=asfloat(bits[i]),error=std::abs(value-expected[i]);
                maximum=std::max(maximum,error);++checked;if(!std::isfinite(value) || error>1e-5)++wrong;}
            if(variant==2)rotationErrors.push_back(analyticMax);
            ID3D11ShaderResourceView* emptySRV[3]={};ID3D11UnorderedAccessView* emptyUAV[1]={};
            context->CSSetShaderResources(0,3,emptySRV);context->CSSetUnorderedAccessViews(0,1,emptyUAV,nullptr);
        }
        for(U i=1;i<rotationErrors.size();++i)if(rotationErrors[i-1]/rotationErrors[i]<3.8)++wrong;
        std::cout<<"variants=17 checked_words="<<checked<<" wrong="<<wrong<<" max_error="<<maximum
            <<" rotation_second_order="<<(wrong==0)<<" visual_accepted=0\n";
        return wrong?1:0;
    }
    catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
