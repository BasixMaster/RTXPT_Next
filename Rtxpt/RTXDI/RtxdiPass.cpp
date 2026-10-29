/*
* Copyright (c) 2025, NVIDIA CORPORATION.  All rights reserved.
*
* NVIDIA CORPORATION and its licensors retain all intellectual property
* and proprietary rights in and to this software, related documentation
* and any modifications thereto.  Any use, reproduction, disclosure or
* distribution of this software and related documentation without an express
* license agreement from NVIDIA CORPORATION is strictly prohibited.
*/

#include "RtxdiPass.h"
#include <cstddef>
#include <cstring>
#include <fstream>
#include <cstdio>
#include <stdexcept>
#include <rtxdi/ImportanceSamplingContext.h>
#include <rtxdi/RtxdiUtils.h>

#include "RtxdiResources.h"
#include "PrepareLightsPass.h"
#include "donut/engine/ShaderFactory.h"
#include "donut/engine/CommonRenderPasses.h"
#include "donut/engine/View.h"
#include "GeneratePdfMipsPass.h"
#include "../Lighting/Distant/EnvMapBaker.h"
#include "../Lighting/Distant/EnvMapImportanceSamplingBaker.h"
#include "../SampleCommon/ExtendedScene.h"
#include "ShaderParameters.h"
#include "../Shaders/SampleConstantBuffer.h"

#include "../SampleCommon/RenderTargets.h"

using namespace donut::math;
using namespace donut::engine;
using namespace donut::render;

static_assert(sizeof(RtxdiBridgeConstants) % 16 == 0, "RTXDI bridge constant buffer must use complete 16-byte rows");
static_assert(offsetof(RtxdiBridgeConstants, restirPT) % 16 == 0, "PT constants must start at a constant-buffer row boundary");
static_assert(sizeof(RTXDI_PTParameters) % 16 == 0, "Runtime PT parameter layout must preserve 16-byte rows");

RtxdiPTUserSettings::RtxdiPTUserSettings()
{
    reconnectionParams.reconnectionMode = RTXDI_PTReconnectionMode::FixedThreshold;
    temporalResamplingParams.duplicationBasedHistoryReduction = 0;
    spatialResamplingParams.duplicationBasedHistoryReduction = 0;
    spatialResamplingParams.enableSpatialHeuristicMode = 0;
    decorrelationParams.decorrelationMode = RTXDI_PTDecorrelationMode::None;
    decorrelationParams.decorrelationFactor = 0.0f;
    decorrelationParams.fireflyReplacementFilterEnable = 0;
    boilingFilterParams.enableBoilingFilter = 0;
}

RtxdiPass::RtxdiPass(
	nvrhi::IDevice* device,
	std::shared_ptr<donut::engine::ShaderFactory> shaderFactory,
	std::shared_ptr<donut::engine::CommonRenderPasses> commonRenderPasses,
	nvrhi::BindingLayoutHandle bindlessLayout) :
		m_device(device),
		m_shaderFactory(shaderFactory),
		m_CommonRenderPasses(commonRenderPasses),
		m_bindlessLayout(bindlessLayout),
		m_PreviousReservoirIndex(0)
{
	//Create binding layouts
	nvrhi::BindingLayoutDesc layoutDesc;
	layoutDesc.visibility = nvrhi::ShaderType::All;
	layoutDesc.bindings = {
		nvrhi::BindingLayoutItem::StructuredBuffer_SRV(21),		//t_LightDataBuffer
		nvrhi::BindingLayoutItem::TypedBuffer_SRV(22),			//t_NeighborOffsets
		nvrhi::BindingLayoutItem::TypedBuffer_SRV(23),			//t_LightIndexMappingBuffer
        nvrhi::BindingLayoutItem::TypedBuffer_SRV(24),            //t_PTPairingOffsets
		nvrhi::BindingLayoutItem::Texture_SRV(25),				//t_LocalLightPdfTexture
		nvrhi::BindingLayoutItem::StructuredBuffer_SRV(26),		//t_GeometryInstanceToLight
		
		nvrhi::BindingLayoutItem::StructuredBuffer_UAV(13),		//u_LightReservoirs
		nvrhi::BindingLayoutItem::StructuredBuffer_UAV(14),		//u_GIReservoirs
		nvrhi::BindingLayoutItem::TypedBuffer_UAV(15),			//u_RisBuffer
        nvrhi::BindingLayoutItem::TypedBuffer_UAV(16),            //u_RisLightDataBuffer
        nvrhi::BindingLayoutItem::StructuredBuffer_UAV(17),       //u_PTReservoirs
        nvrhi::BindingLayoutItem::RawBuffer_UAV(18),              //u_PTSpatialNeighborSelection
        nvrhi::BindingLayoutItem::StructuredBuffer_UAV(19),       //u_PTDiagnosticCounters

		nvrhi::BindingLayoutItem::VolatileConstantBuffer(5),	//g_RtxdiBridgeConst

		nvrhi::BindingLayoutItem::Sampler(4)
	};
	m_bindingLayout = m_device->createBindingLayout(layoutDesc);

	m_rtxdiConstantBuffer = m_device->createBuffer(nvrhi::utils::CreateVolatileConstantBufferDesc(sizeof(RtxdiBridgeConstants), "RtxdiBridgeConstants", 16));
}

RtxdiPass::~RtxdiPass(){}

// Check for changes in the static parameters, these will require the importance sampling context to be recreated
void RtxdiPass::CheckContextStaticParameters()
{
	if (m_ImportanceSamplingContext != nullptr)
	{
		auto& reGIRContext = m_ImportanceSamplingContext->GetReGIRContext();

        const auto& diStatic = m_ImportanceSamplingContext->GetReSTIRDIContext().GetStaticParameters();
        bool needsReset = diStatic.RenderWidth != m_BridgeParameters.frameDims.x ||
            diStatic.RenderHeight != m_BridgeParameters.frameDims.y ||
            (m_rtxdiResources && m_rtxdiResources->HasPTResources() != m_BridgeParameters.usingReSTIRPT);
		if (reGIRContext.GetReGIRStaticParameters().mode != m_BridgeParameters.userSettings.regir.regirStaticParams.mode)
			needsReset = true;
		if (reGIRContext.GetReGIRStaticParameters().lightsPerCell != m_BridgeParameters.userSettings.regir.regirStaticParams.lightsPerCell)
			needsReset = true;

		if (needsReset)
			Reset();
	}
}

