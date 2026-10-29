/* Application-owned implementation of the PT++ section3 link-shuffle construction.
 * SPDX-License-Identifier: LicenseRef-NvidiaProprietary */
#pragma once
#include <array>
#include <cmath>
#include <cstdint>
#include <stdexcept>
#include <vector>

namespace rtxpt::pairing
{
struct Offset { int32_t x, y; };
static_assert(sizeof(Offset) == 8);
inline constexpr std::array<uint32_t,3> Sizes = {254,230,210};
inline constexpr float Sigma = 16.0f;
inline constexpr uint32_t EntryCount = 254*254+230*230+210*210;

class Random
{
    uint32_t state;
public:
    explicit Random(uint32_t seed) : state(seed ? seed : 1u) {}
    uint32_t Next() { state ^= state<<13; state ^= state>>17; state ^= state<<5; return state; }
    uint32_t Bounded(uint32_t count)
    {
        const uint32_t threshold = (0u-count)%count;
        uint32_t x;
        do { x=Next(); } while (x<threshold);
        return x%count;
    }
};

inline std::vector<Offset> Generate(uint32_t size, double sigma, uint32_t seed)
{
    if (size<2 || size>254 || size%2 || !std::isfinite(sigma) || sigma<.8 || sigma>64)
        throw std::invalid_argument("Pairing tables require even size2..254 and finite sigma0.8..64");
    std::vector<uint32_t> links(size*size);
    for (uint32_t i=0;i<links.size();++i) links[i]=i/2;
    Random rng(seed);
    const uint32_t rounds=uint32_t(std::floor(sigma*sigma/2+1.46/sigma+1.76/(sigma*sigma)+.656/(sigma*sigma*sigma)+.5));
    for (uint32_t round=0;round<rounds;++round)
        for (uint32_t y=0;y<size;y+=2)
            for (uint32_t x=0;x<size;x+=2)
            {
                const uint32_t o=round%2;
                std::array<uint32_t,4> cells={((y+o)%size)*size+(x+o)%size,
                    ((y+o)%size)*size+(x+o+1)%size,
                    ((y+o+1)%size)*size+(x+o)%size,
                    ((y+o+1)%size)*size+(x+o+1)%size};
                for (uint32_t i=3;i>0;--i)
                    std::swap(links[cells[i]],links[cells[rng.Bounded(i+1)]]);
            }
    std::vector<uint32_t> first(size*size/2,~0u);
    std::vector<Offset> offsets(size*size);
    for (uint32_t i=0;i<links.size();++i)
    {
        auto& other=first[links[i]];
        if (other==~0u) { other=i; continue; }
        int32_t dx=int32_t(i%size)-int32_t(other%size);
        int32_t dy=int32_t(i/size)-int32_t(other/size);
        const int32_t half=int32_t(size/2);
        if (dx>half) dx-=size; else if (dx<-half) dx+=size;
        if (dy>half) dy-=size; else if (dy<-half) dy+=size;
        offsets[other]={dx,dy}; offsets[i]={-dx,-dy};
    }
    return offsets;
}

inline std::vector<Offset> GenerateAll()
{
    std::vector<Offset> data; data.reserve(EntryCount);
    uint32_t seed=0x50545050u;
    for (auto size:Sizes)
    {
        auto table=Generate(size,Sigma,seed++);
        data.insert(data.end(),table.begin(),table.end());
    }
    return data;
}
}
