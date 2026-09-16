// Compile the actual scalar shader helper as C++; no copied candidate logic.
// Expected results come from the independent exact-rational Python fixture.
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <intrin.h>
using uint=std::uint32_t;
uint asuint(float value){uint bits;std::memcpy(&bits,&value,4);return bits;}
float asfloat(uint bits){float value;std::memcpy(&value,&bits,4);return value;}
int firstbithigh(uint value){unsigned long index;return _BitScanReverse(&index,value)?int(index):-1;}
#include "../../unreal/Plugins/RaftSim/Shaders/Private/RaftSimPortableAdd.ush"
int main(int argc,char** argv)
{
    if(argc!=2)return 2;
    std::ifstream file(argv[1],std::ios::binary);uint header[3]={};
    file.read(reinterpret_cast<char*>(header),sizeof(header));
    if(!file || header[0]!=0x52534650 || header[1]!=10 || header[2]<32 || header[2]>65536)return 2;
    uint wrong=0;
    for(uint i=0;i<header[2];++i)
    {
        uint record[5];file.read(reinterpret_cast<char*>(record),sizeof(record));if(!file)return 2;
        uint actual=asuint(RaftSimPortableAdd(asfloat(record[0]),asfloat(record[1])));
        if(actual!=record[4])
        {if(wrong<16)std::cerr<<"case "<<i<<std::hex<<" a="<<record[0]<<" b="<<record[1]<<" expected="<<record[4]<<" actual="<<actual<<std::dec<<'\n';++wrong;}
    }
    char extra;if(file.read(&extra,1))return 2;
    std::cout<<"cases="<<header[2]<<" mismatches="<<wrong<<'\n';return wrong?1:0;
}