void RtxdiPass::UpdateContextDynamicParameters()
{
	// ReSTIR DI
	m_ImportanceSamplingContext->GetReSTIRDIContext().SetFrameIndex(m_BridgeParameters.frameIndex);
	m_ImportanceSamplingContext->GetReSTIRDIContext().SetInitialSamplingParameters(m_BridgeParameters.userSettings.restirDI.initialSamplingParams);
	m_ImportanceSamplingContext->GetReSTIRDIContext().SetResamplingMode(m_BridgeParameters.userSettings.restirDI.resamplingMode);
	m_ImportanceSamplingContext->GetReSTIRDIContext().SetTemporalResamplingParameters(m_BridgeParameters.userSettings.restirDI.temporalResamplingParams);
	m_ImportanceSamplingContext->GetReSTIRDIContext().SetBoilingFilterParameters(m_BridgeParameters.userSettings.restirDI.boilingFilterParams);
	m_ImportanceSamplingContext->GetReSTIRDIContext().SetSpatialResamplingParameters(m_BridgeParameters.userSettings.restirDI.spatialResamplingParams);
	m_ImportanceSamplingContext->GetReSTIRDIContext().SetShadingParameters(m_BridgeParameters.userSettings.restirDI.shadingParams);

	// ReSTIR GI
	m_ImportanceSamplingContext->GetReSTIRGIContext().SetFrameIndex(m_BridgeParameters.frameIndex);
	m_ImportanceSamplingContext->GetReSTIRGIContext().SetResamplingMode(m_BridgeParameters.userSettings.restirGI.resamplingMode);
	m_ImportanceSamplingContext->GetReSTIRGIContext().SetTemporalResamplingParameters(m_BridgeParameters.userSettings.restirGI.temporalResamplingParams);
	m_ImportanceSamplingContext->GetReSTIRGIContext().SetBoilingFilterParameters(m_BridgeParameters.userSettings.restirGI.boilingFilterParams);
	m_ImportanceSamplingContext->GetReSTIRGIContext().SetSpatialResamplingParameters(m_BridgeParameters.userSettings.restirGI.spatialResamplingParams);
	m_ImportanceSamplingContext->GetReSTIRGIContext().SetFinalShadingParameters(m_BridgeParameters.userSettings.restirGI.finalShadingParams);

    // ReSTIR PT is an explicitly selected alternative to the GI reuse path.
    auto& pt = m_ImportanceSamplingContext->GetReSTIRPTContext();
    const auto& ptSettings = m_BridgeParameters.userSettings.restirPT;
    pt.SetFrameIndex(m_BridgeParameters.frameIndex);
    pt.SetResamplingMode(ptSettings.resamplingMode);
    pt.SetInitialSamplingParameters(ptSettings.initialSamplingParams);
    pt.SetTemporalResamplingParameters(ptSettings.temporalResamplingParams);
    pt.SetSpatialResamplingParameters(ptSettings.spatialResamplingParams);
    pt.SetReconnectionParameters(ptSettings.reconnectionParams);
    pt.SetHybridShiftParameters(ptSettings.hybridShiftParams);
    pt.SetDecorrelationParameters(ptSettings.decorrelationParams);
    pt.SetBoilingFilterParameters(ptSettings.boilingFilterParams);

    // B2 intentionally has no CGNS/duplication/decorrelation passes. Refuse a
    // settings mismatch instead of consuming unwritten side buffers.
    if (m_BridgeParameters.usingReSTIRPT &&
        (ptSettings.spatialResamplingParams.enableSpatialHeuristicMode != 0 ||
         ptSettings.temporalResamplingParams.duplicationBasedHistoryReduction != 0 ||
         ptSettings.spatialResamplingParams.duplicationBasedHistoryReduction != 0 ||
         ptSettings.decorrelationParams.decorrelationMode != RTXDI_PTDecorrelationMode::None ||
         ptSettings.decorrelationParams.fireflyReplacementFilterEnable != 0))
        throw std::runtime_error("B2 ReSTIR PT does not activate B3 CGNS/duplication/decorrelation passes.");

    // ReGIR
    auto regirParams = m_BridgeParameters.userSettings.regir.regirDynamicParameters;
	regirParams.center = { m_BridgeParameters.cameraPosition.x, m_BridgeParameters.cameraPosition.y,m_BridgeParameters.cameraPosition.z };
	m_ImportanceSamplingContext->GetReGIRContext().SetDynamicParameters(regirParams);
}

void RtxdiPass::CreatePipelines(nvrhi::BindingLayoutHandle extraBindingLayout /*= nullptr*/, bool useRayQuery /*= true*/)
{
	const auto& reGIRParams = m_ImportanceSamplingContext->GetReGIRContext().GetReGIRStaticParameters();
	
	std::vector<donut::engine::ShaderMacro> regirMacros = { GetReGirMacro(reGIRParams) };

	m_PresampleLightsPass.Init(m_device, *m_shaderFactory, "app/RTXDI/PresampleLights.hlsl", "main", {}, m_bindingLayout, extraBindingLayout, m_bindlessLayout);
	m_PresampleEnvMapPass.Init(m_device, *m_shaderFactory, "app/RTXDI/PresampleEnvironmentMap.hlsl", "main", {}, m_bindingLayout, extraBindingLayout, m_bindlessLayout);
	if (reGIRParams.mode != rtxdi::ReGIRMode::Disabled)
	{
		m_PresampleReGIRPass.Init(m_device, *m_shaderFactory, "app/RTXDI/PresampleReGIR.hlsl", "main", regirMacros, m_bindingLayout, extraBindingLayout, m_bindlessLayout);
	}
	
	m_GenerateInitialSamplesPass.Init(m_device, *m_shaderFactory, "app/RTXDI/GenerateInitialSamples.hlsl", 
		regirMacros, useRayQuery, RTXDI_SCREEN_SPACE_GROUP_SIZE, m_bindingLayout, extraBindingLayout, m_bindlessLayout);
	m_SpatialResamplingPass.Init(m_device, *m_shaderFactory, "app/RTXDI/SpatialResampling.hlsl",
		{}, useRayQuery, RTXDI_SCREEN_SPACE_GROUP_SIZE, m_bindingLayout, extraBindingLayout, m_bindlessLayout);
	m_TemporalResamplingPass.Init(m_device, *m_shaderFactory, "app/RTXDI/TemporalResampling.hlsl",
		{}, useRayQuery, RTXDI_SCREEN_SPACE_GROUP_SIZE, m_bindingLayout, extraBindingLayout, m_bindlessLayout);
	
	std::vector<donut::engine::ShaderMacro> finalShadingMacros = { { "USE_RAY_QUERY", "1" } };
#if NVRHI_D3D12_WITH_DXR12_OPACITY_MICROMAP
	finalShadingMacros.push_back({ "NVRHI_D3D12_WITH_DXR12_OPACITY_MICROMAP", "1" });
#endif // NVRHI_D3D12_WITH_DXR12_OPACITY_MICROMAP
	m_FinalSamplingPass.Init(m_device, *m_shaderFactory, "app/RTXDI/DIFinalShading.hlsl", "main", finalShadingMacros, m_bindingLayout, extraBindingLayout, m_bindlessLayout);
	
	m_GISpatialResamplingPass.Init(m_device, *m_shaderFactory, "app/RTXDI/GISpatialResampling.hlsl",
		{}, useRayQuery, RTXDI_SCREEN_SPACE_GROUP_SIZE, m_bindingLayout, extraBindingLayout, m_bindlessLayout);
	m_GITemporalResamplingPass.Init(m_device, *m_shaderFactory, "app/RTXDI/GITemporalResampling.hlsl",
		{}, useRayQuery, RTXDI_SCREEN_SPACE_GROUP_SIZE, m_bindingLayout, extraBindingLayout, m_bindlessLayout);
	m_GIFinalShadingPass.Init(m_device, *m_shaderFactory, "app/RTXDI/GIFinalShading.hlsl",
		{}, useRayQuery, RTXDI_SCREEN_SPACE_GROUP_SIZE, m_bindingLayout, extraBindingLayout, m_bindlessLayout);
    m_FusedDIGIFinalShadingPass.Init(m_device, *m_shaderFactory, "app/RTXDI/FusedDIGIFinalShading.hlsl",
        {}, useRayQuery, RTXDI_SCREEN_SPACE_GROUP_SIZE, m_bindingLayout, extraBindingLayout, m_bindlessLayout);
}

