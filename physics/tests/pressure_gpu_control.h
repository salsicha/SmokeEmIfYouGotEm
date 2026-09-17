// Included after the standalone D3D/reflection utilities in transport_gpu_control.cpp.
// This dispatches production pressure + fused distributed PCG40, not CPU pressure.
struct PressureSpec { std::string name,file;int phase;bool prepare;U tag; };
std::vector<PressureSpec> pressure_specs()
{
    std::vector<PressureSpec> result;
    for(int p=0;p<7;++p)result.push_back({"pressure-"+std::to_string(p),"RaftSimNonlinearPressure.usf",p,false,U(p)});
    result.push_back({"acceleration-prepare","RaftSimNonlinearAcceleration.usf",0,true,7});
    for(int p:{1,2,3,4,5,6,11,12,13,14})
        result.push_back({"acceleration-"+std::to_string(p),"RaftSimNonlinearAcceleration.usf",p,false,U(p+7)});
    return result;
}
void compile_pressure(const fs::path& root,const fs::path& output,const std::string& only={})
{
    const auto specs=pressure_specs();
    if(!only.empty() && std::none_of(specs.begin(),specs.end(),[&](const PressureSpec& s){return s.name==only;}))
        throw std::runtime_error("Unknown pressure compile selection");
    if(fs::exists(output))throw std::runtime_error("Preserve previous pressure compile evidence");
    fs::create_directory(output);Includes includes;includes.root=fs::absolute(root);
    includes.exact=includes.root/"RaftSimExactHydrostatic.ush";
    for(const auto& spec:specs)
    {
        if(!only.empty() && spec.name!=only)continue;
        const auto bytes=read(includes.root/spec.file);std::string source(bytes.begin(),bytes.end());
        const std::string attribute="[numthreads(256,1,1)]";size_t pos=0;int entries=0;
        while((pos=source.find(attribute))!=std::string::npos){source.erase(pos,attribute.size());++entries;}
        if(entries!=(spec.file=="RaftSimNonlinearPressure.usf"?1:3))throw std::runtime_error("Unexpected pressure entry layout");
        const bool simple=spec.prepare || spec.file=="RaftSimNonlinearPressure.usf";
        source="#define MainCS ProductionMainCS\n"+source+
            "\n#undef MainCS\nRWStructuredBuffer<uint> HarnessTag;\n[numthreads(256,1,1)]\n"
            "void MainCS(uint3 id:SV_DispatchThreadID,uint3 group:SV_GroupID,uint lane:SV_GroupIndex) {"+
            (simple?std::string("ProductionMainCS(id);"):std::string("ProductionMainCS(id,group,lane);"))+
            "if(id.x==0){InterlockedAdd(HarnessTag["+std::to_string(spec.tag)+"],1u);"
            "HarnessTag[31]=HarnessTag[31]*16777619u+"+std::to_string(spec.tag+1)+"u;}}\n";
        const std::string phase=std::to_string(spec.phase);
        D3D_SHADER_MACRO macros[]={{"RAFTSIM_PRESSURE_PHASE",phase.c_str()},{"RAFTSIM_PRESSURE_BOUNDARY","0"},
            {"RAFTSIM_ACCELERATION_PREPARE",spec.prepare?"1":"0"},{"RAFTSIM_ACCELERATION_PHASE",phase.c_str()},{nullptr,nullptr}};
        ComPtr<ID3DBlob> code,errors;std::cout<<"compiling "<<spec.name<<std::endl;
        const HRESULT status=D3DCompile(source.data(),source.size(),spec.name.c_str(),macros,&includes,"MainCS","cs_5_0",
            D3DCOMPILE_OPTIMIZATION_LEVEL3|D3DCOMPILE_ENABLE_BACKWARDS_COMPATIBILITY|D3DCOMPILE_PACK_MATRIX_ROW_MAJOR,0,&code,&errors);
        if(errors){std::ofstream log(output/(spec.name+".log"),std::ios::binary);log.write(static_cast<const char*>(errors->GetBufferPointer()),errors->GetBufferSize());}
        check(status);std::ofstream file(output/(spec.name+".cso"),std::ios::binary);
        file.write(static_cast<const char*>(code->GetBufferPointer()),code->GetBufferSize());
        if(!file)throw std::runtime_error("Cannot retain pressure bytecode");
    }
}
std::vector<U> float_words(std::initializer_list<float> input)
{
    std::vector<U> words(input.size());std::memcpy(words.data(),input.begin(),words.size()*4);return words;
}
bool test_pressure_activity_guard(const fs::path& bytecode,bool warp)
{
    ComPtr<ID3D11Device> device;ComPtr<ID3D11DeviceContext> context;
    D3D_FEATURE_LEVEL level=D3D_FEATURE_LEVEL_11_0,got;
    check(D3D11CreateDevice(nullptr,warp?D3D_DRIVER_TYPE_WARP:D3D_DRIVER_TYPE_HARDWARE,
        nullptr,0,&level,1,D3D11_SDK_VERSION,&device,&got,&context));
    const auto program=shader(device.Get(),bytecode);bool passed=true;U cases=0;
    // Actual production phase 6, with an identity operator and exact integer
    // sums. Include partial final groups, multi-group dispatch, each active
    // pole, signed zero, and invalid-input early return. Sentinels prove that
    // inactive/invalid dispatches leave outputs untouched rather than simply
    // producing the same zero-force result as a skipped solve.
    const U flags[][2]={{0,0},{0x80000000u,0},{0x3f800000u,0},{0,0x3f800000u},{0x3f800000u,0x3f800000u}};
    for(U rows:{13u,33u})for(const auto& active:flags)for(U invalid:{0u,1u})
    {
        const U count=17*rows,groups=(count+255)/256;
        Buffers b;std::vector<float> direction(count*4),sentinel(count*4,-7.f),partial(groups*4,-9.f),fraction(count,1.f);
        for(U i=0;i<count*4;++i)direction[i]=float(i%4+1);
        for(auto name:{"Center","Edges"})b.emplace(name,buffer(device.Get(),16,count));
        b.emplace("Direction",buffer(device.Get(),16,count,direction.data()));
        b.emplace("Scratch",buffer(device.Get(),16,count,sentinel.data()));
        b.emplace("WValue",buffer(device.Get(),8,count));
        b.emplace("Partial",buffer(device.Get(),16,groups,partial.data()));
        b.emplace("NonbreakingFraction",buffer(device.Get(),4,count,fraction.data()));
        U control[20]={};control[12]=active[0];control[13]=active[1];
        U diagnostics[4]={invalid,0,0,0};
        b.emplace("Control",buffer(device.Get(),16,5,control));
        b.emplace("Diagnostics",buffer(device.Get(),4,4,diagnostics));
        b.emplace("HarnessTag",buffer(device.Get(),4,32));
        Constants values{{"GridSize",{17,rows}},{"Lengths",float_words({.4052787713439809f,.03916567310046354f})},
            {"UseDispersionFraction",{1}}};
        dispatch(device.Get(),context.Get(),program,b,values,groups);
        const bool running=invalid==0 && ((active[0]|active[1])&0x7fffffffu)!=0;
        const auto scratch=download(device.Get(),context.Get(),b.at("Scratch"));
        std::vector<U> expectedScratch(count*4);const auto& expected=running?direction:sentinel;
        std::memcpy(expectedScratch.data(),expected.data(),expectedScratch.size()*4);
        if(running)for(U g=0;g<groups;++g)
        {const U cells=std::min(256u,count-256*g);partial[4*g]=float(5*cells);partial[4*g+1]=float(25*cells);partial[4*g+2]=partial[4*g+3]=0;}
        std::vector<U> expectedPartial(groups*4);std::memcpy(expectedPartial.data(),partial.data(),expectedPartial.size()*4);
        const auto tags=download(device.Get(),context.Get(),b.at("HarnessTag"));
        std::vector<U> expectedTags(32);expectedTags[13]=1;expectedTags[31]=14;
        const bool match=scratch==expectedScratch && download(device.Get(),context.Get(),b.at("Partial"))==expectedPartial && tags==expectedTags;
        passed &= match;++cases;
        std::cout<<"guard_case="<<cases<<" cells="<<count<<" invalid="<<invalid<<" active_bits="<<active[0]<<'/'<<active[1]<<" pass="<<match<<'\n';
    }
    std::cout<<"activity_guard_cases="<<cases<<" activity_guard_pass="<<passed<<" step_accepted=0\n";
    return passed;
}
bool run_pressure(ID3D11Device* device,ID3D11DeviceContext* context,const std::vector<Shader>& shaders,
    Buffers& transport,Constants values,U count,U groups,const std::vector<float>& fraction,
    const std::vector<float>& expectedForce,U index,const fs::path& trace={})
{
    // Same-stage native GPU buffers are shared directly. Expected CPU rates,
    // graph, geometry, slopes and force are NEVER uploaded as pressure inputs.
    Buffers b;
    for(auto name:{"State","HydroRate","Geometry","Pairs","PhysicalBedSlope"})b.emplace(name,transport.at(name));
    b.emplace("NonbreakingFraction",buffer(device,4,count,fraction.data()));
    for(auto name:{"Velocity","Base","BaseW","Force","WValue"})b.emplace(name,buffer(device,8,count));
    for(auto name:{"Terms","Forcing","RightHandSide","Pressure","Center","Edges","Diagonal","Solution","Residual","Direction","Scratch","TrueResidual"})
        b.emplace(name,buffer(device,16,count));
    b.emplace("PressureDiagnostics",buffer(device,4,4));b.emplace("SolverDiagnostics",buffer(device,4,4));
    b.emplace("HarnessTag",buffer(device,4,32));b.emplace("Partial",buffer(device,16,groups));
    b.emplace("NextPartial",buffer(device,16,groups));b.emplace("PartialExponents",buffer(device,8,groups));
    b.emplace("Control",buffer(device,16,5));b.emplace("NextControl",buffer(device,16,3));
    for(auto name:{"Center","Edges","Diagonal"})b.emplace(std::string("Prepared")+name,b.at(name));
    for(auto name:{"Direction","Scratch","Partial","Control"})b.emplace(std::string(name)+"Input",b.at(name));
    b.emplace("Correction",b.at("Solution"));
    values["Lengths"]=float_words({.4052787713439809f,.03916567310046354f});
    values["PoleWeights"]=float_words({.8106202879112342f,.12271304542209915f});
    values["UsePhysicalBedSlope"]={1};values["UseDispersionFraction"]={1};values["Iteration"]={0};
    const auto specs=pressure_specs();std::vector<U> tags(32,0);
    const bool tracing=index==2 && !trace.empty();
    U traceDispatch=0;
    if(tracing)
    {
        if(fs::exists(trace))throw std::runtime_error("Preserve previous pressure trace");
        fs::create_directory(trace);
    }
    const auto run=[&](const std::string& name,U dispatchGroups)
    {
        const auto it=std::find_if(specs.begin(),specs.end(),[&](const PressureSpec& s){return s.name==name;});
        if(it==specs.end())throw std::runtime_error("Unknown pressure dispatch");
        const U slot=U(it-specs.begin());dispatch(device,context,shaders.at(slot),b,values,dispatchGroups);
        ++tags[it->tag];tags[31]=tags[31]*16777619u+it->tag+1u;
        if(tracing && (values.at("Iteration")[0]<2 || values.at("Iteration")[0]==39))
        {
            const auto directory=trace/(std::to_string(traceDispatch++)+"-"+name+"-iter"+std::to_string(values.at("Iteration")[0]));
            if(fs::exists(directory))throw std::runtime_error("Repeated trace stage");
            fs::create_directory(directory);
            for(auto field:{"RightHandSide","Center","Edges","Diagonal","Solution","Residual","Direction","Scratch","WValue","Partial","NextPartial","Control","NextControl","PartialExponents","TrueResidual"})
            {
                const auto data=download(device,context,b.at(field));
                std::ofstream out(directory/(std::string(field)+".bin"),std::ios::binary);
                out.write(reinterpret_cast<const char*>(data.data()),data.size()*sizeof(U));
                if(!out)throw std::runtime_error("Failed to retain pressure trace");
            }
        }
    };
    b["Diagnostics"]=b.at("PressureDiagnostics");
    for(int p=0;p<=4;++p)run("pressure-"+std::to_string(p),groups);
    b["Diagnostics"]=b.at("SolverDiagnostics");
    run("acceleration-prepare",groups);
    run("acceleration-1",groups);run("acceleration-2",1);
    run("acceleration-3",groups);run("acceleration-4",1);
    for(U iteration=0;iteration<40;++iteration)
    {
        values["Iteration"]={iteration};
        for(int p:{5,6,13,14})run("acceleration-"+std::to_string(p),groups);
    }
    values["Iteration"]={0};
    for(int p:{11,5,12})run("acceleration-"+std::to_string(p),groups);
    b["Diagnostics"]=b.at("PressureDiagnostics");
    run("pressure-5",groups);run("pressure-6",groups);
    const bool tagMatch=download(device,context,b.at("HarnessTag"))==tags;
    bool passed=tagMatch && compare(download(device,context,b.at("Force")),expectedForce,"coupled_force",index);
    const auto pd=download(device,context,b.at("PressureDiagnostics")),sd=download(device,context,b.at("SolverDiagnostics"));
    passed &= pd[0]==0 && pd[1]==0 && sd[0]==0 && sd[1]==0 && sd[2]<=40 && sd[3]<=40;
    const auto residual=download(device,context,b.at("TrueResidual")),rhs=download(device,context,b.at("RightHandSide"));
    double r2=0,b2=0;
    for(U i=0;i<count*4;++i)
    {
        const double r=asfloat(residual[i]),v=asfloat(rhs[i]);passed &= std::isfinite(r) && std::isfinite(v);
        r2+=r*r;b2+=v*v;
    }
    const double relative=std::sqrt(b2>0?r2/b2:r2);passed &= relative<2e-5;
    std::cout<<"case="<<index<<" pressure_tags="<<tagMatch<<" true_residual="<<relative
        <<" pressure_diagnostics="<<pd[0]<<'/'<<pd[1]<<" solver_diagnostics="<<sd[0]<<'/'<<sd[1]
        <<" iterations="<<sd[2]<<'/'<<sd[3]<<" coupled_pressure_pass="<<passed<<std::endl;
    return passed;
}
