/* SPDX-License-Identifier: LicenseRef-NvidiaProprietary
 * Native RTXPT transport state exported for the ReSTIR PT application bridge.
 * See the NVIDIA RTX SDK license retained at the repository root. */
#ifndef RTXPT_PT_PRIMARY_DATA_H
#define RTXPT_PT_PRIMARY_DATA_H

// One element per GenericTS address, with the same two current/history planes
// as SurfaceData. This is NOT the packed 64-byte RTXDI path reservoir ABI.
struct RTXPTPTPrimaryData
{
#ifdef __cplusplus
    using uint = unsigned int;
    using float3 = float[3];
#endif
    uint materialID;
    uint interiorSlots[2];
    uint packedCounters;

    float rayConeWidth;
    float rayConeSpread;
    uint nativeVertexIndex; // Low 31 bits: vertex; high bit: authoritative PT ownership.
    uint flags;

    float3 prefixThroughput;
    uint frameIndex;
};
#ifndef __cplusplus
static const uint RTXPT_PT_PRIMARY_ELIGIBLE = 0x80000000u;
uint RTXPT_PTPrimaryVertex(RTXPTPTPrimaryData state) { return state.nativeVertexIndex & 0x7fffffffu; }
bool RTXPT_PTOwnsPrimary(RTXPTPTPrimaryData state, uint frameIndex)
{
    return (state.nativeVertexIndex & RTXPT_PT_PRIMARY_ELIGIBLE) != 0 && state.frameIndex == frameIndex;
}
#endif
#ifdef __cplusplus
static_assert(sizeof(unsigned int) == 4, "PT transport requires 32-bit unsigned integers");
static_assert(sizeof(RTXPTPTPrimaryData) == 48, "PT primary transport ABI must be 48 bytes");
#endif
#endif
