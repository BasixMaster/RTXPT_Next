/* SPDX-License-Identifier: LicenseRef-NvidiaProprietary
 * Application-owned PT++ duplication count producer. See root LICENSE. */
#pragma pack_matrix(row_major)
#include "Bridge.hlsli"

// A 16x16 output tile needs a radius8 halo. Count the 288 other positions
// in the 17x17 window, ignoring empty sample IDs and clipping to the SDK's
// RG8_UNORM count range. Store integer counts directly (no texture rounding).
groupshared uint s_SampleIDs[32][32];

uint LoadSampleID(int2 pixel, uint2 dims)
{
    if (any(pixel < 0) || any(pixel >= int2(dims))) return 0;
    uint2 pos = RTXDI_PixelPosToReservoirPos(pixel, g_RtxdiBridgeConst.runtimeParams.activeCheckerboardField);
    RTXDI_PackedPTReservoir packed = RTXDI_LoadPackedPTReservoir(
        g_RtxdiBridgeConst.restirPT.reservoirBuffer, pos,
        g_RtxdiBridgeConst.restirPT.bufferIndices.finalShadingInputBufferIndex);
    return asfloat(packed.Data0.w) == 0 ? 0u : packed.Data3.w;
}

[numthreads(16,16,1)]
void main(uint2 groupID : SV_GroupID, uint2 tid : SV_GroupThreadID)
{
    uint2 dims = uint2(g_Const.ptConsts.imageWidth,g_Const.ptConsts.imageHeight);
    int2 base = int2(groupID)*16 - 8;
    [unroll] for (int y=0;y<2;++y)
        [unroll] for (int x=0;x<2;++x)
        {
            int2 tile = int2(tid)*2 + int2(x,y);
            s_SampleIDs[tile.y][tile.x] = LoadSampleID(base+tile,dims);
        }
    GroupMemoryBarrierWithGroupSync();
    uint2 pixel = groupID*16 + tid;
    if (any(pixel >= dims)) return;
    uint own = s_SampleIDs[tid.y+8][tid.x+8];
    uint count = 0;
    if (own != 0)
        [unroll] for (int y=-8;y<=8;++y)
            [unroll] for (int x=-8;x<=8;++x)
                count += ((x|y)!=0 && s_SampleIDs[int(tid.y)+8+y][int(tid.x)+8+x]==own) ? 1u : 0u;
    u_PTDuplicationMap[pixel.y*dims.x+pixel.x] = min(count,255u);
    if (g_RtxdiBridgeConst.ptDiagnostics != 0) InterlockedAdd(u_PTDiagnosticCounters[99],1);
}
