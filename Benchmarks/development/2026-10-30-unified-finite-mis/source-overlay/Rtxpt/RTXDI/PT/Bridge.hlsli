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
    uint geometryInstanceBase; // TLAS InstanceID, distinct from native instance array index.
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
        (FalcorBSDF::getLobes(s._data) & s._mtl.getActiveLobes() & (uint)LobeType::Transmission) == 0;
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
// Temporal reuse reads the prior completed frame's map, before the producer
// overwrites it after final resampling. Kept separate from vector/CGNS storage.
RWStructuredBuffer<uint> u_PTDuplicationMap : register(u27 VK_DESCRIPTOR_SET(2));
uint RAB_GetDuplicationMapCount(int2 p)
{
    uint2 dims = uint2(g_Const.ptConsts.imageWidth, g_Const.ptConsts.imageHeight);
    if (any(p < 0) || any(p >= int2(dims))) return 0;
    uint count = u_PTDuplicationMap[uint(p.y) * dims.x + uint(p.x)];
    if (g_RtxdiBridgeConst.ptDiagnostics != 0)
    {
        InterlockedAdd(u_PTDiagnosticCounters[96], 1);
        if (count != 0) InterlockedAdd(u_PTDiagnosticCounters[97], 1);
        InterlockedMax(u_PTDiagnosticCounters[98], count);
    }
    return count;
}
static const float RAB_DISTANT_LIGHT_DISTANCE = 100000.0f;