void RtxdiPass::CreatePTPipelines(nvrhi::BindingLayoutHandle extraBindingLayout)
{
    if (!m_BridgeParameters.usingReSTIRPT || m_PTPipelinesCreated)
        return;
    const bool initialized =
        m_PTGenerateInitialSamplesPass.Init(m_device, *m_shaderFactory, "app/RTXDI/PT/GenerateInitialSamples.hlsl", {}, true, RTXDI_SCREEN_SPACE_GROUP_SIZE, m_bindingLayout, extraBindingLayout, m_bindlessLayout) &&
        m_PTIdentityShiftDiagnosticsPass.Init(m_device, *m_shaderFactory, "app/RTXDI/PT/IdentityShiftDiagnostics.hlsl", {}, true, RTXDI_SCREEN_SPACE_GROUP_SIZE, m_bindingLayout, extraBindingLayout, m_bindlessLayout) &&
        m_PTTemporalResamplingPass.Init(m_device, *m_shaderFactory, "app/RTXDI/PT/TemporalResampling.hlsl", {}, true, RTXDI_SCREEN_SPACE_GROUP_SIZE, m_bindingLayout, extraBindingLayout, m_bindlessLayout) &&
        m_PTSpatialResamplingPass.Init(m_device, *m_shaderFactory, "app/RTXDI/PT/SpatialResampling.hlsl", {}, true, RTXDI_SCREEN_SPACE_GROUP_SIZE, m_bindingLayout, extraBindingLayout, m_bindlessLayout) &&
        m_PTFinalShadingPass.Init(m_device, *m_shaderFactory, "app/RTXDI/PT/FinalShading.hlsl", {}, true, RTXDI_SCREEN_SPACE_GROUP_SIZE, m_bindingLayout, extraBindingLayout, m_bindlessLayout);
    if (!initialized)
        throw std::runtime_error("Failed to compile/create the selected ReSTIR PT passes.");
    m_PTPipelinesCreated = true;
}

void RtxdiPass::CreateBindingSet(const RenderTargets& renderTargets)
{
	for (int currentFrame = 0; currentFrame <= 1; currentFrame++)
	{
		nvrhi::BindingSetDesc bindingSetDesc;
		bindingSetDesc.bindings = {
			// RTXDI resources
			nvrhi::BindingSetItem::StructuredBuffer_SRV(21, m_rtxdiResources->LightDataBuffer),
			nvrhi::BindingSetItem::TypedBuffer_SRV(22, m_rtxdiResources->NeighborOffsetsBuffer),
			nvrhi::BindingSetItem::TypedBuffer_SRV(23, m_rtxdiResources->LightIndexMappingBuffer),
            nvrhi::BindingSetItem::TypedBuffer_SRV(24, m_rtxdiResources->PTPairingOffsets),
			nvrhi::BindingSetItem::Texture_SRV(25, m_rtxdiResources->LocalLightPdfTexture),
			nvrhi::BindingSetItem::StructuredBuffer_SRV(26, m_rtxdiResources->GeometryInstanceToLightBuffer),
			
			// Render targets
			nvrhi::BindingSetItem::StructuredBuffer_UAV(13, m_rtxdiResources->LightReservoirBuffer),
			nvrhi::BindingSetItem::StructuredBuffer_UAV(14, m_rtxdiResources->GIReservoirBuffer),
			nvrhi::BindingSetItem::TypedBuffer_UAV(15, m_rtxdiResources->RisBuffer),
            nvrhi::BindingSetItem::TypedBuffer_UAV(16, m_rtxdiResources->RisLightDataBuffer),
            nvrhi::BindingSetItem::StructuredBuffer_UAV(17, m_rtxdiResources->PTReservoirBuffer),
            nvrhi::BindingSetItem::RawBuffer_UAV(18, m_rtxdiResources->PTSpatialNeighborSelectionBuffer),
            nvrhi::BindingSetItem::StructuredBuffer_UAV(19, m_rtxdiResources->PTDiagnosticCounters),
			
			nvrhi::BindingSetItem::ConstantBuffer(5, m_rtxdiConstantBuffer),

			nvrhi::BindingSetItem::Sampler(4, m_CommonRenderPasses->m_LinearWrapSampler)
		};

		const nvrhi::BindingSetHandle bindingSet = m_device->createBindingSet(bindingSetDesc, m_bindingLayout);
		if (currentFrame)
			m_bindingSet = bindingSet;
		else
			m_PrevBindingSet = bindingSet;
	}
}

void RtxdiPass::Reset()
{
    m_ImportanceSamplingContext = nullptr;
    m_rtxdiResources = nullptr;
    m_LocalLightPdfMipmapPass = nullptr;
    m_bindingSet = nullptr;
    m_PrevBindingSet = nullptr;
    m_PTPipelinesCreated = false;
    m_PTNeedsClear = false;
    m_PTCameraHistoryValid = false;
    // Both hold the scene (the pass also its sub-instance buffer and bakers); PrepareResources sets them again
    m_Scene = nullptr;
    m_PrepareLightsPass = nullptr;
}

