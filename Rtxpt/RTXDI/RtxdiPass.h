/*
* Copyright (c) 2025, NVIDIA CORPORATION.  All rights reserved.
*
* NVIDIA CORPORATION and its licensors retain all intellectual property
* and proprietary rights in and to this software, related documentation
* and any modifications thereto.  Any use, reproduction, disclosure or
* distribution of this software and related documentation without an express
* license agreement from NVIDIA CORPORATION is strictly prohibited.
*/

#pragma once

#include "../Shaders/PathTracer/Config.h"

#include <nvrhi/nvrhi.h>
#include <donut/core/math/math.h>
#include <memory>
#include <unordered_map>
#include <rtxdi/ImportanceSamplingContext.h>
#include "../SampleCommon/ComputePass.h"
#include "RayTracingPass.h"
#include "RtxdiResources.h"
#include "RtxdiApplicationSettings.h"

#include "../Shaders/PathTracer/Lighting/LightingTypes.hlsli"
#include "../Shaders/PathTracer/Lighting/EnvMap.hlsli"

class RenderTargets;
class PrepareLightsPass;
class GenerateMipsPass;
class EnvMapBaker;
struct ReGirIndirectConstants;
class ShaderDebug;

namespace donut::engine
{
	class ShaderFactory;
	class CommonRenderPasses;
	struct ShaderMacro;
	class PlanarView;
}

class ExtendedScene;

// B2 uses the RTXDI runtime with the pre-PT++ reconnectibility policy. B3 controls
// are explicit settings rather than silently inherited DLSS-specific defaults.
struct RtxdiPTUserSettings
{
    rtxdi::ReSTIRPT_ResamplingMode resamplingMode = rtxdi::ReSTIRPT_ResamplingMode::TemporalAndSpatial;
    RTXDI_PTInitialSamplingParameters initialSamplingParams = rtxdi::GetDefaultReSTIRPTInitialSamplingParams();
    RTXDI_PTTemporalResamplingParameters temporalResamplingParams = rtxdi::GetDefaultReSTIRPTTemporalResamplingParams(false);
    RTXDI_PTSpatialResamplingParameters spatialResamplingParams = rtxdi::GetDefaultReSTIRPTSpatialResamplingParams(false);
    RTXDI_PTReconnectionParameters reconnectionParams = rtxdi::GetDefaultReSTIRPTReconnectionParameters();
    RTXDI_PTHybridShiftPerFrameParameters hybridShiftParams = rtxdi::GetDefaultReSTIRPTHybridShiftParams();
    RTXDI_PTDecorrelationParameters decorrelationParams = rtxdi::GetDefaultReSTIRPTDecorrelationParams(false);
    RTXDI_BoilingFilterParameters boilingFilterParams = rtxdi::GetDefaultReSTIRPTBoilingFilterParams(false);
    float russianRouletteProbability = 0.0f; // 0 disables; initial generation only.
    RtxdiPTUserSettings();
};

struct RtxdiUserSettings
{
    RtxdiPTUserSettings restirPT;
	struct
	{
		rtxdi::ReSTIRDI_ResamplingMode resamplingMode = GetReSTIRDI_ResamplingMode();
		RTXDI_DIInitialSamplingParameters initialSamplingParams = getReSTIRDIInitialSamplingParams();
		RTXDI_DITemporalResamplingParameters temporalResamplingParams = getReSTIRDITemporalResamplingParams();
		RTXDI_BoilingFilterParameters boilingFilterParams = getReSTIRDIBoilingFilterParams();
		RTXDI_DISpatialResamplingParameters spatialResamplingParams = getReSTIRDISpatialResamplingParams();
		RTXDI_ShadingParameters shadingParams = getReSTIRDIShadingParams();
	} restirDI;

