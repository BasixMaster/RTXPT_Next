/* SPDX-License-Identifier: LicenseRef-NvidiaProprietary
 * Diagnostic only: compare canonical and same-pixel hybrid-shift targets. */
#pragma pack_matrix(row_major)
#define RTXDI_RESTIR_PT_HYBRID_SHIFT
#include "Bridge.hlsli"
#include <Rtxdi/PT/HybridShift.hlsli>

[numthreads(RTXDI_SCREEN_SPACE_GROUP_SIZE, RTXDI_SCREEN_SPACE_GROUP_SIZE, 1)]
void main(uint2 thread : SV_DispatchThreadID)
{
    uint2 pixel = RTXDI_ReservoirPosToPixelPos(thread, g_RtxdiBridgeConst.runtimeParams.activeCheckerboardField);
    if (any(pixel >= uint2(g_Const.ptConsts.imageWidth,g_Const.ptConsts.imageHeight))) return;
    RAB_Surface surface = RAB_GetGBufferSurface(pixel,false);
    if (!RAB_IsSurfaceValid(surface)) return;
    RTXDI_PTReservoir canonical = RTXDI_LoadPTReservoir(g_RtxdiBridgeConst.restirPT.reservoirBuffer,
        thread,g_RtxdiBridgeConst.restirPT.bufferIndices.initialPathTracerPreservedBufferIndex);
    if (!RTXDI_IsValidPTReservoir(canonical) || !any(canonical.targetFunction > 0)) return;
    RTXDI_PTReservoir shifted = canonical;
    RTXDI_PTHybridShiftRuntimeParameters params = (RTXDI_PTHybridShiftRuntimeParameters)0;
    params.cameraPos = g_RtxdiBridgeConst.ptCameraPosition;
    params.prevCameraPos = params.cameraPos;
    params.prevPrevCameraPos = params.cameraPos;
    RAB_PathTracerUserData user = RAB_EmptyPathTracerUserData();
    user.pixelPosition = pixel;
    user.pathType = RTXDI_PTPathTraceInvocationType_DebugSpatialRetrace;
    float3 target = 1;
    float jacobian = 1;
    RTXDI_ComputeHybridShift(surface,shifted,g_RtxdiBridgeConst.restirPT.hybridShift,params,
        g_RtxdiBridgeConst.restirPT.reconnection,target,jacobian,user);
    bool neeTerminal = canonical.rcVertexLength == canonical.pathLength && RTXDI_ConnectsToNeeLight(canonical);
    bool pureReplay = canonical.rcVertexLength > canonical.pathLength;
    if (!neeTerminal && !pureReplay)
    {
        target *= RAB_GetPTSampleTargetPdfForSurface(shifted.translatedWorldPosition,shifted.radiance,surface);
        if (any(target > 0)) target *= RAB_GetConservativeVisibility(surface,shifted.translatedWorldPosition);
    }
    float3 delta = abs(target * jacobian - canonical.targetFunction);
    float3 relative = delta / max(abs(canonical.targetFunction),1e-5);
    float error = max(relative.x,max(relative.y,relative.z));
    bool bad = !isfinite(error) || (error > 0.01f && max(delta.x,max(delta.y,delta.z)) > 1e-4f);
    uint kind = neeTerminal ? 10 : (pureReplay ? 12 : 14);
    InterlockedAdd(u_PTDiagnosticCounters[7],1);
    InterlockedAdd(u_PTDiagnosticCounters[kind],1);
    if (bad)
    {
        InterlockedAdd(u_PTDiagnosticCounters[8],1);
        if (pureReplay)
        {
            uint claimed;
            InterlockedCompareExchange(u_PTDiagnosticCounters[16],0,1,claimed);
            if (claimed == 0)
            {
                u_PTDiagnosticCounters[17]=pixel.x;
                u_PTDiagnosticCounters[18]=pixel.y;
                u_PTDiagnosticCounters[19]=canonical.pathLength;
                u_PTDiagnosticCounters[20]=canonical.rcVertexLength;
                u_PTDiagnosticCounters[21]=0;
                u_PTDiagnosticCounters[22]=asuint(canonical.targetFunction.x);
                u_PTDiagnosticCounters[23]=asuint(canonical.targetFunction.y);
                u_PTDiagnosticCounters[24]=asuint(canonical.targetFunction.z);
                u_PTDiagnosticCounters[25]=asuint(target.x);
                u_PTDiagnosticCounters[26]=asuint(target.y);
                u_PTDiagnosticCounters[27]=asuint(target.z);
                u_PTDiagnosticCounters[28]=asuint(jacobian);
                u_PTDiagnosticCounters[29]=user.replayDebugFlags;
                u_PTDiagnosticCounters[30]=asuint(user.replayDebugPdf);
                u_PTDiagnosticCounters[31]=asuint(user.replayDebugEmission);
            }
        }
        InterlockedAdd(u_PTDiagnosticCounters[kind+1],1);
    }
    InterlockedMax(u_PTDiagnosticCounters[9],asuint(isfinite(error) ? error : 1e20f));
}