void RtxdiPass::PrepareResources(
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
    std::shared_ptr<ShaderDebug> shaderDebug)
{
    // Frame gaps and changes to the path construction/scheduling contract cannot
    // inherit packed path histories from a different invocation schedule.
    const auto& oldPT = m_BridgeParameters.userSettings.restirPT;
    const auto& newPT = bridgeParams.userSettings.restirPT;
    const bool ptHistoryContractChanged = m_BridgeParameters.usingReSTIRPT && bridgeParams.usingReSTIRPT &&
        (bridgeParams.frameIndex != m_BridgeParameters.frameIndex + 1u ||
         bridgeParams.samplingSeed != m_BridgeParameters.samplingSeed ||
         bridgeParams.giPTPartition != m_BridgeParameters.giPTPartition ||
         bridgeParams.extendedSceneValidation != m_BridgeParameters.extendedSceneValidation ||
         bridgeParams.maxDiffuseBounces != m_BridgeParameters.maxDiffuseBounces ||
         oldPT.resamplingMode != newPT.resamplingMode ||
         oldPT.initialSamplingParams.numInitialSamples != newPT.initialSamplingParams.numInitialSamples ||
         oldPT.initialSamplingParams.maxBounceDepth != newPT.initialSamplingParams.maxBounceDepth ||
         oldPT.initialSamplingParams.maxRcVertexLength != newPT.initialSamplingParams.maxRcVertexLength ||
         oldPT.reconnectionParams.reconnectionMode != newPT.reconnectionParams.reconnectionMode ||
         oldPT.reconnectionParams.roughnessThreshold != newPT.reconnectionParams.roughnessThreshold ||
          oldPT.reconnectionParams.distanceThreshold != newPT.reconnectionParams.distanceThreshold ||
          oldPT.reconnectionParams.minConnectionFootprint != newPT.reconnectionParams.minConnectionFootprint ||
          oldPT.reconnectionParams.minConnectionFootprintSigma != newPT.reconnectionParams.minConnectionFootprintSigma ||
          oldPT.reconnectionParams.minPdfRoughness != newPT.reconnectionParams.minPdfRoughness ||
          oldPT.reconnectionParams.minPdfRoughnessSigma != newPT.reconnectionParams.minPdfRoughnessSigma ||
          oldPT.russianRouletteProbability != newPT.russianRouletteProbability);
    if (bridgeParams.capturePTDiagnostics && bridgeParams.usingReSTIRPT)
        std::printf("PT_HISTORY frame=%u previous=%u requestedReset=%d contractChanged=%d priorHistory=%d\n",
            bridgeParams.frameIndex, m_BridgeParameters.frameIndex, int(bridgeParams.resetReSTIRPT),
            int(ptHistoryContractChanged), int(m_PTCameraHistoryValid));
    m_BridgeParameters = bridgeParams;

    CheckContextStaticParameters();
    m_Scene = scene;    // after the check, whose Reset() clears it

    if (!m_ImportanceSamplingContext)
    {
        // Set static parameters for ReSTIR DI, ReSTIR GI and ReGIR
        rtxdi::ImportanceSamplingContext_StaticParameters staticParameters = {};
        staticParameters.renderWidth = m_BridgeParameters.frameDims.x;
        staticParameters.renderHeight = m_BridgeParameters.frameDims.y;
        staticParameters.regirStaticParams = m_BridgeParameters.userSettings.regir.regirStaticParams;

        m_ImportanceSamplingContext = std::make_unique<rtxdi::ImportanceSamplingContext>(staticParameters);

        // RTXDI context settings affect the shader permutations
        CreatePipelines(extraBindingLayout, true);
    }

    UpdateContextDynamicParameters();
    CreatePTPipelines(extraBindingLayout);
    if (m_BridgeParameters.usingReSTIRPT && (m_BridgeParameters.resetReSTIRPT || ptHistoryContractChanged))
    {
        m_PTNeedsClear = true;
        m_PTCameraHistoryValid = false;
    }

    if (!m_PrepareLightsPass)
    {
        m_PrepareLightsPass = std::make_unique<PrepareLightsPass>(m_device, m_shaderFactory, m_CommonRenderPasses, nullptr, materialsBaker, ommBaker, subInstanceDataBuffer, m_bindlessLayout, shaderDebug);
        m_PrepareLightsPass->CreatePipeline();
    }

    m_PrepareLightsPass->SetScene(m_Scene, envMap, envMapSceneParams);

    //Check if resources have changed
    bool envMapPresent = envMap != nullptr;
    uint32_t numEmissiveMeshes, numEmissiveTriangles = 0;
    m_PrepareLightsPass->CountLightsInScene(numEmissiveMeshes, numEmissiveTriangles);
    // Reserve a record for the baked global environment even without a scene light.
    uint32_t numPrimitiveLights = uint32_t(m_Scene->GetSceneGraph()->GetLights().size()) + uint32_t(envMapPresent);
    uint32_t numGeometryInstances = uint32_t(m_Scene->GetSceneGraph()->GetGeometryInstancesCount());

    if (m_rtxdiResources && (
        numEmissiveMeshes > m_rtxdiResources->GetMaxEmissiveMeshes() ||
        numEmissiveTriangles > m_rtxdiResources->GetMaxEmissiveTriangles() ||
        numPrimitiveLights > m_rtxdiResources->GetMaxPrimitiveLights() ||
        numGeometryInstances > m_rtxdiResources->GetMaxGeometryInstances() ||
        m_rtxdiResources->HasGaussianPairs() != ((m_BridgeParameters.giPTPartition & 4u) != 0)))
    {
        m_rtxdiResources = nullptr;
    }

    bool rtxdiResourceCreated = false;

    if (!m_rtxdiResources)
    {
        uint32_t meshAllocationQuantum = 128;
        uint32_t triangleAllocationQuantum = 1024;
        uint32_t primitiveAllocationQuantum = 128;

        m_rtxdiResources = std::make_shared<RtxdiResources>(
            m_device,
            m_ImportanceSamplingContext->GetReSTIRDIContext(),
            m_ImportanceSamplingContext->GetRISBufferSegmentAllocator(),
            (numEmissiveMeshes + meshAllocationQuantum - 1) & ~(meshAllocationQuantum - 1),
            (numEmissiveTriangles + triangleAllocationQuantum - 1) & ~(triangleAllocationQuantum - 1),
            (numPrimitiveLights + primitiveAllocationQuantum - 1) & ~(primitiveAllocationQuantum - 1),
            numGeometryInstances,
            m_BridgeParameters.usingReSTIRPT ? &m_ImportanceSamplingContext->GetReSTIRPTContext() : nullptr,
            (m_BridgeParameters.giPTPartition & 4u) != 0);

        rtxdiResourceCreated = true;
        m_PTNeedsClear = m_BridgeParameters.usingReSTIRPT;
        m_PTCameraHistoryValid = false;
    }

    if (rtxdiResourceCreated)
    {
        m_PrepareLightsPass->CreateBindingSet(*m_rtxdiResources, renderTargets);
        m_rtxdiResources->InitializeNeighborOffsets(commandList, m_ImportanceSamplingContext->GetNeighborOffsetCount());
        m_LocalLightPdfMipmapPass = nullptr;
    }

    if (rtxdiResourceCreated || m_bindingSet == nullptr)
    {
        CreateBindingSet(renderTargets);
    }
}

void RtxdiPass::BeginFrame(
    nvrhi::CommandListHandle commandList,
    const RenderTargets & renderTargets,
    const nvrhi::BindingLayoutHandle extraBindingLayout,
    nvrhi::BindingSetHandle extraBindingSet )
{
    if (m_BridgeParameters.usingReSTIRPT && m_PTNeedsClear)
    {
        commandList->clearBufferUInt(m_rtxdiResources->PTReservoirBuffer, 0);
        commandList->clearBufferUInt(m_rtxdiResources->PTSpatialNeighborSelectionBuffer, 0xffffffffu);
        nvrhi::utils::BufferUavBarrier(commandList, m_rtxdiResources->PTReservoirBuffer);
        nvrhi::utils::BufferUavBarrier(commandList, m_rtxdiResources->PTSpatialNeighborSelectionBuffer);
        commandList->commitBarriers();
        m_PTNeedsClear = false;
    }

    if (m_BridgeParameters.usingReSTIRPT && m_BridgeParameters.capturePTDiagnostics)
    {
        commandList->clearBufferUInt(m_rtxdiResources->PTDiagnosticCounters, 0);
        nvrhi::utils::BufferUavBarrier(commandList, m_rtxdiResources->PTDiagnosticCounters);
    }
    // Light preparation is needed for DI/ReGIR and PT next-event estimation.
	if (m_BridgeParameters.usingLightSampling)
	{
		//This pass needs to happen before we fill the constant buffers 
        GpuProfiler::Begin(commandList, "Prepare Light");
		RTXDI_LightBufferParameters lightBufferParams = m_PrepareLightsPass->Process(commandList);
        GpuProfiler::End(commandList);

		m_ImportanceSamplingContext->SetLightBufferParams(lightBufferParams);
	}

	FillConstants(commandList);

	// In cases where the RTXDI context is only needed for ReSTIR GI we can skip pdf, presampling and ReGir passes
	if (!m_BridgeParameters.usingLightSampling)
		return;

	if (!m_LocalLightPdfMipmapPass)
	{
		m_LocalLightPdfMipmapPass = std::make_unique<GenerateMipsPass>(
			m_device,
			m_shaderFactory,
			nullptr,
			m_rtxdiResources->LocalLightPdfTexture);
	}

    GpuProfiler::Begin(commandList, "GeneratePDFTextures");

	m_LocalLightPdfMipmapPass->Process(commandList);

    GpuProfiler::End(commandList);

	// Pre-sample lights
	const auto lightBufferParams = m_ImportanceSamplingContext->GetLightBufferParameters();
	if (m_ImportanceSamplingContext->IsLocalLightPowerRISEnabled() && lightBufferParams.localLightBufferRegion.numLights > 0)
	{
		dm::int3 presampleDispatchSize = {
			dm::div_ceil(m_ImportanceSamplingContext->GetLocalLightRISBufferSegmentParams().tileSize, RTXDI_PRESAMPLING_GROUP_SIZE),
			int(m_ImportanceSamplingContext->GetLocalLightRISBufferSegmentParams().tileCount),
			1
		};

		nvrhi::utils::BufferUavBarrier(commandList, m_rtxdiResources->RisBuffer);

		ExecuteComputePass(commandList, m_PresampleLightsPass, "Pre-sample Lights", presampleDispatchSize, extraBindingSet);
	}

	if (lightBufferParams.environmentLightParams.lightPresent)
	{
		dm::int3 presampleDispatchSize = {
			dm::div_ceil(m_ImportanceSamplingContext->GetEnvironmentLightRISBufferSegmentParams().tileSize, RTXDI_PRESAMPLING_GROUP_SIZE),
			int(m_ImportanceSamplingContext->GetEnvironmentLightRISBufferSegmentParams().tileCount),
			1
		};

		nvrhi::utils::BufferUavBarrier(commandList, m_rtxdiResources->RisBuffer);

		ExecuteComputePass(commandList, m_PresampleEnvMapPass, "Pre-sample Envmap", presampleDispatchSize, extraBindingSet);
	}

	//Build ReGIR structure 
	const auto& reGIRContext = m_ImportanceSamplingContext->GetReGIRContext();
	if (m_ImportanceSamplingContext->IsReGIREnabled()
		&& m_BridgeParameters.usingReGIR
		&& reGIRContext.GetReGIRStaticParameters().mode != rtxdi::ReGIRMode::Disabled)
	{
		dm::int3 worldGridDispatchSize = { dm::div_ceil(reGIRContext.GetReGIRLightSlotCount(), RTXDI_GRID_BUILD_GROUP_SIZE), 1, 1 };
		ExecuteComputePass(commandList, m_PresampleReGIRPass, "Pre-sample ReGir", worldGridDispatchSize, extraBindingSet);
	}
}

