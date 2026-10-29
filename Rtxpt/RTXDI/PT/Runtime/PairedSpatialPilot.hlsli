/* SPDX-License-Identifier: LicenseRef-NvidiaProprietary
 * Application-owned reciprocal-pair/vector-shading development pilot.
 * Adjacent pairs isolate the estimator/scheduling prerequisite; Gaussian
 * pairing textures and replay compaction are separate remaining B10 work. */
#ifndef RTXPT_PAIRED_SPATIAL_PILOT_HLSLI
#define RTXPT_PAIRED_SPATIAL_PILOT_HLSLI
#include "PairingLookup.hlsli"

bool RTXPT_PairDiagnostics()
{
#ifdef RTXPT_SUPPRESS_PAIR_DIAGNOSTICS
    return false;
#else
    return g_RtxdiBridgeConst.ptDiagnostics != 0;
#endif
}

struct RTXPT_PairShift
{
    RTXDI_PTReservoir sample;
    float3 target;
    float jacobian;
};

// Unpacked reservoir88 + target12 + Jacobian4. No lossy history repacking
// occurs between shift evaluation and resampling in the queue schedule.
RWStructuredBuffer<RTXPT_PairShift> u_PTShiftCache : register(u22 VK_DESCRIPTOR_SET(2));
RWStructuredBuffer<uint> u_PTReplayQueue : register(u23 VK_DESCRIPTOR_SET(2));
RWByteAddressBuffer u_PTReplayControl : register(u24 VK_DESCRIPTOR_SET(2));
RWByteAddressBuffer u_PTReplayOracle : register(u25 VK_DESCRIPTOR_SET(2));
RWByteAddressBuffer u_PTReplayArgs : register(u26 VK_DESCRIPTOR_SET(2));

uint2 RTXPT_PairPartner(uint2 pixel)
{
    [branch] if ((g_RtxdiBridgeConst.giPTPartition & 4u) != 0)
        return uint2(RTXPT_GaussianPartner(pixel));
    return uint2(pixel.x ^ 1u, pixel.y);
}

RTXPT_PairShift RTXPT_PairShiftTo(RTXDI_PTReservoir source, RAB_Surface sourceSurface,
    RAB_Surface destination, uint2 destinationPixel, RTXDI_PTSpatialResamplingRuntimeParameters params)
{
    RTXPT_PairShift shifted = (RTXPT_PairShift)0;
    shifted.sample = source;
    if (source.M <= 0 || source.weightSum <= 0) return shifted;
    if (RTXPT_PairDiagnostics()) InterlockedAdd(u_PTDiagnosticCounters[41], 1);
    float jacobian = RTXDI_CalculateJacobian(RAB_GetSurfaceWorldPos(destination),
        RAB_GetSurfaceWorldPos(sourceSurface), source.translatedWorldPosition, source.worldNormal);
    float3 target = 1;
    bool reconnect = ShouldEvaluateSpatialReconnection(source);
    RAB_PathTracerUserData user = RAB_EmptyPathTracerUserData();
    user.pixelPosition = destinationPixel;
    RAB_PathTracerUserDataSetPathType(user, RTXDI_PTPathTraceInvocationType_Spatial);
    RTXDI_ComputeHybridShift(destination, shifted.sample, g_RtxdiBridgeConst.restirPT.hybridShift,
        BuildHSParams(params), g_RtxdiBridgeConst.restirPT.reconnection, target, jacobian, user);
    if (reconnect) EvaluateReconnection(g_RtxdiBridgeConst.restirPT.hybridShift, target, destination, shifted.sample);
    if (jacobian > 0 && isfinite(jacobian) && all(isfinite(target)) && all(target >= 0))
    {
        shifted.target = target;
        shifted.jacobian = jacobian;
    }
    return shifted;
}

uint2 RTXPT_PairSourceNormal(uint2 pixel)
{
    RTXDI_PackedPTReservoir input=RTXDI_LoadPackedPTReservoir(g_RtxdiBridgeConst.restirPT.reservoirBuffer,
        RTXDI_PixelPosToReservoirPos(pixel,g_RtxdiBridgeConst.runtimeParams.activeCheckerboardField),
        g_RtxdiBridgeConst.restirPT.bufferIndices.spatialResamplingInputBufferIndex);
    return uint2(input.Data1.x,input.Data1.y & 0xffffu);
}

