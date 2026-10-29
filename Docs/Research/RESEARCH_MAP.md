**Current project context (2026-10-29):** [Canonical B0–B10 and legacy crosswalk](VERSION_MAPPING.md) govern project labels. B0 preserves unchanged RTXPT1.9 original defaults and pins. Legacy migration `7010bb4` is not canonical B1; its native/DI/DI+GI configurations map to B3/B4/B5. The PT-only/DI+PT foundation maps to B6/B7; old-B2 checkpoint `de9fe651` is B7. The GI-off old-B3 pilot is a B7 limited-feature ablation, not B9. B8 requires valid GI/PT sharing; B9/B10 depend on it, and full remaining PT++ work belongs to B10. The SDK stays reference-only. Preserve legacy measurements/IDs; historical original-scene DI+GI rows map to B2/B5 with cap coverage unverified.

# Research map and scope

## Scope and interpretation

The author's conference/journal list is newest first. “Last 12” means ranks 1–12 as checked on 2026-10-28; “wider 20” means ranks 1–20. Other website sections (patents, courses, posters, books) are not counted. Seven user-selected papers receive full-text method/evaluation review. Other papers receive annotated breadth review with exact reading scope; this is a curated engineering review, not an exhaustive systematic survey.

## Questions and stopping conditions

| ID | Priority / dependencies | Decision | Evidence and stop condition |
|---|---|---|---|
| Q1 | High; none | What is already implemented in RTXDI 3.1? | Pin SDK/runtime and inspect active shader + host paths; distinguish helpers from active scheduling, and source inspection from runtime proof. |
| Q2 | High; Q1 | How should RTXPT 1.9 be linked and integrated? | Pin renderer; inspect its own RTXDI3.0 ABI and PT hooks, light sampling, reconstruction, caches and history ownership. End with concrete adapter responsibilities. |
| Q3 | High; Q1 | Which of seven techniques is worth attempting first? | Inspect full methods, estimator assumptions, evaluation and failure modes; identify owned interfaces, incompatibilities, implementation rights and validation needs. |
| Q4 | Medium; Q3 | Which additional recent papers change dependencies or priorities? | Catalog all20 and explicitly label full/abstract/excerpt access. Identify splatting, Area ReSTIR and GRIS prerequisites and explain deferrals. |
| Q5 | High; Q1–Q4 | How do we decide quality/performance improves? | Define raw and reconstructed comparisons, reference estimator, independent seeds, scene/motion matrix, total timings, VRAM budgets and promote/reject rules. |

## Method and access limits

The initial research-stage discovery opened the author list and NVIDIA's RTXDI/RTXPT repositories; focused review followed author PDFs, project pages, supplements and official implementations. Several large PDFs exceeded web extraction limits. Seven focused PDFs were privately cached and text-extracted; original notes retain page/section locators. Breadth access varies per paper. Public availability is not a code license. That source-review stage performed no shader build or GPU paper reproduction; later scoped renderer experiments are separately recorded in the legacy result reports and canonical crosswalk.

## Accepted project decisions

B0 preserves unchanged RTXPT1.9 defaults, renderer/dependency pins and original scenes. The legacy runtime3.1 migration source7010bb4 underlies canonical B3/B4/B5 mode configurations, not canonical B1. App-owned PT integration supplies the B6/B7 foundation; the broader SDK stays a source reference. B8 sharing requires a valid partition/MIS, and full remaining PT++ is B10 work. Keep methods opt-in, preserve legacy evidence identities and compare actual configurations through the canonical matrix rather than old labels alone.

## Canonical numbering and evidence boundary —2026-10-29

Legacy source/report labels remain intact: old B1 migration source7010bb4 maps by active mode to B3/B4/B5; old B2 DI+PT maps to B7; old B3 limited GI-off pilot is a B7 ablation, not B9. The [canonical crosswalk](VERSION_MAPPING.md) supersedes earlier planning labels. B8 sharing needs a valid partition/MIS before B9/B10 can claim it. Historical original-scene old-B0/old-B1 DI+GI rows map to B2/B5 with unverified cap coverage; do not pool them with cap-verified throughput. Current comparisons require actual modes, cap receipts, original-scene coverage and separate simulated-time/throughput labels.