void RtxdiPass::Execute(
	nvrhi::CommandListHandle commandList,
	nvrhi::BindingSetHandle extraBindingSet,
    bool skipFinal
)
{
    GpuProfiler::Begin(commandList, "ReSTIR DI");

	auto& reSTIRDI = m_ImportanceSamplingContext->GetReSTIRDIContext();
	dm::int2 dispatchSize = { (int) reSTIRDI.GetStaticParameters().RenderWidth, (int)reSTIRDI.GetStaticParameters().RenderHeight };
	
	// Not implemented
	//if (reSTIRDI.GetResamplingMode() == rtxdi::ReSTIRDI_ResamplingMode::FusedSpatiotemporal)
	//{
	//	// TODO: combine initial, temporal, spatial and final sampling in one pass
	//       // In case this is implemented, probably no point in doing fused ReSTIR-DI and ReSTIR-GI sampling, so 
	//       // then remove skipFinal and related logic.
	//}
	//else
	{
		//Generate sample, pick re-sampling method, final sampling
		ExecuteRayTracingPass(commandList, m_GenerateInitialSamplesPass, "Generate Initial Samples", dispatchSize, extraBindingSet);

		if (reSTIRDI.GetResamplingMode() == rtxdi::ReSTIRDI_ResamplingMode::Temporal ||
			reSTIRDI.GetResamplingMode() == rtxdi::ReSTIRDI_ResamplingMode::TemporalAndSpatial)
		{
			nvrhi::utils::BufferUavBarrier(commandList, m_rtxdiResources->LightReservoirBuffer);
			ExecuteRayTracingPass(commandList, m_TemporalResamplingPass, "Temporal Re-sampling", dispatchSize, extraBindingSet);
		}
		
		if (reSTIRDI.GetResamplingMode() == rtxdi::ReSTIRDI_ResamplingMode::Spatial ||
			reSTIRDI.GetResamplingMode() == rtxdi::ReSTIRDI_ResamplingMode::TemporalAndSpatial)
		{
			nvrhi::utils::BufferUavBarrier(commandList, m_rtxdiResources->LightReservoirBuffer);
			ExecuteRayTracingPass(commandList, m_SpatialResamplingPass, "Spatial Re-sampling", dispatchSize, extraBindingSet);

		}

        //Full screen light sampling pass
        nvrhi::utils::BufferUavBarrier(commandList, m_rtxdiResources->LightReservoirBuffer);

        if (!skipFinal)
        {
            dm::int3 screenSpaceDispatchSize = {
                ((int)reSTIRDI.GetStaticParameters().RenderWidth + RTXDI_SCREEN_SPACE_GROUP_SIZE - 1) / RTXDI_SCREEN_SPACE_GROUP_SIZE,
                ((int)reSTIRDI.GetStaticParameters().RenderHeight + RTXDI_SCREEN_SPACE_GROUP_SIZE - 1) / RTXDI_SCREEN_SPACE_GROUP_SIZE,
                1 };

            ExecuteComputePass(commandList, m_FinalSamplingPass, "Final Sampling", screenSpaceDispatchSize, extraBindingSet);
        }
    }
    GpuProfiler::End(commandList);
}

void RtxdiPass::FillConstants(nvrhi::CommandListHandle commandList)
{
	// Set the ReGir center and the camera position 
	RtxdiBridgeConstants bridgeConstants{};
	bridgeConstants.lightBufferParams = m_ImportanceSamplingContext->GetLightBufferParameters();
	bridgeConstants.localLightsRISBufferSegmentParams = m_ImportanceSamplingContext->GetLocalLightRISBufferSegmentParams();
	bridgeConstants.environmentLightRISBufferSegmentParams = m_ImportanceSamplingContext->GetEnvironmentLightRISBufferSegmentParams();
	bridgeConstants.runtimeParams = m_ImportanceSamplingContext->GetReSTIRDIContext().GetRuntimeParams();

	FillSharedConstants(bridgeConstants);
	FillDIConstants(bridgeConstants.restirDI);
    FillGIConstants(bridgeConstants.restirGI);
    FillPTConstants(bridgeConstants.restirPT);
	FillReGIRConstant(bridgeConstants.regir);
	FillReGirIndirectConstants(bridgeConstants.regirIndirect);

    if (m_BridgeParameters.samplingSeed != 0)
    {
        // Only random-stream inputs change. Actual frame, history tags and
        // reservoir ping-pong indices retain their native chronology.
        const uint32_t streamFrame = rtxdi::JenkinsHash(m_BridgeParameters.frameIndex ^ rtxdi::JenkinsHash(m_BridgeParameters.samplingSeed));
        bridgeConstants.runtimeParams.frameIndex = streamFrame;
        bridgeConstants.restirPT.temporalResampling.uniformRandomNumber = rtxdi::JenkinsHash(streamFrame);
        bridgeConstants.restirDI.temporalResamplingParams.uniformRandomNumber = rtxdi::JenkinsHash(streamFrame);
        bridgeConstants.restirGI.temporalResamplingParams.uniformRandomNumber = rtxdi::JenkinsHash(streamFrame);
    }
	commandList->writeBuffer(m_rtxdiConstantBuffer, &bridgeConstants, sizeof(RtxdiBridgeConstants));
}

void RtxdiPass::FillSharedConstants(struct RtxdiBridgeConstants& bridgeConstants) const
{
    bridgeConstants.frameIndex = m_BridgeParameters.frameIndex;
    bridgeConstants.ptCameraPosition = m_BridgeParameters.cameraPosition;
    bridgeConstants.ptPreviousCameraPosition = m_PTCameraHistoryValid ? m_PreviousPTCameraPosition : m_BridgeParameters.cameraPosition;
    bridgeConstants.ptPreviousPreviousCameraPosition = m_PTCameraHistoryValid ? m_PreviousPreviousPTCameraPosition : m_BridgeParameters.cameraPosition;
    bridgeConstants.ptHistoryValid = m_PTCameraHistoryValid ? 1 : 0;
    bridgeConstants.ptRouletteProbability = m_BridgeParameters.userSettings.restirPT.russianRouletteProbability;
    bridgeConstants.ptDiagnostics = m_BridgeParameters.capturePTDiagnostics ? 1u : 0u;
    bridgeConstants.giPTPartition = m_BridgeParameters.giPTPartition;
    bridgeConstants.ptExtendedSceneValidation = m_BridgeParameters.extendedSceneValidation ? 1u : 0u;
	bridgeConstants.frameDim = m_BridgeParameters.frameDims;
	bridgeConstants.rayEpsilon = m_BridgeParameters.userSettings.rayEpsilon;
	bridgeConstants.localLightPdfTextureSize = uint2(m_rtxdiResources->LocalLightPdfTexture->getDesc().width, m_rtxdiResources->LocalLightPdfTexture->getDesc().height);
	bridgeConstants.localLightPdfLastMipLevel = m_rtxdiResources->LocalLightPdfTexture->getDesc().mipLevels - 1 ;
	bridgeConstants.maxLights = uint32_t(m_rtxdiResources->LightDataBuffer->getDesc().byteSize / (sizeof(PolymorphicLightInfo) * 2));
	bridgeConstants.reStirGIVaryAgeThreshold = m_BridgeParameters.userSettings.reStirGIVaryAgeThreshold;

	const auto& giSampleMode = m_ImportanceSamplingContext->GetReSTIRGIContext().GetResamplingMode();
	bridgeConstants.reStirGIEnableTemporalResampling = ((giSampleMode == rtxdi::ReSTIRGI_ResamplingMode::Temporal) || (giSampleMode == rtxdi::ReSTIRGI_ResamplingMode::TemporalAndSpatial)) ? 1 : 0;
}

