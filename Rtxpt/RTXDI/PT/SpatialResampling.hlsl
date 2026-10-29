/* SPDX-License-Identifier: LicenseRef-NvidiaProprietary
 * RTXPT Next integration of the NVIDIA RTXDI PT runtime. See root LICENSE. */
#pragma pack_matrix(row_major)
#define RTXDI_RESTIR_PT_HYBRID_SHIFT
#include "Bridge.hlsli"
#include "Runtime/HybridShiftGuard.hlsli"
#include <Rtxdi/PT/SpatialResampling.hlsli>
#include "Runtime/PairedSpatialPilot.hlsli"

[numthreads(RTXDI_SCREEN_SPACE_GROUP_SIZE, RTXDI_SCREEN_SPACE_GROUP_SIZE, 1)]
void main(uint2 thread : SV_DispatchThreadID)
{
    uint2 pixel = RTXDI_ReservoirPosToPixelPos(thread, g_RtxdiBridgeConst.runtimeParams.activeCheckerboardField);
    if (any(pixel >= uint2(g_Const.ptConsts.imageWidth, g_Const.ptConsts.imageHeight))) return;
    if ((g_RtxdiBridgeConst.giPTPartition & 2u) != 0)
    {
        RTXPT_RunPairedSpatialPilot(pixel);
        return;
    }
    RTXDI_PTSpatialResamplingRuntimeParameters params = RTXDI_EmptyPTSpatialResamplingRuntimeParameters();
    params.pixelPosition = pixel;
    params.reservoirPosition = thread;
    params.viewportSize = uint2(g_Const.ptConsts.imageWidth, g_Const.ptConsts.imageHeight);
    params.cameraPos = g_RtxdiBridgeConst.ptCameraPosition;
    params.prevCameraPos = g_RtxdiBridgeConst.ptPreviousCameraPosition;
    params.prevPrevCameraPos = g_RtxdiBridgeConst.ptPreviousPreviousCameraPosition;
    RTXDI_RandomSamplerState rng = RTXDI_InitRandomSampler(pixel,
        g_RtxdiBridgeConst.runtimeParams.frameIndex, RTXDI_PT_SPATIAL_RESAMPLING_RANDOM_SEED);
    RAB_PathTracerUserData user = RAB_EmptyPathTracerUserData();
    user.pixelPosition = pixel;
    bool selectedNeighbor = false;
    RTXDI_PTReservoir reservoir = RTXDI_PTSpatialResampling(params,
        g_RtxdiBridgeConst.restirPT.spatialResampling, g_RtxdiBridgeConst.restirPT.hybridShift,
        g_RtxdiBridgeConst.restirPT.reconnection, g_RtxdiBridgeConst.restirPT.reservoirBuffer,
        g_RtxdiBridgeConst.restirPT.bufferIndices, g_RtxdiBridgeConst.runtimeParams, rng, selectedNeighbor, user);
    RTXDI_StorePTReservoir(reservoir, g_RtxdiBridgeConst.restirPT.reservoirBuffer,
        thread, g_RtxdiBridgeConst.restirPT.bufferIndices.spatialResamplingOutputBufferIndex);
}
