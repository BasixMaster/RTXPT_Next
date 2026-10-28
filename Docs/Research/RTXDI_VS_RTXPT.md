**Current project context (2026-10-28):** RTXPT1.9 with its original scenes is the immutable B0 baseline. B1 at `7010bb4cda80788eb13cd9ee6143eb2f52a5b6ee` applies the RTXDI3.1 runtime/API migration to the existing DI/GI path. It does not add a ReSTIR PT renderer or activate PT++/CGNS features. `External/RTXDI-SDK` remains reference-only. See [B1 results](B1_RESULTS.md) for measured scope and limitations. B2+ remain planned.

# RTXDI versus RTXPT: dependency and renderer comparison

## Direct answer

RTXPT1.9 depends on RTXDI-Library, the reusable runtime; it does not depend on the whole RTXDI SDK/sample repository. NVIDIA's upstream RTXDI3.1 does not depend on RTXPT. The new `External/RTXDI-SDK` link is a deliberate reference addition in this fork.

| Dimension | RTXDI3.1 | RTXPT1.9 |
|---|---|---|
| Role | Reservoir sampling SDK plus sample applications | Complete path-tracing renderer/sample and integration reference |
| Algorithms | ReSTIR DI/GI/PT, ReGIR and related sampling utilities | Unified forward path tracer, NEE-AT, SHaRC, materials, PSR/path decomposition, reconstruction and optional ReSTIR DI/GI |
| Runtime dependency | `Libraries/Rtxdi` → RTXDI-Library atf12037f | `External/Rtxdi` → RTXDI-Library ata14e079 (3.0) |
| Application framework | Donut in samples | Donut |
| Default real-time emphasis | FullSample demonstrates configurable ReSTIR algorithms | Design.md describes NEE-AT + SHaRC, with ReSTIR DI/GI primarily a fallback when DLSS-RR is unavailable |
| Scene responsibility | Runtime asks the application for scene/material/light callbacks; FullSample supplies an implementation | Renderer owns scene loading, material model, path tracing and reconstruction integration |
| ReSTIR PT integration | Exists in FullSample and runtime | Its pinned dependency contains PT code, but inspected RTXPT passes do not establish a ReSTIR PT renderer integration |

## Upstream graph and our fork

Upstream: `RTXDI SDK3.1 → RTXDI-Library3.1`; independently `RTXPT1.9 → RTXDI-Library3.0`. Both use common SDK/framework dependencies such as Donut and NRD, at their own pins. Sharing repository URLs is not the same as using the same revision or ABI.

Our fork preserves exact RTXPT1.9 as B0. B1 updates `External/Rtxdi` to3.1 and adapts the existing DI/GI host/UI APIs; `External/RTXDI-SDK` stays a separate source reference pinned to3.1. This does not execute the reference FullSample or activate its ReSTIR PT integration. A library appearing in a submodule graph does not prove every optional algorithm is executed.

## Dependency alignment and remaining PT work

B1 completed the runtime/API portion below for existing DI/GI. PT-specific bridge/resource work remains proposed, and the separate FullSample SDK is not built into RTXPT.

1. Benchmark RTXDI3.1 FullSample and RTXPT1.9 independently with exact original pins.
2. Choose runtime modification ownership (owned library fork or explicit vendor strategy).
3. Prepare a separately owned RTXPT integration branch or external build/adapter arrangement. Keep the upstream1.9 source tag reachable.
4. Reconcile3.0→3.1 identifiers, host/shader structs, callbacks, constant-buffer layouts and resource requirements; compile DI/GI controls before new PT wiring.
5. Add the PT application bridge/pass resources/scheduling and verify raw transport before reconstruction and async modes.
6. After validation, make both consumers explicitly use the selected3.1 runtime revision. Preserve a baseline configuration for regression and upstream comparison.

Updating only the nested gitlink would skip required integration work. B1 includes the required DI/GI host/API renames and a successful build. Keep the3.1 SDK reference separate; adding its PT pipeline remains a future integration task.

Sources: [RTXDI3.1 .gitmodules](https://github.com/NVIDIA-RTX/RTXDI/blob/a6efab966b7c3b272da0461578eb56ac61c7cbff/.gitmodules), [RTXPT1.9 .gitmodules](https://github.com/NVIDIA-RTX/RTXPT/blob/303b408ab81790a5051abd7573830b7a4112eb8e/.gitmodules), [RTXPT design](https://github.com/NVIDIA-RTX/RTXPT/blob/303b408ab81790a5051abd7573830b7a4112eb8e/Docs/Design.md), [3.1 migration notes](https://github.com/NVIDIA-RTX/RTXDI/blob/a6efab966b7c3b272da0461578eb56ac61c7cbff/ChangeLog.md).

## Summary and lessons learned

RTXDI supplies reusable sampling machinery; RTXPT supplies a renderer that can consume it. Their common foundations reduce adapter work but do not remove estimator, material, history or ABI responsibilities. B1 aligns the existing DI/GI consumer with runtime3.1; PT reference capabilities still require an explicit renderer integration. First local migration results are separate from paper-reported gains.