	struct  
	{
		rtxdi::ReSTIRGI_ResamplingMode resamplingMode = GetReSTIRGI_ResamplingMode();
		RTXDI_GITemporalResamplingParameters temporalResamplingParams = getReSTIRGITemporalResamplingParams();
		RTXDI_BoilingFilterParameters boilingFilterParams = getReSTIRGIBoilingFilterParams();
		RTXDI_GISpatialResamplingParameters spatialResamplingParams = getReSTIRGISpatialResamplingParams();
		RTXDI_GIFinalShadingParameters finalShadingParams = getReSTIRGIFinalShadingParams();
	} restirGI;

	struct 
	{
		rtxdi::ReGIRStaticParameters regirStaticParams = {};
		rtxdi::ReGIRDynamicParameters regirDynamicParameters = getReGIRDynamicParams();
	} regir;

	struct
	{
		int numIndirectSamples = 6;
	} regirIndirect;

	float rayEpsilon = 1.0e-4f;
	bool reStirGIEnableTemporalResampling = true;
	bool reStirGIVaryAgeThreshold = true;
};

struct RtxdiBridgeParameters
{
	uint32_t frameIndex;
	donut::math::uint2 frameDims;
	donut::math::float3 cameraPosition;

	RtxdiUserSettings userSettings;

    bool usingLightSampling;
    bool usingReGIR;
    bool unifiedFiniteNEEPilot = false;
    bool unifiedMIS = false;
    bool usingReSTIRPT = false;
    uint32_t giPTPartition = 0; // Initial-only disjoint development contract.
    bool extendedSceneValidation = false;
    uint32_t maxDiffuseBounces = 0;
    // Assert on camera cuts, scene/material changes and history-invalidating mode changes.
    bool resetReSTIRPT = false;
    bool capturePTDiagnostics = false;
    uint32_t samplingSeed = 0;
};

class RtxdiPass
{
public:
	RtxdiPass(
		nvrhi::IDevice* device,
		std::shared_ptr<donut::engine::ShaderFactory> shaderFactory,
		std::shared_ptr<donut::engine::CommonRenderPasses> commonRenderPasses,
		nvrhi::BindingLayoutHandle bindlessLayout);
	~RtxdiPass();

	void Reset();
    void PrepareResources(
        nvrhi::CommandListHandle commandList,
        const RenderTargets& renderTargets,
        std::shared_ptr<EnvMapBaker> envMap,
        EnvMapSceneParams envMapSceneParams,
        const std::shared_ptr<ExtendedScene> scene,
        std::shared_ptr<class MaterialsBaker> materialsBaker,
        std::shared_ptr<class OmmBaker> ommBaker,
        nvrhi::BufferHandle subInstanceDataBuffer,
        const RtxdiBridgeParameters& bridgeParams,
        const nvrhi::BindingLayoutHandle extraBindingLayout,
        std::shared_ptr<ShaderDebug> shaderDebug);
	void BeginFrame(
		nvrhi::CommandListHandle commandList,
		const RenderTargets& renderTargets,
		const nvrhi::BindingLayoutHandle extraBindingLayout,
		nvrhi::BindingSetHandle extraBindingSet);
	void Execute(
		nvrhi::CommandListHandle commandList,
		nvrhi::BindingSetHandle extraBindingSet, bool skipFinal);
	void ExecuteGI(nvrhi::CommandListHandle commandList,
		nvrhi::BindingSetHandle extraBindingSet, bool skipFinal);
    void ExecuteFusedDIGIFinal(nvrhi::CommandListHandle commandList,
        nvrhi::BindingSetHandle extraBindingSet);
    void ExecutePT(nvrhi::CommandListHandle commandList,
        nvrhi::BindingSetHandle extraBindingSet, bool skipFinal = false);
    void EndFrame();
    // Submitted/idle-safe diagnostic only; never call inside a timed frame.
    void CapturePTReservoirs(const std::string& path);
	
	std::shared_ptr<RtxdiResources> GetRTXDIResources() { return m_rtxdiResources; }
	nvrhi::BufferHandle GetRTXDIConstants() { return m_rtxdiConstantBuffer; }

private:
	void CheckContextStaticParameters();
	void UpdateContextDynamicParameters();
	void CreatePipelines(nvrhi::BindingLayoutHandle extraBindingLayout = nullptr, bool useRayQuery = true);
    void CreateBindingSet(const RenderTargets& renderTargets);
    void CreatePTPipelines(nvrhi::BindingLayoutHandle extraBindingLayout);

