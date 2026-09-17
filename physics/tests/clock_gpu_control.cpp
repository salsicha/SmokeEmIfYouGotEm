// Compile/execute the ORIGINAL step phase4 with reflected resource bindings.
// Reuse the established standalone D3D device/buffer/dispatch implementation.
// No CPU clock value is injected after dispatch; every output word is checked.
#define main transport_control_unused_main
#include "transport_gpu_control.cpp"
#undef main

int main(int argc,char** argv)
{
    try
    {
        if(argc==4 && std::string(argv[1])=="compile")
        {
            const fs::path root=fs::absolute(argv[2]),out=argv[3];
            if(fs::exists(out))throw std::runtime_error("Preserve previous clock bytecode");
            Includes includes;includes.root=root;includes.exact=root/"RaftSimExactHydrostatic.ush";
            const auto source=read(root/"RaftSimTotalDepthStep.usf");
            D3D_SHADER_MACRO macros[]={{"RAFTSIM_STEP_PHASE","4"},{nullptr,nullptr}};
            ComPtr<ID3DBlob> code,errors;
            HRESULT h=D3DCompile(source.data(),source.size(),"production-step-clock",macros,&includes,"MainCS","cs_5_0",
                D3DCOMPILE_OPTIMIZATION_LEVEL3|D3DCOMPILE_ENABLE_BACKWARDS_COMPATIBILITY|D3DCOMPILE_PACK_MATRIX_ROW_MAJOR,
                0,&code,&errors);
            if(errors)std::cerr.write(static_cast<const char*>(errors->GetBufferPointer()),errors->GetBufferSize());
            check(h);std::ofstream output(out,std::ios::binary);
            output.write(static_cast<const char*>(code->GetBufferPointer()),code->GetBufferSize());
            if(!output)throw std::runtime_error("Clock bytecode write failed");
            return 0;
        }
        if(argc!=5 || std::string(argv[1])!="run" ||
           (std::string(argv[4])!="hardware" && std::string(argv[4])!="warp"))return 2;
        std::ifstream fixture(argv[3],std::ios::binary);
        if(word<U>(fixture)!=0x5253434cu || word<U>(fixture)!=1)return 2;
        const U count=word<U>(fixture);if(count<1 || count>4096)return 2;
        // Validate the complete fixture before creating a device or dispatching.
        const auto records=array<U>(fixture,27*count);char extra;
        if(fixture.read(&extra,1))return 2;
        ComPtr<ID3D11Device> device;ComPtr<ID3D11DeviceContext> context;
        const D3D_FEATURE_LEVEL level=D3D_FEATURE_LEVEL_11_0;D3D_FEATURE_LEVEL obtained;
        check(D3D11CreateDevice(nullptr,std::string(argv[4])=="warp"?D3D_DRIVER_TYPE_WARP:D3D_DRIVER_TYPE_HARDWARE,
            nullptr,0,&level,1,D3D11_SDK_VERSION,&device,&obtained,&context));
        const auto code=shader(device.Get(),argv[2]);U wrong=0;
        for(U i=0;i<count;++i)
        {
            const U* p=records.data()+27*i;
            Buffers buffers;
            buffers.emplace("InputProgress",buffer(device.Get(),16,1,p));
            buffers.emplace("Info",buffer(device.Get(),16,1,p+4));
            buffers.emplace("Diagnostics",buffer(device.Get(),4,4,p+8));
            buffers.emplace("OutputProgress",buffer(device.Get(),16,1));
            Constants values={{"UseIntervalEnd",{p[12]}},{"IntervalEnd",{p[13],p[14]}}};
            dispatch(device.Get(),context.Get(),code,buffers,values,1);
            U offset=15;
            for(const char* field:{"OutputProgress","Info","Diagnostics"})
            {
                const auto actual=download(device.Get(),context.Get(),buffers.at(field));
                for(U j=0;j<4;++j)
                {
                    if(actual[j]!=p[offset+j])
                    {
                        if(wrong<32)std::cerr<<"case="<<i<<" field="<<field<<" word="<<j<<std::hex
                            <<" expected="<<p[offset+j]<<" actual="<<actual[j]<<std::dec<<'\n';
                        ++wrong;
                    }
                }
                offset+=4;
            }
        }
        std::cout<<"backend="<<argv[4]<<" cases="<<count<<" clock_word_errors="<<wrong
                 <<" full_step_or_gameplay_accepted=0\n";
        return wrong?1:0;
    }
    catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 2;}
}
