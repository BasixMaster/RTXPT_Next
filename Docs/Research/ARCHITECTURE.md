# Architecture and exact baseline pins

## Repository structure

| Path / ref | Revision | Role |
|---|---|---|
| Root RTXPT v.1.9.0 | `303b408ab81790a5051abd7573830b7a4112eb8e` | Initial renderer source baseline |
| `Assets` | `a56be4ed65029d2733fd02f00f4027ffd541eda8` | Original pinned scenes, models, textures and supporting assets |
| `External/Rtxdi` | `a14e079c727ed8c4fd3173bd2aea8244c9d9f6d6` | Baseline runtime3.0; untouched |
| `External/RTXDI-SDK` | `a6efab966b7c3b272da0461578eb56ac61c7cbff` | Linked SDK3.1 source reference, not a baseline build input |
| SDK3.1's `Libraries/Rtxdi` | `f12037fa8e97ebc08e9e3edfd2de528ed1772a4b` | Proposed B1 runtime target |
| `baseline/rtxpt-1.9`, `rtxpt-1.9-baseline` | `303b408ab81790a5051abd7573830b7a4112eb8e` | Immutable source identity for comparisons |

`Docs/Research` and `Benchmarks` contain planning/evidence. Original renderer shaders, CMake build and RTXDI runtime pin remain identical to RTXPT1.9. The linked SDK is reference-only; no add_subdirectory or dependency override makes it an active renderer component.

## Current renderer surfaces

| Path from repository root | Existing role / future extension surface |
|---|---|
| `Docs/Design.md` | Unified forward PT, NEE-AT, SHaRC, PSR/decomposition, sparse rendering and async reconstruction |
| `Rtxpt/RTXDI/RtxdiPass.cpp`, `RtxdiResources.cpp` | DI/GI host bindings and resources; B1 API/layout alignment first, PT resources separately |
| `Rtxpt/RTXDI/RtxdiApplicationBridge.hlsli` | Existing application callbacks; PT requires replay/context and MIS contracts |
| `Rtxpt/Shaders/PathTracerBridge.hlsli`, `PathTracerBridgeDonut.hlsli` | Scene/ray/material boundary |
| `Rtxpt/Shaders/PathTracer/`, `PathTracerSample.hlsl` | Candidate generation and unified tracing |
| `Rtxpt/Sample.cpp`, `AdvancedSample.cpp` | Scheduling, shader permutations, guide/reset/resource lifetime |
| `Rtxpt/SampleCommon/ExtendedScene.cpp` | Scene, light and material extensions |
| `Testing/` | Existing capture/regression controls; see benchmark protocol for limitations |

RTXPT's existing DI/GI passes do not by themselves establish a ReSTIR PT integration. NEE-AT/SHaRC are important baseline features, and replacing their behavior changes the experiment. RTXPT's path-space denoising layers differ from multi-layer reservoir-splat domains; its light-cluster LoD differs from geometry LoD.

## RTXDI3.1 reference surfaces for B1/B2

The PT++ audit uses paths relative to `External/RTXDI-SDK`, not the root RTXPT renderer. Its `Libraries/Rtxdi/Include/Rtxdi/PT` contains reservoir, initial-generation, hybrid-shift, temporal/spatial, neighbor-selection, duplication and decorrelation code. `Libraries/Rtxdi/Source/ReSTIRPT.cpp` owns host defaults/state. `Samples/FullSample/Source/RenderPasses/LightingPasses/ReSTIRPTRenderPasses.cpp` supplies the reference pass schedule, while FullSample's application bridge supplies material/light/path callbacks. Those callbacks are renderer-specific and cannot be copied without adapting the contracts.

3.1 changes naming and host/shader struct layouts, adds decorrelation/preserved initial samples and CGNS resources. One inspected3.1 spatial path references `g_Const.restirPT.spatialResampling.numSpatialSamples`; the B1 renderer must bind or parameterize this expectation. Never assume a runtime gitlink bump is a completed adapter.

## Dependency ownership and state contracts

Any later edit inside runtime or SDK/renderer submodules requires a reachable owned child commit and updated gitlink, or an explicitly reviewed tracked-vendor strategy. This pass creates no guessed child fork. Keep upstream originals reachable.

Every new estimator declares sample domain, target, PDF measure, Jacobian, confidence, replay RNG/model version, immutable pass inputs and output ownership. Handle camera cuts, resize, geometry/material/light identity changes and mode switches. Guiding models and geometry LoD mappings must stay consistent with reused samples. Define bounded queue/cell/domain overflow and canonical fallback semantics before implementation.
