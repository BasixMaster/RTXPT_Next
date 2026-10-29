#include "HdrCapture.h"
#include <array>
#include <fstream>
#include <iterator>
#include <iostream>
#include <vector>
#include <cstdint>
#include <filesystem>
int main(int argc,char** argv)
{
    if(argc!=2) return 2;
    const std::filesystem::path out(argv[1]);
    const std::array<uint32_t,6> padded = {0u,0x12345678u,0xdeadbeefu,0x89abcdefu,0x01020304u,0xdeadbeefu};
    std::string error;
    if(!rtxpt::WriteMappedPackedThroughput(padded.data(),12,2,2,out,error)) {std::cerr<<error; return 3;}
    std::ifstream file(out,std::ios::binary);
    const std::vector<unsigned char> bytes((std::istreambuf_iterator<char>(file)),{});
    const std::vector<unsigned char> expected = {'R','T','X','P','T','T','H','P',1,0,0,0,2,0,0,0,2,0,0,0,4,0,0,0,
        0,0,0,0,0x78,0x56,0x34,0x12,0xef,0xcd,0xab,0x89,4,3,2,1};
    if(bytes!=expected) {std::cerr<<"Golden header, row pitch, endian or row-order mismatch"; return 4;}
    const auto invalid=out.string()+".invalid";
    if(rtxpt::WriteMappedPackedThroughput(nullptr,12,2,2,invalid,error)) return 5;
    if(rtxpt::WriteMappedPackedThroughput(padded.data(),7,2,2,invalid,error)) return 6;
    if(rtxpt::WriteMappedPackedThroughput(padded.data(),12,0,2,invalid,error)) return 7;
    if(rtxpt::WriteMappedPackedThroughput(padded.data(),0,2,2,invalid,error)) return 8;
    if(std::filesystem::exists(invalid)) return 9;
    std::cout<<"Actual C++ writer: golden bytes, padded rows, boundaries and no invalid output passed\n";
    return 0;
}