void RTXPT_PairStore(uint2 pixel, RTXDI_PTReservoir sample, float3 vectorRadiance, uint2 sourceNormal)
{
    // Initial RIS can retain M=1 for a zero-length, zero-contribution path.
    // The SDK unpacker normalizes its zero placeholder normal, yielding NaN;
    // encoding that NaN gives shader-dependent unused history bits. Keep M
    // and every estimator field, but canonicalize only this absent-path normal.
    bool absent = sample.pathLength == 0 && sample.weightSum == 0 && all(sample.targetFunction == 0);
    if (absent) sample.worldNormal = float3(0,0,1);
    if (RTXPT_PairDiagnostics())
    {
        InterlockedAdd(u_PTDiagnosticCounters[42], 1);
        if (!all(isfinite(vectorRadiance))) InterlockedAdd(u_PTDiagnosticCounters[44], 1);
    }
    uint2 reservoirPos = RTXDI_PixelPosToReservoirPos(pixel, g_RtxdiBridgeConst.runtimeParams.activeCheckerboardField);
    RTXDI_PackedPTReservoir packed = RTXDI_PackPTReservoir(sample);
    // A hybrid shift never changes its reconnection-vertex normal. Preserve
    // its original quantized metadata instead of normalize/re-quantize through
    // shader-dependent float contraction. This is common to both schedules;
    // it does not pack the intermediate shift, target or weights.
    if (!absent)
    {
        packed.Data1.x = sourceNormal.x;
        packed.Data1.y = (packed.Data1.y & 0xffff0000u) | sourceNormal.y;
    }
    RTXDI_StorePackedPTReservoir(packed, g_RtxdiBridgeConst.restirPT.reservoirBuffer,
        reservoirPos, g_RtxdiBridgeConst.restirPT.bufferIndices.spatialResamplingOutputBufferIndex);
    // CGNS is explicitly excluded by the host contract. This buffer has four
    // uints per reservoir, at least the linear pixel count even at odd extents.
    uint address = (pixel.y * g_Const.ptConsts.imageWidth + pixel.x) * 16;
    u_PTSpatialNeighbors.Store3(address, asuint(vectorRadiance));
}

void RTXPT_PairResample(uint2 pixel, RTXDI_PTReservoir own, RTXPT_PairShift incoming,
    float ownNormalization, float incomingNormalization, uint2 ownNormal, uint2 incomingNormal)
{
    RTXDI_RandomSamplerState rng = RTXDI_InitRandomSampler(pixel,
        g_RtxdiBridgeConst.runtimeParams.frameIndex, RTXDI_PT_SPATIAL_RESAMPLING_RANDOM_SEED);
    RTXDI_PTReservoir output = RTXDI_EmptyPTReservoir();
    RTXDI_InternalSimplePTResample(output, own, 0.5, own.targetFunction, ownNormalization, own.M);
    bool selectedIncoming = RTXDI_InternalSimplePTResample(output, incoming.sample, RTXDI_GetNextRandom(rng),
        incoming.target, incomingNormalization, incoming.sample.M);
    RTXDI_FinalizePTResampling(output, 1.0, RTXDI_Luminance(output.targetFunction));
    float3 vectorRadiance = own.targetFunction * ownNormalization + incoming.target * incomingNormalization;
    RTXPT_PairStore(pixel, output, vectorRadiance, selectedIncoming ? incomingNormal : ownNormal);
}

