**Current project context (2026-10-28):** RTXPT1.9 with its original scenes is the immutable B0 baseline. B1 at `7010bb4cda80788eb13cd9ee6143eb2f52a5b6ee` applies the RTXDI3.1 runtime/API migration to the existing DI/GI path. It does not add a ReSTIR PT renderer or activate PT++/CGNS features. `External/RTXDI-SDK` remains reference-only. See [B1 results](B1_RESULTS.md) for measured scope and limitations. B2+ remain planned.

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

Discovery opened the author list and NVIDIA's RTXDI/RTXPT repositories; focused review followed author PDFs, project pages, supplements and official implementations. Several large PDFs exceeded web extraction limits. Seven focused PDFs were downloaded to private work caches and text-extracted locally; original notes retain page/section locators. Breadth access varies and is recorded per paper. Public availability is not a code license. No shader build or local GPU paper reproduction was performed.

## Accepted project decisions

RTXPT1.9 is the immutable renderer/scene baseline. B1 now applies runtime3.1 to the existing DI/GI APIs; the broader SDK remains a source reference. Keep B0's original runtime pin preserved and keep future estimator methods opt-in. Benchmark each against versioned B0/B1 identities.
