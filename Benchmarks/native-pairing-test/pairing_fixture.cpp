#include "PairingTables.h"
#include <fstream>
#include <iostream>
#include <string>

void Require(bool condition,const char* message)
{
    if (!condition) throw std::runtime_error(message);
}
int main(int argc,char** argv)
{
    try
    {
        const auto all=rtxpt::pairing::GenerateAll();
        Require(all.size()==rtxpt::pairing::EntryCount,"Table entry count");
        const auto repeat=rtxpt::pairing::GenerateAll();
        size_t base=0;
        std::cout<<"{\"tables\":[";
        bool comma=false;
        for (auto n:rtxpt::pairing::Sizes)
        {
            double x2=0,y2=0,radius=0;
            for (uint32_t y=0;y<n;++y) for (uint32_t x=0;x<n;++x)
            {
                const size_t i=base+y*n+x;
                const auto d=all[i];
                Require(d.x==repeat[i].x && d.y==repeat[i].y,"Determinism");
                Require(d.x!=0 || d.y!=0,"No self links");
                Require(std::abs(d.x)<=int(n/2) && std::abs(d.y)<=int(n/2),"Signed wrapped bounds");
                const auto xx=uint32_t((int(x)+d.x+int(n))%int(n));
                const auto yy=uint32_t((int(y)+d.y+int(n))%int(n));
                const auto reverse=all[base+yy*n+xx];
                Require(reverse.x==-d.x && reverse.y==-d.y,"Exact reciprocal offsets");
                x2+=double(d.x)*d.x; y2+=double(d.y)*d.y;
                radius+=std::sqrt(double(d.x)*d.x+double(d.y)*d.y);
            }
            const double sx=std::sqrt(x2/(n*n)),sy=std::sqrt(y2/(n*n)),r=radius/(n*n);
            Require(sx>14 && sx<18 && sy>14 && sy<18 && r>18 && r<22,"Gaussian-scale radial moments");
            if (comma) std::cout<<","; comma=true;
            std::cout<<"{\"size\":"<<n<<",\"rms_x\":"<<sx<<",\"rms_y\":"<<sy<<",\"mean_radius\":"<<r<<"}";
            base+=n*n;
        }
        bool rejected=false;
        try { rtxpt::pairing::Generate(255,16,1); } catch (const std::invalid_argument&) { rejected=true; }
        Require(rejected,"Odd-size rejection");
        if (argc>1)
        {
            std::ofstream output(argv[1],std::ios::binary);
            output.write(reinterpret_cast<const char*>(all.data()),all.size()*sizeof(all[0]));
            Require(bool(output),"Native bytes written");
        }
        std::cout<<"],\"entries\":"<<all.size()<<",\"bytes\":"<<all.size()*sizeof(all[0])<<"}\n";
    }
    catch (const std::exception& e) { std::cerr<<e.what()<<"\n"; return 1; }
}
