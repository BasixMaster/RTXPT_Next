/* SPDX-License-Identifier: LicenseRef-NvidiaProprietary
 * Application-owned adapter for NVIDIA RTXDI hybrid shifts.
 * Rejected shifts have zero measure. Return a finite zero target before the
 * runtime forms inverse-MIS sums: IEEE 0 * NaN is not a zero contribution. */
#ifndef RTXPT_HYBRID_SHIFT_GUARD_HLSLI
#define RTXPT_HYBRID_SHIFT_GUARD_HLSLI
#include <Rtxdi/PT/HybridShift.hlsli>

void RTXPT_ComputeHybridShift(inout RAB_Surface surfaceForResampling,
    inout RTXDI_PTReservoir neighborSample,
    RTXDI_PTHybridShiftPerFrameParameters hspfParams,
    RTXDI_PTHybridShiftRuntimeParameters hsrParams,
    RTXDI_PTReconnectionParameters rcParams,
    inout float3 targetFunction, inout float jacobian,
    inout RAB_PathTracerUserData ptud)
{
    RTXDI_ComputeHybridShift(surfaceForResampling,neighborSample,hspfParams,
        hsrParams,rcParams,targetFunction,jacobian,ptud);
    // Fixed-threshold SDK reconnection supplies scatterPdf=0 to its MIS
    // callback. Keep that legacy callback at one and apply the actual marginal
    // BSDF density here once, after light-ID remapping. No second shadow trace.
    if (g_RtxdiBridgeConst.ptUnifiedFiniteNEE == 2 && jacobian != 0.f && ConnectsToNEELight(neighborSample))
    {
        RTXDI_SampledLightData data = RTXDI_GetSampledLightData(neighborSample);
        if (RTXDI_SampledLightData_IsValidLightData(data))
        {
            RAB_LightSample light = RAB_SamplePolymorphicLight(
                RAB_LoadLightInfo(RTXDI_SampledLightData_GetLightIndex(data), hsrParams.isPrevFrame),
                surfaceForResampling, RTXDI_SampledLightData_GetUVDataFloat2(data));
            float scatterPdf = surfaceForResampling.EvalPdf(normalize(light.position - surfaceForResampling.GetPosW()), true);
            targetFunction *= RTXPT_PTFiniteNEEWeight(light, scatterPdf);
        }
    }
    const bool diagnostics = g_RtxdiBridgeConst.ptDiagnostics != 0;
    if (diagnostics)
    {
        InterlockedAdd(u_PTDiagnosticCounters[32],1);
        if (!all(isfinite(targetFunction)))
        {
            InterlockedAdd(u_PTDiagnosticCounters[33],1);
            if (jacobian == 0.f) InterlockedAdd(u_PTDiagnosticCounters[37],1);
            else InterlockedAdd(u_PTDiagnosticCounters[38],1);
        }
        if (!isfinite(jacobian)) InterlockedAdd(u_PTDiagnosticCounters[34],1);
    }
    // RTXDI may reject a terminal light with solidAnglePdf==0 after computing
    // reflectedRadiance/solidAnglePdf. Its Jacobian is explicitly zero, but
    // the NaN target would otherwise poison piSum and erase a valid center.
    // Keep every nonzero-Jacobian target and all PDFs/normalization unchanged.
    if (jacobian == 0.f)
    {
        targetFunction = 0.f;
        if (diagnostics) InterlockedAdd(u_PTDiagnosticCounters[36],1);
    }
    if (diagnostics)
    {
        if (!all(isfinite(targetFunction * jacobian))) InterlockedAdd(u_PTDiagnosticCounters[35],1);
        if (!all(isfinite(targetFunction))) InterlockedAdd(u_PTDiagnosticCounters[39],1);
    }
}

// The SDK include guard keeps its internal calls unchanged. Subsequent
// temporal/spatial and application diagnostic calls use this adapter.
#define RTXDI_ComputeHybridShift RTXPT_ComputeHybridShift
#endif
