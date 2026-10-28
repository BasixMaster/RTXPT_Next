/* SPDX-License-Identifier: LicenseRef-NvidiaProprietary
 * RTXPT Next integration of the NVIDIA RTXDI PT runtime. See root LICENSE. */
#pragma pack_matrix(row_major)
#define RTXDI_RESTIR_PT_INITIAL_SAMPLING
#include "Bridge.hlsli"
#include <Rtxdi/PT/InitialSampling.hlsli>

[numthreads(RTXDI_SCREEN_SPACE_GROUP_SIZE, RTXDI_SCREEN_SPACE_GROUP_SIZE, 1)]
void main(uint2 thread : SV_DispatchThreadID)
{
    uint2 pixel = RTXDI_ReservoirPosToPixelPos(thread, g_RtxdiBridgeConst.runtimeParams.activeCheckerboardField);
    if (any(pixel >= uint2(g_Const.ptConsts.imageWidth, g_Const.ptConsts.imageHeight))) return;
    RTXDI_PTReservoir reservoir = RTXDI_EmptyPTReservoir();
    RAB_Surface surface = RAB_GetGBufferSurface(pixel, false);
    if (RAB_IsSurfaceValid(surface))
    {
        RTXDI_PathTracerRandomContext rng = RTXDI_InitializePathTracerRandomContext(pixel,
            g_RtxdiBridgeConst.runtimeParams.frameIndex,
            RTXDI_PT_GENERATE_INITIAL_SAMPLES_RANDOM_SEED, RTXDI_PT_GENERATE_INITIAL_SAMPLES_REPLAY_RANDOM_SEED);
        RAB_PathTracerUserData user = RAB_EmptyPathTracerUserData();
        user.pixelPosition = pixel;
        RTXDI_PTInitialSamplingRuntimeParameters params = RTXDI_EmptyPTInitialSamplingRuntimeParameters();
        params.cameraPos = g_RtxdiBridgeConst.ptCameraPosition;
        params.prevCameraPos = g_RtxdiBridgeConst.ptPreviousCameraPosition;
        params.prevPrevCameraPos = g_RtxdiBridgeConst.ptPreviousPreviousCameraPosition;
        reservoir = GenerateInitialSamples(g_RtxdiBridgeConst.restirPT.initialSampling, params,
            g_RtxdiBridgeConst.restirPT.reconnection, rng, surface, user);
    }
    RTXDI_StorePTReservoir(reservoir, g_RtxdiBridgeConst.restirPT.reservoirBuffer,
        thread, g_RtxdiBridgeConst.restirPT.bufferIndices.initialPathTracerOutputBufferIndex);
    RTXDI_StorePTReservoir(reservoir, g_RtxdiBridgeConst.restirPT.reservoirBuffer,
        thread, g_RtxdiBridgeConst.restirPT.bufferIndices.initialPathTracerPreservedBufferIndex);
}
