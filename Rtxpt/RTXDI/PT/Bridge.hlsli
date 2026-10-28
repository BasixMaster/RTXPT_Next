/*
 * Copyright (c) 2025-2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
 * Modifications for the RTXPT Next application integration.
 * SPDX-License-Identifier: LicenseRef-NvidiaProprietary
 * See the NVIDIA RTX SDK license retained at the repository root.
 */
#ifndef RTXPT_RESTIR_PT_BRIDGE_HLSLI
#define RTXPT_RESTIR_PT_BRIDGE_HLSLI
#define NON_PATH_TRACING_PASS 1
#define RTXPT_RESTIR_PT_BRIDGE 1
#include "../RtxdiApplicationBridge.hlsli"
#include "../../Shaders/PathTracerSurfaceBridgeDonut.hlsli"
#include "../../Shaders/PathTracer/PathTracerNestedDielectrics.hlsli"
#include "../../Shaders/PathTracer/Utils/HomogeneousVolumeSampler.hlsli"
#include <Rtxdi/DI/InitialSampling.hlsli>
#include <Rtxdi/PT/Reservoir.hlsli>
#include <Rtxdi/Utils/BrdfRaySample.hlsli>

// Native medium state is transported explicitly by the primary auxiliary export
// and rebuilt for every initial/replay invocation. Presence of this code is not
// a transmission validation result; application capability gates remain separate.
struct RAB_RayPayload
{
    uint instanceIndex;
    uint geometryIndex;
    uint primitiveIndex;
    float2 barycentrics;
    float committedRayT;
};
float RAB_RayPayloadGetCommittedHitT(RAB_RayPayload p) { return p.committedRayT; }
bool RTXPT_PTCanReconnectSurface(RAB_Surface s)
{
    // Restrict fixed-threshold mid-path reconnection to non-transmissive,
    // out-of-medium vertices. Other prefixes use deterministic random replay.
    return s._ptNativeState.interiorSlots[0] == 0 &&
        (s._mtl.getActiveLobes() & (uint)LobeType::Transmission) == 0;
}
float RAB_GetSurfaceRoughness(RAB_Surface s) { return RTXPT_PTCanReconnectSurface(s) ? s.GetRoughness() : 0.0f; }
float3 RAB_GetSurfaceViewDir(RAB_Surface s) { return s.GetView(); }
void RAB_SetSurfaceWorldPos(inout RAB_Surface s, float3 p) { s._posW = p; }
void RAB_SetSurfaceNormal(inout RAB_Surface s, float3 n) { s._N = n; }
float3 RAB_LightSamplePosition(RAB_LightSample s) { return s.position; }
float3 RAB_LightSampleRadiance(RAB_LightSample s) { return s.radiance; }
float3 RTXPT_PTShadowTransport(RAB_Surface surface, float3 samplePosition);
float3 RAB_GetReflectedBsdfRadianceForSurface(float3 p, float3 radiance, RAB_Surface s)
{
    return s.Eval(normalize(p - s.GetPosW())).rgb * radiance * RTXPT_PTShadowTransport(s, p);
}
float3 RAB_GetPTSampleTargetPdfForSurface(float3 p, float3 radiance, RAB_Surface s)
{
    return RAB_GetReflectedBsdfRadianceForSurface(p, radiance, s);
}
// B2 has duplication/history reduction disabled. There is no duplication
// texture in this mode; enabling the feature requires its real producer/pass.
uint RAB_GetDuplicationMapCount(int2 p) { return 0; }
static const float RAB_DISTANT_LIGHT_DISTANCE = 100000.0f;