	std::unique_ptr<rtxdi::ImportanceSamplingContext> m_ImportanceSamplingContext;
	std::shared_ptr<RtxdiResources> m_rtxdiResources;
	std::unique_ptr<PrepareLightsPass> m_PrepareLightsPass;
	std::unique_ptr<GenerateMipsPass> m_LocalLightPdfMipmapPass;

	nvrhi::DeviceHandle m_device; 
	std::shared_ptr<donut::engine::ShaderFactory> m_shaderFactory;
	std::shared_ptr<donut::engine::CommonRenderPasses> m_CommonRenderPasses;
	std::shared_ptr<ExtendedScene> m_Scene;
	nvrhi::BindingLayoutHandle m_bindingLayout;
	nvrhi::BindingLayoutHandle m_bindlessLayout;
	nvrhi::BindingSetHandle m_bindingSet;
	nvrhi::BindingSetHandle m_PrevBindingSet;
	nvrhi::BufferHandle m_rtxdiConstantBuffer;

	ComputePass m_PresampleLightsPass;
	ComputePass m_PresampleEnvMapPass;
	ComputePass m_PresampleReGIRPass;
	ComputePass m_FinalSamplingPass;
	RayTracingPass m_GenerateInitialSamplesPass;
	RayTracingPass m_SpatialResamplingPass;
	RayTracingPass m_TemporalResamplingPass;

	RayTracingPass m_GITemporalResamplingPass;
	RayTracingPass m_GISpatialResamplingPass;
    RayTracingPass m_GIFinalShadingPass;
    RayTracingPass m_PTGenerateInitialSamplesPass;
    RayTracingPass m_PTIdentityShiftDiagnosticsPass;
    RayTracingPass m_PTTemporalResamplingPass;
    RayTracingPass m_PTSpatialResamplingPass;
    RayTracingPass m_PTQueuePass[7];
    nvrhi::BindingSetHandle m_PTQueueArgsBindingSet;
    RayTracingPass m_PTFinalShadingPass;
    RayTracingPass m_PTDuplicationMapPass;
    bool m_PTPipelinesCreated = false;
    bool m_PTNeedsClear = false;
    bool m_PTCameraHistoryValid = false;
    donut::math::float3 m_PreviousPTCameraPosition = {};
    donut::math::float3 m_PreviousPreviousPTCameraPosition = {};

    RayTracingPass m_FusedDIGIFinalShadingPass;

	void ExecuteComputePass(
		nvrhi::CommandListHandle& commandList, 
		ComputePass& pass, 
		const char* passName, 
		dm::int3 dispatchSize, 
		nvrhi::BindingSetHandle extraBindingSet = nullptr);

	void ExecuteRayTracingPass(
		nvrhi::CommandListHandle& commandList,
		RayTracingPass& pass,
		const char* passName,
		dm::int2 dispatchSize, 
		nvrhi::IBindingSet* extraBindingSet = nullptr
	);

	donut::engine::ShaderMacro GetReGirMacro(const rtxdi::ReGIRStaticParameters& regirParameters);

	void FillConstants(nvrhi::CommandListHandle commandList);
	void FillSharedConstants(struct RtxdiBridgeConstants& bridgeConstants) const;
	void FillDIConstants(RTXDI_Parameters& diParams);
    void FillGIConstants(RTXDI_GIParameters& giParams);
    void FillPTConstants(RTXDI_PTParameters& ptParams);
	void FillReGIRConstant(ReGIR_Parameters& regirParams);
	void FillReGirIndirectConstants(ReGirIndirectConstants& regirIndirectConstants);

	RtxdiBridgeParameters m_BridgeParameters{};
	uint32_t m_CurrentReservoirIndex;
	uint32_t m_PreviousReservoirIndex;
};