void RtxdiPass::FillDIConstants(RTXDI_Parameters& diParams)
{
	const auto& reSTIRDI = m_ImportanceSamplingContext->GetReSTIRDIContext();
	const auto& lightBufferParams = m_ImportanceSamplingContext->GetLightBufferParameters();

	diParams.reservoirBufferParams = reSTIRDI.GetReservoirBufferParameters();
	diParams.bufferIndices = reSTIRDI.GetBufferIndices();
	diParams.initialSamplingParams = reSTIRDI.GetInitialSamplingParameters();
    if (lightBufferParams.infiniteLightBufferRegion.numLights == 0)
        diParams.initialSamplingParams.numInfiniteLightSamples = 0;
	diParams.initialSamplingParams.environmentMapImportanceSampling = lightBufferParams.environmentLightParams.lightPresent;
	if (!diParams.initialSamplingParams.environmentMapImportanceSampling)
		diParams.initialSamplingParams.numEnvironmentSamples = 0;
	diParams.temporalResamplingParams = reSTIRDI.GetTemporalResamplingParameters();
	diParams.boilingFilterParams = reSTIRDI.GetBoilingFilterParameters();
	diParams.spatialResamplingParams = reSTIRDI.GetSpatialResamplingParameters();
	diParams.shadingParams = reSTIRDI.GetShadingParameters();
}

void RtxdiPass::FillGIConstants(RTXDI_GIParameters& giParams)
{
	const auto& reSTIRGI = m_ImportanceSamplingContext->GetReSTIRGIContext();

	giParams.reservoirBufferParams = reSTIRGI.GetReservoirBufferParameters();
	giParams.bufferIndices = reSTIRGI.GetBufferIndices();
	giParams.temporalResamplingParams = reSTIRGI.GetTemporalResamplingParameters();
	giParams.boilingFilterParams = reSTIRGI.GetBoilingFilterParameters();
	giParams.spatialResamplingParams = reSTIRGI.GetSpatialResamplingParameters();
	giParams.finalShadingParams = reSTIRGI.GetFinalShadingParameters();
}


void RtxdiPass::FillPTConstants(RTXDI_PTParameters& ptParams)
{
    const auto& pt = m_ImportanceSamplingContext->GetReSTIRPTContext();
    ptParams.reservoirBuffer = pt.GetReservoirBufferParameters();
    ptParams.bufferIndices = pt.GetBufferIndices();
    ptParams.initialSampling = pt.GetInitialSamplingParameters();
    ptParams.temporalResampling = pt.GetTemporalResamplingParameters();
    ptParams.spatialResampling = pt.GetSpatialResamplingParameters();
    ptParams.reconnection = pt.GetReconnectionParameters();
    ptParams.hybridShift = pt.GetHybridShiftParameters();
    ptParams.decorrelation = pt.GetDecorrelationParameters();
    ptParams.boilingFilter = pt.GetBoilingFilterParameters();
}

void RtxdiPass::FillReGIRConstant(ReGIR_Parameters& regirParams)
{
	const auto& regir = m_ImportanceSamplingContext->GetReGIRContext();
	auto staticParams = regir.GetReGIRStaticParameters();
	auto dynamicParams = regir.GetReGIRDynamicParameters();
	auto gridParams = regir.GetReGIRGridCalculatedParameters();
	auto onionParams = regir.GetReGIROnionCalculatedParameters();

	regirParams.gridParams.cellsX = staticParams.gridParameters.gridSize.x;
	regirParams.gridParams.cellsY = staticParams.gridParameters.gridSize.y;
	regirParams.gridParams.cellsZ = staticParams.gridParameters.gridSize.z;

	regirParams.commonParams.numRegirBuildSamples = dynamicParams.regirNumBuildSamples;
	regirParams.commonParams.risBufferOffset = regir.GetReGIRCellOffset();
	regirParams.commonParams.lightsPerCell = staticParams.lightsPerCell;
	regirParams.commonParams.centerX = dynamicParams.center.x;
	regirParams.commonParams.centerY = dynamicParams.center.y;
	regirParams.commonParams.centerZ = dynamicParams.center.z;
	regirParams.commonParams.cellSize = (staticParams.mode == rtxdi::ReGIRMode::Onion)
		? dynamicParams.regirCellSize * 0.5f // Onion operates with radii, while "size" feels more like diameter
		: dynamicParams.regirCellSize;
	regirParams.commonParams.localLightSamplingFallbackMode = static_cast<uint32_t>(dynamicParams.fallbackSamplingMode);
	regirParams.commonParams.localLightPresamplingMode = static_cast<uint32_t>(dynamicParams.presamplingMode);
	regirParams.commonParams.samplingJitter = std::max(0.f, dynamicParams.regirSamplingJitter * 2.f);
	regirParams.onionParams.cubicRootFactor = onionParams.regirOnionCubicRootFactor;
	regirParams.onionParams.linearFactor = onionParams.regirOnionLinearFactor;
	regirParams.onionParams.numLayerGroups = uint32_t(onionParams.regirOnionLayers.size());

	assert(onionParams.regirOnionLayers.size() <= RTXDI_ONION_MAX_LAYER_GROUPS);
	for (int group = 0; group < int(onionParams.regirOnionLayers.size()); group++)
	{
		regirParams.onionParams.layers[group] = onionParams.regirOnionLayers[group];
		regirParams.onionParams.layers[group].innerRadius *= regirParams.commonParams.cellSize;
		regirParams.onionParams.layers[group].outerRadius *= regirParams.commonParams.cellSize;
	}

	assert(onionParams.regirOnionRings.size() <= RTXDI_ONION_MAX_RINGS);
	for (int n = 0; n < int(onionParams.regirOnionRings.size()); n++)
	{
		regirParams.onionParams.rings[n] = onionParams.regirOnionRings[n];
	}

	regirParams.onionParams.cubicRootFactor = regir.GetReGIROnionCalculatedParameters().regirOnionCubicRootFactor;
}


void RtxdiPass::FillReGirIndirectConstants(ReGirIndirectConstants& regirIndirectConstants)
{
	regirIndirectConstants.numIndirectSamples = m_BridgeParameters.userSettings.regirIndirect.numIndirectSamples;
}