struct RAB_PathTracerUserData
{
    RTXDI_PTPathTraceInvocationType pathType;
    uint2 pixelPosition;
    float firstHitDistance;
    PathState nativeState;
};
RAB_PathTracerUserData RAB_EmptyPathTracerUserData()
{
    return (RAB_PathTracerUserData)0;
}
void RAB_PathTracerUserDataSetPathType(inout RAB_PathTracerUserData u, RTXDI_PTPathTraceInvocationType t) { u.pathType = t; }
void RAB_ReconnectionDenoiserCallback(RTXDI_PTReservoir sample, RAB_Surface s, inout RAB_PathTracerUserData u)
{
    if (u.firstHitDistance == 0) u.firstHitDistance = length(sample.translatedWorldPosition - s.GetPosW());
}
void RAB_LastBounceDenoiserCallback(float3 p, RAB_Surface s, inout RAB_PathTracerUserData u)
{
    if (u.firstHitDistance == 0) u.firstHitDistance = length(p - s.GetPosW());
}
// NEE-only transport partition: continuous emitter/environment paths are
// represented by explicit light sampling, so the NEE MIS weight is one.
float RAB_GetMISWeightForNEE(uint lightIndex, RAB_LightSample lightSample,
    float3 lightDirection, float lightSolidAnglePdf, float scatterPdf) { return 1.0f; }

#include <Rtxdi/PT/PathTracerContext.hlsli>
#include <Rtxdi/PT/PathTracerRandomContext.hlsli>

RAB_RayPayload RTXPT_PTTrace(RayDesc ray)
{
    RAB_RayPayload p = (RAB_RayPayload)0;
    p.instanceIndex = ~0u;
    RayQuery<RAY_FLAG_SKIP_PROCEDURAL_PRIMITIVES> q;
    q.TraceRayInline(SceneBVH, RAY_FLAG_NONE, INSTANCE_MASK_ALL, ray);
    while (q.Proceed())
    {
        if (q.CandidateType() == CANDIDATE_NON_OPAQUE_TRIANGLE &&
            Bridge::AlphaTestVisibilityRay(q.CandidateInstanceID(), q.CandidateInstanceIndex(),
                q.CandidateGeometryIndex(), q.CandidatePrimitiveIndex(), q.CandidateTriangleBarycentrics()))
            q.CommitNonOpaqueTriangleHit();
    }
    if (q.CommittedStatus() == COMMITTED_TRIANGLE_HIT)
    {
        p.instanceIndex = q.CommittedInstanceIndex();
        p.geometryIndex = q.CommittedGeometryIndex();
        p.primitiveIndex = q.CommittedPrimitiveIndex();
        p.barycentrics = q.CommittedTriangleBarycentrics();
        p.committedRayT = q.CommittedRayT();
    }
    return p;
}

PathTracer::WorkingContext RTXPT_PTWorkingContext()
{
    PathTracer::WorkingContext working;
    working.OutputColor = u_OutputColor;
    working.PtConsts = g_Const.ptConsts;
    working.Debug.Init(g_Const.debug, u_FeedbackBuffer, u_DebugLinesBuffer, u_DebugDeltaPathTree, u_DeltaPathSearchStack);
    working.DenoisingLayers = DenoisingLayersContext::make(u_DenoisingLayersHeader,
        u_DenoisingLayersBuffer, u_StableRadiance, g_Const.ptConsts);
    return working;
}

PathState RTXPT_PTNativePath(RAB_Surface primary, uint2 pixel)
{
    const RTXPTPTPrimaryData state = primary._ptNativeState;
    PathState path = (PathState)0;
    path.SetId(PathIDFromPixel(pixel));
    path.flagsAndVertexIndex = state.flags;
    path.setVertexIndex(RTXPT_PTPrimaryVertex(state));
    path.packedCounters = state.packedCounters;
#if RTXPT_NESTED_DIELECTRICS_QUALITY > 0
    path.interiorList.slots[0] = state.interiorSlots[0];
    path.interiorList.slots[1] = state.interiorSlots[1];
    path.setInsideDielectricVolume(!path.interiorList.isEmpty());
#endif
    path.SetOrigin(primary.GetPosW());
    path.SetDir(-primary.GetView());
    path.SetThp(float3(1, 1, 1));
    path.rayCone = RayCone::make(state.rayConeWidth, state.rayConeSpread);
    path.setActive();
    return path;
}

