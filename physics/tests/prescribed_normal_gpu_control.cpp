// Isolated execution of the CURRENT prescribed-normal function with the
// captured engine-preprocessed DoubleFloat definitions. Not an engine replay.
#define main transport_control_unused_main
#include "transport_gpu_control.cpp"
#undef main
int main(int argc,char** argv)
{
    try
    {
        if(argc==6 && std::string(argv[1])=="compile")
        {
            const fs::path root=fs::absolute(argv[2]),out=argv[4];
            if(fs::exists(out))throw std::runtime_error("Preserve prior normal bytecode");
            auto prefixBytes=read(argv[3]);std::string source(prefixBytes.begin(),prefixBytes.end());
            const std::string function="float3 RaftSimLiquidPrescribedNormalPosition(";
            auto at=source.find(function);if(at==std::string::npos)throw std::runtime_error("Missing captured function boundary");
            source.resize(at);
            const auto current=read(root/"RaftSimLiquidPrescribedNormal.ush");std::string body(current.begin(),current.end());
            at=body.find("// Finish an ALREADY prescribed");if(at==std::string::npos)throw std::runtime_error("Missing current function section");
            source+="#include \"RaftSimPortableClock.ush\"\n"+body.substr(at);
            const auto kernel=read(root/"RaftSimLiquidPrescribedNormalTest.usf");body.assign(kernel.begin(),kernel.end());
            at=body.find("uint Cases;");if(at==std::string::npos)throw std::runtime_error("Missing original test kernel");
            source+=body.substr(at);
            const bool strict=std::string(argv[5])=="strict";
            if(!strict && std::string(argv[5])!="normal")return 2;
            Includes includes;includes.root=root;includes.exact=root/"RaftSimExactHydrostatic.ush";
            ComPtr<ID3DBlob> code,errors;
            HRESULT h=D3DCompile(source.data(),source.size(),"current-normal-captured-engine-prefix",nullptr,&includes,"MainCS","cs_5_0",
                D3DCOMPILE_OPTIMIZATION_LEVEL3|D3DCOMPILE_ENABLE_BACKWARDS_COMPATIBILITY|D3DCOMPILE_PACK_MATRIX_ROW_MAJOR|
                (strict?D3DCOMPILE_IEEE_STRICTNESS:0),0,&code,&errors);
            if(errors)std::cerr.write(static_cast<const char*>(errors->GetBufferPointer()),errors->GetBufferSize());
            check(h);std::ofstream output(out,std::ios::binary);output.write(static_cast<const char*>(code->GetBufferPointer()),code->GetBufferSize());
            if(!output)throw std::runtime_error("Normal bytecode write failed");return 0;
        }
        if(argc!=5 || std::string(argv[1])!="run" ||
            (std::string(argv[4])!="hardware" && std::string(argv[4])!="warp"))return 2;
        std::ifstream fixture(argv[3],std::ios::binary);
        if(word<U>(fixture)!=0x52534e50u || word<U>(fixture)!=1)return 2;
        const U count=word<U>(fixture);if(count<1 || count>4096)return 2;
        const auto input=array<U>(fixture,16*count),expected=array<U>(fixture,4*count);char extra;
        if(fixture.read(&extra,1))return 2;
        ComPtr<ID3D11Device> device;ComPtr<ID3D11DeviceContext> context;
        const D3D_FEATURE_LEVEL level=D3D_FEATURE_LEVEL_11_0;D3D_FEATURE_LEVEL obtained;
        check(D3D11CreateDevice(nullptr,std::string(argv[4])=="warp"?D3D_DRIVER_TYPE_WARP:D3D_DRIVER_TYPE_HARDWARE,
            nullptr,0,&level,1,D3D11_SDK_VERSION,&device,&obtained,&context));
        Buffers buffers;buffers.emplace("Inputs",buffer(device.Get(),16,4*count,input.data()));
        buffers.emplace("Results",buffer(device.Get(),16,count));
        const auto code=shader(device.Get(),argv[2]);dispatch(device.Get(),context.Get(),code,buffers,{{"Cases",{count}}},(count+63)/64);
        const auto actual=download(device.Get(),context.Get(),buffers.at("Results"));U wrong=0;
        for(U i=0;i<4*count;++i)if(actual[i]!=expected[i])
        {if(wrong<32)std::cerr<<"case="<<i/4<<" component="<<i%4<<std::hex<<" expected="<<expected[i]<<" actual="<<actual[i]<<std::dec<<'\n';++wrong;}
        std::cout<<"backend="<<argv[4]<<" cases="<<count<<" normal_word_errors="<<wrong<<" native_or_gameplay_accepted=0\n";
        return wrong?1:0;
    }
    catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 2;}
}
