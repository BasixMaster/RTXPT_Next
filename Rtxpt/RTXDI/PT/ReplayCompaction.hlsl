/* SPDX-License-Identifier: LicenseRef-NvidiaProprietary
 * Application-owned scheduling prototype; same estimator as paired pilot. */
#pragma pack_matrix(row_major)
#define RTXDI_RESTIR_PT_HYBRID_SHIFT
#include "Bridge.hlsli"
#include "Runtime/HybridShiftGuard.hlsli"
#include <Rtxdi/PT/SpatialResampling.hlsli>
#if RTXPT_QUEUE_PHASE == 7
#define RTXPT_SUPPRESS_PAIR_DIAGNOSTICS
#endif
#include "Runtime/PairedSpatialPilot.hlsli"

RTXDI_PTSpatialResamplingRuntimeParameters QueueParams()
{
    RTXDI_PTSpatialResamplingRuntimeParameters p = RTXDI_EmptyPTSpatialResamplingRuntimeParameters();
    p.viewportSize = uint2(g_Const.ptConsts.imageWidth,g_Const.ptConsts.imageHeight);
    p.cameraPos = g_RtxdiBridgeConst.ptCameraPosition;
    p.prevCameraPos = g_RtxdiBridgeConst.ptPreviousCameraPosition;
    p.prevPrevCameraPos = g_RtxdiBridgeConst.ptPreviousPreviousCameraPosition;
    return p;
}

bool QueueSource(uint2 pixel, out uint2 partner, out RAB_Surface a, out RAB_Surface b, out RTXDI_PTReservoir source)
{
    partner=RTXPT_PairPartner(pixel);
    a=RAB_GetGBufferSurface(pixel,false); b=a;
    source=RTXDI_EmptyPTReservoir();
    uint2 dims=uint2(g_Const.ptConsts.imageWidth,g_Const.ptConsts.imageHeight);
    if (any(partner>=dims)) return false;
    if (any(RTXPT_PairPartner(partner)!=pixel)) return false;
    b=RAB_GetGBufferSurface(partner,false);
    RTXDI_PTSpatialResamplingParameters spatial=g_RtxdiBridgeConst.restirPT.spatialResampling;
    if (!IsValidNeighborSurface(spatial,a,b) || !IsValidNeighborSurface(spatial,b,a)) return false;
    source=RTXDI_LoadPTReservoir(g_RtxdiBridgeConst.restirPT.reservoirBuffer,
        RTXDI_PixelPosToReservoirPos(pixel,g_RtxdiBridgeConst.runtimeParams.activeCheckerboardField),
        g_RtxdiBridgeConst.restirPT.bufferIndices.spatialResamplingInputBufferIndex);
    return true;
}