ShadingData RTXPT_PTShadingDataForMedium(RAB_Surface surface)
{
    ShadingData data = ShadingData::make();
    data.shadingFlags = surface._mtl;
    data.SetMaterialIDAndPosErrorScale(surface._ptNativeState.materialID, surface._posErrorScale);
    data.frontFacing = surface._frontFacing;
    data.posW = surface.GetPosW();
    data.N = surface.GetNormal();
    data.V = surface.GetView();
    data.faceNCorrected = surface.GetFaceNCorrected();
    return data;
}

float3 RTXPT_PTMediumTransmittance(PathState path, float distance)
{
#if RTXPT_NESTED_DIELECTRICS_QUALITY > 0
    if (!path.interiorList.isEmpty())
        return HomogeneousVolumeSampler::evalTransmittance(
            Bridge::loadHomogeneousVolumeData(path.interiorList.getTopMaterialID()), max(0.0f, distance));
#endif
    return float3(1, 1, 1);
}

template<typename PTContextType>
void RTXPT_PTApplyMediumThroughput(inout RTXDI_PathTracerContext<PTContextType> ctx, float3 transmittance)
{
    ctx.MultiplyPathThroughput(transmittance);
#if defined(RTXDI_RESTIR_PT_INITIAL_SAMPLING)
    // Application adapter pinned to RTXDI-Library f12037fa8e97ebc08e9e3edfd2de528ed1772a4b.
    // The public MultiplyPathThroughput changes only pathThroughput. Stored
    // suffix radiance uses rcPathThroughput, which the runtime's native BSDF
    // update multiplies exactly when bounceDepth > rcVertexLength (the outgoing
    // segment at RC and every later segment, never the incoming RC segment).
    // Beer attenuation needs that identical partition or reuse loses absorption.
    if (ctx.GetBounceDepth() > ctx.GetRcVertexLength())
        ctx.ctx.ptState.rcPathThroughput *= transmittance;
#endif
}

PathTracer::Surface RTXPT_PTLoadNativeSurface(RAB_RayPayload hit, RayDesc ray, PathState path, uint2 pixel)
{
    const PathTracer::WorkingContext working = RTXPT_PTWorkingContext();
    return Bridge::loadSurface(hit.instanceIndex, hit.geometryIndex, hit.primitiveIndex,
        hit.barycentrics, ray.Direction, path.rayCone, path.getVertexIndex(), pixel, working.Debug);
}

RAB_Surface RTXPT_PTCollectNativeSurface(PathTracer::Surface nativeSurface, float hitDistance, PathState path)
{
    const ShadingData sd = nativeSurface.shadingData;
    RAB_Surface surface = PathTracerCollectedSurfaceData::create(sd.shadingFlags, sd.T(), sd.B(), sd.N, sd.V,
        sd.posW, sd.faceNCorrected, sd.PosErrorScale(), sd.frontFacing, hitDistance, 0,
        sd.GetEta(), nativeSurface.bsdf.data);
    surface._ptNativeState.materialID = sd.MaterialID();
#if RTXPT_NESTED_DIELECTRICS_QUALITY > 0
    surface._ptNativeState.interiorSlots[0] = path.interiorList.slots[0];
    surface._ptNativeState.interiorSlots[1] = path.interiorList.slots[1];
#endif
    surface._ptNativeState.packedCounters = path.packedCounters;
    surface._ptNativeState.rayConeWidth = path.rayCone.getWidth();
    surface._ptNativeState.rayConeSpread = path.rayCone.getSpreadAngle();
    surface._ptNativeState.nativeVertexIndex = path.getVertexIndex();
    surface._ptNativeState.flags = path.flagsAndVertexIndex;
    surface._ptNativeState.prefixThroughput = float3(1, 1, 1);
    surface._ptNativeState.frameIndex = g_Const.ptConsts.frameIndex;
    return surface;
}