struct RAB_PathTracerUserData
{
    RTXDI_PTPathTraceInvocationType pathType;
    uint2 pixelPosition;
    float firstHitDistance;
    uint replayDebugFlags;
    float replayDebugPdf;
    float replayDebugEmission;
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

RAB_RayPayload RTXPT_PTTrace(RayDesc ray, bool visibilityRay = false)
{
    RAB_RayPayload p = (RAB_RayPayload)0;
    p.instanceIndex = ~0u;
    RayQuery<RAY_FLAG_SKIP_PROCEDURAL_PRIMITIVES> q;
    q.TraceRayInline(SceneBVH, RAY_FLAG_NONE, INSTANCE_MASK_ALL, ray);
    while (q.Proceed())
    {
        if (q.CandidateType() == CANDIDATE_NON_OPAQUE_TRIANGLE &&
            (visibilityRay ?
                Bridge::AlphaTestVisibilityRay(q.CandidateInstanceID(), q.CandidateInstanceIndex(),
                    q.CandidateGeometryIndex(), q.CandidatePrimitiveIndex(), q.CandidateTriangleBarycentrics()) :
                Bridge::AlphaTest(q.CandidateInstanceID(), q.CandidateInstanceIndex(),
                    q.CandidateGeometryIndex(), q.CandidatePrimitiveIndex(), q.CandidateTriangleBarycentrics())))
            q.CommitNonOpaqueTriangleHit();
    }
    if (q.CommittedStatus() == COMMITTED_TRIANGLE_HIT)
    {
        p.instanceIndex = q.CommittedInstanceIndex();
        p.geometryInstanceBase = q.CommittedInstanceID();
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
    if (g_RtxdiBridgeConst.ptDiagnostics != 0 && any(transmittance < 1.0f))
        InterlockedAdd(u_PTDiagnosticCounters[5], 1);
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
        RAB_RayPayload hit = RTXPT_PTTrace(ray, true);
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

RTXDI_BrdfRaySample RTXPT_PTSampleBsdf(RAB_Surface s, inout RTXDI_RandomSamplerState rng, out uint nativeLobe)
{
    nativeLobe = 0;
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
    nativeLobe = sample.lobe;
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
    // A binding diffuse budget depends on the sampled native component. Full
    // marginal BSDF throughput with a sampled-component cutoff changes the
    // estimator. In the full-prefix PSS replay track preserve native component
    // weight (including lobe-selection factors); terminal NEE still uses the
    // complete BSDF, and its final edge is outside the counted prefix.
    brs.brdfTimesNoL = (delta || g_RtxdiBridgeConst.ptExtendedSceneValidation != 0) ?
        sample.weight * brs.outPdf : s.Eval(brs.outDirection).rgb;
    if (delta) { brs.properties.SetDelta(); brs.properties.SetSpecular(); }
    if ((sample.lobe & (uint)LobeType::Specular) != 0) brs.properties.SetSpecular();
    if ((sample.lobe & (uint)LobeType::Transmission) != 0) brs.properties.SetTransmission();
    return brs;
}

RTXDI_BrdfRaySample RTXPT_PTSampleBsdf(RAB_Surface s, inout RTXDI_RandomSamplerState rng)
{
    uint ignoredNativeLobe;
    return RTXPT_PTSampleBsdf(s, rng, ignoredNativeLobe);
}

// NVIDIA reference RAB_MISCallbacks.hlsli balance heuristic, finite M=1.
// Uniform discrete light mass times conditional solid-angle density. Analytic
// point lights have no continuous BSDF companion. Environment is host-rejected.
float RTXPT_PTFiniteNEEWeight(RAB_LightSample light, float scatterPdf)
{
    if (RAB_IsAnalyticLightSample(light)) return 1.f;
    float pNee = light.solidAnglePdf / float(g_RtxdiBridgeConst.lightBufferParams.localLightBufferRegion.numLights);
    return pNee > 0.f ? pNee / (pNee + scatterPdf) : 0.f;
}
float RTXPT_PTFiniteEmitterWeight(RAB_RayPayload hit, RAB_Surface previousSurface, RTXDI_BrdfRaySample brs)
{
    if (brs.properties.IsDelta()) return 1.f;
    uint lightIndex = getLightIndex(hit.geometryInstanceBase, hit.geometryIndex, hit.primitiveIndex);
    if (lightIndex == RTXDI_InvalidLightIndex) return 1.f;
    // Light sampling takes a square UV, not raw triangle hit barycentrics.
    float2 uv = randomFromBarycentric(hitUVToBarycentric(hit.barycentrics));
    RAB_LightSample light = RAB_SamplePolymorphicLight(RAB_LoadLightInfo(lightIndex, false), previousSurface, uv);
    float pNee = light.solidAnglePdf / float(g_RtxdiBridgeConst.lightBufferParams.localLightBufferRegion.numLights);
    return brs.outPdf > 0.f ? brs.outPdf / (brs.outPdf + pNee) : 0.f;
}

// PT++ main section6.1 initial-tree ownership prerequisite. This pilot retains
// the existing NEE-only continuous transport partition, not supplemental MIS.
// Exactly one uniformly selected local light gives a known source probability;
// no RIS-selected PDF is substituted for the hypothetical PSS source PDF.
template<typename PTContextType>
void RTXPT_PTRecordUniformFiniteNEE(inout RTXDI_PathTracerContext<PTContextType> ctx,
    inout RTXDI_PathTracerRandomContext randomContext)
{
    const RTXDI_LightBufferRegion region = g_RtxdiBridgeConst.lightBufferParams.localLightBufferRegion;
    if (region.numLights == 0) return;
    uint offset = min(uint(RTXDI_GetNextRandom(randomContext.initialRandomSamplerState) * region.numLights), region.numLights - 1);
    uint lightIndex = region.firstLightIndex + offset;
    float2 uv = float2(RTXDI_GetNextRandom(randomContext.initialRandomSamplerState), RTXDI_GetNextRandom(randomContext.initialRandomSamplerState));
    RAB_Surface surface = ctx.GetIntersectionSurface();
    RAB_LightSample light = RAB_SamplePolymorphicLight(RAB_LoadLightInfo(lightIndex, false), surface, uv);
    if (!(light.solidAnglePdf > 0.f)) return;
    float3 reflected = RAB_GetReflectedBsdfRadianceForSurface(light.position, light.radiance, surface);
    reflected *= float(region.numLights) / light.solidAnglePdf;
    float scatterPdf = surface.EvalPdf(normalize(light.position - surface.GetPosW()), true);
    if (g_RtxdiBridgeConst.ptUnifiedFiniteNEE == 2)
        reflected *= RTXPT_PTFiniteNEEWeight(light, scatterPdf);
    RTXDI_SampledLightData data = RTXDI_SampledLightData_CreateInvalidData();
    RTXDI_SampledLightData_SetLightData(data, lightIndex);
    RTXDI_SampledLightData_SetUVData(data, uv);
    ctx.RecordNeeLightSample(data, reflected, 1.f / float(region.numLights),
        surface.EvalPdf(normalize(light.position - surface.GetPosW()), true), light, randomContext.initialRandomSamplerState);
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
#if defined(RTXDI_RESTIR_PT_INITIAL_SAMPLING)
    if (g_RtxdiBridgeConst.ptUnifiedFiniteNEE != 0)
    {
        // The SDK starts continuation tracing at depth2. At the primary hit,
        // NEE has light-inclusive length2. Restore depth before BSDF tracing.
        ctx.ctx.ptState.bounceDepth = 1;
        RTXPT_PTRecordUniformFiniteNEE(ctx, randomContext);
        ctx.ctx.ptState.bounceDepth = 2;
    }
#endif
    while (ctx.GetBounceDepth() <= ctx.GetMaxPathBounce())
    {
        ctx.BeginPathState();
        RAB_Surface previousSurface = ctx.GetIntersectionSurface();
        uint nativeLobe;
        RTXDI_BrdfRaySample brs = RTXPT_PTSampleBsdf(previousSurface, randomContext.replayRandomSamplerState, nativeLobe);
        user.replayDebugFlags = brs.properties.IsDelta() ? 1 : 0;
        user.replayDebugPdf = brs.outPdf;
        ctx.SetBrdfRaySample(brs);
        if (!ctx.ValidContinuationRayBrdfOverPdf()) { user.replayDebugFlags |= 64; break; }
        ctx.MultiplyPathThroughput(ctx.GetContinuationRayBrdfOverPdf());
        // PT++ section 6.2.4: initial RNG owns roulette. The hybrid-shift
        // context returns false, preserving the complete deterministic replay.
        const float rr = g_RtxdiBridgeConst.ptRouletteProbability;
        if (rr > 0.0f && rr < 1.0f && ctx.ShouldRunRussianRoulette())
        {
            if (g_RtxdiBridgeConst.ptDiagnostics != 0)
            {
                InterlockedAdd(u_PTDiagnosticCounters[0], 1);
                if (user.pathType != RTXDI_PTPathTraceInvocationType_Initial)
                    InterlockedAdd(u_PTDiagnosticCounters[3], 1);
            }
            if (RTXDI_GetNextRandom(randomContext.initialRandomSamplerState) >= rr)
            {
                if (g_RtxdiBridgeConst.ptDiagnostics != 0) InterlockedAdd(u_PTDiagnosticCounters[1], 1);
                break;
            }
            if (g_RtxdiBridgeConst.ptDiagnostics != 0) InterlockedAdd(u_PTDiagnosticCounters[2], 1);
            ctx.MultiplyPathThroughput(1.0f / rr);
            ctx.RecordRussianRouletteProbability(rr);
        }
        bool diffuseBudgetExceeded = false;
        if (g_RtxdiBridgeConst.ptExtendedSceneValidation != 0)
        {
            // Match native GenerateScatterRay, including its alternating diffuse
            // transmission policy. Null/alpha-rejected intersections never enter here.
            const bool diffuse = (nativeLobe & (uint)LobeType::Diffuse) != 0 ||
                previousSurface.GetRoughness() > 0.25f; // Native kSpecularRoughnessThreshold.
            if (diffuse && !((nativeLobe & (uint)LobeType::DiffuseTransmission) != 0 &&
                (user.nativeState.getVertexIndex() % 2) == 1))
                user.nativeState.incrementCounter(PackedCounters::DiffuseBounces);
            diffuseBudgetExceeded = user.nativeState.getCounter(PackedCounters::DiffuseBounces) > Bridge::getMaxDiffuseBounceLimit();
            if (diffuseBudgetExceeded && g_RtxdiBridgeConst.ptDiagnostics != 0)
                InterlockedAdd(u_PTDiagnosticCounters[6], 1);
        }
        user.nativeState.clearScatterEventFlags();
        if (brs.properties.IsTransmission())
        {
            if (g_RtxdiBridgeConst.ptDiagnostics != 0) InterlockedAdd(u_PTDiagnosticCounters[4], 1);
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
        if (!ctx.AnalyzePathReconnectibilityBeforeTrace()) { user.replayDebugFlags |= 128; break; }
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
        if (!accepted) { user.replayDebugFlags |= 32; ctx.SetPathTermination(true); break; }
        hit.committedRayT = totalHitDistance;
        ctx.SetTraceResult(hit);
        if (hit.instanceIndex == ~0u)
        {
            user.replayDebugFlags |= 2;
            ctx.RecordPathRadianceMiss(randomContext.initialRandomSamplerState);
            // Continuous misses are covered by NEE. A delta connection cannot
            // be sampled by NEE and therefore retains explicit emitted light.
            if ((g_RtxdiBridgeConst.giPTPartition == 0 || ctx.GetBounceDepth() >= 4) && brs.properties.IsDelta() && ctx.ShouldSampleEmissiveSurfaces() && Bridge::HasEnvMap())
            {
                EnvMap env = Bridge::CreateEnvMap();
#if defined(RTXDI_RESTIR_PT_HYBRID_SHIFT)
                // RTXDI's default hybrid callback omits secondary-bounce
                // environment light for its direct-light partition. RTXPT's PT
                // owner retains the discrete delta connection: NEE/DI cannot
                // evaluate that Dirac lobe. Restore only this pure-PSS domain.
                if (ctx.IsSecondaryBounce() && ctx.ctx.selectedPathLength == ctx.GetBounceDepth() &&
                    ctx.ctx.replayRcVertexLength > ctx.GetBounceDepth())
                    ctx.ctx.radiance += env.Eval(ray.Direction) * ctx.GetPathThroughput();
                else
#endif
                    ctx.RecordEnvironmentMapLightSample(env.Eval(ray.Direction), previousSurface, randomContext.initialRandomSamplerState);
            }
            break;
        }
        if (user.firstHitDistance == 0) user.firstHitDistance = hit.committedRayT;
        float3 emission = nativeSurface.shadingData.GetEmission();
        user.replayDebugEmission = RTXDI_Luminance(emission);
        if (any(emission>0)) user.replayDebugFlags |= 4;
        RAB_Surface surface = RTXPT_PTCollectNativeSurface(nativeSurface, hit.committedRayT, user.nativeState);
#if defined(RTXDI_RESTIR_PT_HYBRID_SHIFT)
        // A terminal connection can be evaluated by RecordPathIntersection
        // itself. Reject an over-budget replay prefix BEFORE that callback;
        // terminal BSDF emission at selectedPathLength is still allowed.
        // Pinned adapter for RTXDI-Library f12037f's selectedPathLength member.
        if (diffuseBudgetExceeded && ctx.GetBounceDepth() < ctx.ctx.selectedPathLength)
        {
            ctx.SetPathTermination(true);
            break;
        }
#endif
        ctx.RecordPathIntersection(surface);
        if (ctx.IsPathTerminated()) { user.replayDebugFlags |= 8; break; }
        if ((g_RtxdiBridgeConst.giPTPartition == 0 || ctx.GetBounceDepth() >= 4) &&
            (brs.properties.IsDelta() || g_RtxdiBridgeConst.ptUnifiedFiniteNEE == 2) && ctx.ShouldSampleEmissiveSurfaces())
        {
            if (g_RtxdiBridgeConst.ptUnifiedFiniteNEE == 2)
                emission *= RTXPT_PTFiniteEmitterWeight(hit, previousSurface, brs);
            ctx.RecordEmissiveLightSample(emission, previousSurface, randomContext.initialRandomSamplerState);
        }
        // Native truncation keeps terminal emission from this trace, but no
        // NEE or further scatter at its endpoint. Replay reconstructs all counters;
        // no unstored suffix diffuse budget is guessed at a mid-path connection.
        if (diffuseBudgetExceeded) { ctx.SetPathTermination(true); break; }
        if (ctx.ShouldSampleNee() && g_RtxdiBridgeConst.ptUnifiedFiniteNEE != 0)
            RTXPT_PTRecordUniformFiniteNEE(ctx, randomContext);
        else if (ctx.ShouldSampleNee())
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
                // Filter contributions, not the prefix or proposal draws. NEE at
                // depth2 is k2; NEE atdepth3 is k3 (light-inclusive length4).
                if (g_RtxdiBridgeConst.giPTPartition == 0 || ctx.GetBounceDepth() + 1 >= 4)
                    ctx.RecordNeeLightSample(data, reflected, 1.0f / r.weightSum,
                    surface.EvalPdf(normalize(light.position - surface.GetPosW()), true), light, randomContext.initialRandomSamplerState);
            }
        }
        ctx.IncreaseBounceDepth();
    }
}
#endif
