# Canonical B1/B4: native PT with DI on

**Measured 2026-10-29.** Both native controls activate ReSTIR DI with GI and ReSTIR PT off. Twelve quality captures cover the original Convergence and Kitchen scenes. No new throughput result is accepted: two PresentMon attempts produced no CSV and were excluded. Temporary NVIDIA profiles were restored and verified.

| Scene | Configuration | Median LDR-FLIP ↓ | Three-process range |
|---|---|---:|---|
| Convergence | B1: native PT + DI 3.0; GI off | 0.341609 | 0.341503–0.341815 |
| Convergence | B4: native PT + DI 3.1; GI off | 0.341623 | 0.341150–0.342512 |
| Kitchen | B1: native PT + DI 3.0; GI off | 0.386252 | 0.385524–0.386585 |
| Kitchen | B4: native PT + DI 3.1; GI off | 0.386295 | 0.385848–0.386644 |

The observed display-error differences are small across these process repeats. Three restarts are not independent Monte Carlo seeds and establish no statistical equivalence or speedup. The runtime migration retains the native rendering shaders; these results do not compare ReSTIR PT against native PT.

## Matched settings and provenance

Original scene files, materials and cameras are unchanged: Convergence `convergence-test.scene.json`, exposure0; Kitchen `kitchen-with-test-stuff.scene.json`, exposure2. Both use1280×720,1spp, total/diffuse limits14/2, AA/denoiser/cache/subsampling off, NEE on/type2 and original realtime approximate MIS. Quality snapshots use the original simple-capture history behavior. No per-candidate exposure/brightness normalization is applied.

| Variant | Base source | Runtime | Separate host-control adapter |
|---|---|---|---|
| B1 | `303b408` | RTXDI3.0 `a14e079` | `4e380f9f85dba35b86b6a3bbd97e7acdfb324dec` |
| B4 | `7010bb4` | RTXDI3.1 `f12037f` | `13d023fc6b8a7ff4ea6b6f5d5d7937bea4a86077` |

The controls-v2 adapters add benchmark controls and effective transport/build receipts. All164 original renderer shader-source hashes and dependency pins are preserved; protected original/legacy binaries remain unchanged. Frozen manifests validate source, executable and compiled-cache identity before and after accepted captures. Actual receipts show `di=1 gi=0 pt=0`,1280×720,1spp and14/2 limits. These adapters are separately identified from unchanged B0.

## Quality reference and limits

Official FLIP1.7 runs in LDR mode at67pixels/degree on encoded sRGB PNGs. The finite4096spp references and their hashes are reused from the retained original-scene reference dataset. Its2048-versus4096 reference discrepancies remain attached; they are approximately0.02761 Convergence and0.04723 Kitchen. Display RGB MSE/PSNR and display-luma SMAPE are retained in the metric JSON. These are display-space diagnostics, not linear-HDR error, HDR-FLIP or an unbiasedness proof. Original-shader native controls currently lack linear-HDR/explicit independent-seed export.

## Timing exclusions and coverage

The planned protocol uses three process repetitions/configuration/scene,45s warm-up and15s PresentMon, selecting the last600 target rows after dropping16. Two unchanged Convergence/B1 attempts exited PresentMon0 but produced no CSV, so no presentation timing or observed SyncInterval could be accepted. Known app/NVIDIA/RTSS settings were checked; this does not turn absent trace data into a verified timing result. Both temporary exact-executable driver profiles were restored; the user-owned RTSS profile was read only. Desktop screenshots were unavailable and LogonUI was observed, suggesting a locked display session; its causal role is unproven. Timing awaits an available interactive desktop.

| Mandatory scene | Quality | Throughput / remaining gate |
|---|---|---|
| Original Convergence | B1/B4,3process captures each | No accepted new trace; retry with available display session |
| Original Kitchen | B1/B4,3process captures each | Pending same repeated timing protocol |
| Owned opaque room | Pending matched DI captures | Separate registered zero-intensity environment fixture needed for original native controls |

Equal-time/error convergence sweeps, temporal behavior, reconstructed output and renderer-exclusive memory remain pending. Historical DI+GI timings retain their unverified-cap scope and are not pooled with this DI-only quality experiment.

## Inspect captures

Click a capture to enlarge it; Escape closes the shared preview.

| Scene | B1: PT + DI3.0 | B4: PT + DI3.1 |
|---|---|---|
| Convergence | [![convergence B1](assets/canonical-native-di/convergence-B1.png)](assets/canonical-native-di/convergence-B1.png) | [![convergence B4](assets/canonical-native-di/convergence-B4.png)](assets/canonical-native-di/convergence-B4.png) |
| Kitchen | [![kitchen B1](assets/canonical-native-di/kitchen-B1.png)](assets/canonical-native-di/kitchen-B1.png) | [![kitchen B4](assets/canonical-native-di/kitchen-B4.png)](assets/canonical-native-di/kitchen-B4.png) |

Public-safe source/build/capture/metric identities are retained in `Benchmarks/development/2026-10-29-canonical-native-di`. [Canonical numbering and legacy mapping](VERSION_MAPPING.md) defines all B0–B10 variants.

## Summary and lessons learned

Actual first-frame receipts now distinguish the missing DI-on native controls from older DI-off measurements. Preserve quality evidence independently of missing throughput evidence; an internal partial PT log cannot replace a complete presentation trace.

GUI input hardening and version-neutral labels were rebuilt and passed a separate finite-HDR/counter smoke on the existing B7 limited-ablation path. That smoke is not a new B9/B10 implementation or performance result; its retained receipt is `Benchmarks/development/2026-10-29-canonical-gui-smoke`.
