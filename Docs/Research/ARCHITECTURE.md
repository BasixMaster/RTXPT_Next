# Architecture and exact baseline pins

Current project labels follow [canonical B0–B10](VERSION_MAPPING.md). B0 keeps original RTXPT1.9 defaults/pins; legacy migration tag `B1` / source7010bb4 is not canonical B1. Runtime3.1 native/DI/DI+GI configurations map to B3/B4/B5. The app-owned PT foundation maps to B6/B7; B8 sharing and B9/B10 additions require explicit valid contribution ownership.

## Repository structure

| Path / ref | Revision | Role |
|---|---|---|
| Root RTXPT v.1.9.0 | `303b408ab81790a5051abd7573830b7a4112eb8e` | Initial renderer source baseline |
| `Assets` | `a56be4ed65029d2733fd02f00f4027ffd541eda8` | Original pinned scenes, models, textures and supporting assets |
| B0 `External/Rtxdi` | `a14e079c727ed8c4fd3173bd2aea8244c9d9f6d6` | Immutable baseline runtime3.0 |
| Legacy migration root / retained tag `B1` | `7010bb4cda80788eb13cd9ee6143eb2f52a5b6ee` | Runtime/API migration only; canonical B3/B4/B5 depend on selected native/DI/GI modes |
| Migrated `External/Rtxdi` | `f12037fa8e97ebc08e9e3edfd2de528ed1772a4b` | Runtime3.1 used by migrated configurations and subsequent PT integration |
| `External/RTXDI-SDK` | `a6efab966b7c3b272da0461578eb56ac61c7cbff` | Linked SDK3.1 source reference, not a baseline build input |
| SDK3.1's `Libraries/Rtxdi` | `f12037fa8e97ebc08e9e3edfd2de528ed1772a4b` | Reference uses the same runtime revision as the retained migration source |
| `baseline/rtxpt-1.9`, `rtxpt-1.9-baseline` | `303b408ab81790a5051abd7573830b7a4112eb8e` | Immutable source identity for comparisons |

`Docs/Research` and `Benchmarks` contain planning/evidence. The retained legacy migration source preserves original renderer shaders/CMake and changes four host/UI compatibility files plus the runtime pin. Later app-owned PT bridge/passes are separate changes, described in the [legacy integration history](B2_IMPLEMENTATION.md). The linked SDK is reference-only, not an active build component. The [legacy migration report](B1_RESULTS.md) maps historical DI+GI observations to canonical B2/B5.

## Current renderer surfaces

| Path from repository root | Existing role / future extension surface |
|---|---|
| `Docs/Design.md` | Unified forward PT, NEE-AT, SHaRC, PSR/decomposition, sparse rendering and async reconstruction |
| `Rtxpt/RTXDI/RtxdiPass.cpp`, `RtxdiResources.cpp` | DI/GI host bindings and separately integrated PT resources/passes; runtime migration is distinct from PT activation |
| `Rtxpt/RTXDI/RtxdiApplicationBridge.hlsli`, `Rtxpt/RTXDI/PT/` | App-owned scene callbacks, PT initial/replay/temporal/spatial/final bridge and ownership contracts |
| `Rtxpt/Shaders/PathTracerBridge.hlsli`, `PathTracerBridgeDonut.hlsli` | Scene/ray/material boundary |
| `Rtxpt/Shaders/PathTracer/`, `PathTracerSample.hlsl` | Candidate generation and unified tracing |
| `Rtxpt/Sample.cpp`, `AdvancedSample.cpp` | Scheduling, shader permutations, guide/reset/resource lifetime |
| `Rtxpt/SampleCommon/ExtendedScene.cpp` | Scene, light and material extensions |
| `Testing/` | Existing capture/regression controls; see benchmark protocol for limitations |

RTXPT's existing DI/GI passes do not by themselves establish a ReSTIR PT integration. NEE-AT/SHaRC are important baseline features, and replacing their behavior changes the experiment. RTXPT's path-space denoising layers differ from multi-layer reservoir-splat domains; its light-cluster LoD differs from geometry LoD.

## RTXDI3.1 reference surfaces and app integration

The PT++ audit uses paths relative to `External/RTXDI-SDK`, not the root RTXPT renderer. Its `Libraries/Rtxdi/Include/Rtxdi/PT` contains reservoir, initial-generation, hybrid-shift, temporal/spatial, neighbor-selection, duplication and decorrelation code. `Libraries/Rtxdi/Source/ReSTIRPT.cpp` owns host defaults/state. `Samples/FullSample/Source/RenderPasses/LightingPasses/ReSTIRPTRenderPasses.cpp` supplies the reference pass schedule, while FullSample's application bridge supplies material/light/path callbacks. Those callbacks are renderer-specific and cannot be copied without adapting the contracts.

3.1 changes naming/layouts and supplies preserved initial samples, decorrelation and CGNS interfaces. The historical reference inspection found a PT spatial path tied to `g_Const.restirPT.spatialResampling.numSpatialSamples`; app integration must satisfy that contract. The legacy migration source alone did not add a PT adapter. Subsequent B6/B7 bridge/passes are app-owned integration and have scoped opaque evidence; merely linking SDK source still does not activate its other optional passes.

## Dependency ownership and state contracts

Any later edit inside runtime or SDK/renderer submodules requires a reachable owned child commit and updated gitlink, or an explicitly reviewed tracked-vendor strategy. This pass creates no guessed child fork. Keep upstream originals reachable.

Every new estimator declares sample domain, target, PDF measure, Jacobian, confidence, replay RNG/model version, immutable pass inputs and output ownership. Handle camera cuts, resize, geometry/material/light identity changes and mode switches. Guiding models and geometry LoD mappings must stay consistent with reused samples. Define bounded queue/cell/domain overflow and canonical fallback semantics before implementation.

## Canonical configuration and history boundaries

Canonical B6 has PT with separate DI/GI off; B7 adds DI3.1 with GI off. Planned B8 needs valid GI/PT sharing; B9/B10 cannot inherit that foundation until it is implemented and validated. The old-B3 GI-off limited pilot is a B7 ablation, not B9. Preserve legacy refs and measurements through the [crosswalk](VERSION_MAPPING.md); historical original-scene DI+GI rows map to B2/B5 and have unverified external-cap coverage. Future comparisons record actual algorithms, explicit cap receipts and original-scene gaps.
