/*
* Copyright (c) 2025, NVIDIA CORPORATION.  All rights reserved.
*
* NVIDIA CORPORATION and its licensors retain all intellectual property
* and proprietary rights in and to this software, related documentation
* and any modifications thereto.  Any use, reproduction, disclosure or
* distribution of this software and related documentation without an express
* license agreement from NVIDIA CORPORATION is strictly prohibited.
*/

#define RTXDI_WITH_RESTIR_GI

#include "RtxdiResources.h"
#include <rtxdi/DI/ReSTIRDI.h>
#include <rtxdi/PT/ReSTIRPT.h>
#include <rtxdi/LightSampling/RISBufferSegmentAllocator.h>

#include <donut/core/math/math.h>

using namespace dm;
#include "ShaderParameters.h"

uint32_t getNextPowerOf2(uint32_t a)
{
    // https://graphics.stanford.edu/~seander/bithacks.html#RoundUpPowerOf2
	a--;
	a |= a >> 1;
	a |= a >> 2;
	a |= a >> 4;
	a |= a >> 8;
	a |= a >> 16;
	a++;
	return a;
}

RtxdiResources::RtxdiResources(
    nvrhi::IDevice* device, 
    const rtxdi::ReSTIRDIContext& context,
    const rtxdi::RISBufferSegmentAllocator& risBufferSegmentAllocator,
    uint32_t maxEmissiveMeshes,
    uint32_t maxEmissiveTriangles,
    uint32_t maxPrimitiveLights,
    uint32_t maxGeometryInstances,
    const rtxdi::ReSTIRPTContext* ptContext) : m_MaxEmissiveMeshes(maxEmissiveMeshes)
    , m_MaxEmissiveTriangles(maxEmissiveTriangles)
    , m_MaxPrimitiveLights(maxPrimitiveLights)
    , m_MaxGeometryInstances(maxGeometryInstances)
{
    nvrhi::BufferDesc taskBufferDesc;
    taskBufferDesc.byteSize = sizeof(PrepareLightsTask) * std::max((maxEmissiveMeshes + maxPrimitiveLights), 1u);
    taskBufferDesc.structStride = sizeof(PrepareLightsTask);
    taskBufferDesc.initialState = nvrhi::ResourceStates::ShaderResource;
    taskBufferDesc.keepInitialState = true;
    taskBufferDesc.debugName = "TaskBuffer";
    taskBufferDesc.canHaveUAVs = true;
    TaskBuffer = device->createBuffer(taskBufferDesc);


    nvrhi::BufferDesc primitiveLightBufferDesc;
    primitiveLightBufferDesc.byteSize = sizeof(PolymorphicLightInfoFull) * std::max(maxPrimitiveLights, 1u);
    primitiveLightBufferDesc.structStride = sizeof(PolymorphicLightInfoFull);
    primitiveLightBufferDesc.initialState = nvrhi::ResourceStates::ShaderResource;
    primitiveLightBufferDesc.keepInitialState = true;
    primitiveLightBufferDesc.debugName = "PrimitiveLightBuffer";
    PrimitiveLightBuffer = device->createBuffer(primitiveLightBufferDesc);


    nvrhi::BufferDesc risBufferDesc;
    risBufferDesc.byteSize = sizeof(uint32_t) * 2 * std::max(risBufferSegmentAllocator.GetTotalSizeInElements(), 1u); // RG32_UINT per element
    risBufferDesc.format = nvrhi::Format::RG32_UINT;
    risBufferDesc.canHaveTypedViews = true;
    risBufferDesc.initialState = nvrhi::ResourceStates::ShaderResource;
    risBufferDesc.keepInitialState = true;
    risBufferDesc.debugName = "RisBuffer";
    risBufferDesc.canHaveUAVs = true;
    RisBuffer = device->createBuffer(risBufferDesc);


    risBufferDesc.byteSize = sizeof(uint32_t) * 8 * std::max(risBufferSegmentAllocator.GetTotalSizeInElements(), 1u); // RGBA32_UINT x 2 per element
    risBufferDesc.format = nvrhi::Format::RGBA32_UINT;
    risBufferDesc.debugName = "RisLightDataBuffer";
    RisLightDataBuffer = device->createBuffer(risBufferDesc);


    uint32_t maxLocalLights = maxEmissiveTriangles + maxPrimitiveLights;
    uint32_t lightBufferElements = maxLocalLights * 2;

    nvrhi::BufferDesc lightBufferDesc;
    lightBufferDesc.byteSize = sizeof(PolymorphicLightInfoFull) * std::max(lightBufferElements, 1u);
    lightBufferDesc.structStride = sizeof(PolymorphicLightInfoFull);
    lightBufferDesc.initialState = nvrhi::ResourceStates::ShaderResource;
    lightBufferDesc.keepInitialState = true;
    lightBufferDesc.debugName = "LightDataBuffer";
    lightBufferDesc.canHaveUAVs = true;
    LightDataBuffer = device->createBuffer(lightBufferDesc);


    nvrhi::BufferDesc geometryInstanceToLightBufferDesc;
    geometryInstanceToLightBufferDesc.byteSize = sizeof(uint32_t) * maxGeometryInstances;
    geometryInstanceToLightBufferDesc.structStride = sizeof(uint32_t);
    geometryInstanceToLightBufferDesc.initialState = nvrhi::ResourceStates::ShaderResource;
    geometryInstanceToLightBufferDesc.keepInitialState = true;
    geometryInstanceToLightBufferDesc.debugName = "GeometryInstanceToLightBuffer";
    GeometryInstanceToLightBuffer = device->createBuffer(geometryInstanceToLightBufferDesc);


    nvrhi::BufferDesc lightIndexMappingBufferDesc;
    lightIndexMappingBufferDesc.byteSize = sizeof(uint32_t) * std::max(lightBufferElements, 1u);
    lightIndexMappingBufferDesc.format = nvrhi::Format::R32_UINT;
    lightIndexMappingBufferDesc.canHaveTypedViews = true;
    lightIndexMappingBufferDesc.initialState = nvrhi::ResourceStates::ShaderResource;
    lightIndexMappingBufferDesc.keepInitialState = true;
    lightIndexMappingBufferDesc.debugName = "LightIndexMappingBuffer";
    lightIndexMappingBufferDesc.canHaveUAVs = true;
    LightIndexMappingBuffer = device->createBuffer(lightIndexMappingBufferDesc);
    

    nvrhi::BufferDesc neighborOffsetBufferDesc;
    neighborOffsetBufferDesc.byteSize = context.GetStaticParameters().NeighborOffsetCount * 2;
    neighborOffsetBufferDesc.format = nvrhi::Format::RG8_SNORM;
    neighborOffsetBufferDesc.canHaveTypedViews = true;
    neighborOffsetBufferDesc.debugName = "NeighborOffsets";
    neighborOffsetBufferDesc.initialState = nvrhi::ResourceStates::ShaderResource;
    neighborOffsetBufferDesc.keepInitialState = true;
    NeighborOffsetsBuffer = device->createBuffer(neighborOffsetBufferDesc);


    nvrhi::BufferDesc lightReservoirBufferDesc;
    lightReservoirBufferDesc.byteSize = sizeof(RTXDI_PackedDIReservoir) * context.GetReservoirBufferParameters().reservoirArrayPitch * rtxdi::c_NumReSTIRDIReservoirBuffers;
    lightReservoirBufferDesc.structStride = sizeof(RTXDI_PackedDIReservoir);
    lightReservoirBufferDesc.initialState = nvrhi::ResourceStates::UnorderedAccess;
    lightReservoirBufferDesc.keepInitialState = true;
    lightReservoirBufferDesc.debugName = "LightReservoirBuffer";
    lightReservoirBufferDesc.canHaveUAVs = true;
    LightReservoirBuffer = device->createBuffer(lightReservoirBufferDesc);


    nvrhi::BufferDesc giReservoirBufferDesc;
    giReservoirBufferDesc.byteSize = sizeof(RTXDI_PackedGIReservoir) * context.GetReservoirBufferParameters().reservoirArrayPitch * rtxdi::c_NumReSTIRDIReservoirBuffers;
    giReservoirBufferDesc.structStride = sizeof(RTXDI_PackedGIReservoir);
    giReservoirBufferDesc.initialState = nvrhi::ResourceStates::UnorderedAccess;
    giReservoirBufferDesc.keepInitialState = true;
    giReservoirBufferDesc.debugName = "GIReservoirBuffer";
    giReservoirBufferDesc.canHaveUAVs = true;
    GIReservoirBuffer = device->createBuffer(giReservoirBufferDesc);

    // Bind valid minimum-size resources in the legacy path without allocating a
    // screen-sized PT history. Toggling PT recreates this resource set explicitly.
    m_HasPTResources = ptContext != nullptr;
    const uint64_t ptPitch = ptContext ? ptContext->GetReservoirBufferParameters().reservoirArrayPitch : 1;
    static_assert(sizeof(RTXDI_PackedPTReservoir) == 64, "PT reservoir ABI must match runtime packing");
    nvrhi::BufferDesc ptReservoirDesc;
    ptReservoirDesc.byteSize = sizeof(RTXDI_PackedPTReservoir) * ptPitch * (ptContext ? rtxdi::c_NumReSTIRPTReservoirBuffers : 1);
    ptReservoirDesc.structStride = sizeof(RTXDI_PackedPTReservoir);
    ptReservoirDesc.initialState = nvrhi::ResourceStates::UnorderedAccess;
    ptReservoirDesc.keepInitialState = true;
    ptReservoirDesc.canHaveUAVs = true;
    ptReservoirDesc.debugName = "PTReservoirBuffer";
    PTReservoirBuffer = device->createBuffer(ptReservoirDesc);

    // Runtime CGNS stores four packed pixel coordinates per reservoir. B2 keeps
    // that algorithm disabled; reserve its real ABI so later B3 activation is explicit.
    nvrhi::BufferDesc ptNeighborDesc;
    ptNeighborDesc.byteSize = sizeof(uint32_t) * ptPitch * 4;
    ptNeighborDesc.initialState = nvrhi::ResourceStates::UnorderedAccess;
    ptNeighborDesc.keepInitialState = true;
    ptNeighborDesc.canHaveUAVs = true;
    ptNeighborDesc.canHaveRawViews = true;
    ptNeighborDesc.debugName = "PTSpatialNeighborSelectionBuffer";
    PTSpatialNeighborSelectionBuffer = device->createBuffer(ptNeighborDesc);

    nvrhi::TextureDesc localLightPdfDesc;
    rtxdi::ComputePdfTextureSize(maxLocalLights, localLightPdfDesc.width, localLightPdfDesc.height, localLightPdfDesc.mipLevels);
    assert(localLightPdfDesc.width * localLightPdfDesc.height >= maxLocalLights);
    localLightPdfDesc.isUAV = true;
    localLightPdfDesc.debugName = "LocalLightPdf";
    localLightPdfDesc.initialState = nvrhi::ResourceStates::ShaderResource;
    localLightPdfDesc.keepInitialState = true;
    localLightPdfDesc.format = nvrhi::Format::R32_FLOAT; // Use FP32 here to allow a wide range of flux values, esp. when downsampled.
    LocalLightPdfTexture = device->createTexture(localLightPdfDesc);
}

void RtxdiResources::InitializeNeighborOffsets(nvrhi::ICommandList* commandList, uint32_t neighborOffsetCount)
{
    if (m_NeighborOffsetsInitialized)
        return;

    std::vector<uint8_t> offsets;
    offsets.resize(neighborOffsetCount * 2); 

    rtxdi::FillNeighborOffsetBuffer(offsets.data(), neighborOffsetCount);

    commandList->writeBuffer(NeighborOffsetsBuffer, offsets.data(), offsets.size());

    m_NeighborOffsetsInitialized = true;
}
