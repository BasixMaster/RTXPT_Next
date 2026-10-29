/* SPDX-License-Identifier: LicenseRef-NvidiaProprietary
 * RTXPT Next integration of the NVIDIA RTXDI PT runtime. See root LICENSE. */
#pragma pack_matrix(row_major)
#include "Bridge.hlsli"

[numthreads(RTXDI_SCREEN_SPACE_GROUP_SIZE, RTXDI_SCREEN_SPACE_GROUP_SIZE, 1)]
void main(uint2 thread : SV_DispatchThreadID)
{
    uint2 pixel = RTXDI_ReservoirPosToPixelPos(thread, g_RtxdiBridgeConst.runtimeParams.activeCheckerboardField);
    if (any(pixel >= uint2(g_Const.ptConsts.imageWidth, g_Const.ptConsts.imageHeight))) return;
    RAB_Surface surface = RAB_GetGBufferSurface(pixel, false);
    if (!RAB_IsSurfaceValid(surface)) return;
    RTXDI_PTReservoir r = RTXDI_LoadPTReservoir(g_RtxdiBridgeConst.restirPT.reservoirBuffer,
        thread, g_RtxdiBridgeConst.restirPT.bufferIndices.finalShadingInputBufferIndex);
    if (!RTXDI_IsValidPTReservoir(r)) return;
    if (g_RtxdiBridgeConst.giPTPartition != 0 && r.pathLength < 4) return;
    // targetFunction already includes the primary BSDF. Multiplying it again
    // would double-apply the primary surface's response.
    float3 radiance = r.targetFunction * r.weightSum;
    if ((g_RtxdiBridgeConst.giPTPartition & 2u) != 0)
    {
        // Dedicated pilot alias of the inactive CGNS scratch buffer. Scalar
        // reservoir history stays separate from this conditional RGB mean.
        uint address = (pixel.y * g_Const.ptConsts.imageWidth + pixel.x) * 16;
        radiance = asfloat(u_PTSpatialNeighbors.Load3(address));
    }
    if (any(isnan(radiance)) || any(isinf(radiance))) return;
    float3 direction = normalize(r.translatedWorldPosition - surface.GetPosW());
    if (r.rcVertexLength > 2)
    {
        RTXDI_RandomSamplerState rng = RTXDI_GetRngForShading(r);
        direction = RTXPT_PTSampleBsdf(surface, rng).outDirection;
    }
    float4 bsdf = surface.Eval(direction);
    float specularFraction = saturate(bsdf.a / max(Average(bsdf.rgb), 1e-20));
    float4 contribution = float4(radiance, Average(radiance) * specularFraction);
    if (g_Const.ptConsts.denoisingEnabled)
    {
        uint address = DenoisingLayersContext::ComputeDominantAddress(pixel,
            u_DenoisingLayersHeader, u_DenoisingLayersBuffer, u_StableRadiance, g_Const.ptConsts);
        float4 current = Fp16ToFp32(u_DenoisingLayersBuffer[address].PackedNoisyRadianceAndSpecAvg);
        u_DenoisingLayersBuffer[address].PackedNoisyRadianceAndSpecAvg = Fp32ToFp16(current + contribution);
    }
    else
        u_OutputColor[pixel] += float4(radiance, 0);
}