void RtxdiPass::ExecuteGI(nvrhi::CommandListHandle commandList, nvrhi::BindingSetHandle extraBindingSet, bool skipFinal)
{
    GpuProfiler::Begin(commandList, "ReSTIR GI");

	auto& reSTIRGI = m_ImportanceSamplingContext->GetReSTIRGIContext();

	dm::int2 dispatchSize = { (int)reSTIRGI.GetStaticParams().RenderWidth, (int)reSTIRGI.GetStaticParams().RenderHeight };

    if (m_BridgeParameters.giPTPartition != 0)
    {
        // GI-short initial estimator reads only this frame's native exports.
        // No reservoir reuse, Jacobian clamp or approximate final blend.
        if (!skipFinal)
            ExecuteRayTracingPass(commandList, m_GIFinalShadingPass, "GI Short Initial Shading", dispatchSize, extraBindingSet);
        GpuProfiler::End(commandList);
        return;
    }
	ExecuteRayTracingPass(commandList, m_GITemporalResamplingPass, "Temporal Resampling", dispatchSize, extraBindingSet);

	if (reSTIRGI.GetResamplingMode() == rtxdi::ReSTIRGI_ResamplingMode::Spatial || reSTIRGI.GetResamplingMode() == rtxdi::ReSTIRGI_ResamplingMode::TemporalAndSpatial)
	{
		nvrhi::utils::BufferUavBarrier(commandList, m_rtxdiResources->GIReservoirBuffer);

		ExecuteRayTracingPass(commandList, m_GISpatialResamplingPass, "Spatial Resampling", dispatchSize, extraBindingSet);
	}

	nvrhi::utils::BufferUavBarrier(commandList, m_rtxdiResources->GIReservoirBuffer);

    if (!skipFinal)
	    ExecuteRayTracingPass(commandList, m_GIFinalShadingPass, "Final Shading", dispatchSize, extraBindingSet);

    GpuProfiler::End(commandList); // ReSTIR GI
}

void RtxdiPass::ExecuteFusedDIGIFinal(nvrhi::CommandListHandle commandList, nvrhi::BindingSetHandle extraBindingSet)
{
	auto& reSTIRDI = m_ImportanceSamplingContext->GetReSTIRDIContext();
	dm::int2 dispatchSize = { (int)reSTIRDI.GetStaticParameters().RenderWidth, (int)reSTIRDI.GetStaticParameters().RenderHeight };

    ExecuteRayTracingPass(commandList, m_FusedDIGIFinalShadingPass, "Fused DI GI Final Shading", dispatchSize, extraBindingSet);
}

void RtxdiPass::ExecutePT(nvrhi::CommandListHandle commandList, nvrhi::BindingSetHandle extraBindingSet, bool skipFinal)
{
    if (!m_BridgeParameters.usingReSTIRPT || !m_PTPipelinesCreated || !m_rtxdiResources->HasPTResources())
        throw std::runtime_error("ReSTIR PT dispatched without its selected resource/pipeline state.");
    GpuProfiler::Begin(commandList, "ReSTIR PT");
    const auto& pt = m_ImportanceSamplingContext->GetReSTIRPTContext();
    const auto mode = pt.GetResamplingMode();
    if ((m_BridgeParameters.giPTPartition & 2u) != 0 &&
        pt.GetBufferIndices().spatialResamplingInputBufferIndex == pt.GetBufferIndices().spatialResamplingOutputBufferIndex)
        throw std::runtime_error("Paired spatial pilot requires immutable source and separate output reservoirs");
    const auto params = pt.GetStaticParams();
    const dm::int2 dispatchSize = { int(params.RenderWidth), int(params.RenderHeight) };
    nvrhi::utils::BufferUavBarrier(commandList, m_rtxdiResources->PTReservoirBuffer);
    ExecuteRayTracingPass(commandList, m_PTGenerateInitialSamplesPass, "PT Initial Sampling", dispatchSize, extraBindingSet);
    if (m_BridgeParameters.capturePTDiagnostics)
    {
        nvrhi::utils::BufferUavBarrier(commandList,m_rtxdiResources->PTReservoirBuffer);
        ExecuteRayTracingPass(commandList,m_PTIdentityShiftDiagnosticsPass,"PT Identity Shift Diagnostics",dispatchSize,extraBindingSet);
    }
    if (mode == rtxdi::ReSTIRPT_ResamplingMode::Temporal || mode == rtxdi::ReSTIRPT_ResamplingMode::TemporalAndSpatial)
    {
        nvrhi::utils::BufferUavBarrier(commandList, m_rtxdiResources->PTReservoirBuffer);
        ExecuteRayTracingPass(commandList, m_PTTemporalResamplingPass, "PT Temporal Resampling", dispatchSize, extraBindingSet);
    }
    if (mode == rtxdi::ReSTIRPT_ResamplingMode::Spatial || mode == rtxdi::ReSTIRPT_ResamplingMode::TemporalAndSpatial)
    {
        nvrhi::utils::BufferUavBarrier(commandList, m_rtxdiResources->PTReservoirBuffer);
        ExecuteRayTracingPass(commandList, m_PTSpatialResamplingPass, "PT Spatial Resampling", dispatchSize, extraBindingSet);
        if ((m_BridgeParameters.giPTPartition & 2u) != 0)
            nvrhi::utils::BufferUavBarrier(commandList, m_rtxdiResources->PTSpatialNeighborSelectionBuffer);
    }
    nvrhi::utils::BufferUavBarrier(commandList, m_rtxdiResources->PTReservoirBuffer);
    if (!skipFinal)
    ExecuteRayTracingPass(commandList, m_PTFinalShadingPass, "PT Final Shading", dispatchSize, extraBindingSet);
    GpuProfiler::End(commandList);
}

void RtxdiPass::EndFrame()
{
    if (m_BridgeParameters.usingReSTIRPT)
    {
        m_PreviousPreviousPTCameraPosition = m_PTCameraHistoryValid ? m_PreviousPTCameraPosition : m_BridgeParameters.cameraPosition;
        m_PreviousPTCameraPosition = m_BridgeParameters.cameraPosition;
        m_PTCameraHistoryValid = true;
    }
}

void RtxdiPass::ExecuteComputePass(
	nvrhi::CommandListHandle& commandList,
	ComputePass& pass,
	const char* passName,
	dm::int3 dispatchSize,
	nvrhi::BindingSetHandle extraBindingSet /*= nullptr*/)
{
    GpuProfiler::Begin(commandList, passName);
    
    SampleMiniConstants unusedPushConstants = { };  // shared bindings require them
	pass.Execute(commandList, dispatchSize.x, dispatchSize.y, dispatchSize.z, m_bindingSet,
		extraBindingSet, m_Scene->GetDescriptorTable(), &unusedPushConstants, sizeof(unusedPushConstants));

    GpuProfiler::End(commandList);
}

void RtxdiPass::ExecuteRayTracingPass(
	nvrhi::CommandListHandle& commandList, 
	RayTracingPass& pass, 
	const char* passName, 
	dm::int2 dispatchSize, 
	nvrhi::IBindingSet* extraBindingSet /* = nullptr */
)
{
    GpuProfiler::Begin(commandList, passName);
	
    SampleMiniConstants unusedPushConstants = { };  // shared bindings require them
	pass.Execute(commandList, dispatchSize.x, dispatchSize.y, m_bindingSet, 
		extraBindingSet, m_Scene->GetDescriptorTable(), &unusedPushConstants, sizeof(unusedPushConstants));

    GpuProfiler::End(commandList);
}

donut::engine::ShaderMacro RtxdiPass::GetReGirMacro(const rtxdi::ReGIRStaticParameters& regirParameters)
{
	std::string regirMode;

	switch (regirParameters.mode)
	{
	case rtxdi::ReGIRMode::Disabled :
		regirMode = "RTXDI_REGIR_DISABLED";
		break;
	case rtxdi::ReGIRMode::Grid :
		regirMode = "RTXDI_REGIR_GRID";
		break;
	case rtxdi::ReGIRMode::Onion :
		regirMode = "RTXDI_REGIR_ONION";
		break;
	}

	return { "RTXDI_REGIR_MODE", regirMode };
}


