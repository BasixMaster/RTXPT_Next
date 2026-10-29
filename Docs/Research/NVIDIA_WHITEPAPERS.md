# NVIDIA engineering whitepapers: implications for RTXPT Next

Added 2026-10-28 from the [official repository](https://github.com/NVIDIA-RTX/Whitepapers/blob/20463fd355c817a50381343d9d12b7ac811d2e39/README.md), pinned at `20463fd355c817a50381343d9d12b7ac811d2e39`. These are vendor engineering guides, separate from the Wyman paper catalog and our measured B7 results. Full Markdown was retrieved; the performance sections listed below and the geometry guide's text were reviewed. Figures and linked samples/specifications were not independently audited.

Project labels updated 2026-10-29 under [canonical B0–B10](VERSION_MAPPING.md); source pin, inspection date and vendor claims are unchanged. Retained B2_RESULTS.md is the legacy filename for B7 evidence. Full remaining PT++ work is B10, dependent on valid B8 sharing; the GI-off limited pilot is not B9.

## Priority map

| Priority | Source and inspected sections | Application to this project | Acceptance gate |
|---|---|---|---|
| Now | [Real-Time Path Tracing in Games](https://github.com/NVIDIA-RTX/Whitepapers/blob/20463fd355c817a50381343d9d12b7ac811d2e39/pt_performance_whitepaper/README.md), §§1,3,11–14 | Add per-signal ray budgets, AS/dispatch/cache/reconstruction timings and shader/memory diagnostics around the corrected B7 estimator | Real pass/hardware measurements; existing GPUBusy is not a complete GPU critical-path profile |
| After B7 coverage | Same guide, SER/OMM and TraceRay/RayQuery sections | Compare the native RTXPT and new PT bridge's traversal/material execution choices; profile divergence and any-hit cost before choosing an optimization | Representative glossy/alpha-heavy/dynamic scenes, feature capability queries, fallback and equal-quality tests |
| Later geometry branch | [Clustered Geometry and Partitioned TLAS](https://github.com/NVIDIA-RTX/Whitepapers/blob/20463fd355c817a50381343d9d12b7ac811d2e39/dx_clusters_and_ptlas/README.md) | Investigate GPU-driven AS work for dense instancing, animated topology reuse and geometry LoD workloads | Separate toolchain/driver capability gate; preserve conventional BLAS/TLAS fallback and stable reservoir geometry identity |

## Path-tracing performance guide

The June 2026 guide budgets work separately for direct visibility, diffuse transport, glossy response and cache updates. It requests native/output resolution, path/termination policy, AS build/update cost, tracing, reconstruction, memory and temporal stability per platform/preset. That supports extending our existing measurement protocol; it does not convert our 640×360 opaque-room timing into a shipping-performance result.

Its traversal guidance is workload-dependent. Inline RayQuery is a good candidate for lightweight visibility, while substantial inline material evaluation can increase divergence and register pressure. TraceRay supports hit groups and material dispatch. A mixed design is an experiment to profile, not a promised speedup. Our B7 bridge currently uses RayQuery; whether it has a material/register bottleneck remains an unmeasured hypothesis.

SER needs capability checks and measured coherence-hint choices. OMM should target demonstrated any-hit cost. The guide also discusses forcing opacity in performance-oriented approximations: that changes transport and must remain outside strict B7 correctness comparisons. Similarly, ray/material LoD, cache termination and low-contribution pruning require their own quality/reference contract. Already-shipped RTXPT features must be audited before they are counted as new work.

For precision, the guide emphasizes footprint, bandwidth and register-pressure benefits rather than assuming FP16 automatically improves scalar ALU throughput. Keep our raw-HDR finite/range checks and measure conversions and occupancy before changing reservoir or material formats.

The reviewed case studies use other configurations, including an RTX 5090/1920×1080 SHaRC/SER example. Their numbers are source-reported, not local RTX 4090/B7 gains. They justify profiling questions, not transferable speedup ratios.

## Clustered geometry and PTLAS

The October 28 guide describes three distinct tools: CLAS groups spatially organized triangles; cluster templates reuse topology-dependent build work; PTLAS updates changed instance partitions rather than rebuilding an entire large top-level structure. These address AS construction and scene-scale organization. They do not implement ReSTIR-LoD's estimator mappings, area Jacobians or reservoir weighting.

The guide identifies DirectX Agility SDK **1.722.0-preview**, HLSL **6.10**, and NVIDIA driver **621.01** as its documented launch stack, with support reported for all RTX GPUs. Our benchmark driver remains **617.42**; this is not the documented deployment stack. No driver, SDK or API upgrade was performed. Query actual runtime feature support and use a separate experimental backend before claiming this path runs on our RTX 4090 setup.

The forest example is described as upcoming in the inspected guide. Its scale and demonstrations are source claims, not locally reproduced performance. No linked game/forest images are copied into our docs.

A geometry branch must preserve instance/primitive identity, update versioning, inverse-shift assumptions and history invalidation across cluster and LoD changes. Acceleration-structure optimization can complement ReSTIR LoD, but cannot replace those sampling contracts. Measure AS build/update, traversal, CPU synchronization, memory and complete-frame cost separately.

## Concrete roadmap additions

1. Extend the B7 profiler with separate DI/PT ray/visibility counts, path-depth and termination diagnostics, per-pass GPU timings and allocated-resource accounting. Keep instrumentation out of accepted throughput captures.
2. Add alpha-heavy, glossy, dynamic-light and camera-motion scenes after material/medium gates pass. Compare raw and reconstructed tracks with frozen references and histories.
3. Profile RayQuery/TraceRay and SER/OMM alternatives as isolated later ablations. Preserve fallback semantics, capability receipts and known bias controls.
4. Open a later CLAS/PTLAS design branch only when scene-scale profiling identifies AS work as consequential and the documented driver/SDK prerequisites are available. Keep B7/B10 estimator steps independently measurable.

## Attribution and reuse scope

NVIDIA Corporation and affiliates, 2026. Both folders publish their own CC BY 4.0 license. The [geometry license](https://github.com/NVIDIA-RTX/Whitepapers/blob/20463fd355c817a50381343d9d12b7ac811d2e39/dx_clusters_and_ptlas/LICENSE) explicitly excludes specified Microsoft/Gears of War and Remedy/CONTROL images from its blanket attribution license; [performance-guide terms](https://github.com/NVIDIA-RTX/Whitepapers/blob/20463fd355c817a50381343d9d12b7ac811d2e39/pt_performance_whitepaper/LICENSE) are separate. This chapter contains original summaries and project-specific proposals, with source links and changed context; no source images or sample code were copied. Those text licenses do not relicense RTX SDK code, drivers, games or sample assets.

## Summary and lessons learned

Use the performance guide now to improve measurement and feature ablations around the corrected B7 path. Treat geometry APIs as a later capability-gated scalability project. Neither source establishes our performance, makes optional approximations unbiased or removes the remaining material/motion validation gates. See [current B7 results](B2_RESULTS.md) and the [roadmap](ROADMAP.md).
