**Current project context (2026-10-29):** [Canonical B0–B10 and legacy crosswalk](VERSION_MAPPING.md) govern project labels. B0 preserves unchanged RTXPT1.9 original defaults and pins. Legacy migration `7010bb4` is not canonical B1; its native/DI/DI+GI configurations map to B3/B4/B5. The PT-only/DI+PT foundation maps to B6/B7; old-B2 checkpoint `de9fe651` is B7. The GI-off old-B3 pilot is a B7 limited-feature ablation, not B9. B8 requires valid GI/PT sharing; B9/B10 depend on it, and full remaining PT++ work belongs to B10. The SDK stays reference-only. Preserve legacy measurements/IDs; historical original-scene DI+GI rows map to B2/B5 with cap coverage unverified.

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

Our fork preserves unchanged RTXPT1.9 defaults/pins as B0. Legacy migration source7010bb4 updated `External/Rtxdi` to3.1 and the DI/GI host/UI APIs; actual native/DI/GI modes map to canonical B3/B4/B5. Later app-owned PT bridge/passes supply B6/B7 and scoped opaque evidence. The SDK stays a separate source reference: neither its link nor our app adapter executes FullSample wholesale or proves every optional SDK feature is active.

## Dependency alignment and remaining PT work

The legacy migration completed runtime/API alignment. Subsequent app-owned PT bridge/resources are implemented with scoped opaque validation and unresolved wider-scene gates. The following original checklist records the dependency responsibilities; it is not a claim that the separate FullSample SDK is built into RTXPT.

1. Benchmark RTXDI3.1 FullSample and RTXPT1.9 independently with exact original pins.
2. Choose runtime modification ownership (owned library fork or explicit vendor strategy).
3. Prepare a separately owned RTXPT integration branch or external build/adapter arrangement. Keep the upstream1.9 source tag reachable.
4. Reconcile3.0→3.1 identifiers, host/shader structs, callbacks, constant-buffer layouts and resource requirements; compile DI/GI controls before new PT wiring.
5. Validate the implemented PT app bridge/resources/scheduling across the required material, motion and diffuse-budget coverage before reconstruction/async claims.
6. After validation, make both consumers explicitly use the selected3.1 runtime revision. Preserve a baseline configuration for regression and upstream comparison.

Updating only a gitlink would skip integration work. The legacy migration included host/API renames and a successful build; the later PT adapter is a separately evidenced change. Keep SDK reference code separate, inherited mechanisms explicit and further B8–B10 sharing/feature work behind correctness gates.

Sources: [RTXDI3.1 .gitmodules](https://github.com/NVIDIA-RTX/RTXDI/blob/a6efab966b7c3b272da0461578eb56ac61c7cbff/.gitmodules), [RTXPT1.9 .gitmodules](https://github.com/NVIDIA-RTX/RTXPT/blob/303b408ab81790a5051abd7573830b7a4112eb8e/.gitmodules), [RTXPT design](https://github.com/NVIDIA-RTX/RTXPT/blob/303b408ab81790a5051abd7573830b7a4112eb8e/Docs/Design.md), [3.1 migration notes](https://github.com/NVIDIA-RTX/RTXDI/blob/a6efab966b7c3b272da0461578eb56ac61c7cbff/ChangeLog.md).

## Summary and lessons learned

RTXDI supplies sampling machinery and RTXPT supplies the renderer. Shared foundations do not remove estimator/material/history/ABI responsibilities. The legacy migration, app-owned B6/B7 PT foundation and planned B8–B10 sharing/features are distinct evidence scopes. Source presence and paper-reported gains do not establish local activation or performance.