void RtxdiPass::CapturePTReservoirs(const std::string& path)
{
    if (!m_BridgeParameters.usingReSTIRPT || !m_rtxdiResources->HasPTResources())
        throw std::runtime_error("PT reservoir capture requires active PT resources");
    const auto source = m_rtxdiResources->PTReservoirBuffer;
    nvrhi::BufferDesc desc;
    desc.byteSize = source->getDesc().byteSize;
    desc.cpuAccess = nvrhi::CpuAccessMode::Read;
    desc.debugName = "PTReservoirDiagnosticReadback";
    auto staging = m_device->createBuffer(desc);
    if (!staging) throw std::runtime_error("PT reservoir staging allocation failed");
    auto copy = m_device->createCommandList();
    copy->open();
    copy->copyBuffer(staging, 0, source, 0, desc.byteSize);
    copy->close();
    m_device->executeCommandList(copy);
    m_device->waitForIdle();
    const void* mapped = m_device->mapBuffer(staging, nvrhi::CpuAccessMode::Read);
    if (!mapped) throw std::runtime_error("PT reservoir map failed");
    std::ofstream binary(path, std::ios::binary);
    binary.write(static_cast<const char*>(mapped), std::streamsize(desc.byteSize));
    m_device->unmapBuffer(staging);
    if (!binary) throw std::runtime_error("PT reservoir write failed");
    const auto& ctx = m_ImportanceSamplingContext->GetReSTIRPTContext();
    const auto& layout = ctx.GetReservoirBufferParameters();
    const auto& indices = ctx.GetBufferIndices();
    std::ofstream meta(path + ".json");
    meta << "{\n  \"schema_version\": 1,\n  \"packed_stride_bytes\": 64,\n  \"block_size\": " << RTXDI_RESERVOIR_BLOCK_SIZE
         << ",\n  \"width\": " << m_BridgeParameters.frameDims.x << ",\n  \"height\": " << m_BridgeParameters.frameDims.y
         << ",\n  \"frame_index\": " << m_BridgeParameters.frameIndex << ",\n  \"history_valid\": " << (m_PTCameraHistoryValid ? "true" : "false")
         << ",\n  \"array_pitch\": " << layout.reservoirArrayPitch << ",\n  \"block_row_pitch\": " << layout.reservoirBlockRowPitch
         << ",\n  \"initial_preserved_index\": " << indices.initialPathTracerPreservedBufferIndex
         << ",\n  \"temporal_input_index\": " << indices.temporalResamplingInputBufferIndex
         << ",\n  \"temporal_output_index\": " << indices.temporalResamplingOutputBufferIndex
         << ",\n  \"final_index\": " << indices.finalShadingInputBufferIndex << "\n}\n";
    if (!meta) throw std::runtime_error("PT reservoir metadata write failed");
    nvrhi::BufferDesc statsDesc;
    statsDesc.byteSize = 48 * sizeof(uint32_t);
    statsDesc.cpuAccess = nvrhi::CpuAccessMode::Read;
    statsDesc.debugName = "PTCounterReadback";
    auto stats = m_device->createBuffer(statsDesc);
    if (!stats) throw std::runtime_error("PT counter staging allocation failed");
    auto statsCopy = m_device->createCommandList();
    statsCopy->open();
    statsCopy->copyBuffer(stats, 0, m_rtxdiResources->PTDiagnosticCounters, 0, statsDesc.byteSize);
    statsCopy->close();
    m_device->executeCommandList(statsCopy);
    m_device->waitForIdle();
    const auto* counters = static_cast<const uint32_t*>(m_device->mapBuffer(stats, nvrhi::CpuAccessMode::Read));
    if (!counters) throw std::runtime_error("PT counter map failed");
    float selfShiftMaxError = 0;
    std::memcpy(&selfShiftMaxError,counters+9,sizeof(float));
    std::ofstream statFile(path + ".stats.json");
    statFile << "{\n  \"scope\": \"last captured frame, diagnostics only\",\n  \"roulette_tests\": " << counters[0]
        << ",\n  \"roulette_terminated\": " << counters[1] << ",\n  \"roulette_survived\": " << counters[2]
        << ",\n  \"replay_roulette_tests\": " << counters[3]
        << ",\n  \"transmission_scatter_events\": " << counters[4]
        << ",\n  \"attenuated_medium_segments\": " << counters[5]
        << ",\n  \"diffuse_budget_terminations\": " << counters[6]
        << ",\n  \"identity_shift_tests_legacy_slot\": " << counters[7]
        << ",\n  \"identity_shift_tests\": " << counters[7]
        << ",\n  \"identity_shift_failures\": " << counters[8]
        << ",\n  \"identity_shift_max_relative_error\": " << selfShiftMaxError
        << ",\n  \"identity_nee_tests\": " << counters[10] << ",\n  \"identity_nee_failures\": " << counters[11]
        << ",\n  \"identity_replay_tests\": " << counters[12] << ",\n  \"identity_replay_failures\": " << counters[13]
        << ",\n  \"identity_other_tests\": " << counters[14] << ",\n  \"identity_other_failures\": " << counters[15];
    statFile << ",\n  \"identity_debug_words\": [";
    for (int i=16;i<32;++i) { if(i>16) statFile << ","; statFile << counters[i]; }
    statFile << "]"
        << ",\n  \"hybrid_shift_calls\": " << counters[32]
        << ",\n  \"hybrid_raw_nonfinite_target\": " << counters[33]
        << ",\n  \"hybrid_raw_nonfinite_jacobian\": " << counters[34]
        << ",\n  \"hybrid_returned_nonfinite_weight_product\": " << counters[35]
        << ",\n  \"hybrid_rejected_shift_zeroed\": " << counters[36]
        << ",\n  \"hybrid_nonfinite_target_zero_jacobian\": " << counters[37]
        << ",\n  \"hybrid_nonfinite_target_nonzero_jacobian\": " << counters[38]
        << ",\n  \"hybrid_returned_nonfinite_target\": " << counters[39]
        << ",\n  \"paired_eligible_pairs\": " << counters[40]
        << ",\n  \"paired_directed_shift_calls\": " << counters[41]
        << ",\n  \"paired_vector_output_pixels\": " << counters[42]
        << ",\n  \"paired_fallback_pixels\": " << counters[43]
        << ",\n  \"paired_nonfinite_vectors\": " << counters[44]
        << ",\n  \"paired_nonreciprocal_links\": " << counters[45]
        << ",\n  \"paired_in_view_nonlocal_pairs\": " << counters[46]
        << ",\n  \"paired_max_link_distance_squared\": " << counters[47] << "\n}\n";
    m_device->unmapBuffer(stats);
    if (!statFile) throw std::runtime_error("PT counter metadata write failed");
    if ((m_BridgeParameters.giPTPartition & 4u) != 0)
    {
        const auto table = m_rtxdiResources->PTPairingOffsets;
        nvrhi::BufferDesc readDesc;
        readDesc.byteSize = table->getDesc().byteSize;
        readDesc.cpuAccess = nvrhi::CpuAccessMode::Read;
        readDesc.debugName = "PairTableDiagnosticReadback";
        auto readback = m_device->createBuffer(readDesc);
        if (!readback) throw std::runtime_error("Pair table staging allocation failed");
        auto copyTables = m_device->createCommandList();
        copyTables->open(); copyTables->copyBuffer(readback,0,table,0,readDesc.byteSize); copyTables->close();
        m_device->executeCommandList(copyTables); m_device->waitForIdle();
        const void* data = m_device->mapBuffer(readback,nvrhi::CpuAccessMode::Read);
        if (!data) throw std::runtime_error("Pair table staging map failed");
        std::ofstream output(path+".pairs.bin",std::ios::binary);
        output.write(static_cast<const char*>(data),std::streamsize(readDesc.byteSize));
        m_device->unmapBuffer(readback);
        if (!output) throw std::runtime_error("Pair table readback write failed");
    }
}
