# B10 unified lighting: paper correspondence and estimator gates

## Summary and lessons learned

The remaining unification work follows PT++ §6.1 and the authors' supplement, especially §§1 and5. An independent exact finite-domain oracle now passes eight tests for RIS/NEE MIS and conversion to primary sample space. **This is a mathematical prerequisite, not a GPU implementation or a full B10 result.**

The paper's full target uses one PT reservoir over direct and indirect path lengths. Accordingly, the paper-native B10 preset must let unified PT own primary direct lighting and all indirect paths, replacing standalone DI/GI resampling and shading passes. The existing B8 short-GI/long-PT split remains a preserved control. Retaining short-GI separately while merging only direct and long-PT paths would be a hybrid adaptation, and must be labelled as such rather than called a complete reproduction of §6.1. The user-confirmed B10/B11 numbering stays unchanged.

## Primary sources

- [PT++ paper](https://cwyman.org/papers/i3d26_ReSTIRPT++.pdf), §6.1: include primary-surface NEE in the initial path tree and allow a direct path to win initial resampling.
- [Authors' supplementary document](https://research.nvidia.com/labs/rtr/publication/lin2026restirptenhanced/lin2026restirptenhanced_supplemental.pdf), §§1 and5: lobe-indexed PSS, multi-candidate NEE MIS and UCW conversion. The privately cached supplement has13pages and SHA256 `6c43cf0d8cc01d0352a85800c00477ad3179fa9d5ab78dc217dfb23408e650b5`.
- Pinned NVIDIA runtime `PT/InitialSamplingPathTracerContext.hlsli`, `PT/InitialSampling.hlsli`, `PT/HybridShift.hlsli` and the SDK shader/application bridge documentation define the integration interfaces. Presence of those interfaces does not establish application-side unification.

## Exact finite-domain prerequisite

For a common path measure, the supplemental multi-candidate MIS weights are

\[
w_{\mathrm{NEE}}(x)=\frac{M p_{\mathrm{NEE}}(x)}{M p_{\mathrm{NEE}}(x)+p_{\mathrm{BSDF}}(x)},\qquad w_{\mathrm{BSDF}}(x)=1-w_{\mathrm{NEE}}(x).
\]

The hypothetical single-sample NEE PDF used by the PSS parameterization is distinct from the RIS-selected sample's actual distribution. The path-space RIS weight converts as

\[
W_{\mathrm{PSS}}(U)=W_{\mathrm{RIS,path}}(\mathcal{X}(U))\,p_{\mathrm{NEE}}(\mathcal{X}(U)).
\]

The oracle exhaustively enumerates candidate streams and reservoir selections using exact rational arithmetic. For a three-element domain with unequal NEE/BSDF probabilities and a nonuniform RIS target, the combined expectation equals the known integral20 for candidate budgets1,2,3 and4. Separate negative controls detect omission of the PSS conversion factor and a one-sided MIS update that leaves the BSDF companion weight unchanged. Other tests cover single-candidate unit PSS weight, the RIS/source-PDF distinction and proposal/target support.

[Calculated oracle results](../../Benchmarks/development/2026-10-30-unified-ris-oracle/results.json) · [Portable implementation](../../Benchmarks/tools/unified_lighting_oracle.py)

This discrete oracle does not validate continuous area/solid-angle transformations, hybrid shift Jacobians, visibility, delta lights/lobes, media, temporal reuse or the GPU. Those are separate required gates. It is not evidence of a rendering quality gain or speedup.

## Renderer integration requirements

| Boundary | Required paper-aligned behavior | Acceptance before activation |
|---|---|---|
| Path ownership | Unified PT covers primary direct and all indirect paths; native emission/delta exceptions are enumerated explicitly | No duplicate or missing contribution when standalone DI/GI shading is disabled; retain the B8 split control |
| Initial RIS | Add primary-surface NEE to the same path-tree selection, including short direct paths | Direct-only analytic/finite-light tests, empty/occluded cases and mixed direct/indirect selection |
| RIS and BSDF MIS | Apply companion weights consistently and preserve the supplement's assumed source PDF and PSS UCW conversion | Exact finite-domain prerequisite plus GPU density/weight instrumentation; finite-area, environment and delta supports tested separately |
| Reuse and reconnection | Short and long selected paths retain correct path type, random replay state, support and Jacobians | Identity shifts, direct/glossy/indirect reconnection, motion and raw-HDR mean checks |
| Storage and scheduling | Remove redundant standalone reservoir work in the unified preset; retain only genuinely reused light-proposal preparation | Actual pass/binding receipts, total cost and memory measurement; no undocumented hidden overlap |
| Comparison | Original Convergence, Kitchen and controlled Room with the actual active algorithm label | Matched convergence/error curves, images, repeated uncapped timing and explicit bias presets |

The currently implemented duplication, pairing and queue pilots do not satisfy this entire table. B11 active CGNS remains a later stage with its own topology and normalization requirements.

Changelog:2026-10-30 — source-grounded full-path ownership target and exact supplemental RIS/PSS prerequisite; no unification renderer activation claimed.