void RTXPT_RunPairedSpatialPilot(uint2 pixel, bool cached = false)
{
    const uint2 dims = uint2(g_Const.ptConsts.imageWidth, g_Const.ptConsts.imageHeight);
    const bool gaussian=(g_RtxdiBridgeConst.giPTPartition & 4u)!=0;
    uint2 partner = uint2(pixel.x ^ 1u, pixel.y);
    // Keep the disabled policy from evaluating a large lookup against the
    // one-element dummy resource, including on backends without robust reads.
    [branch] if (gaussian) partner=uint2(RTXPT_GaussianPartner(pixel));
    // An incomplete edge pair retains its original estimate. Never clamp an
    // out-of-view neighbor: that would destroy the reciprocal relation.
    bool single = any(partner >= dims);
    [branch] if (gaussian)
    {
        if (!single && any(RTXPT_GaussianPartner(partner)!=int2(pixel)))
        {
            if (RTXPT_PairDiagnostics()) InterlockedAdd(u_PTDiagnosticCounters[45],1);
            single=true;
        }
    }
    if (!single && pixel.y*dims.x+pixel.x > partner.y*dims.x+partner.x) return;
    if (!single && gaussian && RTXPT_PairDiagnostics())
    {
        int2 delta=int2(partner)-int2(pixel);
        uint distanceSquared=uint(delta.x*delta.x+delta.y*delta.y);
        if (distanceSquared>1) InterlockedAdd(u_PTDiagnosticCounters[46],1);
        InterlockedMax(u_PTDiagnosticCounters[47],distanceSquared);
    }
    const RTXDI_ReservoirBufferParameters buffers = g_RtxdiBridgeConst.restirPT.reservoirBuffer;
    const RTXDI_PTBufferIndices indices = g_RtxdiBridgeConst.restirPT.bufferIndices;
    RAB_Surface a = RAB_GetGBufferSurface(pixel, false);
    uint2 apos = RTXDI_PixelPosToReservoirPos(pixel, g_RtxdiBridgeConst.runtimeParams.activeCheckerboardField);
    RTXDI_PTReservoir ra = RTXDI_LoadPTReservoir(buffers, apos, indices.spatialResamplingInputBufferIndex);
    if (single)
    {
        if (RTXPT_PairDiagnostics()) InterlockedAdd(u_PTDiagnosticCounters[43], 1);
        if (!RAB_IsSurfaceValid(a)) ra = RTXDI_EmptyPTReservoir();
        RTXPT_PairStore(pixel, ra, ra.targetFunction * ra.weightSum, RTXPT_PairSourceNormal(pixel));
        return;
    }
    RAB_Surface b = RAB_GetGBufferSurface(partner, false);
    uint2 bpos = RTXDI_PixelPosToReservoirPos(partner, g_RtxdiBridgeConst.runtimeParams.activeCheckerboardField);
    RTXDI_PTReservoir rb = RTXDI_LoadPTReservoir(buffers, bpos, indices.spatialResamplingInputBufferIndex);
    const RTXDI_PTSpatialResamplingParameters spatial = g_RtxdiBridgeConst.restirPT.spatialResampling;
    if (!IsValidNeighborSurface(spatial, a, b) || !IsValidNeighborSurface(spatial, b, a))
    {
        if (RTXPT_PairDiagnostics()) InterlockedAdd(u_PTDiagnosticCounters[43], 2);
        if (!RAB_IsSurfaceValid(a)) ra = RTXDI_EmptyPTReservoir();
        if (!RAB_IsSurfaceValid(b)) rb = RTXDI_EmptyPTReservoir();
        RTXPT_PairStore(pixel, ra, ra.targetFunction * ra.weightSum, RTXPT_PairSourceNormal(pixel));
        RTXPT_PairStore(partner, rb, rb.targetFunction * rb.weightSum, RTXPT_PairSourceNormal(partner));
        return;
    }
    RTXDI_PTSpatialResamplingRuntimeParameters params = RTXDI_EmptyPTSpatialResamplingRuntimeParameters();
    params.viewportSize = dims;
    params.cameraPos = g_RtxdiBridgeConst.ptCameraPosition;
    params.prevCameraPos = g_RtxdiBridgeConst.ptPreviousCameraPosition;
    params.prevPrevCameraPos = g_RtxdiBridgeConst.ptPreviousPreviousCameraPosition;
    if (RTXPT_PairDiagnostics()) InterlockedAdd(u_PTDiagnosticCounters[40], 1);
    // Immutable input pair; both directed shifts are shared by both outputs.
    RTXPT_PairShift ab, ba;
    [branch] if (cached)
    {
        ab = u_PTShiftCache[pixel.y*dims.x+pixel.x];
        ba = u_PTShiftCache[partner.y*dims.x+partner.x];
    }
    else
    {
        ab = RTXPT_PairShiftTo(ra, a, b, partner, params);
        ba = RTXPT_PairShiftTo(rb, b, a, pixel, params);
    }
    float pa = RTXDI_Luminance(ra.targetFunction);
    float pb = RTXDI_Luminance(rb.targetFunction);
    float da = ra.M * pa + rb.M * RTXDI_Luminance(ab.target) * ab.jacobian;
    float db = rb.M * pb + ra.M * RTXDI_Luminance(ba.target) * ba.jacobian;
    float wa = da > 0 ? ra.weightSum * ra.M * pa / da : 0;
    float wb = db > 0 ? rb.weightSum * rb.M * pb / db : 0;
    RTXPT_PairResample(pixel, ra, ba, wa, wb * ba.jacobian, RTXPT_PairSourceNormal(pixel), RTXPT_PairSourceNormal(partner));
    RTXPT_PairResample(partner, rb, ab, wb, wa * ab.jacobian, RTXPT_PairSourceNormal(partner), RTXPT_PairSourceNormal(pixel));
}
#endif