#if RTXPT_QUEUE_PHASE == 1
[numthreads(8,8,1)]
void main(uint2 pixel:SV_DispatchThreadID)
{
    uint2 dims=uint2(g_Const.ptConsts.imageWidth,g_Const.ptConsts.imageHeight);
    if (any(pixel>=dims)) return;
    uint index=pixel.y*dims.x+pixel.x;
    if(index==0 && g_RtxdiBridgeConst.ptDiagnostics!=0)
    {
        uint elements,stride; u_PTShiftCache.GetDimensions(elements,stride);
        u_PTDiagnosticCounters[54]=stride; u_PTDiagnosticCounters[55]=elements;
    }
    uint2 partner; RAB_Surface a,b; RTXDI_PTReservoir source;
    u_PTShiftCache[index]=(RTXPT_PairShift)0;
    if (!QueueSource(pixel,partner,a,b,source)) return;
    // Zero-weight samples still carry M into pair resampling. Preserve the
    // complete early-return result instead of replacing it by an empty sample.
    RTXPT_PairShift unchanged=(RTXPT_PairShift)0;
    unchanged.sample=source;
    u_PTShiftCache[index]=unchanged;
    if (source.M<=0 || source.weightSum<=0) return;
    if (NeedToRunRandomReplayPathTracer(source))
    {
        uint slot; u_PTReplayControl.InterlockedAdd(0,1,slot);
        if (slot<dims.x*dims.y) u_PTReplayQueue[slot]=index;
        else
        {
            // Capacity N follows from one request per source pixel. Preserve
            // the work even on an unexpected overflow, and fail diagnostics.
            InterlockedAdd(u_PTDiagnosticCounters[48],1);
            InterlockedOr(u_PTDiagnosticCounters[95],1);
            u_PTShiftCache[index]=RTXPT_PairShiftTo(source,a,b,partner,QueueParams());
        }
    }
    else
    {
        if(g_RtxdiBridgeConst.ptDiagnostics!=0) InterlockedAdd(u_PTDiagnosticCounters[49],1);
        u_PTShiftCache[index]=RTXPT_PairShiftTo(source,a,b,partner,QueueParams());
    }
}
#elif RTXPT_QUEUE_PHASE == 2
[numthreads(8,8,1)]
void main(uint2 pixel:SV_DispatchThreadID)
{
    if(any(pixel!=0)) return;
    uint count=min(u_PTReplayControl.Load(0),g_Const.ptConsts.imageWidth*g_Const.ptConsts.imageHeight);
    uint groups=(count+63)/64;
    u_PTReplayControl.Store(4,min(groups,65535u));
    u_PTReplayArgs.Store3(0,uint3(min(groups,65535u),(groups+65534u)/65535u,1));
    if(g_RtxdiBridgeConst.ptDiagnostics!=0) InterlockedAdd(u_PTDiagnosticCounters[50],count);
}
#elif RTXPT_QUEUE_PHASE == 3
[numthreads(64,1,1)]
void main(uint3 group:SV_GroupID,uint lane:SV_GroupIndex)
{
    uint slot=(group.y*u_PTReplayControl.Load(4)+group.x)*64+lane;
    uint2 dims=uint2(g_Const.ptConsts.imageWidth,g_Const.ptConsts.imageHeight);
    if(slot>=min(u_PTReplayControl.Load(0),dims.x*dims.y)) return;
    uint index=u_PTReplayQueue[slot];
    uint2 pixel=uint2(index%dims.x,index/dims.x),partner;
    RAB_Surface a,b; RTXDI_PTReservoir source;
    if(QueueSource(pixel,partner,a,b,source))
        u_PTShiftCache[index]=RTXPT_PairShiftTo(source,a,b,partner,QueueParams());
}
#else
[numthreads(8,8,1)]
void main(uint2 pixel:SV_DispatchThreadID)
{
    uint2 dims=uint2(g_Const.ptConsts.imageWidth,g_Const.ptConsts.imageHeight);
    if(any(pixel>=dims)) return;
#if RTXPT_QUEUE_PHASE == 4
    RTXPT_RunPairedSpatialPilot(pixel,true);
#elif RTXPT_QUEUE_PHASE == 7
    RTXPT_RunPairedSpatialPilot(pixel,false);
#else
    // Oracle reads identical input/frame/RNG; compare every packed reservoir
    // word and every vector-radiance bit after the direct control executes.
    uint index=pixel.y*dims.x+pixel.x;
    uint2 pos=RTXDI_PixelPosToReservoirPos(pixel,g_RtxdiBridgeConst.runtimeParams.activeCheckerboardField);
    RTXDI_PackedPTReservoir packed=RTXDI_LoadPackedPTReservoir(g_RtxdiBridgeConst.restirPT.reservoirBuffer,pos,
        g_RtxdiBridgeConst.restirPT.bufferIndices.spatialResamplingOutputBufferIndex);
    uint words[16];
    words[0]=packed.Data0.x; words[1]=packed.Data0.y; words[2]=packed.Data0.z; words[3]=packed.Data0.w;
    words[4]=packed.Data1.x; words[5]=packed.Data1.y; words[6]=packed.Data1.z; words[7]=packed.Data1.w;
    words[8]=packed.Data2.x; words[9]=packed.Data2.y; words[10]=packed.Data2.z; words[11]=packed.Data2.w;
    words[12]=packed.Data3.x; words[13]=packed.Data3.y; words[14]=packed.Data3.z; words[15]=packed.Data3.w;
#if RTXPT_QUEUE_PHASE == 5
    for(uint i=0;i<16;++i) u_PTReplayOracle.Store(index*76+i*4,words[i]);
    u_PTReplayOracle.Store3(index*76+64,u_PTSpatialNeighbors.Load3(index*16));
#elif RTXPT_QUEUE_PHASE == 6
    bool different=false;
    for(uint i=0;i<16;++i)
    {
        uint saved=u_PTReplayOracle.Load(index*76+i*4);
        if(words[i]!=saved)
        {
            different=true; InterlockedAdd(u_PTDiagnosticCounters[56+i],1);
            uint prior; u_PTReplayControl.InterlockedCompareExchange(24,0,1,prior);
            if(prior==0)
            {
                u_PTDiagnosticCounters[72]=index; u_PTDiagnosticCounters[73]=i;
                u_PTDiagnosticCounters[74]=saved; u_PTDiagnosticCounters[75]=words[i];
                uint2 partner=RTXPT_PairPartner(pixel); uint partnerIndex=partner.y*dims.x+partner.x;
                RTXDI_PTReservoir ownIn=RTXDI_LoadPTReservoir(g_RtxdiBridgeConst.restirPT.reservoirBuffer,pos,g_RtxdiBridgeConst.restirPT.bufferIndices.spatialResamplingInputBufferIndex);
                RTXDI_PTReservoir otherIn=RTXDI_LoadPTReservoir(g_RtxdiBridgeConst.restirPT.reservoirBuffer,RTXDI_PixelPosToReservoirPos(partner,g_RtxdiBridgeConst.runtimeParams.activeCheckerboardField),g_RtxdiBridgeConst.restirPT.bufferIndices.spatialResamplingInputBufferIndex);
                uint3 cn=asuint(u_PTShiftCache[index].sample.worldNormal);
                uint3 pn=asuint(u_PTShiftCache[partnerIndex].sample.worldNormal);
                uint3 on=asuint(ownIn.worldNormal), bn=asuint(otherIn.worldNormal);
                u_PTDiagnosticCounters[76]=cn.x;u_PTDiagnosticCounters[77]=cn.y;u_PTDiagnosticCounters[78]=cn.z;
                u_PTDiagnosticCounters[79]=pn.x;u_PTDiagnosticCounters[80]=pn.y;u_PTDiagnosticCounters[81]=pn.z;
                u_PTDiagnosticCounters[82]=on.x;u_PTDiagnosticCounters[83]=on.y;u_PTDiagnosticCounters[84]=on.z;
                u_PTDiagnosticCounters[85]=bn.x;u_PTDiagnosticCounters[86]=bn.y;u_PTDiagnosticCounters[87]=bn.z;
                u_PTDiagnosticCounters[88]=ownIn.rcVertexLength;u_PTDiagnosticCounters[89]=otherIn.rcVertexLength;
                u_PTDiagnosticCounters[90]=asuint(ownIn.weightSum);u_PTDiagnosticCounters[91]=asuint(otherIn.weightSum);

            }
        }
    }
    InterlockedAdd(u_PTDiagnosticCounters[51],1);
    if(index==0) InterlockedAdd(u_PTDiagnosticCounters[92],1);
    if(different)
    {
        InterlockedAdd(u_PTDiagnosticCounters[52],1);
        InterlockedOr(u_PTDiagnosticCounters[93],1);
    }
    if(any(u_PTSpatialNeighbors.Load3(index*16)!=u_PTReplayOracle.Load3(index*76+64)))
    {
        InterlockedAdd(u_PTDiagnosticCounters[53],1);
        InterlockedOr(u_PTDiagnosticCounters[94],1);
    }
    // The direct control is diagnostic only. Restore the exact queued words
    // and vector bits so the next frame follows the actual queue history.
    RTXDI_PackedPTReservoir queued;
    queued.Data0=u_PTReplayOracle.Load4(index*76);
    queued.Data1=u_PTReplayOracle.Load4(index*76+16);
    queued.Data2=u_PTReplayOracle.Load4(index*76+32);
    queued.Data3=u_PTReplayOracle.Load4(index*76+48);
    RTXDI_StorePackedPTReservoir(queued,g_RtxdiBridgeConst.restirPT.reservoirBuffer,pos,
        g_RtxdiBridgeConst.restirPT.bufferIndices.spatialResamplingOutputBufferIndex);
    u_PTSpatialNeighbors.Store3(index*16,u_PTReplayOracle.Load3(index*76+64));
#endif
#endif
}
#endif