// Real RGB visibility, used both by the PT target-function callbacks and by
// their conservative boolean predicates. True dielectric interfaces block a
// straight NEE/reconnection edge; lower-priority false interfaces are traversed
// with exactly the native stack/rejection policy and per-segment attenuation.
float3 RTXPT_PTShadowTransport(RAB_Surface surface, float3 samplePosition)
{
    PathState path = RTXPT_PTNativePath(surface, uint2(0, 0));
    const PathTracer::WorkingContext working = RTXPT_PTWorkingContext();
    const float3 toLight = samplePosition - surface.GetPosW();
    const float distance = length(toLight);
    if (!(distance > 0.0f) || !isfinite(distance)) return float3(0, 0, 0);
    RayDesc ray;
    ray.Direction = toLight / distance;
    const bool transmission = dot(ray.Direction, surface.GetNormal()) < 0;
    ray.Origin = surface.ComputeNewRayOrigin(!transmission);
    ray.TMin = 0;
    ray.TMax = max(0.0f, dot(samplePosition - ray.Origin, ray.Direction) - g_RtxdiBridgeConst.rayEpsilon);
    if (transmission)
        PathTracer::UpdateNestedDielectricsOnScatterTransmission(RTXPT_PTShadingDataForMedium(surface), path, working);
    float3 transmittance = float3(1, 1, 1);
    // Native quality modes reject at most 4/16 false hits before their documented
    // fallback/termination; 32 bounds traversal without inventing an unbounded loop.
    for (uint segment = 0; segment < 32; ++segment)
    {
        RAB_RayPayload hit = RTXPT_PTTrace(ray);
        const float segmentDistance = hit.instanceIndex == ~0u ? ray.TMax : hit.committedRayT;
        transmittance *= RTXPT_PTMediumTransmittance(path, segmentDistance);
        if (hit.instanceIndex == ~0u) return transmittance;
        path.rayCone = path.rayCone.propagateDistance(hit.committedRayT);
        path.setVertexIndex(RTXPT_PTPrimaryVertex(surface._ptNativeState) + 1);
        PathTracer::Surface blocker = RTXPT_PTLoadNativeSurface(hit, ray, path, uint2(0, 0));
        if (PathTracer::HandleNestedDielectrics(blocker, path, working) || path.isTerminated())
            return float3(0, 0, 0);
        ray.Origin = path.GetOrigin();
        ray.TMax = max(0.0f, dot(samplePosition - ray.Origin, ray.Direction) - g_RtxdiBridgeConst.rayEpsilon);
        if (ray.TMax == 0) return transmittance;
    }
    return float3(0, 0, 0); // Same conservative failure policy as a terminated native path.
}

RTXDI_BrdfRaySample RTXPT_PTSampleBsdf(RAB_Surface s, inout RTXDI_RandomSamplerState rng)
{
    RTXDI_BrdfRaySample brs = RTXDI_EmptyBrdfRaySample();
    BSDFSample sample = (BSDFSample)0;
    float3 wo;
    FalcorBSDF bsdf = FalcorBSDF::make(s._mtl, s._N, s._V, s._data, s._eta);
#if RecycleSelectSamples
    float3 randoms = float3(RTXDI_GetNextRandom(rng), RTXDI_GetNextRandom(rng), RTXDI_GetNextRandom(rng));
#else
    float4 randoms = float4(RTXDI_GetNextRandom(rng), RTXDI_GetNextRandom(rng), RTXDI_GetNextRandom(rng), RTXDI_GetNextRandom(rng));
#endif
    if (!bsdf.sample(s._ToLocal(s._V), wo, sample.pdf, sample.weight, sample.lobe, sample.lobeP, randoms)) return brs;
    brs.outDirection = s._FromLocal(wo);
    // The native BSDF marks a delta event with a zero solid-angle PDF, while
    // sample.weight already includes discrete lobe selection. RTXDI's context
    // forms brdfTimesNoL/outPdf even for delta rays, so carry the discrete mass
    // in this case; passing the native zero would turn a valid ray into 0/0.
    const bool delta = (sample.lobe & (uint)LobeType::Delta) != 0;
    brs.outPdf = delta ? sample.lobeP : sample.pdf;
    // For a continuous mixture the native sampler's component weight is not
    // the marginal BSDF used by RTXDI reconnection. Use that same full BSDF
    // here with its full mixture PDF. Discrete delta mass remains separate.
    brs.brdfTimesNoL = delta ? sample.weight * brs.outPdf : s.Eval(brs.outDirection).rgb;
    if (delta) { brs.properties.SetDelta(); brs.properties.SetSpecular(); }
    if ((sample.lobe & (uint)LobeType::Specular) != 0) brs.properties.SetSpecular();
    if ((sample.lobe & (uint)LobeType::Transmission) != 0) brs.properties.SetTransmission();
    return brs;
}

