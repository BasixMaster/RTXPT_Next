/* SPDX-License-Identifier: LicenseRef-NvidiaProprietary
 * RTXPT Next integration of the NVIDIA RTXDI PT runtime. See root LICENSE. */
#pragma pack_matrix(row_major)
#define RTXDI_RESTIR_PT_HYBRID_SHIFT
#include "Bridge.hlsli"
#include <Rtxdi/PT/TemporalResampling.hlsli>

[numthreads(RTXDI_SCREEN_SPACE_GROUP_SIZE, RTXDI_SCREEN_SPACE_GROUP_SIZE, 1)]
void main(uint2 thread : SV_DispatchThreadID)
{
    uint2 pixel = RTXDI_ReservoirPosToPixelPos(thread, g_RtxdiBridgeConst.runtimeParams.activeCheckerboardField);
    if (any(pixel >= uint2(g_Const.ptConsts.imageWidth, g_Const.ptConsts.imageHeight))) return;
    RTXDI_PTReservoir reservoir;
    if (g_RtxdiBridgeConst.ptHistoryValid)
    {
        RTXDI_PTTemporalResamplingRuntimeParameters params = RTXDI_EmptyPTTemporalResamplingRuntimeParameters();
        params.pixelPosition = pixel;
        params.reservoirPosition = thread;
        params.motionVector = convertMotionVectorToPixelSpace(g_Const.view, g_Const.previousView, pixel, u_MotionVectors[pixel].xyz);
        params.cameraPos = g_RtxdiBridgeConst.ptCameraPosition;
        params.prevCameraPos = g_RtxdiBridgeConst.ptPreviousCameraPosition;
        params.prevPrevCameraPos = g_RtxdiBridgeConst.ptPreviousPreviousCameraPosition;
        RTXDI_RandomSamplerState rng = RTXDI_InitRandomSampler(pixel,
            g_RtxdiBridgeConst.runtimeParams.frameIndex, RTXDI_PT_TEMPORAL_RESAMPLING_RANDOM_SEED);
        RAB_PathTracerUserData user = RAB_EmptyPathTracerUserData();
        user.pixelPosition = pixel;
        bool selectedPrevious = false;
        reservoir = RTXDI_PTTemporalResampling(g_RtxdiBridgeConst.restirPT.temporalResampling, params,
            g_RtxdiBridgeConst.restirPT.hybridShift, g_RtxdiBridgeConst.restirPT.reconnection,
            g_RtxdiBridgeConst.runtimeParams, g_RtxdiBridgeConst.restirPT.reservoirBuffer,
            rng, g_RtxdiBridgeConst.restirPT.bufferIndices, selectedPrevious, user);
    }
    else
        reservoir = RTXDI_LoadPTReservoir(g_RtxdiBridgeConst.restirPT.reservoirBuffer,
            thread, g_RtxdiBridgeConst.restirPT.bufferIndices.initialPathTracerOutputBufferIndex);
    RTXDI_StorePTReservoir(reservoir, g_RtxdiBridgeConst.restirPT.reservoirBuffer,
        thread, g_RtxdiBridgeConst.restirPT.bufferIndices.temporalResamplingOutputBufferIndex);
}
