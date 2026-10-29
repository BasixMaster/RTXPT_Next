/* Application-owned tiled reciprocal-table lookup and frame isometries.
 * SPDX-License-Identifier: LicenseRef-NvidiaProprietary */
#ifndef RTXPT_PAIRING_LOOKUP_HLSLI
#define RTXPT_PAIRING_LOOKUP_HLSLI
uint RTXPT_PairHash(uint x)
{
    x ^= x>>16; x *= 0x7feb352du; x ^= x>>15; x *= 0x846ca68bu; return x^(x>>16);
}
int2 RTXPT_PairRotate(int2 p, uint r)
{
    if (r==1) return int2(-p.y,p.x);
    if (r==2) return -p;
    if (r==3) return int2(p.y,-p.x);
    return p;
}
int2 RTXPT_GaussianPartner(uint2 pixel)
{
    uint frame=g_RtxdiBridgeConst.runtimeParams.frameIndex;
    uint table=frame%3;
    int size=table==0 ? 254 : (table==1 ? 230 : 210);
    uint base=table==0 ? 0 : (table==1 ? 254*254 : 254*254+230*230);
    uint state=RTXPT_PairHash(frame ^ 0x50414952u);
    int2 offset=int2(state%uint(size),RTXPT_PairHash(state)%uint(size));
    int2 p=int2(pixel);
    if ((state&4u)!=0) p.x=-p.x;
    p=RTXPT_PairRotate(p,state&3u)+offset;
    int2 cell=((p%size)+size)%size;
    int2 delta=t_PTPairingOffsets[base+uint(cell.y*size+cell.x)];
    p=RTXPT_PairRotate(p+delta-offset,(4u-(state&3u))&3u);
    if ((state&4u)!=0) p.x=-p.x;
    return p;
}
#endif