template<typename PTContextType>
void RAB_PathTrace(inout RTXDI_PathTracerContext<PTContextType> ctx,
    inout RTXDI_PathTracerRandomContext randomContext, inout RAB_PathTracerUserData user)
{
    // The exact native primary state comes from the candidate pixel/frame's
    // auxiliary export, including inverse shifts. No camera-origin reconstruction
    // or empty-medium assumption is substituted for an existing native prefix.
    user.nativeState = RTXPT_PTNativePath(ctx.GetIntersectionSurface(), user.pixelPosition);
    const PathTracer::WorkingContext working = RTXPT_PTWorkingContext();
    while (ctx.GetBounceDepth() <= ctx.GetMaxPathBounce())
    {
        ctx.BeginPathState();
        RAB_Surface previousSurface = ctx.GetIntersectionSurface();
        RTXDI_BrdfRaySample brs = RTXPT_PTSampleBsdf(previousSurface, randomContext.replayRandomSamplerState);
        ctx.SetBrdfRaySample(brs);
        if (!ctx.ValidContinuationRayBrdfOverPdf()) break;
        ctx.MultiplyPathThroughput(ctx.GetContinuationRayBrdfOverPdf());
        user.nativeState.clearScatterEventFlags();
        if (brs.properties.IsTransmission())
        {
            user.nativeState.setScatterTransmission();
            PathTracer::UpdateNestedDielectricsOnScatterTransmission(
                RTXPT_PTShadingDataForMedium(previousSurface), user.nativeState, working);
        }
        if (brs.properties.IsSpecular()) user.nativeState.setScatterSpecular();
        if (brs.properties.IsDelta()) user.nativeState.setScatterDelta();
        else
            user.nativeState.rayCone = RayCone::make(user.nativeState.rayCone.getWidth(),
                min(user.nativeState.rayCone.getSpreadAngle() + ComputeRayConeSpreadAngleExpansionByScatterPDF(brs.outPdf), 2.0 * K_PI));
        // A user replay-length cap must not force an unqualified medium vertex
        // to become reconnectible. The context still chooses earlier safe vertices.
        if (!RTXPT_PTCanReconnectSurface(previousSurface))
            ctx.SetMaxRcVertexLengthIfUnset(uint16_t(ctx.GetMaxPathBounce() + 1));
        RayDesc ray;
        ray.Direction = brs.outDirection;
        ray.Origin = previousSurface.ComputeNewRayOrigin(dot(brs.outDirection, previousSurface.GetFaceNCorrected()) >= 0);
        ray.TMin = 0.0;
        ray.TMax = RTXDI_MAX_FLOAT32;
        ctx.SetContinuationRay(ray);
        if (!ctx.AnalyzePathReconnectibilityBeforeTrace()) break;
        const uint nextNativeVertex = user.nativeState.getVertexIndex() + 1;
        RAB_RayPayload hit = (RAB_RayPayload)0;
        PathTracer::Surface nativeSurface = (PathTracer::Surface)0;
        float totalHitDistance = 0;
        bool accepted = false;
        for (uint segment = 0; segment < 32; ++segment)
        {
            hit = RTXPT_PTTrace(ray);
            if (hit.instanceIndex == ~0u) { accepted = true; break; }
            totalHitDistance += hit.committedRayT;
            RTXPT_PTApplyMediumThroughput(ctx, RTXPT_PTMediumTransmittance(user.nativeState, hit.committedRayT));
            user.nativeState.rayCone = user.nativeState.rayCone.propagateDistance(hit.committedRayT);
            user.nativeState.setVertexIndex(nextNativeVertex);
            nativeSurface = RTXPT_PTLoadNativeSurface(hit, ray, user.nativeState, user.pixelPosition);
            if (PathTracer::HandleNestedDielectrics(nativeSurface, user.nativeState, working))
            {
                accepted = true;
                break;
            }
            if (user.nativeState.isTerminated()) break;
            // False interfaces consume neither a BSDF draw nor a PT bounce.
            ray.Origin = user.nativeState.GetOrigin();
        }
        if (!accepted) { ctx.SetPathTermination(true); break; }
        hit.committedRayT = totalHitDistance;
        ctx.SetTraceResult(hit);
        if (hit.instanceIndex == ~0u)
        {
            ctx.RecordPathRadianceMiss(randomContext.initialRandomSamplerState);
            // Continuous misses are covered by NEE. A delta connection cannot
            // be sampled by NEE and therefore retains explicit emitted light.
            if (brs.properties.IsDelta() && ctx.ShouldSampleEmissiveSurfaces() && Bridge::HasEnvMap())
            {
                EnvMap env = Bridge::CreateEnvMap();
                ctx.RecordEnvironmentMapLightSample(env.Eval(ray.Direction), previousSurface, randomContext.initialRandomSamplerState);
            }
            break;
        }
        if (user.firstHitDistance == 0) user.firstHitDistance = hit.committedRayT;
        float3 emission = nativeSurface.shadingData.GetEmission();
        RAB_Surface surface = RTXPT_PTCollectNativeSurface(nativeSurface, hit.committedRayT, user.nativeState);
        ctx.RecordPathIntersection(surface);
        if (ctx.IsPathTerminated()) break;
        if (brs.properties.IsDelta() && ctx.ShouldSampleEmissiveSurfaces())
            ctx.RecordEmissiveLightSample(emission, previousSurface, randomContext.initialRandomSamplerState);
        if (ctx.ShouldSampleNee())
        {
            RAB_LightSample light = RAB_EmptyLightSample();
            RTXDI_DIInitialSamplingParameters parameters = g_RtxdiBridgeConst.restirDI.initialSamplingParams;
            // Brdf candidates would overlap the explicit delta-hit partition.
            parameters.numBrdfSamples = 0;
            RTXDI_DIReservoir r = RTXDI_SampleLightsForSurface(randomContext.initialRandomSamplerState,
                randomContext.initialCoherentRandomSamplerState, surface, parameters, g_RtxdiBridgeConst.lightBufferParams,
#if RTXDI_ENABLE_PRESAMPLING
                g_RtxdiBridgeConst.localLightsRISBufferSegmentParams, g_RtxdiBridgeConst.environmentLightRISBufferSegmentParams,
#if RTXDI_REGIR_MODE != RTXDI_REGIR_MODE_DISABLED
                g_RtxdiBridgeConst.regir,
#endif
#endif
                light);
            if (r.weightSum > 0 && light.solidAnglePdf > 0)
            {
                float3 reflected = RAB_GetReflectedBsdfRadianceForSurface(light.position, light.radiance, surface);
                reflected *= RAB_GetConservativeVisibility(surface, light);
                reflected *= RTXDI_GetDIReservoirInvPdf(r) / light.solidAnglePdf;
                RTXDI_SampledLightData data = RTXDI_SampledLightData_CreateInvalidData();
                data.lightData = r.lightData;
                data.uvData = r.uvData;
                ctx.RecordNeeLightSample(data, reflected, 1.0f / r.weightSum,
                    surface.EvalPdf(normalize(light.position - surface.GetPosW()), true), light, randomContext.initialRandomSamplerState);
            }
        }
        ctx.IncreaseBounceDepth();
    }
}
#endif
